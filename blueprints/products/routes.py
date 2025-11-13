# blueprints/products/routes.py - Admin Product Management
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from services.db_service import (
    get_all_products, get_product_by_id, add_product, 
    update_product, delete_product, add_inventory_reception,
    get_inventory_history
)

products_bp = Blueprint("products", __name__, url_prefix="/products")

def admin_required(f):
    """Decorator to require admin access."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('Admin access required', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@products_bp.route('/')
@admin_required
def products_list():
    """Admin product management page with pagination."""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    all_products = get_all_products()
    total_products = len(all_products)
    total_pages = (total_products + per_page - 1) // per_page  # Ceiling division
    
    # Paginate
    start = (page - 1) * per_page
    end = start + per_page
    products = all_products[start:end]
    
    return render_template('products.html', 
                         products=products, 
                         page=page, 
                         total_pages=total_pages,
                         total_products=total_products)

@products_bp.route('/add', methods=['GET', 'POST'])
@admin_required
def add_product_page():
    """Add new product."""
    if request.method == 'GET':
        return render_template('product_form.html', action='add')
    
    # POST - create product
    data = request.form.to_dict()
    
    required = ['name', 'category', 'price', 'upc', 'epc', 'producer']
    missing = [f for f in required if not data.get(f)]
    
    if missing:
        flash(f'Missing fields: {", ".join(missing)}', 'danger')
        return redirect(url_for('products.add_product_page'))
    
    product = add_product(
        name=data['name'],
        category=data['category'],
        price=float(data['price']),
        upc=data['upc'],
        epc=data['epc'],
        producer=data['producer'],
        image_url=data.get('image_url')
    )
    
    if product:
        flash(f'Product "{data["name"]}" added successfully!', 'success')
        return redirect(url_for('products.products_list'))
    else:
        flash('Error adding product', 'danger')
        return redirect(url_for('products.add_product_page'))

@products_bp.route('/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product_page(product_id):
    """Edit existing product."""
    product = get_product_by_id(product_id)
    
    if not product:
        flash('Product not found', 'danger')
        return redirect(url_for('products.products_list'))
    
    if request.method == 'GET':
        return render_template('product_form.html', action='edit', product=product)
    
    # POST - update product
    data = request.form.to_dict()
    
    update_data = {
        'name': data.get('name'),
        'category': data.get('category'),
        'price': float(data.get('price', 0)),
        'upc': data.get('upc'),
        'epc': data.get('epc'),
        'producer': data.get('producer'),
        'image_url': data.get('image_url')
    }
    
    if update_product(product_id, **update_data):
        flash('Product updated successfully!', 'success')
    else:
        flash('Error updating product', 'danger')
    
    return redirect(url_for('products.products_list'))

@products_bp.route('/delete/<int:product_id>')
@admin_required
def delete_product_route(product_id):
    """Delete product."""
    if delete_product(product_id):
        flash('Product deleted', 'success')
    else:
        flash('Error deleting product', 'danger')
    
    return redirect(url_for('products.products_list'))

@products_bp.route('/inventory/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def manage_inventory(product_id):
    """Manage product inventory (receive stock)."""
    product = get_product_by_id(product_id)
    
    if not product:
        flash('Product not found', 'danger')
        return redirect(url_for('products.products_list'))
    
    if request.method == 'GET':
        history = get_inventory_history(product_id)
        return render_template('inventory.html', product=product, history=history)
    
    # POST - add stock
    quantity = int(request.form.get('quantity', 0))
    
    if quantity < 1:
        flash('Invalid quantity', 'danger')
        return redirect(url_for('products.manage_inventory', product_id=product_id))
    
    if add_inventory_reception(product_id, quantity):
        flash(f'Added {quantity} units to inventory', 'success')
    else:
        flash('Error adding inventory', 'danger')
    
    return redirect(url_for('products.manage_inventory', product_id=product_id))


@products_bp.route('/api/search', methods=['GET'])
def api_search_products():
    """Search products by name, UPC, or EPC."""
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'success': True, 'products': []})
    
    products = get_all_products()
    
    # Simple search
    results = [
        p for p in products
        if query.lower() in p.get('name', '').lower()
        or query in p.get('upc', '')
        or query in p.get('epc', '')
    ]
    
    return jsonify({'success': True, 'products': results})

@products_bp.route('/api/product/<int:product_id>')
def api_get_product(product_id):
    """Get product details."""
    product = get_product_by_id(product_id)
    
    if product:
        return jsonify({'success': True, 'product': product})
    else:
        return jsonify({'success': False, 'error': 'Product not found'}), 404

@products_bp.route('/api/add', methods=['POST'])
@admin_required
def api_add_product():
    """API endpoint to add product via AJAX."""
    try:
        data = request.json
        
        required = ['name', 'category', 'price', 'upc', 'epc', 'producer']
        missing = [f for f in required if not data.get(f)]
        
        if missing:
            return jsonify({'success': False, 'error': f'Missing fields: {", ".join(missing)}'}), 400
        
        product = add_product(
            name=data['name'],
            category=data['category'],
            price=float(data['price']),
            upc=data['upc'],
            epc=data['epc'],
            producer=data['producer'],
            image_url=data.get('image_url')
        )
        
        if product:
            return jsonify({'success': True, 'product': product})
        else:
            return jsonify({'success': False, 'error': 'Error adding product'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@products_bp.route('/api/update/<int:product_id>', methods=['POST'])
@admin_required
def api_update_product(product_id):
    """API endpoint to update product via AJAX."""
    try:
        data = request.json
        
        update_data = {
            'name': data.get('name'),
            'category': data.get('category'),
            'price': float(data.get('price', 0)),
            'upc': data.get('upc'),
            'epc': data.get('epc'),
            'producer': data.get('producer'),
            'image_url': data.get('image_url')
        }
        
        if update_product(product_id, **update_data):
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Error updating product'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@products_bp.route('/api/delete/<int:product_id>', methods=['POST'])
@admin_required
def api_delete_product(product_id):
    """API endpoint to delete product via AJAX."""
    try:
        if delete_product(product_id):
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Error deleting product'}), 500
    except Exception as e:
        error_msg = str(e)
        # Check if it's a foreign key constraint error
        if 'purchase_items' in error_msg or '23503' in error_msg or 'foreign key' in error_msg.lower():
            return jsonify({
                'success': False, 
                'error': 'Cannot delete product - it has been purchased before. You can set inventory to 0 instead.'
            }), 400
        return jsonify({'success': False, 'error': error_msg}), 500

@products_bp.route('/api/inventory/<int:product_id>', methods=['POST'])
@admin_required
def api_add_inventory(product_id):
    """API endpoint to adjust inventory via AJAX (add or subtract)."""
    try:
        data = request.json
        quantity = int(data.get('quantity', 0))
        
        # Get current product to check stock levels
        product = get_product_by_id(product_id)
        if not product:
            return jsonify({'success': False, 'error': 'Product not found'}), 404
        
        current_stock = product.get('total_quantity', 0)
        new_stock = current_stock + quantity
        
        # Check we don't go negative
        if new_stock < 0:
            return jsonify({
                'success': False, 
                'error': f'Cannot subtract {abs(quantity)} - only {current_stock} units in stock'
            }), 400
        
        # Use the existing function for positive quantities, or update directly for negative/zero
        if quantity > 0:
            if add_inventory_reception(product_id, quantity):
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'Error adding inventory'}), 500
        else:
            # Subtract inventory or set to 0 by updating the product directly
            if update_product(product_id, total_quantity=new_stock):
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'Error updating inventory'}), 500
                
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
