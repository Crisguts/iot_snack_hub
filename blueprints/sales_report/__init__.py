from flask import Blueprint

dashboard_bp = Blueprint(
    'sales',
    __name__,
    template_folder='../../templates',
    static_folder='../../static'
)