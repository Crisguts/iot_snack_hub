# Raspberry Pi Setup Guide - Smart Store IoT System

Quick guide to configure the Smart Store system on Raspberry Pi for the first time.

## Prerequisites

### Hardware Required
- **Raspberry Pi 4** (2GB+ RAM recommended)
- **ESP32 Development Boards** (2x with DHT11 sensors)
- **RFID Reader CF600** (USB connection)
- **USB Barcode Scanner**
- **GPIO Components**: LEDs, Buzzer, DC Motor + L298N Driver
- **Power Supply** - 5V/3A for Raspberry Pi
- **Network Connection** - WiFi or Ethernet

---

## Step 1: System Setup

### 1.1 Update System
```bash
sudo apt update && sudo apt upgrade -y
```

### 1.2 Install Dependencies
```bash
# Python and GPIO
sudo apt install python3-pip python3-venv python3-rpi.gpio -y

# MQTT Broker
sudo apt install mosquitto mosquitto-clients -y
```

---

## Step 2: Install Project

### 2.1 Setup Virtual Environment
```bash
cd ~/smart-store
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Step 3: Hardware Connection

### 3.1 GPIO Components
Wire your LEDs, buzzer, and motor according to your setup. The code uses these GPIO pins:
- **LEDs**: GPIO 20, 21
- **Buzzer**: GPIO 16
- **Motor**: GPIO 17, 27, 22

### 3.2 USB Devices
- Plug in **RFID Reader** (USB)
- Plug in **Barcode Scanner** (USB)

---

## Step 4: Flash ESP32 Boards

### 4.1 Get Pi IP Address
**IMPORTANT:** Pi IP changes on different networks.

Find current IP:
```bash
hostname -I
# Example: 192.168.1.50
```

### 4.2 Configure and Upload
ESP32 firmware is in `esp32/` folder:
- `esp32/Frig1/Frig1.ino`
- `esp32/Frig2/Frig2.ino`

Before uploading:
1. Open `.ino` file in Arduino IDE
2. Update WiFi credentials (SSID and password)
3. Update MQTT broker IP to Pi's IP from Step 4.1
   ```cpp
   const char* mqtt_server = "192.168.1.50";  // Use Pi's IP
   ```
4. Upload to ESP32 board
5. Repeat for second ESP32

### 4.3 Demo with Multiple Networks

**Option A: Single Pi**
1. Connect Pi to hotspot
2. Find IP: `hostname -I`
3. Update ESP32 code with new IP
4. Re-flash both ESP32 boards
5. Connect ESP32s to same hotspot

**Option B: Two Pi Setup**

Use two Pis on different networks sharing one database.

**Pi #1 (MQTT Server):**
- Connected to main WiFi
- Runs MQTT broker + app
- ESP32s connect here
- Saves sensor data to Supabase
- `.env` settings:
  ```bash
  MOCK_MODE=False
  MQTT_BROKER=localhost
  MQTT_AUTO_START=true
  ```

**Pi #2 (Demo Station):**
- Connected to hotspot (for email)
- Runs app only
- Reads from Supabase
- `.env` settings:
  ```bash
  MOCK_MODE=False
  SCANNER_MOCK_MODE=False
  MQTT_AUTO_START=false
  EMAIL_ENABLED=True
  ```

Both Pis use same Supabase credentials. Pi #1 writes sensor data, Pi #2 reads it.

**ESP32 Configuration:**
```cpp
const char* ssid = "Main_WiFi_Name";
const char* mqtt_server = "192.168.X.X";  // Pi #1 IP address
```

---

## Step 5: Configure Environment

### 5.1 Edit .env File
```bash
cd ~/smart-store
nano .env
```

### 5.2 Update Key Settings

**Single Pi Setup:**
```bash
MOCK_MODE=False
SCANNER_MOCK_MODE=False
MQTT_AUTO_START=true

SUPABASE_URL=https://pkcgpxxxtxgmqasusrrl.supabase.co
SUPABASE_KEY=your-key-here

MQTT_BROKER=localhost
MQTT_PORT=1883

RFID_SERIAL_PORT=/dev/ttyUSB0

EMAIL_ENABLED=True
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-gmail-app-password
```

**Two Pi Setup:**

*Pi #1 (MQTT Server):*
```bash
MOCK_MODE=False
SCANNER_MOCK_MODE=True
MQTT_AUTO_START=true

SUPABASE_URL=https://pkcgpxxxtxgmqasusrrl.supabase.co
SUPABASE_KEY=your-shared-key

MQTT_BROKER=localhost
EMAIL_ENABLED=False
```

*Pi #2 (Demo Station):*
```bash
MOCK_MODE=False
SCANNER_MOCK_MODE=False
MQTT_AUTO_START=false

SUPABASE_URL=https://pkcgpxxxtxgmqasusrrl.supabase.co
SUPABASE_KEY=your-shared-key

RFID_SERIAL_PORT=/dev/ttyUSB0

EMAIL_ENABLED=True
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-gmail-app-password
```

> **Note:** Dashboard uses mock data by default. Update `blueprints/dashboard/routes.py` to read from database when using real hardware. MQTT service saves to Supabase automatically.

### 5.3 Find RFID USB Port
```bash
ls /dev/ttyUSB*  # Usually /dev/ttyUSB0 or /dev/ttyUSB1
```

---

## Step 6: Start MQTT Broker

```bash
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
```

Test:
```bash
mosquitto_sub -h localhost -t "Frig1" -t "Frig2"
# Should see ESP32 messages
```

---

## Step 7: Run Application

```bash
cd ~/smart-store
source venv/bin/activate
python3 app.py
```

Access at: `http://PI_IP:5000`

Find Pi IP:
```bash
hostname -I
```

---

## Auto-Start on Boot (Optional)

Create service:
```bash
sudo nano /etc/systemd/system/smartstore.service
```

Add:
```ini
[Unit]
Description=Smart Store Application
After=network.target mosquitto.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/smart-store
Environment="PATH=/home/pi/smart-store/venv/bin"
ExecStart=/home/pi/smart-store/venv/bin/python3 app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl daemon-reload
sudo systemctl enable smartstore.service
sudo systemctl start smartstore.service
```

---

## Quick Tests

✅ **MQTT**: Run `mosquitto_sub -h localhost -t "#"` - should see ESP32 data  
✅ **RFID**: Login → Self-Checkout → Disable test mode → Scan tag  
✅ **Barcode**: Scan product  
✅ **GPIO**: Dashboard → Toggle fan/buzzer  
✅ **Dashboard**: Check temps from ESP32  

---

## Troubleshooting

**RFID not working:**
```bash
ls /dev/ttyUSB*
sudo chmod 666 /dev/ttyUSB0
```

**ESP32 not connecting:**
- Check WiFi credentials in .ino files
- Verify Pi IP address
- Ensure same network

**Permission errors:**
```bash
sudo usermod -a -G gpio,dialout $USER
# Logout and login
```

**App won't start:**
```bash
source venv/bin/activate
python3 app.py  # Check errors
```

**Database connection failed:**
- Verify Supabase credentials in .env
- Test internet: `ping google.com`

---

## Login

- **Admin**: `admin` / `admin123`
- **Customer**: Create at `/store/home`

---

**Done.** 🎉

---

## Auto-Start on Boot (Optional)

Create service file:
```bash
sudo nano /etc/systemd/system/smartstore.service
```

Add:
```ini
[Unit]
Description=Smart Store Application
After=network.target mosquitto.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/smart-store
Environment="PATH=/home/pi/smart-store/venv/bin"
ExecStart=/home/pi/smart-store/venv/bin/python3 app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl daemon-reload
sudo systemctl enable smartstore.service
sudo systemctl start smartstore.service
```

---

## Quick Test Checklist

✅ **MQTT**: Run `mosquitto_sub -h localhost -t "#"` - should see ESP32 messages  
✅ **RFID**: Login → Self-Checkout → Disable test mode → Scan tag  
✅ **Barcode**: Scan product in checkout  
✅ **GPIO**: Dashboard → Toggle fan/buzzer  
✅ **Dashboard**: Should show real temps from ESP32  

---

## Troubleshooting

**RFID not working?**
```bash
ls /dev/ttyUSB*           # Find the port
sudo chmod 666 /dev/ttyUSB0  # Fix permissions
```

**ESP32 not connecting?**
- Check WiFi credentials in .ino files
- Verify Pi IP address is correct
- Make sure ESP32 and Pi are on same network

**Permission denied errors?**
```bash
sudo usermod -a -G gpio,dialout $USER
# Then logout and login again
```

**App won't start?**
```bash
source venv/bin/activate  # Make sure venv is active
python3 app.py           # Check error messages
```

---

## Login Credentials

- **Admin**: `admin` / `admin123`
- **Customer**: Create account at `/store/home`

---

**That's it! Your Smart Store is ready.** 🎉
