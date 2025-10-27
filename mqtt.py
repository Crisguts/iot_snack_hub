import paho.mqtt.client as mqtt
import json
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv
import os

# Import email system for temperature alerts
try:
    from emailSystem.integrated_email import email_system
    EMAIL_ALERTS_ENABLED = True
    print("✅ Email alerts system loaded for MQTT monitoring")
except ImportError as e:
    EMAIL_ALERTS_ENABLED = False
    print(f"⚠️  Email alerts disabled for MQTT: {e}")

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# MQTT Configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPICS = ["Frig1", "Frig2"]

latest_readings = {
    "Frig1": {"temperature": None, "humidity": None, "timestamp":None},
    "Frig2": {"temperature": None, "humidity": None, "timestamp":None},
}

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to the MQTT broker successfully")
        for topic in MQTT_TOPICS:
            client.subscribe(topic)
            print("Subscribed to topic: " + topic)
    else:
        print("Failed to connect to MQTT broker. RC =" + rc)


def on_message(client, userdata, msg):
    try:
        topic = msg.topic
        payload = msg.payload.decode()
        print("Message Received:", payload)

        data = json.loads(payload)

        temperature = data.get("temperature")
        humidity = data.get("humidity")

        fridge_id_map = {
            "Frig1": 1,
            "Frig2": 2
        }

        fridge_id = fridge_id_map.get(topic)

        if fridge_id is None:
            print("Unknown fridge for topic:", topic)
            return

        latest_readings[topic] = {
            "temperature": temperature,
            "humidity": humidity,
            "fridge_id": fridge_id,
            "timestamp": datetime.now().isoformat()
        }

        save_to_db(fridge_id, temperature, humidity)
        
        # Check temperature alerts
        temperature_alert(fridge_id, temperature)

    except json.JSONDecodeError:
        print("Invalid JSON Error. payload:", msg.payload)
    except Exception as e:
        print("Error processing message. payload:", getattr(msg, "payload", None), "error:", repr(e))


def save_to_db(fridge_id, temperature, humidity):
    try:
        # Ensure numeric types (avoid inserting strings)
        temp_val = float(temperature) if temperature is not None else None
        hum_val = float(humidity) if humidity is not None else None

        data = {
            "fridge_id": fridge_id,
            "temperature": temp_val,
            "humidity": hum_val,
            # use created_at if your table expects that column, or remove it to let DB set default
            "created_at": datetime.now().isoformat()
        }

        print("Inserting to DB:", data)
        response = supabase.table("temperature_readings").insert(data).execute()

        # Inspect response fully
        print("Supabase insert response:", getattr(response, "status_code", None), getattr(response, "data", None), getattr(response, "error", None))

        # Basic success check
        if getattr(response, "data", None):
            print("Successfully saved to db. row:", response.data)
            return True
        # some clients return no data but still succeed
        if getattr(response, "status_code", None) in (200, 201, 204):
            print("Insert reported success (status_code).")
            return True

        print("Insert may have failed. Check dashboard and Supabase logs.")
        return False

    except Exception as e:
        print("Did not save to db. error:", repr(e))
        return False
    
# Temperature Alert System
def temperature_alert(fridge_id, temperature):
    """
    Check temperature against threshold and send email alert if exceeded
    
    Args:
        fridge_id (int): ID of the refrigerator (1 or 2)
        temperature (float): Current temperature reading
    """
    try:
        # Get threshold and fridge info from database
        response = supabase.table("refrigerators")\
            .select("temperature_threshold, name")\
            .eq("fridge_id", fridge_id)\
            .execute()
        
        if response.data and len(response.data) > 0:
            threshold = response.data[0].get("temperature_threshold", 25.0)
            fridge_name = response.data[0].get("name", f"Refrigerator {fridge_id}")
            
            # Check if temperature exceeds threshold
            if temperature > threshold:
                print(f"🚨 ALERT: {fridge_name} (ID: {fridge_id}) temperature ({temperature}°C) exceeds threshold ({threshold}°C)")
                
                # Send email alert if enabled
                if EMAIL_ALERTS_ENABLED:
                    try:
                        success = send_temperature_email_alert(fridge_id, temperature, threshold, fridge_name)
                        if success:
                            print(f"📧 Temperature alert email sent for {fridge_name}")
                        else:
                            print(f"⚠️  Failed to send email alert for {fridge_name}")
                    except Exception as email_error:
                        print(f"❌ Email alert error for {fridge_name}: {email_error}")
                else:
                    print(f"📧 Email alerts disabled - would send alert for {fridge_name}")
                    
            else:
                print(f"✅ {fridge_name} temperature ({temperature}°C) within threshold ({threshold}°C)")
                
        else:
            print(f"⚠️  No threshold configuration found for fridge {fridge_id}")
            # Use default threshold if no configuration found
            default_threshold = 25.0
            if temperature > default_threshold:
                print(f"🚨 ALERT: Fridge {fridge_id} temperature ({temperature}°C) exceeds default threshold ({default_threshold}°C)")
                
                if EMAIL_ALERTS_ENABLED:
                    send_temperature_email_alert(fridge_id, temperature, default_threshold, f"Refrigerator {fridge_id}")
                    
    except Exception as e:
        print(f"❌ Error checking temperature threshold for fridge {fridge_id}: {e}")

def send_temperature_email_alert(fridge_id, current_temp, threshold, fridge_name):
    """
    Send temperature alert email for specific fridge using integrated email system
    """
    if not EMAIL_ALERTS_ENABLED:
        print("❌ Email alerts disabled")
        return False
    
    try:
        # Get email credentials
        login = os.getenv("EMAIL_LOGIN")
        password = os.getenv("EMAIL_APP_PASSWORD")
        recipient = os.getenv("EMAIL_RECIPIENT", login)
        
        if not login or not password:
            print("❌ Email credentials not configured")
            return False
        
        # Create alert email
        subject = f"TEMPERATURE ALERT - {fridge_name}"
        body = f"""TEMPERATURE ALERT!

{fridge_name} has exceeded the temperature threshold:

Current Temperature: {current_temp}°C
Threshold Setting: {threshold}°C
Alert Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

The temperature is too high! Would you like to turn on the fan?

Reply 'YES' to this email to automatically activate the fan for {fridge_name}.
Reply 'NO' to take no action.

This is an automated alert from your IoT Smart Store monitoring system.
"""
        
        # Use integrated email system
        import smtplib
        import ssl
        
        email_message = f"Subject: {subject}\nTo: {recipient}\nFrom: {login}\n\n{body}"
        
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(login, password)
            server.sendmail(login, recipient, email_message.encode('utf-8'))
            
        print(f"📧 Temperature alert email sent for {fridge_name}")
        
        # Start email monitoring if not already running
        if not email_system.monitoring:
            email_system.start_monitoring()
            print("🔄 Started email monitoring for replies")
            
        return True
        
    except Exception as e:
        print(f"❌ Failed to send temperature alert email: {e}")
        return False
    
def on_disconnect(client, userdata, rc):
        if(rc != 0):
            print("MQTT server got disconnected")

def main():
    print("Starting MQTT Listener for IoT Temperature Monitoring")
    print()
    
    # Create MQTT client
    client = mqtt.Client()
    
    # Attach callback functions
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    
    # Connect to MQTT broker
    try:
        print(f"Connecting to MQTT Broker at {MQTT_BROKER}:{MQTT_PORT}...")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        # Start the loop to process MQTT messages
        print("MQTT Listener is running. Press Ctrl+C to stop.\n")
        client.loop_forever()
        
    except KeyboardInterrupt:
        print("\n\nShutting down MQTT Listener...")
        client.disconnect()
        print("MQTT Listener stopped.")
        
    except Exception as e:
        print(f"Error connecting to MQTT Broker: {e}")

if __name__ == "__main__":
    main()