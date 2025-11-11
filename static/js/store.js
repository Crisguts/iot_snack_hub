// static/js/store.js - Product catalog functionality

// Add to cart handler
document.querySelectorAll('.add-to-cart').forEach(btn => {
    btn.addEventListener('click', async function () {
        const productId = this.dataset.productId;
        this.disabled = true;
        this.textContent = 'Adding...';

        try {
            const response = await fetch('/store/api/cart/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ product_id: parseInt(productId), quantity: 1 })
            });

            const data = await response.json();

            if (data.success) {
                showNotification(data.message, 'success');
                this.textContent = '✓ Added';

                // Update cart badge
                const badge = document.querySelector('.badge');
                if (badge) {
                    badge.textContent = data.cart_count;
                }

                setTimeout(() => {
                    this.disabled = false;
                    this.textContent = 'Add to Cart';
                }, 1500);
            } else {
                showNotification(data.error, 'danger');
                this.disabled = false;
                this.textContent = 'Add to Cart';
            }
        } catch (error) {
            console.error('Add to cart error:', error);
            showNotification('Error adding to cart', 'danger');
            this.disabled = false;
            this.textContent = 'Add to Cart';
        }
    });
});

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
