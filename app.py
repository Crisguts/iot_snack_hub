import re
from flask import Flask, jsonify, request, render_template, flash, url_for, redirect
import db   # our custom db.py file
# # Try to import GPIO modules with fallback
try:
    import gpioScripts.gpiozeroBlink as gpio  # Try RPi.GPIO first
    print("GPIOZERO")
    import gpioScripts.motor as motor
except ImportError:
    try:
        import gpioScripts.gpioBlink as gpio  # Fallback to gpiozero
    except ImportError:
        from unittest.mock import MagicMock
        gpio = MagicMock()
        gpio.blink = MagicMock()


app = Flask(__name__)
app.secret_key = "Cookies"


# @app.route('/')
# def index():
#     # Current sensor readings for each fridge
#     fridge_data = {
#         1: {"temperature": 4, "humidity": 60},
#         2: {"temperature": -2, "humidity": 55}
#     }

#     # Historical data for charts (optional)
#     historical_data = {
#         1: {
#             "timestamps": ["10:00", "10:05", "10:10"],
#             "temperature": [4, 4.1, 3.9],
#             "humidity": [60, 62, 59]
#         },
#         2: {
#             "timestamps": ["10:00", "10:05", "10:10"],
#             "temperature": [-2, -1.8, -2.2],
#             "humidity": [55, 54, 56]
#         }
#     }

#     return render_template("index.html", fridge_data=fridge_data, historical_data=historical_data)

@app.route('/')
def index():

    # Fetch REAL data from database instead of hardcoded values
    fridge_1_data = db.get_latest_temperature_readings(1)
    fridge_2_data = db.get_latest_temperature_readings(2)
    
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
        
        for reading in reversed(history_list):  # Reverse to show oldest first
            # Format timestamp
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

    print("Fridge Data:", fridge_data)
    print("Historical Data:", historical_data)
    
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



# Motor Routes
@app.route('/fan/on', methods=['POST'])
def turn_fan_on():
    motor.turnFanOn()
    return redirect('/')

@app.route('/fan/off', methods=['POST'])
def turn_fan_off():
    motor.turnFanOff()
    return redirect('/')

# Temperature
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

# essentially this has the ability to look for the json data with no UI
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

# @app.route("/dashboard")
# def dashboard():
#     # page with the gauges
#     return render_template("")# to decide?

if __name__ == "__main__":
    # app.run(host="0.0.0.0", port=8080, debug=False)
    app.run(host="http://127.0.0.1", port=8080, debug=False)

