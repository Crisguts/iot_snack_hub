# blueprints/store/routes.py - Customer Store & Cart System
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash
from services.db_service import (
    get_all_products, get_product_by_code, create_purchase,
    get_customer_purchases, get_purchase_details, get_customer_by_id,
    get_customer_by_membership
)
from services.scanner_service import scanner_service

store_bp = Blueprint("store", __name__, url_prefix="/store")

# Session-based cart
def get_cart():
    """Get cart from session."""
    if 'cart' not in session:
        session['cart'] = []
    return session['cart']

def save_cart(cart):
    """Save cart to session."""
    session['cart'] = cart
    session.modified = True

def calculate_cart_total(cart):
    """Calculate total price of cart."""
    return sum(item['price'] * item['quantity'] for item in cart)

def calculate_points(total_amount):
    """Calculate loyalty points (1 point per $1 spent)."""
    return int(total_amount)

# --- Customer Routes ---
@store_bp.route('/')
@store_bp.route('/home')
def store_home():
    """Customer store homepage (product catalog). Supports guest browsing."""
    # Allow guests, logged-in customers, or verified members
    role = session.get('role')
    guest_mode = session.get('guest_mode', False)
    
    if not (role == 'customer' or guest_mode):
        flash('Please login or continue as guest', 'warning')
        return redirect(url_for('home'))
    
    products = get_all_products()
    # Filter only products with stock
    available_products = [p for p in products if p.get('total_quantity', 0) > 0]
    
    cart = get_cart()
    cart_count = sum(item['quantity'] for item in cart)
    
    return render_template('store.html', products=available_products, cart_count=cart_count)

@store_bp.route('/cart')
def cart():
    """View shopping cart. Supports guest checkout."""
    role = session.get('role')
    guest_mode = session.get('guest_mode', False)
    customer_id = session.get('customer_id')
    
    if not (role == 'customer' or guest_mode):
        flash('Please login or continue as guest', 'warning')
        return redirect(url_for('home'))
    
    cart = get_cart()
    total = calculate_cart_total(cart)
    points = calculate_points(total)
    
    # Get customer points if logged in or verified member
    available_points = 0
    if customer_id:
        from services.db_service import get_customer_by_id
        customer = get_customer_by_id(customer_id)
        available_points = customer.get('points', 0) if customer else 0
    
    return render_template('cart.html', cart=cart, total=total, points=points, available_points=available_points, guest_mode=guest_mode)

@store_bp.route('/checkout', methods=['GET', 'POST'])
def checkout():
    """Self-checkout page with scanner integration. Supports guests."""
    role = session.get('role')
    guest_mode = session.get('guest_mode', False)
    
    if not (role == 'customer' or guest_mode):
        flash('Please login or continue as guest', 'warning')
        return redirect(url_for('home'))
    
    cart = get_cart()
    total = calculate_cart_total(cart)
    points = calculate_points(total)
    
    return render_template('checkout.html', cart=cart, total=total, points=points)

# --- Cart Management API ---
@store_bp.route('/api/cart/add', methods=['POST'])
def api_add_to_cart():
    """Add product to cart (from product page or scanner)."""
    data = request.get_json() or {}
    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 1))
    
    if not product_id:
        return jsonify({'success': False, 'error': 'Product ID required'}), 400
    
    # Get product from DB
    from services.db_service import get_product_by_id
    product = get_product_by_id(product_id)
    
    if not product:
        return jsonify({'success': False, 'error': 'Product not found'}), 404
    
    if product.get('total_quantity', 0) < quantity:
        return jsonify({'success': False, 'error': 'Insufficient stock'}), 400
    
    # Add to cart
    cart = get_cart()
    
    # Check if product already in cart
    existing = next((item for item in cart if item['product_id'] == product_id), None)
    if existing:
        existing['quantity'] += quantity
    else:
        cart.append({
            'product_id': product['product_id'],
            'name': product['name'],
            'price': product['price'],
            'quantity': quantity,
            'image_url': product.get('image_url')
        })
    
    save_cart(cart)
    cart_count = sum(item['quantity'] for item in cart)
    
    return jsonify({
        'success': True,
        'message': f'{product["name"]} added to cart',
        'cart_count': cart_count
    })

@store_bp.route('/api/cart/remove', methods=['POST'])
def api_remove_from_cart():
    """Remove product from cart."""
    data = request.get_json() or {}
    product_id = data.get('product_id')
    
    cart = get_cart()
    cart = [item for item in cart if item['product_id'] != product_id]
    save_cart(cart)
    
    return jsonify({'success': True, 'message': 'Item removed'})

@store_bp.route('/api/cart/update', methods=['POST'])
def api_update_cart_quantity():
    """Update quantity of item in cart."""
    data = request.get_json() or {}
    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 1))
    
    if quantity < 1:
        return api_remove_from_cart()
    
    cart = get_cart()
    item = next((i for i in cart if i['product_id'] == product_id), None)
    
    if item:
        item['quantity'] = quantity
        save_cart(cart)
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Item not in cart'}), 404

@store_bp.route('/api/cart/clear', methods=['POST'])
def api_clear_cart():
    """Clear entire cart."""
    session['cart'] = []
    session.modified = True
    return jsonify({'success': True})

# --- Guest Mode & Membership ---
@store_bp.route('/api/guest/start', methods=['POST'])
def api_start_guest_mode():
    """Enable guest browsing mode."""
    session['guest_mode'] = True
    session['role'] = None
    session.modified = True
    return jsonify({'success': True, 'message': 'Guest mode enabled'})

@store_bp.route('/api/membership/verify', methods=['POST'])
def api_verify_membership():
    """Verify membership number and enable checkout with points."""
    data = request.get_json() or {}
    membership_number = data.get('membership_number', '').strip()
    
    if not membership_number:
        return jsonify({'success': False, 'error': 'Membership number required'}), 400
    
    from services.db_service import get_customer_by_membership
    customer = get_customer_by_membership(membership_number)
    
    if not customer:
        return jsonify({'success': False, 'error': 'Invalid membership number'}), 404
    
    # Set session for guest checkout with membership
    session['customer_id'] = customer['customer_id']
    session['guest_mode'] = True  # Still guest, but with member benefits
    session['username'] = customer['email']  # For receipt email
    session.modified = True
    
    return jsonify({
        'success': True,
        'customer': {
            'name': f"{customer['first_name']} {customer['last_name']}",
            'email': customer['email'],
            'points': customer.get('points', 0),
            'membership_number': customer['membership_number']
        },
        'message': f"Welcome back, {customer['first_name']}! Your membership is verified."
    })

# --- Scanner Integration ---
@store_bp.route('/api/scan', methods=['POST'])
def api_scan_product():
    """Handle product scan (barcode or RFID)."""
    data = request.get_json() or {}
    code = data.get('code', '').strip()
    scan_type = data.get('type', 'barcode')  # 'barcode' or 'rfid'
    
    if not code:
        return jsonify({'success': False, 'error': 'No code provided'}), 400
    
    # Find product by code
    if scan_type == 'barcode':
        product = get_product_by_code(upc=code)
    else:
        product = get_product_by_code(epc=code)
    
    if not product:
        return jsonify({'success': False, 'error': 'Product not found in system'}), 404
    
    if product.get('total_quantity', 0) < 1:
        return jsonify({'success': False, 'error': 'Product out of stock'}), 400
    
    # Add to cart
    cart = get_cart()
    existing = next((item for item in cart if item['product_id'] == product['product_id']), None)
    
    if existing:
        existing['quantity'] += 1
    else:
        cart.append({
            'product_id': product['product_id'],
            'name': product['name'],
            'price': product['price'],
            'quantity': 1,
            'image_url': product.get('image_url')
        })
    
    save_cart(cart)
    
    return jsonify({
        'success': True,
        'product': {
            'name': product['name'],
            'price': product['price'],
            'image_url': product.get('image_url')
        },
        'cart_count': sum(item['quantity'] for item in cart)
    })

# --- Purchase / Checkout ---
@store_bp.route('/api/purchase', methods=['POST'])
def api_complete_purchase():
    """Complete purchase and generate receipt. Supports guest checkout and point redemption."""
    data = request.get_json() or {}
    
    # Get customer_id - can be from session (logged in) or from membership verification (guest with member #)
    customer_id = session.get('customer_id')
    guest_mode = session.get('guest_mode', False)
    points_to_redeem = int(data.get('points_to_redeem', 0))
    
    cart = get_cart()
    if not cart:
        return jsonify({'success': False, 'error': 'Cart is empty'}), 400
    
    original_total = calculate_cart_total(cart)
    discount = 0
    
    # Handle point redemption (only for logged-in or verified members)
    if customer_id and points_to_redeem > 0:
        from services.db_service import get_customer_by_id
        customer = get_customer_by_id(customer_id)
        
        if not customer:
            return jsonify({'success': False, 'error': 'Customer not found'}), 404
        
        available_points = customer.get('points', 0)
        
        # Validate point redemption
        if points_to_redeem > available_points:
            return jsonify({'success': False, 'error': f'Insufficient points. You have {available_points} points.'}), 400
        
        # Calculate discount (100 points = $1)
        discount = points_to_redeem / 100.0
        
        # Can't redeem more than the total
        if discount > original_total:
            return jsonify({'success': False, 'error': 'Discount cannot exceed cart total'}), 400
    
    # Calculate final total after discount
    final_total = max(0, original_total - discount)
    
    # Calculate points to earn (only if customer_id exists, not for pure guests)
    points_to_earn = calculate_points(final_total) if customer_id else 0
    
    # Prepare items for DB
    items = [
        {
            'product_id': item['product_id'],
            'quantity': item['quantity'],
            'price': item['price']
        }
        for item in cart
    ]
    
    # Create purchase (customer_id can be None for pure guests)
    purchase_id = create_purchase(customer_id, final_total, points_to_earn, items, points_redeemed=points_to_redeem)
    
    if purchase_id:
        # Clear cart
        session['cart'] = []
        session.modified = True
        
        # Send receipt email (optional)
        try:
            from services.email_service import email_service
            customer_email = session.get('username')  # email stored as username
            if customer_email:
                send_receipt_email(customer_email, purchase_id, cart, final_total, points_to_earn)
        except Exception as e:
            print(f"Failed to send receipt email: {e}")
        
        # Build response message
        message = f'Purchase complete for ${final_total:.2f}!'
        if discount > 0:
            message += f' You redeemed {points_to_redeem} points for ${discount:.2f} off.'
        if points_to_earn > 0:
            message += f' You earned {points_to_earn} points.'
        
        return jsonify({
            'success': True,
            'purchase_id': purchase_id,
            'points_earned': points_to_earn,
            'points_redeemed': points_to_redeem,
            'discount': discount,
            'final_total': final_total,
            'message': message
        })
    else:
        return jsonify({'success': False, 'error': 'Failed to process purchase'}), 500

# --- Customer Account ---
@store_bp.route('/account')
def account():
    """Customer account page with purchase history."""
    if session.get('role') != 'customer':
        flash('Please login as a customer', 'warning')
        return redirect(url_for('auth.login'))
    
    customer_id = session.get('customer_id')
    purchases = get_customer_purchases(customer_id, limit=20)
    
    # Get customer points
    from services.db_service import get_customer_by_email
    customer = get_customer_by_email(session.get('username'))
    points = customer.get('points', 0) if customer else 0
    
    return render_template('account.html', purchases=purchases, points=points, customer=customer)

@store_bp.route('/change-password', methods=['POST'])
def change_password():
    """Change customer password."""
    if session.get('role') != 'customer':
        flash('Please login as a customer', 'warning')
        return redirect(url_for('auth.login'))
    
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    # Validation
    if not all([current_password, new_password, confirm_password]):
        flash('All password fields are required', 'danger')
        return redirect(url_for('store.account'))
    
    if new_password != confirm_password:
        flash('New passwords do not match', 'danger')
        return redirect(url_for('store.account'))
    
    if len(new_password) < 6:
        flash('Password must be at least 6 characters', 'danger')
        return redirect(url_for('store.account'))
    
    # Get customer
    from services.db_service import get_customer_by_email, supabase
    customer = get_customer_by_email(session.get('username'))
    
    if not customer:
        flash('Customer not found', 'danger')
        return redirect(url_for('store.account'))
    
    # Verify current password
    if not check_password_hash(customer.get('password_hash', ''), current_password):
        flash('Current password is incorrect', 'danger')
        return redirect(url_for('store.account'))
    
    # Update password
    try:
        new_hash = generate_password_hash(new_password)
        supabase.table("customers").update({
            "password_hash": new_hash
        }).eq("customer_id", customer['customer_id']).execute()
        
        flash('Password updated successfully!', 'success')
    except Exception as e:
        print(f"Error updating password: {e}")
        flash('Failed to update password', 'danger')
    
    return redirect(url_for('store.account'))

@store_bp.route('/receipt/<int:purchase_id>')
def view_receipt(purchase_id):
    """View receipt for a purchase (accessible by customer owner or admin)."""
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Please login', 'warning')
        return redirect(url_for('auth.login'))
    
    user_role = session.get('role')
    
    # Must be either customer or admin
    if user_role not in ['customer', 'admin']:
        flash('Access denied', 'danger')
        return redirect(url_for('home'))
    
    details = get_purchase_details(purchase_id)
    
    if not details:
        flash('Receipt not found', 'danger')
        if user_role == 'admin':
            return redirect(url_for('payments.payments_list'))
        return redirect(url_for('store.account'))
    
    # For customers: verify they own this purchase
    # For admins: allow access to any receipt
    if user_role == 'customer':
        if details['purchase']['customer_id'] != session.get('customer_id'):
            flash('Access denied', 'danger')
            return redirect(url_for('store.account'))
    
    return render_template('receipt.html', purchase=details['purchase'], items=details['items'])


def send_receipt_email(email, purchase_id, items, total, points):
    """Send receipt email to customer."""
    from services.email_service import email_service
    
    # Build receipt body
    body = f"""Thank you for shopping at Smart Store!

Purchase ID: {purchase_id}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Items:
"""
    for item in items:
        body += f"- {item['name']} x{item['quantity']} @ ${item['price']:.2f} = ${item['price'] * item['quantity']:.2f}\n"
    
    body += f"""
Total: ${total:.2f}
Points Earned: {points}

Thank you for your purchase!
"""
    
    email_service._send_email(f"Receipt #{purchase_id} - Smart Store", body)
