from flask import Blueprint

dashboard_bp = Blueprint(
    'inventory',
    __name__,
    template_folder='../../templates',
    static_folder='../../static'
)
