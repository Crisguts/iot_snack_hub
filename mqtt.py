import paho.mqtt.client as mqtt
import json
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv
import os

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
        print("Message Received")

        data = json.loads(payload)

        temperature = data.get("temperature")
        humidity = data.get("humidity")

        fridge_id_map = {
            "Frig1": 1,
            "Frig2": 2
        }

        fridge_id = fridge_id_map.get(topic)

        if(fridge_id is None):
            print ("Unknown fridge")
            return
        
        latest_readings[topic] = {
            "temperature": temperature,
            "humidity": humidity,
            "fridge_id": fridge_id,
            "timestamp": datetime.now().isoformat()
        }

        save_to_db(fridge_id, temperature, humidity)



    except json.JSONDecodeError:
        print("Invalid JSON Error: "+ payload)
    except Exception as e:
        print("Error processing message "+ payload)

# -----------------Save to db
def save_to_db(fridge_id, temperature, humidity):
    try:
        data = {
            "fridge_id": fridge_id,
            "temperature": temperature,
            "humidity": humidity,
            "timestamp": datetime.now().isoformat()
        }

        response = supabase.table("temperature_readings").insert(data).execute()
        print("Successfully saved to db.")
        return True
    except Exception as e:
        print("Did not save to db")
        return False
    
# ------------Checking the fridge temperature
def temperature_alert(fridge_id, temperature):
    try:
        response = supabase.table("refrigerators").select("temperature_threshold").eq("fridge_id", fridge_id).execute()

        response = supabase.table("refrigerators")\
            .select("temperature_threshold, name")\
            .eq("fridge_id", fridge_id)\
            .execute()
        
        if response.data and len(response.data) > 0:
            threshold = response.data[0].get("temperature_threshold", 25.0)
            fridge_name = response.data[0].get("name", f"Fridge {fridge_id}")
            
            if temperature > threshold:
                print(f"ALERT: {fridge_name} (ID: {fridge_id}) temperature ({temperature}°C) exceeds threshold ({threshold}°C)")
                # TODO: Send email alert
                # use code from lab
    except Exception as e:
        print("Error Checking the threshold. Error: " +  e)
    
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