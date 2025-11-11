from flask import Blueprint
from .routes import auth_bp
auth_bp = Blueprint(
    'auth',
    __name__,
    template_folder='../../templates',
    static_folder='../../static'
)
