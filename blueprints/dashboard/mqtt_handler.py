# blueprints/dashboard/mqtt_handler.py
from flask import Blueprint, jsonify, request
from services.mqtt_client import get_latest_readings, get_latest_for_fridge, get_historical

mqtt_api = Blueprint("mqtt_api", __name__, url_prefix="/dashboard/api")

@mqtt_api.route("/latest", methods=["GET"])
def api_latest_all():
    """
    Return latest readings for all configured topics.
    Format: { topic: {temperature, humidity, timestamp, fridge_id}, ... }
    """
    data = get_latest_readings()
    return jsonify(success=True, data=data)


@mqtt_api.route("/latest/<int:fridge_id>", methods=["GET"])
def api_latest_fridge(fridge_id):
    data = get_latest_for_fridge(fridge_id)
    if not data:
        return jsonify(success=False, message="No data for fridge"), 404
    return jsonify(success=True, data=data)


@mqtt_api.route("/history/<int:fridge_id>", methods=["GET"])
def api_history(fridge_id):
    limit = int(request.args.get("limit", 100))
    rows = get_historical(fridge_id, limit=limit)
    return jsonify(success=True, data=rows)
