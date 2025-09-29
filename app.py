from flask import Flask, request, render_template, flash
import db   # our custom db.py file

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
        try:
            db.add_customer(first_name, last_name, email)
            flash(f"{first_name} {last_name} Client added successfully!", "success")
        except Exception as e:
            flash(f"Failed to add client {str(e)}", "danger")
    else:
        flash("Client name cannot be empty.", "danger")
    return index()

@app.route("/delete/<int:customer_id>")
def delete(customer_id):
    try:
        db.delete_customer(customer_id)
        flash("Client removed successfully!", "success")
    except Exception as e:
        flash(f"Failed to remove client: {str(e)}", "danger")
    return index()

if __name__ == "__main__":
    # app.run(host="0.0.0.0", port=8080, debug=False)
    app.run(host="http://127.0.0.1", port=8080, debug=False)

   
