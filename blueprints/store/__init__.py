from flask import Blueprint

store_bp = Blueprint(
    'store',
    __name__,
    template_folder='../../templates',
    static_folder='../../static'
)
