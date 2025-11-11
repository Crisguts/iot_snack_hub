# 🚀 Quick Start Guide

## Running on Mac (No Hardware Required)

### 1. First Time Setup (5 minutes)

```bash
# Navigate to project
cd /Users/guts-/Binder/smart-store

# Create virtual environment (if not done)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file (copy from example)
cp .env.example .env
# Edit .env with Supabase credentials
```

### 2. Supabase Setup (5 minutes)

1. Go to https://supabase.com and create free account
2. Create new project
3. Go to Settings → API → Copy:
   - `Project URL` → Put in `SUPABASE_URL`
   - `anon/public key` → Put in `SUPABASE_KEY`
4. Go to SQL Editor, paste and run schema from README.md
5. Insert initial fridge data:
   ```sql
   INSERT INTO refrigerators (fridge_id, name, temperature_threshold) VALUES
   (1, 'Refrigerator 1', 5.0),
   (2, 'Refrigerator 2', 6.0);
   ```

### 3. Run the App

```bash
python3 app.py
```

Open browser: http://localhost:8080

## Testing the System

### Test Admin Access
1. Click "Login"
2. Username: `admin` / Password: `admin123`
3. You'll see:
   - **Dashboard**: Fridge monitoring (mock data)
   - **Products**: Add/manage products
   - **Clients**: Customer management

### Test Customer Flow
1. Click "Sign Up" from home page
2. Fill form → Creates account with membership number
3. Login with email
4. Access:
   - **Shop**: Product catalog
   - **Self-Checkout**: Scan products (simulated)
   - **Cart**: View/edit cart
   - **My Account**: Purchase history

### Test Self-Checkout

1. **Admin: Add Product First**
   - Login as admin
   - Products → Add New Product
   - Example:
     - Name: Coca-Cola
     - Category: Beverage
     - Price: 1.99
     - UPC: `012000001234` (barcode)
     - EPC: `E200001234567890ABCD` (RFID)
     - Producer: Coca-Cola Company
   - Inventory → Add stock: 50 units

2. **Customer: Shop & Checkout**
   - Logout admin, login as customer
   - Go to Self-Checkout
   - **Barcode Input**: Type `012000001234` and press Enter
   - Product appears in cart
   - Click "Confirm Purchase"
   - See success message with points earned

## Mock Mode Features (Mac Development)

No hardware needed. Everything works in mock mode:

- ✅ **Database**: Real Supabase (cloud)
- ✅ **Scanner**: Manual input (simulates USB/RFID)
- ✅ **MQTT**: Console messages (simulates ESP32 data)
- ✅ **GPIO**: Console messages (simulates LED/motor)
- ✅ **Email**: Real emails if Gmail configured

## Adding Sample Products (Quick Test Data)

Run this SQL in Supabase:

```sql
INSERT INTO products (name, category, price, upc, epc, producer, total_quantity) VALUES
('Coca-Cola 500ml', 'Beverage', 1.99, '012000001234', 'E200001234567890ABCD', 'Coca-Cola Company', 50),
('Pepsi 500ml', 'Beverage', 1.99, '012000005678', 'E200005678901234EFGH', 'PepsiCo', 50),
('Snickers Bar', 'Snack', 1.49, '028400001234', 'E200001111222233334', 'Mars Inc.', 100),
('Red Bull 250ml', 'Energy Drink', 2.99, '083400101234', 'E200005555666677778', 'Red Bull GmbH', 75),
('Kit Kat', 'Chocolate', 1.29, '034000001234', 'E200009999888877776', 'Nestle', 120);
```

## Troubleshooting

### "Import Error: supabase"
```bash
pip install supabase
```

### "No module named 'serial'"
```bash
pip install pyserial
```

### "Connection to Supabase failed"
- Check `.env` file has correct `SUPABASE_URL` and `SUPABASE_KEY`
- Verify internet connection

### Port 8080 already in use
```bash
# Change port in app.py last line:
app.run(debug=True, host="0.0.0.0", port=8081)
```

## Hardware Integration (Later)

When Raspberry Pi + ESP32 + Scanners available:

1. **Update .env**:
   ```env
   MOCK_MODE=False
   SCANNER_MOCK_MODE=False
   MQTT_AUTO_START=True
   MQTT_BROKER=192.168.x.x  # Pi IP
   ```

2. **ESP32 Setup**:
   - Flash with DHT11 sensor code
   - Configure WiFi credentials
   - Set MQTT broker to Pi IP
   - Topics: `Frig1`, `Frig2`

3. **Raspberry Pi**:
   - Install Mosquitto: `sudo apt-get install mosquitto`
   - Connect GPIO components (see README wiring)
   - Run app: `python3 app.py`

4. **Scanners**:
   - USB Barcode: Plug in, works instantly
   - RFID CF600: Connect to `/dev/ttyAMA10`, configure baud 9600

## File Structure Quick Reference

```
Most Important Files:
├── app.py                          # Start here - main app
├── .env                            # Your secrets (create from .env.example)
├── blueprints/
│   ├── auth/routes.py              # Login/signup logic
│   ├── store/routes.py             # Customer shopping
│   └── products/routes.py          # Admin product management
├── services/
│   ├── db_service.py               # All database queries
│   └── scanner_service.py          # Barcode/RFID handler
└── templates/
    ├── checkout.html               # Self-checkout UI
    ├── store.html                  # Product catalog
    └── cart.html                   # Shopping cart
```

## Next Steps

1. ✅ Set up Supabase (5 min)
2. ✅ Configure `.env` file
3. ✅ Run `python3 app.py`
4. ✅ Create admin products
5. ✅ Test customer signup → shop → checkout
6. 🎯 Add products
7. 🎯 Customize design (CSS in `static/css/styles.css`)
8. 🎯 Later: Connect hardware

## Support

Check `README.md` for detailed documentation.

**Works now on Mac. No hardware needed to test.**
