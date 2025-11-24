# Smart Store IoT

Automated store with self-checkout, RFID/barcode scanning, temperature monitoring, and customer management.

## Features

**IoT Monitoring**
- Temperature sensors (ESP32 + DHT11)
- MQTT communication
- Email alerts with fan control
- Real-time dashboard with charts

**Self-Checkout**
- USB barcode + RFID scanner support
- Auto-detect scanner ports
- Invisible scanner inputs (kiosk mode)
- Guest checkout or member login
- Point system (100 pts = $1)
- Multi-language (EN/FR)
- Email receipts

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
    rfid_card VARCHAR(24) UNIQUE,
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

## Setup

**Prerequisites**
- Python 3.8+
- Supabase account (free)
- Gmail for alerts (optional)

**Install**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Configure**
Create `.env` file:

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

# Scanner (for development - set to False to enable real hardware)
SCANNER_MOCK_MODE=True
MOCK_MODE=True

# RFID (optional - auto-detects if not set)
# RFID_PORT=/dev/ttyUSB0
# RFID_BAUD=9600
```

**Database**
1. Create project at supabase.com
2. Run SQL schema (see below)
3. Add test data:
```sql
INSERT INTO refrigerators (fridge_id, name, temperature_threshold) VALUES
(1, 'Refrigerator 1', 5.0), (2, 'Refrigerator 2', 6.0);
```

**Run**
```bash
python3 app.py
# Visit http://localhost:8080
```

## Login

**Admin**: `admin` / `admin123` (dashboard, products, customers)  
**Customer**: Sign up at `/auth/signup` (store, cart, purchase history)

## How to Use

**Checkout**
1. Go to `/store/checkout`
2. Scan products (USB barcode or RFID) - inputs are invisible
3. Status badge shows "Ready to Scan" / "Scanning..."
4. Complete purchase (login, guest, or member verification)

**Points**
- 100 points = $1 discount
- Redeem in multiples of 100
- Must be logged in or enter membership #

## Hardware

**ESP32**: Flash with DHT11 sensor code, publish to MQTT (`Frig1`, `Frig2`)  
**Pi GPIO**: LEDs (pins 21, 20), Buzzer (16), Motor (17, 27, 22)  
**Scanners**: USB barcode (plug & play), RFID auto-detects serial port

**Mock Mode**: Set `SCANNER_MOCK_MODE=True` and `MOCK_MODE=True` in `.env` to test without hardware

## Routes

**Customer**: `/store/`, `/store/cart`, `/store/checkout`, `/store/account`  
**Admin**: `/dashboard/`, `/products/`, `/client/`

## Troubleshooting

- **No DB connection**: Check `.env` Supabase credentials
- **Email alerts fail**: Use Gmail App Password, not regular password
- **MQTT won't connect**: Check Mosquitto is running (`sudo systemctl status mosquitto`)
- **Scanner not working**: Set `SCANNER_MOCK_MODE=False`, check USB connection

