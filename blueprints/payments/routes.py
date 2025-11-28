# Payment management interface for admin users
# Displays all purchases/payments with customer information
from flask import Blueprint, render_template, request, session, redirect, url_for, flash
import math
from functools import wraps
from services.db_service import (
    get_all_purchases_paginated,
    get_purchases_count,
    get_customer_purchases_with_details
)

payments_bp = Blueprint("payments", __name__, url_prefix="/payments")

def admin_required(f):
    """Decorator to require admin access."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('Admin access required', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@payments_bp.route('/')
@payments_bp.route('/list')
@admin_required
def payments_list():
    """Display paginated payments list with search functionality."""
    search = request.args.get('search', '').strip()
    page = int(request.args.get('page', 1))
    per_page = 15
    
    # Calculate pagination
    total = get_purchases_count(search if search else None)
    total_pages = math.ceil(total / per_page) if total > 0 else 1
    
    # Fetch paginated payments from database
    offset = (page - 1) * per_page
    payments = get_all_purchases_paginated(per_page, offset, search if search else None)
    
    return render_template(
        'payments.html',
        payments=payments,
        page=page,
        total_pages=total_pages,
        search=search
    )
