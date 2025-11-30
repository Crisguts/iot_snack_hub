# Database service layer - Supabase PostgreSQL integration
# Handles all database operations for customers, products, purchases, and temperature readings
from unittest.mock import MagicMock
import os
import secrets
from datetime import datetime

try:
    from supabase import create_client, Client
    from dotenv import load_dotenv
    load_dotenv()
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    DB_AVAILABLE = True
except Exception as e:
    print(f"⚠️ DB mock loaded: {e}")
    supabase = MagicMock()
    DB_AVAILABLE = False


def init_db():
    """Initialize database connection (Supabase tables are managed online)."""
    print("✅ Supabase connection ready." if DB_AVAILABLE else "⚠️ Mock DB active")


# =============================================================================
# EPC Generator and Stock Management Functions
# =============================================================================

def generate_epc():
    """Generate a unique 24-character hexadecimal EPC code for RFID tags.
    Format: 24 hex characters (e.g., '3034257BF7194E4FAFA8B9B8')
    """
    return secrets.token_hex(12).upper()  # 12 bytes = 24 hex chars


def add_stock_item(product_id, epc=None):
    """Add a single stock item with unique EPC to product_stock table.
    
    Args:
        product_id: ID of the product this stock item belongs to
        epc: Optional EPC code (if None, will be auto-generated)
    
    Returns:
        stock_id of the created item, or None on error
    """
    try:
        if not epc:
            epc = generate_epc()
        
        data = {
            "epc": epc,
            "product_id": product_id,
            "status": "available",
            "created_at": datetime.now().isoformat()
        }
        response = supabase.table("product_stock").insert(data).execute()
        return response.data[0]["stock_id"] if response.data else None
    except Exception as e:
        print(f"Error adding stock item: {e}")
        return None


def get_available_stock_items(product_id, quantity=1):
    """Get available stock items for a product.
    
    Args:
        product_id: Product to find stock for
        quantity: Number of items needed
    
    Returns:
        List of stock_id values (up to quantity requested)
    """
    try:
        response = (
            supabase.table("product_stock")
            .select("stock_id, epc")
            .eq("product_id", product_id)
            .eq("status", "available")
            .limit(quantity)
            .execute()
        )
        return [item["stock_id"] for item in (response.data or [])]
    except Exception as e:
        print(f"Error fetching available stock: {e}")
        return []


def mark_stock_as_sold(stock_id, purchase_id):
    """Mark a stock item as sold and link to purchase.
    
    Args:
        stock_id: ID of the stock item to mark as sold
        purchase_id: ID of the purchase this item belongs to
    
    Returns:
        True on success, False on error
    """
    try:
        supabase.table("product_stock").update({
            "status": "sold",
            "sold_at": datetime.now().isoformat(),
            "purchase_id": purchase_id
        }).eq("stock_id", stock_id).execute()
        return True
    except Exception as e:
        print(f"Error marking stock as sold: {e}")
        return False


def get_stock_items_for_product(product_id):
    """Get all stock items for a product (for admin stock modal).
    
    Args:
        product_id: Product to get stock items for
    
    Returns:
        List of stock items with their EPCs, status, and timestamps
    """
    try:
        response = (
            supabase.table("product_stock")
            .select("stock_id, epc, status, created_at, sold_at, purchase_id")
            .eq("product_id", product_id)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data or []
    except Exception as e:
        print(f"Error fetching stock items: {e}")
        return []


def get_stock_by_epc(epc):
    """Find stock item by EPC and join with product info.
    
    Args:
        epc: The EPC code to search for
    
    Returns:
        Dictionary with stock item and product details, or None if not found
    """
    try:
        response = (
            supabase.table("product_stock")
            .select("*, product_info(*)")
            .eq("epc", epc)
            .execute()
        )
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error finding stock by EPC: {e}")
        return None


# =============================================================================
# Customer Management Functions
# =============================================================================
def get_customers():
    """Fetch all customers sorted by name."""
    try:
        response = (
            supabase.table("customers")
            .select("*")
            .order("first_name")
            .order("last_name")
            .execute()
        )
        return response.data or []
    except Exception as e:
        print(f"Error fetching customers: {e}")
        return []


def add_customer(first_name, last_name, email, dob, phone_num=None):
    """Add a new customer to Supabase."""
    try:
        data = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "date_of_birth": dob,
            "phone_num": phone_num,
        }
        response = supabase.table("customers").insert(data).execute()
        return getattr(response, "status_code", None) in (200, 201, 204)
    except Exception as e:
        print(f"Error adding customer: {e}")
        return False


def update_customer(customer_id, first_name, last_name, email, phone_num=None):
    """Update customer info."""
    try:
        supabase.table("customers").update({
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone_num": phone_num,
        }).eq("customer_id", customer_id).execute()
        return True
    except Exception as e:
        print(f"Error updating customer: {e}")
        return False


def delete_customer(customer_id):
    """Delete a customer by ID."""
    try:
        supabase.table("customers").delete().eq("customer_id", customer_id).execute()
        return True
    except Exception as e:
        print(f"Error deleting customer: {e}")
        return False


def get_customers_paginated(limit, offset, search=None):
    """Fetch paginated customer list with optional search filter."""
    try:
        # Fetch all customers first
        response = supabase.table("customers").select("*").order("first_name").order("last_name").execute()
        all_customers = response.data or []
        
        # Apply search filter (Python-side since Supabase client lacks .or() method)
        if search:
            search_lower = search.lower()
            filtered = [
                c for c in all_customers
                if (search_lower in (c.get('first_name') or '').lower() or
                    search_lower in (c.get('last_name') or '').lower() or
                    search_lower in (c.get('email') or '').lower())
            ]
        else:
            filtered = all_customers
        
        # Apply pagination
        paginated = filtered[offset:offset + limit]
        return paginated
    except Exception as e:
        print(f"Error fetching paginated customers: {e}")
        return []


def get_customer_count(search=None):
    """Return total customer count for pagination calculations."""
    try:
        # Fetch all customers
        response = supabase.table("customers").select("customer_id").execute()
        all_customers = response.data or []
        
        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            # Need full records to search by name and email
            response_full = supabase.table("customers").select("*").execute()
            all_customers_full = response_full.data or []
            
            filtered = [
                c for c in all_customers_full
                if (search_lower in c.get('first_name', '').lower() or
                    search_lower in c.get('last_name', '').lower() or
                    search_lower in c.get('email', '').lower())
            ]
            return len(filtered)
        
        return len(all_customers)
    except Exception as e:
        print(f"Error counting customers: {e}")
        return 0


# Temperature monitoring functions
def get_latest_temperature_reading(fridge_id):
    """Fetch most recent temperature reading for a fridge."""
    try:
        response = (
            supabase.table("temperature_readings")
            .select("*")
            .eq("fridge_id", int(fridge_id))
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error fetching latest temperature: {e}")
        return None


def get_temperature_history(fridge_id, limit=50):
    """Get recent temperature readings for charts and history."""
    try:
        response = (
            supabase.table("temperature_readings")
            .select("*")
            .eq("fridge_id", int(fridge_id))
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data or []
    except Exception as e:
        print(f"Error fetching temperature history: {e}")
        return []


# Fridge threshold management
def get_fridge_threshold(fridge_id):
    """Get temperature threshold setting for a fridge."""
    try:
        response = (
            supabase.table("refrigerators")
            .select("temperature_threshold")
            .eq("fridge_id", fridge_id)
            .execute()
        )
        if response.data:
            return response.data[0].get("temperature_threshold", 25.0)
        return 25.0
    except Exception as e:
        print(f"Error fetching threshold: {e}")
        return 25.0


def update_fridge_threshold(fridge_id, new_threshold):
    """Update temperature threshold for a fridge."""
    try:
        supabase.table("refrigerators").update({
            "temperature_threshold": new_threshold
        }).eq("fridge_id", fridge_id).execute()
        return True
    except Exception as e:
        print(f"Error updating threshold: {e}")
        return False


# Product management functions
def get_all_products():
    """Fetch all products with inventory information calculated from product_stock."""
    try:
        # Get all products
        response = supabase.table("product_info").select("*").order("name").execute()
        products = response.data or []
        
        if not products:
            return []
        
        # Fetch all available stock counts in one query
        stock_response = (
            supabase.table("product_stock")
            .select("product_id")
            .eq("status", "available")
            .execute()
        )
        
        # Count stock items per product
        stock_counts = {}
        for item in (stock_response.data or []):
            product_id = item["product_id"]
            stock_counts[product_id] = stock_counts.get(product_id, 0) + 1
        
        # Assign counts to products
        for product in products:
            product["total_quantity"] = stock_counts.get(product["product_id"], 0)
        
        return products
    except Exception as e:
        print(f"Error fetching products: {e}")
        return []


def get_product_by_id(product_id):
    """Get single product by ID with calculated stock quantity."""
    try:
        response = supabase.table("product_info").select("*").eq("product_id", product_id).single().execute()
        product = response.data
        
        if product:
            # Calculate actual stock quantity from product_stock
            stock_response = (
                supabase.table("product_stock")
                .select("stock_id", count="exact")
                .eq("product_id", product_id)
                .eq("status", "available")
                .execute()
            )
            product["total_quantity"] = stock_response.count or 0
        
        return product
    except Exception as e:
        print(f"Error fetching product: {e}")
        return None


def get_product_by_code(upc=None, epc=None):
    """Find product by barcode (UPC) or RFID tag (EPC).
    
    Args:
        upc: Product UPC barcode (finds product type)
        epc: Stock item EPC tag (finds specific stock item with product info)
    
    Returns:
        Product dictionary (from product_info or joined from product_stock)
    """
    try:
        if upc:
            # UPC lookup: find product type in product_info
            response = supabase.table("product_info").select("*").eq("upc", upc).execute()
            if response.data:
                return response.data[0]
        if epc:
            # EPC lookup: find stock item and join with product_info
            stock_item = get_stock_by_epc(epc)
            if stock_item and stock_item.get("product_info"):
                # Return the product_info part, but include the stock_id for reference
                product = stock_item["product_info"]
                product["stock_id"] = stock_item["stock_id"]  # Add stock_id to track which item was scanned
                product["epc"] = epc  # Add EPC back for display purposes
                return product
        return None
    except Exception as e:
        print(f"Error finding product by code: {e}")
        return None


def add_product(name, category, price, upc, producer, image_url=None):
    """Add new product to database (product_info table).
    Note: Stock quantity is calculated from product_stock table, not stored here.
    
    Args:
        name: Product name
        category: Product category
        price: Product price
        upc: Universal Product Code (barcode)
        producer: Product producer/manufacturer
        image_url: Optional product image URL
    
    Returns:
        Created product dictionary, or None on error
    """
    try:
        data = {
            "name": name,
            "category": category,
            "price": price,
            "upc": upc,
            "producer": producer,
            "image_url": image_url
        }
        response = supabase.table("product_info").insert(data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error adding product: {e}")
        return None


def update_product(product_id, **kwargs):
    """Update product fields."""
    try:
        supabase.table("product_info").update(kwargs).eq("product_id", product_id).execute()
        return True
    except Exception as e:
        print(f"Error updating product: {e}")
        return False


def delete_product(product_id):
    """Delete product."""
    try:
        supabase.table("product_info").delete().eq("product_id", product_id).execute()
        return True
    except Exception as e:
        print(f"Error deleting product: {e}")
        raise  # Re-raise the exception so the caller can handle it


def add_inventory_reception(product_id, quantity, date_received=None):
    """Record stock reception, generate EPCs, and update product inventory.
    
    Args:
        product_id: ID of the product receiving stock
        quantity: Number of items being added
        date_received: Optional timestamp (defaults to now)
    
    Returns:
        True on success, False on error
    """
    try:
        if not date_received:
            date_received = datetime.now().isoformat()
        
        # Record the inventory reception
        data = {
            "product_id": product_id,
            "quantity_received": quantity,
            "date_received": date_received
        }
        supabase.table("inventory_receptions").insert(data).execute()
        
        # Generate EPC-tagged stock items for each unit received
        for _ in range(quantity):
            add_stock_item(product_id)
        
        # Note: total_quantity is now calculated dynamically from product_stock
        
        return True
    except Exception as e:
        print(f"Error adding inventory: {e}")
        return False


def get_inventory_history(product_id):
    """Get reception history for a product."""
    try:
        response = supabase.table("inventory_receptions").select("*").eq("product_id", product_id).order("date_received", desc=True).execute()
        return response.data or []
    except Exception as e:
        print(f"Error fetching inventory history: {e}")
        return []


# Customer account functions (with authentication)
def create_customer_account(first_name, last_name, email, password_hash, phone=None, dob=None):
    """Create new customer with membership number and loyalty points."""
    try:
        # Generate unique membership number
        membership_number = f"MB{int(datetime.now().timestamp() * 1000)}"
        
        data = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "password_hash": password_hash,
            "phone_num": phone,
            "date_of_birth": dob,
            "membership_number": membership_number,
            "points": 0
        }
        response = supabase.table("customers").insert(data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error creating customer: {e}")
        return None


def get_customer_by_email(email):
    """Get customer by email (for login)."""
    try:
        response = supabase.table("customers").select("*").eq("email", email).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error fetching customer by email: {e}")
        return None


def get_customer_by_id(customer_id):
    """Get customer by ID."""
    try:
        response = supabase.table("customers").select("*").eq("customer_id", customer_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error fetching customer by ID: {e}")
        return None


def get_customer_by_membership(membership_number):
    """Get customer by membership number."""
    try:
        response = supabase.table("customers").select("*").eq("membership_number", membership_number).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error fetching customer by membership: {e}")
        return None


def get_customer_by_rfid(rfid_tag):
    """Get customer by RFID card tag."""
    try:
        response = supabase.table("customers").select("*").eq("rfid_card", rfid_tag).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error fetching customer by RFID: {e}")
        return None


def update_customer_points(customer_id, points_to_add):
    """Add loyalty points to customer account."""
    try:
        # Get current points
        response = supabase.table("customers").select("points").eq("customer_id", customer_id).single().execute()
        current_points = response.data.get("points", 0) if response.data else 0
        new_points = current_points + points_to_add
        
        supabase.table("customers").update({"points": new_points}).eq("customer_id", customer_id).execute()
        return True
    except Exception as e:
        print(f"Error updating points: {e}")
        return False


# Purchase and receipt functions
def create_purchase(customer_id, total_amount, points_earned, items, points_redeemed=0):
    """Create purchase record with items, mark stock as sold, and update inventory.
    
    Args:
        customer_id: Customer ID (can be None for guest purchases)
        total_amount: Total purchase amount after any discounts
        points_earned: Points to award (0 for guests)
        items: List of purchase items (each with product_id, quantity, price, and optional stock_ids)
        points_redeemed: Points customer redeemed for discount (deducted from their account)
    
    Returns:
        purchase_id on success, None on error
    """
    try:
        # Create purchase record
        purchase_data = {
            "customer_id": customer_id,  # Can be None for guests
            "total_amount": float(total_amount),
            "points_earned": points_earned,
            "purchase_date": datetime.now().isoformat()
        }
        purchase_response = supabase.table("purchases").insert(purchase_data).execute()
        if not purchase_response.data:
            return None
        
        purchase_id = purchase_response.data[0]["purchase_id"]
        
        # Create purchase items and mark stock as sold
        for item in items:
            item_data = {
                "purchase_id": purchase_id,
                "product_id": item["product_id"],
                "quantity": item["quantity"],
                "price_at_purchase": float(item["price"])
            }
            supabase.table("purchase_items").insert(item_data).execute()
            
            # Mark stock items as sold
            # If stock_ids are provided (from scanning), use those
            # Otherwise, allocate available stock items
            if "stock_ids" in item and item["stock_ids"]:
                stock_ids = item["stock_ids"]
            else:
                stock_ids = get_available_stock_items(item["product_id"], item["quantity"])
            
            # Mark each stock item as sold
            for stock_id in stock_ids:
                mark_stock_as_sold(stock_id, purchase_id)
            
            # Note: total_quantity is now calculated dynamically from product_stock
        
        # Handle customer points (only if customer_id provided)
        if customer_id:
            # Deduct redeemed points first
            if points_redeemed > 0:
                update_customer_points(customer_id, -points_redeemed)
            # Add earned points
            if points_earned > 0:
                update_customer_points(customer_id, points_earned)
        
        return purchase_id
    except Exception as e:
        print(f"Error creating purchase: {e}")
        return None


def get_customer_purchases(customer_id, limit=20):
    """Get purchase history for customer."""
    try:
        response = supabase.table("purchases").select("*").eq("customer_id", customer_id).order("purchase_date", desc=True).limit(limit).execute()
        return response.data or []
    except Exception as e:
        print(f"Error fetching purchases: {e}")
        return []


def get_purchase_details(purchase_id):
    """Get full purchase details with items."""
    try:
        # Get purchase
        purchase = supabase.table("purchases").select("*").eq("purchase_id", purchase_id).single().execute()
        if not purchase.data:
            return None
        
        # Get items
        items = supabase.table("purchase_items").select("*, products(*)").eq("purchase_id", purchase_id).execute()
        
        return {
            "purchase": purchase.data,
            "items": items.data or []
        }
    except Exception as e:
        print(f"Error fetching purchase details: {e}")
        return None


def get_all_purchases_paginated(limit, offset, search=None):
    """Fetch all purchases with customer info (admin view) - paginated."""
    try:
        # Fetch all purchases with customer info
        response = supabase.table("purchases").select("*, customers(customer_id, first_name, last_name, email, membership_number)").order("purchase_date", desc=True).execute()
        all_purchases = response.data or []
        
        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            filtered = [
                p for p in all_purchases
                if (search_lower in str(p.get('purchase_id', '')) or
                    (p.get('customers') and (
                        search_lower in p['customers'].get('first_name', '').lower() or
                        search_lower in p['customers'].get('last_name', '').lower() or
                        search_lower in p['customers'].get('email', '').lower() or
                        search_lower in p['customers'].get('membership_number', '').lower()
                    )))
            ]
        else:
            filtered = all_purchases
        
        # Apply pagination
        return filtered[offset:offset + limit]
    except Exception as e:
        print(f"Error fetching all purchases: {e}")
        return []


def get_purchases_count(search=None):
    """Get total count of purchases for pagination."""
    try:
        response = supabase.table("purchases").select("*, customers(first_name, last_name, email, membership_number)").execute()
        all_purchases = response.data or []
        
        if search:
            search_lower = search.lower()
            filtered = [
                p for p in all_purchases
                if (search_lower in str(p.get('purchase_id', '')) or
                    (p.get('customers') and (
                        search_lower in p['customers'].get('first_name', '').lower() or
                        search_lower in p['customers'].get('last_name', '').lower() or
                        search_lower in p['customers'].get('email', '').lower() or
                        search_lower in p['customers'].get('membership_number', '').lower()
                    )))
            ]
            return len(filtered)
        
        return len(all_purchases)
    except Exception as e:
        print(f"Error counting purchases: {e}")
        return 0


def get_customer_purchases_with_details(customer_id):
    """Get all purchases for a specific customer with full details (for admin modal)."""
    try:
        response = supabase.table("purchases").select("*").eq("customer_id", customer_id).order("purchase_date", desc=True).execute()
        return response.data or []
    except Exception as e:
        print(f"Error fetching customer purchases: {e}")
        return []

"""Inventory Report"""

def get_inventory_report_paginated(limit, offset, search=None):
    """
    Fetch all products for the Inventory Report (admin view) - paginated + search.
    """

    try:
        # Fetch all products
        response = supabase.table("product_info").select("*").order("product_id").execute()
        all_products = response.data or []

        stock_response = supabase.table("product_stock")\
            .select("product_id, status")\
            .execute()
        
        # Count available stock per product
        stock_counts = {}
        for item in stock_response.data:
            if item["status"] == "available":
                product_id = item["product_id"]
                stock_counts[product_id] = stock_counts.get(product_id, 0) + 1
                
        # Compute stock value
        for p in all_products:
            qty = stock_counts.get(p["product_id"], 0)
            price = float(p.get("price", 0) or 0)
            
            p["total_quantity"] = qty  # Add this field for compatibility
            p["stock_value"] = qty * price

        # SEARCH FILTER
        if search:
            search_lower = search.lower()
            filtered = [
                p for p in all_products
                if search_lower in p.get("name", "").lower()
                or search_lower in p.get("category", "").lower()
            ]
        else:
            filtered = all_products

        paginated = filtered[offset : offset + limit]

        return paginated, len(filtered)

    except Exception as e:
        print("Error fetching paginated products:", e)
        return [], 0

def get_inventory_products():
    try:
        response = supabase.table("product_info").select(
            "product_id, name, category, price"
        ).order("name", desc=False).execute()
        products = response.data or []
    # Get stock counts
        stock_response = supabase.table("product_stock")\
            .select("product_id, status")\
            .execute()
        
        # Count available stock per product
        stock_counts = {}
        for item in stock_response.data:
            if item["status"] == "available":
                product_id = item["product_id"]
                stock_counts[product_id] = stock_counts.get(product_id, 0) + 1
        
        # Add total_quantity to each product
        for p in products:
            p["total_quantity"] = stock_counts.get(p["product_id"], 0)
        
        return products
    
    except Exception as e:
        print("Error fetching inventory products:", e)
        return []
    
def get_total_inventory_value(search=None):
    """
    Calculate the TOTAL stock value for ALL products (respects search filter).
    This ensures the total remains consistent across pagination pages.
    """
    try:
        # Fetch all products
        response = supabase.table("product_info").select("*").execute()
        all_products = response.data or []

        # Get stock counts
        stock_response = supabase.table("product_stock")\
            .select("product_id, status")\
            .execute()
        
        # Count available stock per product
        stock_counts = {}
        for item in stock_response.data:
            if item["status"] == "available":
                product_id = item["product_id"]
                stock_counts[product_id] = stock_counts.get(product_id, 0) + 1


        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            all_products = [
                p for p in all_products
                if search_lower in p.get("name", "").lower()
                or search_lower in p.get("category", "").lower()
            ]

        # Calculate total stock value
        total_value = 0.0
        for p in all_products:
            qty = stock_counts.get(p["product_id"], 0)
            price = float(p.get("price", 0) or 0)
            total_value += qty * price


        return total_value

    except Exception as e:
        print("Error calculating total inventory value:", e)
        return 0.0