// Self-checkout scanner functionality
// Handles barcode/RFID scanning, cart management, and purchase completion

// Listen for barcode scanner input (USB scanner acts as keyboard)
document.getElementById('barcodeInput').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        e.preventDefault();
        const barcode = this.value.trim();
        if (barcode) {
            // Validate barcode format (8-14 digits for UPC/EAN)
            if (!/^\d{8,14}$/.test(barcode)) {
                showNotification('Invalid barcode format. Please try again.', 'danger');
                this.value = '';
                return;
            }
            scanProduct(barcode, 'barcode');
            this.value = '';
        }
    }
});

// Manual RFID scan handler
function scanRFID() {
    const rfid = document.getElementById('rfidInput').value.trim();
    if (rfid) {
        // Validate RFID format (typically alphanumeric, 8-24 characters)
        if (!/^[A-Fa-f0-9]{8,24}$/.test(rfid)) {
            showNotification('Invalid RFID format. Please try again.', 'danger');
            document.getElementById('rfidInput').value = '';
            return;
        }
        scanProduct(rfid, 'rfid');
        document.getElementById('rfidInput').value = '';
    }
}

// Scan product and add to cart
async function scanProduct(code, type) {
    try {
        const response = await fetch('/store/api/scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code: code, type: type })
        });

        const data = await response.json();

        if (data.success) {
            showNotification(`${data.product.name} added to cart!`, 'success');
            addItemToCartUI(data.product);
            updateCartTotals();

            // Re-focus barcode input
            document.getElementById('barcodeInput').focus();
        } else {
            // Show specific error message
            showNotification(data.error || 'Product not found in database', 'danger');
        }
    } catch (error) {
        console.error('Scan error:', error);
        showNotification('Error scanning product', 'danger');
    }
}

// Add item to cart UI dynamically
function addItemToCartUI(product) {
    const cartItems = document.getElementById('cartItems');
    const emptyCart = document.getElementById('emptyCart');

    if (emptyCart) {
        emptyCart.remove();
    }

    // Check if product already in cart
    const existing = cartItems.querySelector(`[data-product-id="${product.product_id}"]`);
    if (existing) {
        const qtyInput = existing.querySelector('.qty-input');
        qtyInput.value = parseInt(qtyInput.value) + 1;
        qtyInput.dispatchEvent(new Event('change'));
        return;
    }

    // Add new row
    const row = document.createElement('div');
    row.className = 'row align-items-center mb-2 border-bottom pb-2';
    row.setAttribute('data-product-id', product.product_id);
    row.innerHTML = `
        <div class="col-4">
            ${product.image_url ? `<img src="${product.image_url}" style="width:40px;height:40px;object-fit:cover;margin-right:10px;">` : ''}
            ${product.name}
        </div>
        <div class="col-2">$${parseFloat(product.price).toFixed(2)}</div>
        <div class="col-2">
            <input type="number" class="form-control form-control-sm qty-input" 
                value="1" min="1" data-product-id="${product.product_id}">
        </div>
        <div class="col-2 subtotal">$${parseFloat(product.price).toFixed(2)}</div>
        <div class="col-2">
            <button class="btn btn-sm btn-danger remove-item" 
                data-product-id="${product.product_id}">Remove</button>
        </div>
    `;

    cartItems.appendChild(row);

    // Attach event listeners
    attachItemListeners(row);
}

// Attach event listeners to cart item
function attachItemListeners(row) {
    const qtyInput = row.querySelector('.qty-input');
    const removeBtn = row.querySelector('.remove-item');

    qtyInput.addEventListener('change', function () {
        const quantity = parseInt(this.value);
        if (quantity < 1) {
            this.value = 1;
            return;
        }
        updateItemQuantity(this.dataset.productId, quantity);
    });

    // Also handle input event for real-time updates
    qtyInput.addEventListener('input', function () {
        const quantity = parseInt(this.value) || 1;
        if (quantity < 1) {
            this.value = 1;
        }
        // Update UI immediately
        const price = parseFloat(row.querySelector('.col-2:nth-child(2)').textContent.replace('$', ''));
        const subtotal = price * quantity;
        row.querySelector('.subtotal').textContent = `$${subtotal.toFixed(2)}`;
        updateCartTotals();
    });

    removeBtn.addEventListener('click', function () {
        removeItem(this.dataset.productId);
    });
}

// Update item quantity
async function updateItemQuantity(productId, quantity) {
    try {
        const response = await fetch('/store/api/cart/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ product_id: parseInt(productId), quantity: quantity })
        });

        const data = await response.json();
        if (data.success) {
            // Update totals after backend confirms
            updateCartTotals();
        } else {
            showNotification('Failed to update quantity', 'danger');
        }
    } catch (error) {
        console.error('Update error:', error);
        showNotification('Error updating quantity', 'danger');
    }
}

// Remove item from cart
async function removeItem(productId) {
    try {
        const response = await fetch('/store/api/cart/remove', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ product_id: parseInt(productId) })
        });

        if (response.ok) {
            const row = document.querySelector(`[data-product-id="${productId}"]`);
            if (row) {
                row.remove();
            }
            updateCartTotals();
            checkEmptyCart();
        }
    } catch (error) {
        console.error('Remove error:', error);
    }
}

// Update cart totals
function updateCartTotals() {
    const rows = document.querySelectorAll('#cartItems > .row[data-product-id]');
    let total = 0;

    rows.forEach(row => {
        const price = parseFloat(row.querySelector('.col-2:nth-child(2)').textContent.replace('$', ''));
        const qty = parseInt(row.querySelector('.qty-input').value);
        const subtotal = price * qty;

        row.querySelector('.subtotal').textContent = `$${subtotal.toFixed(2)}`;
        total += subtotal;
    });

    document.getElementById('cartTotal').textContent = `$${total.toFixed(2)}`;
    document.getElementById('pointsEarn').textContent = Math.floor(total);
}

// Check if cart is empty
function checkEmptyCart() {
    const cartItems = document.getElementById('cartItems');
    const rows = cartItems.querySelectorAll('.row[data-product-id]');

    if (rows.length === 0) {
        cartItems.innerHTML = '<div class="text-center text-light mt-5" id="emptyCart">No items scanned. Start scanning products!</div>';
    }
}

// Clear cart
async function clearCart() {
    if (!confirm('Are you sure you want to clear the entire cart?')) {
        return;
    }

    try {
        const response = await fetch('/store/api/cart/clear', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        if (response.ok) {
            document.getElementById('cartItems').innerHTML =
                '<div class="text-center text-light mt-5" id="emptyCart">No items scanned. Start scanning products!</div>';
            updateCartTotals();
            showNotification('Cart cleared', 'info');
        }
    } catch (error) {
        console.error('Clear cart error:', error);
    }
}

// Confirm purchase - only if button exists
const confirmBtn = document.getElementById('confirmPurchaseBtn');
if (confirmBtn) {
    confirmBtn.addEventListener('click', async function () {
        this.disabled = true;
        this.textContent = 'Processing...';

        try {
            const response = await fetch('/store/api/purchase', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            const data = await response.json();

            if (data.success) {
                document.getElementById('successMessage').textContent = data.message;
                const modal = new bootstrap.Modal(document.getElementById('successModal'));
                modal.show();

                // Clear cart UI
                document.getElementById('cartItems').innerHTML =
                    '<div class="text-center text-light mt-5" id="emptyCart">No items scanned. Start scanning products!</div>';
                updateCartTotals();
            } else {
                showNotification(data.error || 'Purchase failed', 'danger');
                this.disabled = false;
                this.textContent = 'Confirm Purchase';
            }
        } catch (error) {
            console.error('Purchase error:', error);
            showNotification('Error processing purchase', 'danger');
            this.disabled = false;
            this.textContent = 'Confirm Purchase';
        }
    });
}

// Initialize: attach listeners to existing items
document.addEventListener('DOMContentLoaded', function () {
    // Attach listeners to existing cart items
    document.querySelectorAll('#cartItems > .row[data-product-id]').forEach(row => {
        attachItemListeners(row);
    });

    // Focus barcode input
    document.getElementById('barcodeInput').focus();

    // Initial totals calculation
    updateCartTotals();
});

// Helper: show notification
function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top:20px;right:20px;z-index:9999;max-width:350px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);

    setTimeout(() => {
        alertDiv.classList.add('hide-slide');
        setTimeout(() => alertDiv.remove(), 500);
    }, 3000);
}
