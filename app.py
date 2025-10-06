import re
from flask import Flask, request, render_template, flash, url_for, redirect
import db   # our custom db.py file
# # Try to import GPIO modules with fallback
try:
    import gpioScripts.gpiozeroBlink as gpio  # Try RPi.GPIO first
    print("GPIOZERO")
except ImportError:
    try:
        import gpioScripts.gpioBlink as gpio  # Fallback to gpiozero
    except ImportError:
        from unittest.mock import MagicMock
        gpio = MagicMock()
        gpio.blink = MagicMock()


app = Flask(__name__)
app.secret_key = "Cookies"

@app.route("/", defaults={"page": 1})
@app.route("/page/<int:page>")
def index(page):
    per_page = 6
    offset = (page - 1) * per_page
    search_query = request.args.get("search", "").strip()

    customers = db.get_customers_paginated(limit=per_page, offset=offset, search=search_query)
    total = db.get_customer_count(search=search_query)
    total_pages = (total + per_page - 1) // per_page

    return render_template("index.html",
                           customers=customers,
                           page=page,
                           total_pages=total_pages,
                           search=search_query)

# @app.route("/", methods=["GET"])
# def index():
#     customers = db.get_customers()
#     return render_template("index.html", customers=customers)

@app.route("/add", methods=["POST"])
def add():

    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    email = request.form.get("email")

    if first_name and last_name and email:
            # Regex for name validation
            name_regex = r"^[a-zA-Z]+([ '-][a-zA-Z]+)*$"
            if not re.match(name_regex, first_name):
                flash("Invalid first name.", "danger")
                return redirect(url_for("index"))
            if not re.match(name_regex, last_name):
                flash("Invalid last name.", "danger")
                return redirect(url_for("index"))
            # Regex for basic email validation
            if not re.match('^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                flash("Invalid email address.", "danger")
                return redirect(url_for("index"))
            
            # Try adding customer to db
            if db.add_customer(first_name.strip(), last_name.strip(), email.strip()):
                flash(f"{first_name} {last_name} Client added successfully!", "success")
                gpio.blink("blue")  # Blink blue LED on success
            else:
                flash(f"Failed to add client", "danger")
                gpio.blink("red")  # Blink red LED and sound buzzer on error
    else:
        flash("Fields cannot be left blank.", "danger")  # Then show message
        gpio.blink("red")  # Blink red LED first (screen frozen during blink)

    return redirect(url_for("index"))

@app.route("/delete/<int:customer_id>")
def delete(customer_id):
    try:
        db.delete_customer(customer_id)
        flash("Client removed successfully!", "success")
        gpio.blink("blue")  # Blink blue LED on success
    except Exception as e:
        flash(f"Failed to remove client: {str(e)}", "danger")
        gpio.blink("red")  # Blink red LED and sound buzzer on error
    return redirect(url_for("index"))

if __name__ == "__main__":
    # app.run(host="0.0.0.0", port=8080, debug=False)
    app.run(host="http://127.0.0.1", port=8080, debug=False)

   
