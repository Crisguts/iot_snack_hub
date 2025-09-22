from flask import Flask, request, render_template, flash
import db   # our custom db.py file

app = Flask(__name__)
app.secret_key = "Cookies"

@app.route("/", methods=["GET"])
def index():
    items = db.get_items()
    return render_template("index.html", items=items)

@app.route("/add", methods=["POST"])
def add():
    item = request.form.get("item")
    if item:
        try:
            db.add_item(item)
            flash(f"{item} Client added successfully!", "success")
        except Exception as e:
            flash(f"Failed to add client {str(e)}", "danger")
    else:
        flash("Client name cannot be empty.", "danger")
    return index()

@app.route("/delete/<int:item_id>")
def delete(item_id):
    try:
        db.delete_item(item_id)
        flash("Client removed successfully!", "success")
    except Exception as e:
        flash(f"Failed to remove client: {str(e)}", "danger")
    return index()

if __name__ == "__main__":
    # app.run(host="0.0.0.0", port=8080, debug=False)
    app.run(host="http://127.0.0.1", port=8080, debug=False)

   
