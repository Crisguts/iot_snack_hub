# Main Flask application entry point
# Handles app initialization, blueprint registration, and root routes
from flask import Flask, render_template, redirect, url_for, session, request
import os
from flask_babel import Babel

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_key_change_in_production")

# Multi-language support configuration
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'
babel = Babel(app)

def get_locale():
    """Detect user's preferred language from session or browser."""
    if 'language' in session:
        return session['language']
    return request.accept_languages.best_match(['en', 'fr']) or 'en'

babel.init_app(app, locale_selector=get_locale)

# Import and initialize services with fallback to mock mode
# This allows the app to run even if hardware/external services aren't available
try:
    from services.gpio_service import blink
    print("✅ GPIO service loaded")
except Exception as e:
    print(f"⚠️ GPIO service mock loaded: {e}")
    def blink(color): 
        print(f"[MOCK] Blink {color} LED")

try:
    from services.db_service import init_db
    db_available = True
    init_db()
    print("✅ DB service loaded")
except Exception as e:
    print(f"⚠️ DB mock loaded: {e}")
    db_available = False

try:
    from services.email_service import email_service
    email_service.start_monitoring()
    print("✅ Email service loaded and monitoring started")
except Exception as e:
    print(f"⚠️ Email service mock loaded: {e}")

try:
    from services.mqtt_client import start_in_thread
    start_in_thread()
    print("✅ MQTT client started")
except Exception as e:
    print(f"⚠️ MQTT client mock loaded: {e}")

# Register all blueprints (modular route handlers)
from blueprints.auth.routes import auth_bp
from blueprints.client.routes import client_bp
from blueprints.dashboard.routes import dashboard_bp
from blueprints.dashboard.mqtt_handler import mqtt_api
from blueprints.store.routes import store_bp
from blueprints.products.routes import products_bp
from blueprints.payments.routes import payments_bp
from blueprints.sales_report.routes import sales_bp
from blueprints.inventory_report.routes import inventory_bp

app.register_blueprint(sales_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(client_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(mqtt_api)
app.register_blueprint(store_bp)
app.register_blueprint(products_bp)
app.register_blueprint(payments_bp)
app.register_blueprint(inventory_bp)

# Root routes
@app.route("/")
def home():
    """Landing page - redirects based on user role."""
    if 'user_id' in session:
        role = session.get('role')
        if role == 'admin':
            return redirect(url_for('dashboard.dashboard'))
        elif role == 'customer':
            return redirect(url_for('store.store_home'))
    
    return render_template("index.html")

@app.route("/set_language/<language>")
def set_language(language):
    """Update user's language preference."""
    if language in ['en', 'fr']:
        session['language'] = language
    return redirect(request.referrer or url_for('home'))

# Make user info available to all templates
@app.context_processor
def inject_user():
    """Inject user session data into template context."""
    return {
        'logged_in': 'user_id' in session,
        'user_role': session.get('role'),
        'user_name': session.get('first_name'),
        'username': session.get('username'),
        'current_language': get_locale()
    }

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)