# Customer management interface for admin users
# Handles CRUD operations for customer accounts with search and pagination
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
import math
from werkzeug.security import generate_password_hash
from services.db_service import (
    get_customers_paginated,
    get_customer_count,
    create_customer_account,
    update_customer,
    delete_customer
)

client_bp = Blueprint("client", __name__, url_prefix="/client")

@client_bp.route('/')
@client_bp.route('/list')
def client():
    """Display paginated customer list with search functionality."""
    search = request.args.get('search', '').strip()
    page = int(request.args.get('page', 1))
    per_page = 10
    
    # Calculate pagination
    total = get_customer_count(search if search else None)
    total_pages = math.ceil(total / per_page) if total > 0 else 1
    
    # Fetch paginated customers from database
    offset = (page - 1) * per_page
    customers = get_customers_paginated(per_page, offset, search if search else None)
    
    return render_template(
        'client.html',
        customers=customers,
        page=page,
        total_pages=total_pages,
        search=search
    )

@client_bp.route('/add', methods=['POST'])
def add():
    """Create new customer account (admin only)."""
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        
        # Validate required fields
        required = ['first_name', 'last_name', 'email', 'password']
        missing = [f for f in required if not data.get(f)]
        if missing:
            if request.is_json:
                return jsonify({'success': False, 'error': f'Missing: {", ".join(missing)}'}), 400
            flash(f'Missing required fields: {", ".join(missing)}', 'danger')
            return redirect(url_for('client.client'))
        
        # Hash password before storing
        password_hash = generate_password_hash(data['password'])
        
        # Create customer with password, membership number, and points
        customer = create_customer_account(
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            password_hash=password_hash,
            phone=data.get('phone_num'),
            dob=data.get('dob')
        )
        
        if customer:
            # Success feedback with LED indicator
            try:
                from services.gpio_service import blink
                blink('blue')
            except:
                print("[MOCK] Blue LED blink")
            
            if request.is_json:
                return jsonify({'success': True, 'message': 'Customer added successfully'}), 201
            
            flash('Customer added successfully!', 'success')
        else:
            if request.is_json:
                return jsonify({'success': False, 'error': 'Failed to add customer'}), 500
            flash('Failed to add customer', 'danger')
        
        return redirect(url_for('client.client'))
        
    except Exception as e:
        # Error feedback with LED and buzzer
        try:
            from services.gpio_service import blink
            blink('red')
        except:
            print("[MOCK] Red LED blink + buzzer")
        
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 500
        flash(f'Error adding customer: {str(e)}', 'danger')
        return redirect(url_for('client.client'))

@client_bp.route('/update/<int:customer_id>', methods=['POST'])
def update(customer_id):
    """Update existing customer information."""
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        
        # Update customer in database
        success = update_customer(
            customer_id=customer_id,
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            email=data.get('email'),
            phone_num=data.get('phone_num')
        )
        
        if success:
            if request.is_json:
                return jsonify({'success': True, 'message': 'Customer updated'}), 200
            flash('Customer updated successfully!', 'success')
        else:
            if request.is_json:
                return jsonify({'success': False, 'error': 'Customer not found'}), 404
            flash('Customer not found', 'danger')
        
        return redirect(url_for('client.client'))
        
    except Exception as e:
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 500
        flash(f'Error updating customer: {str(e)}', 'danger')
        return redirect(url_for('client.client'))

@client_bp.route('/delete/<int:customer_id>')
def delete(customer_id):
    """Remove customer from system."""
    try:
        success = delete_customer(customer_id)
        
        if success:
            flash('Customer deleted successfully', 'success')
        else:
            flash('Customer not found or could not be deleted', 'warning')
            
    except Exception as e:
        flash(f'Error deleting customer: {str(e)}', 'danger')
    
    return redirect(url_for('client.client'))

@client_bp.route('/payments/<int:customer_id>')
def get_customer_payments(customer_id):
    """API endpoint to fetch all payments for a specific customer."""
    try:
        from services.db_service import get_customer_purchases_with_details
        
        payments = get_customer_purchases_with_details(customer_id)
        return jsonify({
            'success': True,
            'payments': payments
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
