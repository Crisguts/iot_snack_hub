import re
from flask import Flask, jsonify, request, render_template, flash, url_for, redirect
import db

# Import email system
try:
    from emailSystem.integrated_email import email_system
    EMAIL_ALERTS_ENABLED = True
    print("✅ Email system loaded")
except ImportError:
    EMAIL_ALERTS_ENABLED = False
    print("❌ Email alerts disabled - emailSystem not found")

try:
    import gpioScripts.gpiozeroBlink as gpio
    import gpioScripts.motor as motor
except ImportError:
    try:
        import gpioScripts.gpioBlink as gpio
    except ImportError:
        from unittest.mock import MagicMock
        gpio = MagicMock()
        gpio.blink = MagicMock()

app = Flask(__name__)
app.secret_key = "Cookies"

fan_states = {
    1: False,
    2: False
}

def check_temperature_thresholds(fridge_data, fridge_id):
    """
    Check if temperature exceeds threshold and send email alert
    
    Args:
        fridge_data (dict): Latest temperature data from database
        fridge_id (int): Fridge ID (1 or 2)
    """
    if not fridge_data or not fridge_data.get("temperature"):
        return  # No data to check
    
    if not EMAIL_ALERTS_ENABLED:
        return  # Email alerts disabled
    
    try:
        current_temp = float(fridge_data.get("temperature"))
        
        # Get threshold from database
        threshold_data = db.get_fridge_threshold(fridge_id)
        threshold = threshold_data if threshold_data else 25.0
        
        # Get fridge name from database or use default
        fridge_name = f"Refrigerator {fridge_id}"
        
        # Check if temperature exceeds threshold
        if current_temp > threshold:
            print(f"🚨 THRESHOLD ALERT: {fridge_name} temp ({current_temp}°C) > threshold ({threshold}°C)")
            
            # Use the integrated email system that waits for YES replies (same as test email)
            try:
                success = email_system.send_temperature_alert_email(fridge_id, current_temp, threshold, fridge_name)
                if success:
                    # Start email monitoring to listen for replies (same as test email)
                    if not email_system.monitoring:
                        email_system.start_monitoring()
                        print("🔄 Started email monitoring for threshold alert replies")
                    print(f"📧 Temperature alert email sent for {fridge_name}")
                else:
                    print(f"⚠️  Failed to send email alert for {fridge_name}")
            except Exception as email_error:
                print(f"❌ Email alert error for {fridge_name}: {email_error}")
        else:
            print(f"✅ {fridge_name} temperature ({current_temp}°C) within threshold ({threshold}°C)")
            
    except Exception as e:
        print(f"❌ Error checking temperature threshold for fridge {fridge_id}: {e}")


@app.route('/')
def index():

    # Fetch REAL data from database instead of hardcoded values
    fridge_1_data = db.get_latest_temperature_readings(1)
    fridge_2_data = db.get_latest_temperature_readings(2)
    
    # Check temperature thresholds and send alerts if needed
    check_temperature_thresholds(fridge_1_data, 1)
    check_temperature_thresholds(fridge_2_data, 2)
    
    # Get historical data
    fridge_1_history = db.get_temperature_history(1, limit=10)
    fridge_2_history = db.get_temperature_history(2, limit=10)
    
    # Format data for template
    fridge_data = {
        1: {
            "temperature": fridge_1_data.get("temperature") if fridge_1_data else None,
            "humidity": fridge_1_data.get("humidity") if fridge_1_data else None
        },
        2: {
            "temperature": fridge_2_data.get("temperature") if fridge_2_data else None,
            "humidity": fridge_2_data.get("humidity") if fridge_2_data else None
        }
    }
    
    # Format historical data for charts
    def format_history(history_list):
        if not history_list:
            return {"timestamps": [], "temperature": [], "humidity": []}
        
        timestamps = []
        temperatures = []
        humidities = []
        
        for reading in reversed(history_list):
            ts = reading.get("timestamp") or reading.get("created_at")
            if ts:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    timestamps.append(dt.strftime("%H:%M"))
                except:
                    timestamps.append("--:--")
            
            temperatures.append(reading.get("temperature"))
            humidities.append(reading.get("humidity"))
        
        return {
            "timestamps": timestamps,
            "temperature": temperatures,
            "humidity": humidities
        }
    
    historical_data = {
        1: format_history(fridge_1_history),
        2: format_history(fridge_2_history)
    }
    
    return render_template("index.html", fridge_data=fridge_data, historical_data=historical_data)

@app.route("/client", defaults={"page": 1})
@app.route("/client/page/<int:page>")
def client(page):
    per_page = 6
    offset = (page - 1) * per_page
    search_query = request.args.get("search", "").strip()

    customers = db.get_customers_paginated(limit=per_page, offset=offset, search=search_query)
    total = db.get_customer_count(search=search_query)
    total_pages = (total + per_page - 1) // per_page

    return render_template(
        "client.html",
        customers=customers,
        page=page,
        total_pages=total_pages,
        search=search_query
    )


@app.route("/add", methods=["POST"])
def add():

    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    phone_num = request.form.get("phone_num")
    email = request.form.get("email")
    dob = request.form.get("dob")

    if first_name and last_name and email:
            # Regex for name validation
            name_regex = r"^[a-zA-Z]+([ '-][a-zA-Z]+)*$"
            if not re.match(name_regex, first_name.strip()):
                flash("Invalid first name.", "danger")
                return redirect(url_for("client"))
            if not re.match(name_regex, last_name):
                flash("Invalid last name.", "danger")
                return redirect(url_for("client"))
            # Regex for basic email validation
            if not re.match('^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email.strip()):
                flash("Invalid email address.", "danger")
                return redirect(url_for("client"))
            
            # Try adding customer to db
            if db.add_customer(first_name.strip(), last_name.strip(), email.strip(),dob.strip(), phone_num.strip() if phone_num else None):
                flash(f"{first_name} {last_name} Client added successfully!", "success")
                gpio.blink("blue")  # Blink blue LED on success
            else:
                flash(f"Failed to add client", "danger")
                gpio.blink("red")  # Blink red LED and sound buzzer on error
    else:
        flash("Fields cannot be left blank.", "danger")  # Then show message
        gpio.blink("red")  # Blink red LED first (screen frozen during blink)

    return redirect(url_for("client"))

@app.route("/delete/<int:customer_id>")
def delete(customer_id):
    try:
        print(f"Attempting to delete customer with ID: {customer_id} (type: {type(customer_id)})")
        db.delete_customer(customer_id)
        flash("Client removed successfully!", "success")
        gpio.blink("blue")  # Blink blue LED on success
    except Exception as e:
        flash(f"Failed to remove client: {str(e)}", "danger")
        gpio.blink("red")  # Blink red LED and sound buzzer on error
    return redirect(url_for("client"))

@app.route("/update/<int:customer_id>", methods=["POST"])
def update(customer_id):
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    email = request.form.get("email")

    if not first_name or not last_name or not email:
        flash("All fields are required to update a client.", "danger")
        gpio.blink("red")
        return redirect(url_for("client"))

    name_regex = r"^[a-zA-Z]+([ '-][a-zA-Z]+)*$"
    # email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.match(name_regex, first_name):
        flash("Invalid first name.", "danger")
        gpio.blink("red")
        return redirect(url_for("client"))
    if not re.match(name_regex, last_name):
        flash("Invalid last name.", "danger")
        gpio.blink("red")
        return redirect(url_for("client"))
    # if not re.match(email_regex, email):
    #     flash("Invalid email address.", "danger")
        # gpio.blink("red")
        # return redirect(url_for("index"))

    # Update customer in database
    if db.update_customer(customer_id, first_name.strip(), last_name.strip(), email.strip()):
        flash(f"{first_name} {last_name} updated successfully!", "success")
        gpio.blink("blue")
    else:
        flash("Failed to update client.", "danger")
        gpio.blink("red")

    return redirect(url_for("client"))



# Motor Routes - Individual fan control for each fridge
@app.route('/fan/<int:fridge_id>', methods=['POST'])
def toggle_fan(fridge_id):
    if fridge_id not in [1, 2]:
        return jsonify({"success": False, "error": "Invalid fridge ID"}), 400
    fan_states[fridge_id] = not fan_states[fridge_id]
    
    try:
        if fan_states[fridge_id]:
            motor.turnFanOn(fridge_id)
            message = f"Fan {fridge_id} turned ON"
        else:
            motor.turnFanOff(fridge_id)
            message = f"Fan {fridge_id} turned OFF"
        
        return jsonify({
            "success": True, 
            "fan_state": fan_states[fridge_id],
            "motor_running": motor.getMotorState(),
            "message": message
        })
    except Exception as e:
        fan_states[fridge_id] = not fan_states[fridge_id]
        return jsonify({"success": False, "error": str(e)}), 500
    
@app.route('/api/latest')
def get_latest_readings():
    from supabase import create_client, Client
    from dotenv import load_dotenv
    import os
    load_dotenv()

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    print("SUPABASE_URL:", url)
    print("SUPABASE_KEY exists:", bool(key))

    supabase: Client = create_client(url, key)

    # Get the latest entry per fridge
    data = {}
    for fridge_id in [1, 2]:
        response = supabase.table("temperature_readings") \
            .select("temperature, humidity, created_at") \
            .eq("fridge_id", fridge_id) \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()
        data[fridge_id] = response.data[0] if response.data else None

    return jsonify({"success": True, "data": data})


@app.route('/fan/states', methods=['GET'])
def get_fan_states():
    try:
        return jsonify({
            "success": True,
            "fan_states": fan_states,
            "motor_running": motor.getMotorState(),
            "all_fan_states": motor.getFanState()
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Legacy routes for backwards compatibility
@app.route('/fan/on', methods=['POST'])
def turn_fan_on():
    motor.turnFanOn(1)
    return redirect('/')

@app.route('/fan/off', methods=['POST'])
def turn_fan_off():
    motor.turnFanOff(1)
    return redirect('/')

@app.route("/api/temperature/<fridge_id>")
def get_temperature(fridge_id):
    try:
        reading = db.get_latest_temperature_readings(fridge_id)
        if reading:
            return jsonify({
                "success": True,
                "fridge_id": fridge_id,
                "temperature": reading.get("temperature"),
                "humidity": reading.get("humidity"),
                "timestamp": reading.get("timestamp")
            })
        else:
            return jsonify({
                "success": False,
                "message": "No data available"
            }), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/temperature/<fridge_id>/history")
def get_temperature_history(fridge_id):
    try:
        limit = request.args.get("limit", 50, type=int)
        history = db.get_temperature_history(fridge_id, limit)
        return jsonify({
            "success": True,
            "fridge_id": fridge_id,
            "data": history
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Simple Email Test Route
@app.route("/api/email/test", methods=["POST"])
def test_email():
    """Send a simple test email"""
    print("📧 Test email route called")
    
    if not EMAIL_ALERTS_ENABLED:
        print("❌ Email alerts disabled")
        return jsonify({"success": False, "error": "Email system not configured"}), 500
    
    try:
        print("📤 Attempting to send test email...")
        success = email_system.send_test_email()
        print(f"📧 Email send result: {success}")
        
        if success:
            # Start email monitoring to listen for replies
            if not email_system.monitoring:
                email_system.start_monitoring()
                print("🔄 Started email monitoring for test email replies")
            
            flash("Test email sent successfully! Reply 'YES' for automatic fan control.", "success")
            print("✅ Test email sent successfully")
            return jsonify({"success": True, "message": "Test email sent successfully"})
        else:
            print("❌ Failed to send test email")
            return jsonify({"success": False, "error": "Failed to send test email"}), 500
    except Exception as e:
        print(f"❌ Exception in test email: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

# Check for email signals and activate fan
@app.route("/api/email/check-signals", methods=["GET"])
def check_email_signals():
    """Check for email signals from background monitor"""
    if not EMAIL_ALERTS_ENABLED:
        return jsonify({"success": False, "error": "Email system not configured"}), 500
    
    try:
        # Check if there's a signal from email system
        state = email_system.get_and_clear_state()
        
        if state and state.get("action") == "activate_fan":
            fridge_id = state.get("fridge_id", 1)
            
            # Activate the fan
            fan_states[fridge_id] = True
            motor.turnFanOn(fridge_id)
            
            message = f"Fan activated for Fridge {fridge_id} via email reply!"
            
            return jsonify({
                "success": True,
                "fan_activated": True,
                "fridge_id": fridge_id,
                "message": message,
                "timestamp": state.get("timestamp")
            })
        else:
            return jsonify({
                "success": True,
                "fan_activated": False,
                "message": "No email signals"
            })
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="http://127.0.0.1", port=8080, debug=False)

