"""
services/mqtt_client.py
Clean, thread-safe MQTT client service.

Responsibilities:
- connect to broker, subscribe to topics (MQTT_TOPICS)
- parse JSON payloads from ESP32s (temperature, humidity)
- save readings to DB via services.db_service.supabase
- maintain an in-memory latest_readings cache (thread-safe)
- call services.email_system to send alerts when thresholds exceeded
- expose helper getters for other blueprints to read latest/historical data
"""

import os
import json
import threading
import time
from datetime import datetime

from unittest.mock import MagicMock
try:
    import paho.mqtt.client as mqtt
except Exception as e:
    print(f"⚠️ MQTT mock loaded: {e}")
    mqtt = MagicMock()

# Import app services
from services.db_service import supabase
from services import email_service

# CONFIG from environment (use .env)
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPICS = os.getenv("MQTT_TOPICS", "Frig1,Frig2").split(",")

# Map topic name to fridge id
FRIDGE_TOPIC_MAP = {t: idx + 1 for idx, t in enumerate(MQTT_TOPICS)}

# thread-safe latest cache
_latest_lock = threading.Lock()
latest_readings = {topic: {"temperature": None, "humidity": None, "timestamp": None, "fridge_id": FRIDGE_TOPIC_MAP.get(topic)} for topic in MQTT_TOPICS}

# MQTT client instance and thread control
_client = None
_thread = None
_running = threading.Event()


def get_latest_readings():
    """Return a shallow copy of latest_readings (safe to call from other threads)."""
    with _latest_lock:
        return {k: v.copy() for k, v in latest_readings.items()}


def get_latest_for_fridge(fridge_id):
    with _latest_lock:
        for topic, data in latest_readings.items():
            if data.get("fridge_id") == int(fridge_id):
                return data.copy()
    return None


def get_historical(fridge_id, limit=100):
    """
    Returns recent rows from temperature_readings table for fridge_id.
    NOTE: This does a DB query; caller should handle request performance.
    """
    try:
        resp = supabase.table("temperature_readings").select("*").eq("fridge_id", int(fridge_id)).order("created_at", desc=True).limit(limit).execute()
        return resp.data or []
    except Exception as e:
        print("mqtt_client.get_historical DB error:", e)
        return []


def _save_to_db(fridge_id, temperature, humidity):
    """Insert reading to Supabase. Returns True on likely success, False otherwise."""
    try:
        temp_val = float(temperature) if temperature is not None else None
        hum_val = float(humidity) if humidity is not None else None
    except (TypeError, ValueError):
        print("mqtt_client._save_to_db: non-numeric temperature/humidity", temperature, humidity)
        return False

    payload = {
        "fridge_id": int(fridge_id),
        "temperature": temp_val,
        "humidity": hum_val,
        "created_at": datetime.utcnow().isoformat()
    }

    try:
        resp = supabase.table("temperature_readings").insert(payload).execute()
        # best-effort success check
        if getattr(resp, "data", None):
            return True
        if getattr(resp, "status_code", None) in (200, 201, 204):
            return True
        print("mqtt_client._save_to_db: insert may have failed: ", getattr(resp, "error", None), getattr(resp, "data", None))
        return False
    except Exception as e:
        print("mqtt_client._save_to_db exception:", e)
        return False


def _check_threshold_and_alert(fridge_id, temperature):
    """
    Query refrigerators table for threshold and send email alert if exceeded.
    """
    try:
        resp = supabase.table("refrigerators").select("temperature_threshold, name").eq("fridge_id", int(fridge_id)).limit(1).execute()
        data = (resp.data or [])
        if data:
            cfg = data[0]
            threshold = float(cfg.get("temperature_threshold", 25.0))
            fridge_name = cfg.get("name") or f"Refrigerator {fridge_id}"
        else:
            threshold = 25.0
            fridge_name = f"Refrigerator {fridge_id}"

        if temperature is None:
            return

        try:
            temp_val = float(temperature)
        except (TypeError, ValueError):
            print(f"mqtt_client: invalid temperature value: {temperature}")
            return

        if temp_val > threshold:
            print(f"mqtt_client: 🚨 ALERT {fridge_name} temp {temp_val}°C > {threshold}°C")
            try:
                # Send alert via email service
                if hasattr(email_service, "send_temperature_alert"):
                    ok = email_service.send_temperature_alert(
                        fridge_id=int(fridge_id), 
                        current_temp=temp_val, 
                        threshold=threshold, 
                        fridge_name=fridge_name
                    )
                    if ok:
                        print(f"mqtt_client: ✅ Email alert sent for {fridge_name}")
                        # Ensure monitoring thread in email system is running to capture replies
                        if hasattr(email_service, "start_monitoring"):
                            try:
                                email_service.start_monitoring()
                            except Exception as mon_err:
                                print(f"mqtt_client: email monitoring already running or failed: {mon_err}")
                    else:
                        print(f"mqtt_client: ❌ Email alert failed to send for {fridge_name}")
                else:
                    print("mqtt_client: ⚠️ email_service.send_temperature_alert not implemented")
            except Exception as e:
                print(f"mqtt_client: ❌ Error sending alert: {e}")
        else:
            print(f"mqtt_client: ✅ {fridge_name} temp {temp_val}°C within threshold {threshold}°C")
    except Exception as e:
        print(f"mqtt_client: ❌ Threshold check error: {e}")


def _on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("mqtt_client connected to broker")
        for topic in MQTT_TOPICS:
            try:
                client.subscribe(topic)
                print("mqtt_client subscribed to", topic)
            except Exception as e:
                print("mqtt_client subscribe error for", topic, e)
    else:
        print("mqtt_client failed to connect. rc=", rc)


def _on_disconnect(client, userdata, rc):
    print("mqtt_client disconnected, rc=", rc)


def _on_message(client, userdata, msg):
    try:
        topic = msg.topic
        payload = msg.payload.decode("utf-8")
        # print for debugging
        print("mqtt_client message:", topic, payload)

        # parse payload as JSON
        data = json.loads(payload)

        temperature = data.get("temperature")
        humidity = data.get("humidity")

        fridge_id = FRIDGE_TOPIC_MAP.get(topic) or data.get("fridge_id")
        if fridge_id is None:
            print("mqtt_client: unknown fridge for topic", topic)
            return

        # update latest cache (thread-safe)
        with _latest_lock:
            latest_readings[topic] = {
                "temperature": temperature,
                "humidity": humidity,
                "timestamp": datetime.utcnow().isoformat(),
                "fridge_id": fridge_id
            }

        # persist to DB (non-blocking optional)
        saved = _save_to_db(fridge_id, temperature, humidity)
        if not saved:
            print("mqtt_client: warning: failed to save reading to DB")

        # check threshold and possibly send email
        _check_threshold_and_alert(fridge_id, temperature)

    except json.JSONDecodeError:
        print("mqtt_client: payload is not valid JSON:", getattr(msg, "payload", None))
    except Exception as e:
        print("mqtt_client: unexpected error handling message:", e)


def start_client(loop_forever=False):
    """
    Start the MQTT client in the current thread.
    If loop_forever is False, it returns after starting loop_start() (background).
    """
    global _client
    if _client is not None:
        print("mqtt_client: already running")
        return

    _client = mqtt.Client()
    _client.on_connect = _on_connect
    _client.on_message = _on_message
    _client.on_disconnect = _on_disconnect

    try:
        _client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    except Exception as e:
        print("mqtt_client connect error:", e)
        _client = None
        return

    if loop_forever:
        # blocking call
        _client.loop_forever()
    else:
        # non-blocking background loop
        _client.loop_start()
        print("mqtt_client: started (background loop)")

    _running.set()


def stop_client():
    global _client
    if _client:
        try:
            _client.loop_stop()
            _client.disconnect()
        except Exception:
            pass
    _client = None
    _running.clear()
    print("mqtt_client: stopped")


def start_in_thread():
    """Start the MQTT client in a daemon thread (call from app startup)."""
    global _thread
    if _thread and _thread.is_alive():
        print("mqtt_client: thread already running")
        return
    _thread = threading.Thread(target=start_client, kwargs={"loop_forever": False}, daemon=True)
    _thread.start()
    # small sleep to give client time to connect in many environments
    time.sleep(0.2)
    print("mqtt_client: background thread started")


# Module initialization: start MQTT if configured
if os.getenv("MQTT_AUTO_START", "false").lower() in ("1", "true", "yes"):
    start_in_thread()
