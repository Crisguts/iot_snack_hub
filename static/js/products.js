// Products page - Admin product management with modals

function showNotification(message, type = 'success') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);
    setTimeout(() => alertDiv.remove(), 3000);
}

// Add product
async function addProduct() {
    const form = document.getElementById('addProductForm');
    const formData = new FormData(form);
    const data = Object.fromEntries(formData);

    try {
        const response = await fetch('/products/api/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        if (result.success) {
            bootstrap.Modal.getInstance(document.getElementById('addProductModal')).hide();
            showNotification(`Product "${data.name}" added successfully!`, 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        alert('Error adding product: ' + error);
    }
}

// Open edit modal with product data
function openEditModal(id, name, category, price, upc, producer, imageUrl) {
    document.getElementById('editProductId').value = id;
    document.getElementById('editName').value = name;
    document.getElementById('editCategory').value = category;
    document.getElementById('editPrice').value = price;
    document.getElementById('editUpc').value = upc;
    document.getElementById('editProducer').value = producer;
    document.getElementById('editImageUrl').value = imageUrl;
    new bootstrap.Modal(document.getElementById('editProductModal')).show();
}

// Update product
async function updateProduct() {
    const id = document.getElementById('editProductId').value;
    const data = {
        name: document.getElementById('editName').value,
        category: document.getElementById('editCategory').value,
        price: document.getElementById('editPrice').value,
        upc: document.getElementById('editUpc').value,
        producer: document.getElementById('editProducer').value,
        image_url: document.getElementById('editImageUrl').value
    };

    try {
        const response = await fetch(`/products/api/update/${id}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        if (result.success) {
            bootstrap.Modal.getInstance(document.getElementById('editProductModal')).hide();
            showNotification(`Product "${data.name}" updated successfully!`, 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        alert('Error updating product: ' + error);
    }
}

// Delete product
async function deleteProduct(id, name) {
    if (!confirm(`Delete product "${name}"?`)) return;

    try {
        const response = await fetch(`/products/api/delete/${id}`, {
            method: 'POST'
        });

        const result = await response.json();
        if (response.ok && result.success) {
            showNotification(`Product "${name}" deleted successfully!`, 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            alert(result.error || 'Error deleting product');
        }
    } catch (error) {
        alert('Error deleting product: ' + error);
    }
}

// Open inventory modal
function openInventoryModal(id, name, currentStock) {
    document.getElementById('inventoryProductId').value = id;
    document.getElementById('inventoryProductName').textContent = name;
    document.getElementById('inventoryCurrentStock').textContent = currentStock;
    document.getElementById('inventoryCurrentStockValue').value = currentStock;
    document.getElementById('inventoryQuantity').value = 1;
    new bootstrap.Modal(document.getElementById('inventoryModal')).show();
}

// Open stock items modal and load EPCs for product
async function openStockModal(id, name) {
    document.getElementById('stockProductId').value = id;
    document.getElementById('stockProductName').textContent = name;

    // Show modal immediately with loading state
    const modal = new bootstrap.Modal(document.getElementById('stockItemsModal'));
    modal.show();

    // Show loading, hide content
    document.getElementById('stockItemsLoading').style.display = 'block';
    document.getElementById('stockItemsContent').style.display = 'none';

    // Load stock items
    await loadStockItems(id);
}

// Load and display stock items for a product
async function loadStockItems(productId) {
    try {
        const response = await fetch(`/products/api/products/${productId}/stock`);
        const result = await response.json();

        // Hide loading
        document.getElementById('stockItemsLoading').style.display = 'none';
        document.getElementById('stockItemsContent').style.display = 'block';

        if (result.success && result.stock_items && result.stock_items.length > 0) {
            const tbody = document.getElementById('stockItemsTableBody');
            tbody.innerHTML = '';

            result.stock_items.forEach(item => {
                const tr = document.createElement('tr');

                // Status badge color
                let statusClass = 'secondary';
                if (item.status === 'available') statusClass = 'success';
                else if (item.status === 'sold') statusClass = 'danger';
                else if (item.status === 'damaged') statusClass = 'warning';

                // Format dates
                const createdDate = item.created_at ? new Date(item.created_at).toLocaleDateString() : '-';
                const soldDate = item.sold_at ? new Date(item.sold_at).toLocaleDateString() : '-';

                tr.innerHTML = `
                    <td>${item.stock_id}</td>
                    <td><code class="text-warning">${item.epc}</code></td>
                    <td><span class="badge bg-${statusClass}">${item.status}</span></td>
                    <td>${createdDate}</td>
                    <td>${soldDate}</td>
                `;
                tbody.appendChild(tr);
            });

            document.getElementById('stockItemsEmpty').style.display = 'none';
        } else {
            // No stock items found
            document.getElementById('stockItemsEmpty').style.display = 'block';
            document.getElementById('stockItemsTableBody').innerHTML = '';
        }
    } catch (error) {
        alert('Error loading stock items: ' + error);
        document.getElementById('stockItemsLoading').style.display = 'none';
        document.getElementById('stockItemsContent').style.display = 'block';
        document.getElementById('stockItemsEmpty').style.display = 'block';
    }
}


// Adjust inventory (add or subtract)
async function adjustInventory() {
    const id = document.getElementById('inventoryProductId').value;
    const quantity = parseInt(document.getElementById('inventoryQuantity').value);
    const currentStock = parseInt(document.getElementById('inventoryCurrentStockValue').value);

    if (isNaN(quantity)) {
        alert('Please enter a valid number');
        return;
    }

    // If quantity is 0, set stock to 0 by subtracting all current stock
    const adjustAmount = quantity === 0 ? -currentStock : quantity;

    // Check if subtracting would result in negative stock
    const newStock = currentStock + adjustAmount;
    if (newStock < 0) {
        alert(`Cannot subtract ${Math.abs(adjustAmount)} - only ${currentStock} units in stock. To set to 0, enter 0 or -${currentStock}`);
        return;
    }

    try {
        const response = await fetch(`/products/api/inventory/${id}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ quantity: adjustAmount })
        });

        const result = await response.json();

        if (response.ok && result.success) {
            bootstrap.Modal.getInstance(document.getElementById('inventoryModal')).hide();
            const productName = document.getElementById('inventoryProductName').textContent;
            if (adjustAmount > 0) {
                showNotification(`Added ${adjustAmount} units to ${productName}`, 'success');
            } else if (adjustAmount < 0) {
                showNotification(`Removed ${Math.abs(adjustAmount)} units from ${productName}`, 'success');
            } else {
                showNotification(`Stock set to 0 for ${productName}`, 'success');
            }
            setTimeout(() => location.reload(), 1000);
        } else {
            alert(result.error || 'Error updating inventory');
        }
    } catch (error) {
        alert('Error updating inventory: ' + error);
    }
}

// Event listeners for action buttons (replaces inline onclick to avoid linter errors)
document.addEventListener('DOMContentLoaded', function () {
    // Inventory buttons
    document.querySelectorAll('.inventory-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            const id = parseInt(this.dataset.productId);
            const name = this.dataset.productName;
            const stock = parseInt(this.dataset.totalQuantity);
            openInventoryModal(id, name, stock);
        });
    });

    // Stock Items buttons
    document.querySelectorAll('.stock-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            const id = parseInt(this.dataset.productId);
            const name = this.dataset.productName;
            openStockModal(id, name);
        });
    });

    // Edit buttons
    document.querySelectorAll('.edit-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            const id = parseInt(this.dataset.productId);
            const name = this.dataset.productName;
            const category = this.dataset.category;
            const price = parseFloat(this.dataset.price);
            const upc = this.dataset.upc;
            const producer = this.dataset.producer;
            const imageUrl = this.dataset.imageUrl;
            openEditModal(id, name, category, price, upc, producer, imageUrl);
        });
    });

    // Delete buttons
    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            const id = parseInt(this.dataset.productId);
            const name = this.dataset.productName;
            deleteProduct(id, name);
        });
    });

    // Update Product button in Edit Modal
    const updateProductBtn = document.getElementById('updateProductBtn');
    if (updateProductBtn) {
        updateProductBtn.addEventListener('click', updateProduct);
    }

    // Update Stock button in Inventory Modal
    const updateStockBtn = document.getElementById('updateStockBtn');
    if (updateStockBtn) {
        updateStockBtn.addEventListener('click', adjustInventory);
    }
});
