# Smart Store IoT Project
**Phase 2 & 3 Complete Implementation**

IoT-enabled smart store system with self-checkout, RFID/barcode scanning, temperature monitoring, and customer management.

## 🌟 Features

### Phase 2 - IoT Dashboard & Monitoring
- **Real-time Temperature Monitoring**: DHT11 sensors on 2 ESP32 boards
- **MQTT Communication**: Mosquitto broker on Raspberry Pi
- **Alert System**: Email alerts when temperature exceeds threshold
- **Remote Fan Control**: Email-reply activation ("YES" to turn on fan)
- **Visual Dashboard**: Real-time gauges and historical charts

### Phase 3 - Smart Self-Checkout
- **Product Management**: Full CRUD with UPC/EPC codes
- **Inventory Tracking**: Reception history and stock levels
- **Barcode Scanner**: USB scanner integration (acts as keyboard)
- **RFID Reader**: CF600 UHF desktop reader support
- **Self-Checkout**: Real-time cart updates, payment simulation
- **Customer Accounts**: Membership numbers, points system, purchase history
- **Receipt Generation**: Automatic email receipts with point tracking

## 🗂️ Project Structure

```
smart-store/
├── app.py                    # Main Flask application
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (create this!)
├── .gitignore               # Git ignore rules
├── blueprints/              # Modular routes
│   ├── auth/                # Authentication (admin/customer)
│   ├── client/              # Customer management (admin)
│   ├── dashboard/           # Fridge monitoring (admin)
│   ├── store/               # Shopping & cart (customer)
│   └── products/            # Product management (admin)
├── services/                # Business logic
│   ├── db_service.py        # Supabase database operations
│   ├── email_service.py     # SMTP/IMAP email system
│   ├── gpio_service.py      # Raspberry Pi GPIO control
│   ├── mqtt_client.py       # MQTT subscriber for sensors
│   └── scanner_service.py   # Barcode/RFID scanner
├── static/                  # Frontend assets
│   ├── css/styles.css
│   └── js/                  # JavaScript modules
├── templates/               # Jinja2 HTML templates
└── esp32/                   # ESP32 sensor code (to be added)
```

## 📊 Database Schema

### Supabase Tables (PostgreSQL)

#### 1. customers
```sql
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone_num VARCHAR(20),
    date_of_birth DATE,
    membership_number VARCHAR(50) UNIQUE,
    points INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 2. products
```sql
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    price DECIMAL(10, 2) NOT NULL,
    upc VARCHAR(13) UNIQUE NOT NULL,
    epc VARCHAR(24) UNIQUE NOT NULL,
    producer VARCHAR(255),
    image_url TEXT,
    total_quantity INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 3. inventory_receptions
```sql
CREATE TABLE inventory_receptions (
    reception_id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(product_id) ON DELETE CASCADE,
    quantity_received INTEGER NOT NULL,
    date_received TIMESTAMP DEFAULT NOW()
);
```

#### 4. purchases
```sql
CREATE TABLE purchases (
    purchase_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    total_amount DECIMAL(10, 2) NOT NULL,
    points_earned INTEGER DEFAULT 0,
    purchase_date TIMESTAMP DEFAULT NOW()
);
```

#### 5. purchase_items
```sql
CREATE TABLE purchase_items (
    item_id SERIAL PRIMARY KEY,
    purchase_id INTEGER REFERENCES purchases(purchase_id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(product_id),
    quantity INTEGER NOT NULL,
    price_at_purchase DECIMAL(10, 2) NOT NULL
);
```

#### 6. refrigerators
```sql
CREATE TABLE refrigerators (
    fridge_id INTEGER PRIMARY KEY,
    name VARCHAR(100),
    temperature_threshold DECIMAL(5, 2) DEFAULT 25.0
);
```

#### 7. temperature_readings
```sql
CREATE TABLE temperature_readings (
    reading_id SERIAL PRIMARY KEY,
    fridge_id INTEGER REFERENCES refrigerators(fridge_id),
    temperature DECIMAL(5, 2),
    humidity DECIMAL(5, 2),
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 🚀 Setup Instructions

### 1. Prerequisites
- Python 3.8+
- Raspberry Pi (for hardware)
- Supabase account (free tier)
- Gmail account (for email alerts)

### 2. Clone & Install
```bash
cd /path/to/project
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

### 3. Environment Variables
Create `.env` file in project root:

```env
# Flask
SECRET_KEY=your_super_secret_key_change_this

# Supabase
SUPABASE_URL=https://yourproject.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# Email (Gmail)
EMAIL_LOGIN=your-email@gmail.com
EMAIL_APP_PASSWORD=your_gmail_app_password
EMAIL_RECIPIENT=alert-recipient@gmail.com

# MQTT (default for local Raspberry Pi)
MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_TOPICS=Frig1,Frig2

# Scanner (for development on Mac)
SCANNER_MOCK_MODE=True
MOCK_MODE=True

# RFID (when hardware connected)
RFID_PORT=/dev/ttyAMA10
RFID_BAUD=9600
```

### 4. Database Setup
1. Create Supabase project at https://supabase.com
2. Run SQL schema above in Supabase SQL Editor
3. Insert initial fridge data:
```sql
INSERT INTO refrigerators (fridge_id, name, temperature_threshold) VALUES
(1, 'Refrigerator 1', 5.0),
(2, 'Refrigerator 2', 6.0);
```

### 5. Run Application
```bash
python3 app.py
```

Visit: http://localhost:8080

## 👥 User Accounts

### Admin Access
- **Username**: `admin`
- **Password**: `admin123`
- **Access**: Dashboard, Product Management, Customer Management

### Customer Access
- **Create Account**: Sign up at http://localhost:8080/auth/signup
- **Access**: Store, Cart, Self-Checkout, Purchase History

## 🛒 Self-Checkout Flow

1. **Login** as customer
2. Navigate to **Self-Checkout**
3. **Scan products**:
   - USB Barcode Scanner: Focus on "Barcode Input" field, scan automatically
   - RFID: Enter tag manually or use CF600 reader
4. Products appear in cart real-time
5. **Review cart**, adjust quantities
6. **Confirm Purchase** → Receipt emailed + points added

## 🔧 Hardware Integration

### ESP32 Setup (Phase 2)
- Flash ESP32 with DHT11 sensor code
- Connect to WiFi
- Publish to MQTT topics: `Frig1`, `Frig2`
- JSON payload: `{"temperature": 4.5, "humidity": 45}`

### Raspberry Pi GPIO
- **Blue LED** (Pin 21): Customer add success
- **Red LED** (Pin 20): Errors
- **Buzzer** (Pin 16): Alert sound
- **Motor** (Pins 17, 27, 22): Fan control

### Scanners
- **USB Barcode**: Plug & play (acts as keyboard)
- **RFID CF600**: Connect via serial (`/dev/ttyAMA10`)

## 🧪 Testing Without Hardware

App runs in **mock mode** on Mac/Windows:
- GPIO operations print to console
- MQTT uses mock data
- Scanner accepts manual input
- All features testable via UI

## 📝 Key Endpoints

### Customer Routes
- `GET /store/` - Product catalog
- `GET /store/cart` - View cart
- `GET /store/checkout` - Self-checkout
- `POST /store/api/scan` - Scan product
- `POST /store/api/purchase` - Complete purchase
- `GET /store/account` - Purchase history

### Admin Routes
- `GET /dashboard/` - Fridge monitoring
- `GET /products/` - Product management
- `GET /client/` - Customer management
- `POST /fan/<id>` - Toggle fan

## 🎨 Customization

### Add Sample Products
```python
# In services/db_service.py or Supabase SQL Editor
INSERT INTO products (name, category, price, upc, epc, producer, total_quantity) VALUES
('Coca-Cola 500ml', 'Beverage', 1.99, '012000001234', 'E200001234567890ABCD', 'Coca-Cola Company', 50),
('Snickers Bar', 'Snack', 1.49, '028400005678', 'E200009876543210DCBA', 'Mars Inc.', 100);
```

### Customize Points System
Edit `blueprints/store/routes.py`:
```python
def calculate_points(total_amount):
    return int(total_amount * 2)  # 2 points per dollar
```

## 🐛 Troubleshooting

### Database Connection Failed
- Check `SUPABASE_URL` and `SUPABASE_KEY` in `.env`
- Verify network connection to Supabase

### Email Alerts Not Working
- Enable "Less secure app access" or use App Password for Gmail
- Check `EMAIL_APP_PASSWORD` format

### MQTT Not Connecting
- Ensure Mosquitto broker running: `sudo systemctl status mosquitto`
- Check `MQTT_BROKER` IP address

### Scanner Not Working
- USB Barcode: Focus input field, check USB connection
- RFID: Verify serial port in `RFID_PORT`

## 📄 License

Educational project for IoT Course (420-521-VA) at Vanier College.

