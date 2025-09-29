from flask import Flask, request, render_template, flash
import db   # our custom db.py file
<<<<<<< Updated upstream
import gpioBlink as gpio # our gpio control file (RPI.GPIO)
# import gpiozeroBlink as gpio # our gpio control file (GPIOZERO)
=======
# # Try to import GPIO modules with fallback
# try:
#     import gpiozeroBlink as gpio  # Try RPi.GPIO first
#     print("GPIOZERO")
# except Exception as e:
#     import gpioBlink as gpio  # Fallback to gpiozero

import gpiozeroBlink as gpio  # Try RPi.GPIO first
>>>>>>> Stashed changes

app = Flask(__name__)
app.secret_key = "Cookies"

@app.route("/", methods=["GET"])
def index():
    customers = db.get_customers()
    return render_template("index.html", customers=customers)

@app.route("/add", methods=["POST"])
def add():

    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    email = request.form.get("email")

    if first_name and last_name and email:
<<<<<<< Updated upstream
        try:
            db.add_customer(first_name, last_name, email)
            gpio.blink("blue")  # Blink blue LED on success
            flash(f"{first_name} {last_name} Client added successfully!", "success")
        except Exception as e:
            flash(f"Failed to add client {str(e)}", "danger")
            gpio.blink("red")  # Blink red LED and sound buzzer on error
=======
            if db.add_customer(first_name, last_name, email):
                flash(f"{first_name} {last_name} Client added successfully!", "success")
                gpio.blink("blue")  # Blink blue LED on success
            else:
                flash(f"Failed to add client", "danger")
                gpio.blink("red")  # Blink red LED and sound buzzer on error
>>>>>>> Stashed changes
    else:
        flash("Client name cannot be empty.", "danger")  # Then show message
        gpio.blink("red")  # Blink red LED first (screen frozen during blink)

    return index()

@app.route("/delete/<int:customer_id>")
def delete(customer_id):
    try:
        db.delete_customer(customer_id)
        flash("Client removed successfully!", "success")
        gpio.blink("blue")  # Blink blue LED on success
    except Exception as e:
        flash(f"Failed to remove client: {str(e)}", "danger")
        gpio.blink("red")  # Blink red LED and sound buzzer on error
    return index()

if __name__ == "__main__":
    # app.run(host="0.0.0.0", port=8080, debug=False)
    app.run(host="http://127.0.0.1", port=8080, debug=False)

   
