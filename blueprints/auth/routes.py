# Authentication routes - handles login, logout, and signup for both admin and customers
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from services.db_service import get_customer_by_email, create_customer_account

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Hardcoded admin credentials (for employee dashboard access)
ADMIN_USER = {
    'username': 'admin',
    'password_hash': generate_password_hash('admin123'),
    'role': 'admin'
}

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Unified login page for admin staff and customers."""
    if request.method == 'GET':
        return render_template('login.html')
    
    # Handle login POST request
    email_or_username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    
    if not email_or_username or not password:
        flash('Please enter both email/username and password', 'danger')
        return redirect(url_for('auth.login'))
    
    # Check admin login first
    if email_or_username == ADMIN_USER['username']:
        if check_password_hash(ADMIN_USER['password_hash'], password):
            session['user_id'] = 0
            session['username'] = 'admin'
            session['role'] = 'admin'
            session['first_name'] = 'Admin'
            flash('Welcome Admin!', 'success')
            return redirect(url_for('dashboard.dashboard'))
        else:
            flash('Invalid admin credentials', 'danger')
            return redirect(url_for('auth.login'))
    
    # Check customer login by email
    customer = get_customer_by_email(email_or_username)
    if customer and check_password_hash(customer.get('password_hash', ''), password):
        session['user_id'] = customer['customer_id']
        session['username'] = customer['email']
        session['role'] = 'customer'
        session['first_name'] = customer['first_name']
        session['customer_id'] = customer['customer_id']
        session['membership_number'] = customer.get('membership_number')
        flash(f'Welcome back, {customer["first_name"]}!', 'success')
        return redirect(url_for('store.store_home'))
    else:
        flash('Invalid email or password', 'danger')
        return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
def logout():
    """Clear session and log user out."""
    username = session.get('first_name', 'User')
    session.clear()
    flash(f'Goodbye, {username}! You have been logged out.', 'info')
    return redirect(url_for('home'))

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """Customer self-registration page."""
    if request.method == 'GET':
        return render_template('signup.html')
    
    # Create new customer account
    data = request.form.to_dict()
    
    # Validate required fields
    required_fields = ['first_name', 'last_name', 'email', 'password']
    missing = [f for f in required_fields if not data.get(f)]
    
    if missing:
        flash(f'Missing required fields: {", ".join(missing)}', 'danger')
        return redirect(url_for('auth.signup'))
    
    # Check for duplicate email
    existing = get_customer_by_email(data['email'])
    if existing:
        flash('Email already registered. Please login.', 'warning')
        return redirect(url_for('auth.login'))
    
    # Create customer account with hashed password
    password_hash = generate_password_hash(data['password'])
    customer = create_customer_account(
        first_name=data['first_name'],
        last_name=data['last_name'],
        email=data['email'],
        password_hash=password_hash,
        phone=data.get('phone_num'),
        dob=data.get('dob')
    )
    
    if customer:
        flash(f'Account created successfully! Your membership number is {customer["membership_number"]}', 'success')
        return redirect(url_for('auth.login'))
    else:
        flash('Error creating account. Please try again.', 'danger')
        return redirect(url_for('auth.signup'))

@auth_bp.route('/api/signup', methods=['POST'])
def api_signup():
    """AJAX endpoint for customer registration."""
    data = request.get_json() or {}
    
    # Basic validation
    if not data.get('email') or not data.get('password'):
        return jsonify({'success': False, 'error': 'Missing email or password'}), 400
    
    # Check for existing account
    existing = get_customer_by_email(data['email'])
    if existing:
        return jsonify({'success': False, 'error': 'Email already registered'}), 400
    
    # Create account
    password_hash = generate_password_hash(data['password'])
    customer = create_customer_account(
        first_name=data.get('first_name', ''),
        last_name=data.get('last_name', ''),
        email=data['email'],
        password_hash=password_hash,
        phone=data.get('phone_num'),
        dob=data.get('dob')
    )
    
    if customer:
        return jsonify({
            'success': True, 
            'message': 'Account created successfully!',
            'membership_number': customer['membership_number']
        }), 201
    else:
        return jsonify({'success': False, 'error': 'Failed to create account'}), 500
