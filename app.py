from flask import Flask, request, render_template
import db   # our custom db.py file

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    items = db.get_items()
    return render_template("index.html", items=items)

@app.route("/add", methods=["POST"])
def add():
    item = request.form.get("item")
    if item:
        db.add_item(item)
    return index()

@app.route("/delete/<int:item_id>")
def delete(item_id):
    db.delete_item(item_id)
    return index()

if __name__ == "__main__":
    # app.run(host="0.0.0.0", port=8080, debug=False)
    app.run(host="http://127.0.0.1", port=8080, debug=False)

   
