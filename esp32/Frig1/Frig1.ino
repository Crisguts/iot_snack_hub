#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>

// WiFi Configuration - UPDATE THESE!
const char* ssid = "iotvanier";           // Your WiFi network name
const char* password = "14730078";   // Your WiFi password

// MQTT Configuration - UPDATE RASPBERRY PI IP!
const char* mqtt_server = "192.168.0.193";     // Your Raspberry Pi IP address
const int mqtt_port = 1883;
const char* mqtt_topic = "Frig1";              // MQTT topic name

// DHT11 Configuration
#define DHTPIN 14          // GPIO pin connected to DHT11
#define DHTTYPE DHT11     // DHT11 sensor type

// Create instances
WiFiClient espClient;
PubSubClient client(espClient);
DHT dht(DHTPIN, DHTTYPE);

// Variables
unsigned long lastMsg = 0;
const long interval = 5000;  // Send data every 5 seconds

void setup() {
  Serial.begin(115200);
  
  // Initialize DHT sensor
  dht.begin();
  Serial.println("DHT11 sensor initialized");
  
  // Connect to WiFi
  setup_wifi();
  
  // Configure MQTT
  client.setServer(mqtt_server, mqtt_port);
  
  Serial.println("Setup complete!");
}

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  
  // Wait for connection
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println();
  Serial.println("WiFi connected!");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  // Loop until we're reconnected to MQTT
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    
    // Create a random client ID
    String clientId = "ESP32-Frig1-";
    clientId += String(random(0xffff), HEX);
    
    // Attempt to connect
    if (client.connect(clientId.c_str())) {
      Serial.println("connected!");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" trying again in 5 seconds");
      delay(5000);
    }
  }
}

void loop() {
  // Ensure MQTT connection
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  
  // Send sensor data every 'interval' milliseconds
  unsigned long now = millis();
  if (now - lastMsg > interval) {
    lastMsg = now;
    
    // Read sensor data
    float humidity = dht.readHumidity();
    float temperature = dht.readTemperature();
    
    // Check if readings are valid
    if (isnan(humidity) || isnan(temperature)) {
      Serial.println("Failed to read from DHT sensor!");
      return;
    }
    
    // Create JSON message
   String message = "{";
   message += "\"temperature\":" + String(temperature, 1) + ",";
   message += "\"humidity\":" + String(humidity, 1) + ",";
   message += "\"fridge\":\"Frig1\",";
   message += "\"timestamp\":" + String(millis());
   message += "}";

    
    // Publish to MQTT
    Serial.print("Publishing message: ");
    Serial.println(message);
    
    client.publish(mqtt_topic, message.c_str());
    
    // Also print to Serial Monitor
    Serial.print("Temperature: ");
    Serial.print(temperature);
    Serial.print("°C | Humidity: ");
    Serial.print(humidity);
    Serial.println("%");
  }
}