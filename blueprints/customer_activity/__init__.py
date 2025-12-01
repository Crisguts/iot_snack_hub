from flask import Blueprint

products_bp = Blueprint(
    'customer_activity',
    __name__,
    template_folder='../../templates',
    static_folder='../../static'
)
