# blueprints/store/routes.py - Customer Store & Cart System
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash
from services.db_service import (
    get_all_products, get_product_by_code, create_purchase,
    get_customer_purchases, get_purchase_details
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
    """Customer store homepage (product catalog)."""
    if session.get('role') != 'customer':
        flash('Please login as a customer to access the store', 'warning')
        return redirect(url_for('auth.login'))
    
    products = get_all_products()
    # Filter only products with stock
    available_products = [p for p in products if p.get('total_quantity', 0) > 0]
    
    cart = get_cart()
    cart_count = sum(item['quantity'] for item in cart)
    
    return render_template('store.html', products=available_products, cart_count=cart_count)

@store_bp.route('/cart')
def cart():
    """View shopping cart."""
    if session.get('role') != 'customer':
        flash('Please login as a customer', 'warning')
        return redirect(url_for('auth.login'))
    
    cart = get_cart()
    total = calculate_cart_total(cart)
    points = calculate_points(total)
    
    return render_template('cart.html', cart=cart, total=total, points=points)

@store_bp.route('/checkout', methods=['GET', 'POST'])
def checkout():
    """Self-checkout page with scanner integration."""
    if session.get('role') != 'customer':
        flash('Please login as a customer', 'warning')
        return redirect(url_for('auth.login'))
    
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
    """Complete purchase and generate receipt."""
    customer_id = session.get('customer_id')
    
    if not customer_id:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    cart = get_cart()
    if not cart:
        return jsonify({'success': False, 'error': 'Cart is empty'}), 400
    
    total = calculate_cart_total(cart)
    points = calculate_points(total)
    
    # Prepare items for DB
    items = [
        {
            'product_id': item['product_id'],
            'quantity': item['quantity'],
            'price': item['price']
        }
        for item in cart
    ]
    
    # Create purchase
    purchase_id = create_purchase(customer_id, total, points, items)
    
    if purchase_id:
        # Clear cart
        session['cart'] = []
        session.modified = True
        
        # Send receipt email (optional)
        try:
            from services.email_service import email_service
            customer_email = session.get('username')  # email stored as username
            if customer_email:
                send_receipt_email(customer_email, purchase_id, cart, total, points)
        except Exception as e:
            print(f"Failed to send receipt email: {e}")
        
        return jsonify({
            'success': True,
            'purchase_id': purchase_id,
            'points_earned': points,
            'message': f'Purchase complete! You earned {points} points.'
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
    """View receipt for a purchase."""
    if session.get('role') != 'customer':
        flash('Please login', 'warning')
        return redirect(url_for('auth.login'))
    
    details = get_purchase_details(purchase_id)
    
    if not details:
        flash('Receipt not found', 'danger')
        return redirect(url_for('store.account'))
    
    # Verify ownership
    if details['purchase']['customer_id'] != session.get('customer_id'):
        flash('Access denied', 'danger')
        return redirect(url_for('store.account'))
    
    return render_template('receipt.html', purchase=details['purchase'], items=details['items'])

# --- Helper Functions ---
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
