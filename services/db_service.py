# Database Service Layer
# Handles all database operations using Supabase PostgreSQL
# This file contains functions grouped by feature area for easy navigation

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
    print(f"⚠️ DB connection failed: {e}")
    supabase = None
    DB_AVAILABLE = False


def requires_db(func):
    """Decorator to ensure DB is available before executing function."""
    def wrapper(*args, **kwargs):
        if not DB_AVAILABLE:
            print(f"⚠️ DB not available for {func.__name__}")
            return None
        return func(*args, **kwargs)
    return wrapper


def init_db():
    """Initializes database connection."""
    print("Supabase connection ready." if DB_AVAILABLE else "Mock DB active")


# =============================================================================
# STOCK MANAGEMENT - EPC Generation and Inventory Tracking
# =============================================================================

def generate_epc():
    """Generates a unique 24-character EPC code for RFID tags."""
    return secrets.token_hex(12).upper()


def add_stock_item(product_id, epc=None):
    """Creates a new stock item with a unique EPC tag.
    If no EPC is provided, one will be generated automatically.
    Returns the stock_id of the created item."""
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


def get_available_stock_items(product_id, quantity=1, exclude_stock_ids=None):
    """Finds available stock items for a product.
    Returns a list of stock_id values up to the requested quantity.
    
    Args:
        product_id: The product to find stock for
        quantity: How many stock items to return
        exclude_stock_ids: List of stock_ids to exclude (already in cart)
    """
    try:
        if exclude_stock_ids is None:
            exclude_stock_ids = []
        
        query = (
            supabase.table("product_stock")
            .select("stock_id, epc")
            .eq("product_id", product_id)
            .eq("status", "available")
        )
        
        # Exclude stock_ids already allocated in cart
        if exclude_stock_ids:
            query = query.not_.in_("stock_id", exclude_stock_ids)
        
        response = query.limit(quantity).execute()
        return [item["stock_id"] for item in (response.data or [])]
    except Exception as e:
        print(f"Error fetching available stock: {e}")
        return []


def mark_stock_as_sold(stock_id, purchase_id):
    """Marks a stock item as sold and links it to a purchase record."""
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
    """Retrieves all stock items for a product including EPCs, status, and timestamps.
    Used in admin stock management modal."""
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
    """Finds a stock item by its EPC code and returns it with product details."""
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
# CUSTOMER MANAGEMENT - Account Creation, Updates, and Lookups
# =============================================================================

def get_customers():
    """Retrieves all customers from the database sorted alphabetically."""
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
    """Creates a new customer record with the provided information."""
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
    """Updates an existing customer's information."""
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
    """Removes a customer from the database."""
    try:
        supabase.table("customers").delete().eq("customer_id", customer_id).execute()
        return True
    except Exception as e:
        print(f"Error deleting customer: {e}")
        return False


def get_customers_paginated(limit, offset, search=None):
    """Retrieves a specific page of customers with optional name or email search."""
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
    """Counts total customers, optionally filtered by search term."""
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


# =============================================================================
# TEMPERATURE MONITORING - IoT Sensor Data and Fridge Thresholds
# =============================================================================

def get_latest_temperature_reading(fridge_id):
    """Gets the most recent temperature reading for a specific fridge."""
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
    """Retrieves recent temperature readings for displaying charts and history."""
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


def get_fridge_threshold(fridge_id):
    """Gets the temperature threshold setting for a fridge."""
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
        response = supabase.table("refrigerators").update({
            "temperature_threshold": new_threshold
        }).eq("fridge_id", fridge_id).execute()
        
        # Verify update succeeded by checking response
        if response.data and len(response.data) > 0:
            print(f"Threshold updated: Fridge {fridge_id} -> {new_threshold}°C")
            return True
        else:
            print(f"Warning: Update returned no data for fridge {fridge_id}")
            return False
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


def get_product_by_code(upc=None, epc=None, include_quantity=False):
    """Find product by barcode (UPC) or RFID tag (EPC).
    
    Args:
        upc: Product UPC barcode (finds product type)
        epc: Stock item EPC tag (finds specific stock item with product info)
        include_quantity: If True, calculate total_quantity (slower). Default False for fast scanning.
    
    Returns:
        Product dictionary (from product_info or joined from product_stock)
    """
    try:
        if upc:
            # UPC lookup: find product type in product_info
            response = supabase.table("product_info").select("*").eq("upc", upc).execute()
            if response.data:
                product = response.data[0]
                
                # Only calculate total_quantity if explicitly requested
                if include_quantity:
                    product_id = product.get("product_id")
                    stock_count = supabase.table("product_stock").select("stock_id").eq("product_id", product_id).eq("status", "available").execute()
                    product["total_quantity"] = len(stock_count.data) if stock_count.data else 0
                else:
                    product["total_quantity"] = 1  # Assume available if found
                
                return product
        if epc:
            # EPC lookup: find stock item and join with product_info
            stock_item = get_stock_by_epc(epc)
            if stock_item and stock_item.get("product_info"):
                # Return the product_info part, but include the stock_id for reference
                product = stock_item["product_info"]
                product["stock_id"] = stock_item["stock_id"]
                product["epc"] = epc
                
                # Only calculate total_quantity if explicitly requested
                if include_quantity:
                    product_id = product.get("product_id")
                    stock_count = supabase.table("product_stock").select("stock_id").eq("product_id", product_id).eq("status", "available").execute()
                    product["total_quantity"] = len(stock_count.data) if stock_count.data else 0
                else:
                    product["total_quantity"] = 1  # Assume available if found
                
                return product
        return None
    except Exception as e:
        print(f"Error finding product by code: {e}")
        return None


def add_product(name, category, price, upc, producer, image_url=None):
    """Creates a new product in the database.
    Stock quantity is managed separately through the product_stock table."""
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
    """Updates one or more fields of an existing product."""
    try:
        supabase.table("product_info").update(kwargs).eq("product_id", product_id).execute()
        return True
    except Exception as e:
        print(f"Error updating product: {e}")
        return False


def delete_product(product_id):
    """Removes a product from the database."""
    try:
        supabase.table("product_info").delete().eq("product_id", product_id).execute()
        return True
    except Exception as e:
        print(f"Error deleting product: {e}")
        raise  # Re-raise the exception so the caller can handle it


def add_inventory_reception(product_id, quantity, date_received=None):
    """Records incoming stock, generates EPC tags for each item, and updates inventory."""
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
    """Retrieves the reception history for a specific product."""
    try:
        response = supabase.table("inventory_receptions").select("*").eq("product_id", product_id).order("date_received", desc=True).execute()
        return response.data or []
    except Exception as e:
        print(f"Error fetching inventory history: {e}")
        return []


# =============================================================================
# CUSTOMER AUTHENTICATION - Account Creation and Login Functions
# =============================================================================

def create_customer_account(first_name, last_name, email, password_hash, phone=None, dob=None):
    """Creates a customer account with login credentials, membership number, and loyalty points."""
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
    """Finds a customer by their email address. Used for login."""
    if not DB_AVAILABLE:
        return None
    try:
        response = supabase.table("customers").select("*").eq("email", email).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error fetching customer by email: {e}")
        return None


def get_customer_by_id(customer_id):
    """Retrieves a customer's full information using their customer ID."""
    if not DB_AVAILABLE:
        return None
    try:
        response = supabase.table("customers").select("*").eq("customer_id", customer_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error fetching customer by ID: {e}")
        return None


def get_customer_by_membership(membership_number):
    """Finds a customer using their membership number."""
    try:
        response = supabase.table("customers").select("*").eq("membership_number", membership_number).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error fetching customer by membership: {e}")
        return None


def get_customer_by_rfid(rfid_tag):
    """Finds a customer using their RFID card tag."""
    try:
        response = supabase.table("customers").select("*").eq("rfid_card", rfid_tag).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error fetching customer by RFID: {e}")
        return None


def update_customer_points(customer_id, points_to_add):
    """Adds or removes loyalty points from a customer's account."""
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


# =============================================================================
# PURCHASE MANAGEMENT - Creating and Retrieving Purchase Records
# =============================================================================

def create_purchase(customer_id, total_amount, points_earned, items, points_redeemed=0):
    """Creates a complete purchase record including items, updates stock status, and manages loyalty points.
    Supports both customer and guest purchases."""
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
    """Retrieves purchase history for a specific customer."""
    try:
        response = supabase.table("purchases").select("*").eq("customer_id", customer_id).order("purchase_date", desc=True).limit(limit).execute()
        return response.data or []
    except Exception as e:
        print(f"Error fetching purchases: {e}")
        return []


def get_purchase_details(purchase_id):
    """Retrieves complete details for a purchase including all items and product information."""
    try:
        # Get purchase
        purchase = supabase.table("purchases").select("*").eq("purchase_id", purchase_id).single().execute()
        if not purchase.data:
            return None
        
        # Get items with product info (table is product_info, not products)
        items = supabase.table("purchase_items").select("*, product_info(*)").eq("purchase_id", purchase_id).execute()
        
        return {
            "purchase": purchase.data,
            "items": items.data or []
        }
    except Exception as e:
        print(f"Error fetching purchase details: {e}")
        return None


def get_all_purchases_paginated(limit, offset, search=None):
    """Retrieves all purchases with customer information for admin view. Supports pagination and search."""
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
    """Counts total purchases for pagination calculations."""
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

# =============================================================================
# SALES REPORT - Product Sales Analysis and Revenue Tracking
# =============================================================================

def get_customer_purchases_with_details(customer_id):
    """Retrieves all purchases for a customer with complete details for admin review."""
    try:
        response = supabase.table("purchases").select("*").eq("customer_id", customer_id).order("purchase_date", desc=True).execute()
        return response.data or []
    except Exception as e:
        print(f"Error fetching customer purchases: {e}")
        return []

def get_sales_by_product(start_date, end_date, limit=None, offset=None, search=None):
    """Calculates total units sold per product within a date range.
    Supports pagination and searching by product name or category."""

    try:
        # First get all purchases in the date range
        purchases_response = (
            supabase.table("purchases")
            .select("purchase_id, purchase_date")
            .gte("purchase_date", start_date)
            .lte("purchase_date", end_date)
            .execute()
        )
        
        purchase_ids = [p["purchase_id"] for p in (purchases_response.data or [])]
        
        if not purchase_ids:
            return [], 0
        
        # Then get purchase items for those purchases with product info
        response = (
            supabase.table("purchase_items")
            .select("product_id, quantity, product_info(name, category)")
            .in_("purchase_id", purchase_ids)
            .execute()
        )

        raw = response.data or []

        # Aggregate
        agg = {}
        for item in raw:
            pid = item["product_id"]
            qty = item["quantity"]
            info = item["product_info"]
            name = info["name"]
            cat = info["category"]

            if pid not in agg:
                agg[pid] = {
                    "product_id": pid,
                    "name": name,
                    "category": cat,
                    "total_sold": 0
                }

            agg[pid]["total_sold"] += qty

        products = list(agg.values())

        # ---- SEARCH FILTER ----
        if search:
            s = search.lower()
            products = [
                p for p in products
                if s in p["name"].lower() or s in p["category"].lower()
            ]

        total_count = len(products)

        # ---- PAGINATION ----
        if limit is not None and offset is not None:
            products = products[offset : offset + limit]

        return products, total_count

    except Exception as e:
        print("Error fetching paginated sales:", e)
        return [], 0


def get_total_sales_value(start_date, end_date):
    """Calculates total revenue for all purchases within a date range."""
    try:
        resp = (
            supabase.table("purchases")
            .select("total_amount, purchase_date")
            .gte("purchase_date", start_date)
            .lte("purchase_date", end_date)
            .execute()
        )

        records = resp.data or []
        total = sum(float(r["total_amount"]) for r in records)

        return total

    except Exception as e:
        print("Error fetching total sales value:", e)
        return 0


def get_top_and_bottom_sellers(start_date, end_date):
    """Returns the top 3 best-selling and bottom 3 least-selling products for a date range."""

    # get_sales_by_product returns: (products_list, total_count)
    products, _ = get_sales_by_product(start_date, end_date)

    # Normalize data
    clean_sales = []
    for p in products:
        if isinstance(p, dict):
            clean_sales.append({
                "product_id": p.get("product_id"),
                "name": p.get("name"),
                "category": p.get("category"),
                "total_sold": p.get("total_sold", 0)
            })

    # Sort descending
    sorted_sales = sorted(clean_sales, key=lambda x: x["total_sold"], reverse=True)

    # Always 3 top + 3 bottom
    top = sorted_sales[:3]
    bottom = sorted_sales[-3:] if sorted_sales else []

    return top, bottom


# =============================================================================
# INVENTORY REPORT - Stock Levels and Value Analysis
# =============================================================================

def get_inventory_report_paginated(limit=10, offset=0, search=None):
    """Generates a paginated inventory report with product details and stock counts."""
    try:
        # Get all products with their stock counts
        products = get_all_products()
        
        # Add stock_value field (price * quantity)
        for p in products:
            p['stock_value'] = p.get('price', 0) * p.get('total_quantity', 0)
        
        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            products = [
                p for p in products
                if (search_lower in p.get('name', '').lower() or
                    search_lower in p.get('category', '').lower() or
                    search_lower in p.get('producer', '').lower())
            ]
        
        # Apply pagination
        paginated = products[offset:offset + limit]
        
        return paginated, len(products)
    except Exception as e:
        print(f"Error fetching inventory report: {e}")
        return [], 0


def get_inventory_products():
    """Get all products with inventory information for reporting."""
    try:
        products = get_all_products()
        # Add stock_value field for PDF export
        for p in products:
            p['stock_value'] = p.get('price', 0) * p.get('total_quantity', 0)
        return products
    except Exception as e:
        print(f"Error fetching inventory products: {e}")
        return []


def get_total_inventory_value(search=None):
    """Calculates the total value of all inventory stock."""
    try:
        products = get_all_products()
        
        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            products = [
                p for p in products
                if (search_lower in p.get('name', '').lower() or
                    search_lower in p.get('category', '').lower() or
                    search_lower in p.get('producer', '').lower())
            ]
        
        total_value = sum(
            p.get('price', 0) * p.get('total_quantity', 0) 
            for p in products
        )
        return total_value
    except Exception as e:
        print(f"Error calculating inventory value: {e}")
        return 0.0


def get_inventory_summary(search=None):
    """Calculates inventory statistics including low stock, critical, and out-of-stock items."""
    try:
        products = get_all_products()
        
        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            products = [
                p for p in products
                if (search_lower in p.get('name', '').lower() or
                    search_lower in p.get('category', '').lower() or
                    search_lower in p.get('producer', '').lower())
            ]
        
        total_products = len(products)
        low_stock_count = sum(1 for p in products if 5 <= p.get('total_quantity', 0) <= 10)
        critical_count = sum(1 for p in products if 0 < p.get('total_quantity', 0) < 5)
        out_of_stock_count = sum(1 for p in products if p.get('total_quantity', 0) == 0)
        
        return {
            'total_products': total_products,
            'low_stock_count': low_stock_count,
            'critical_count': critical_count,
            'out_of_stock_count': out_of_stock_count
        }
    except Exception as e:
        print(f"Error calculating inventory summary: {e}")
        return {
            'total_products': 0,
            'low_stock_count': 0,
            'critical_count': 0,
            'out_of_stock_count': 0
        }


# =============================================================================
# CUSTOMER ACTIVITY REPORT - New vs Returning Customer Analysis
# =============================================================================

def get_customer_activity(start_date, end_date):
    """Analyzes customer activity for a date range, distinguishing between new and returning customers."""
    try:
        
        # Step 1: Get ALL purchases and filter in Python (most reliable method)
        purchases_response = supabase.table("purchases")\
            .select("customer_id, purchase_date")\
            .execute()
        
        print(f"Total purchases in DB: {len(purchases_response.data)}")
        
        # Filter purchases by date range in Python
        filtered_purchases = []
        for purchase in purchases_response.data:
            purchase_date_str = purchase["purchase_date"][:10]  # Get YYYY-MM-DD
            if start_date <= purchase_date_str <= end_date:
                filtered_purchases.append(purchase)
        
        print(f"Purchases in date range: {len(filtered_purchases)}")
        
        if not filtered_purchases:
            print("No purchases found in date range")
            return {
                "total_customers": 0,
                "new_customers": 0,
                "returning_customers": 0
            }
        
        # Get unique customer IDs who made purchases (exclude None)
        customer_ids = list(set(
            purchase["customer_id"] 
            for purchase in filtered_purchases 
            if purchase["customer_id"] is not None
        ))
        total_customers = len(customer_ids)
        print(f"Unique customers: {total_customers}")
        print(f"Customer IDs: {customer_ids}")
        
        if total_customers == 0:
            print("No registered customers made purchases (all guest purchases)")
            return {
                "total_customers": 0,
                "new_customers": 0,
                "returning_customers": 0
            }
        
        # Get customer registration dates
        customers_response = supabase.table("customers")\
            .select("customer_id, created_at")\
            .in_("customer_id", customer_ids)\
            .execute()
        
        print(f"Customer data retrieved: {len(customers_response.data)}")
        
        # Count new customers (registered within date range)
        new_customers = 0
        returning_customers = 0
        new_customers_list = []
        returning_customers_list = []
        
        for customer in customers_response.data:
            customer_created = customer["created_at"][:10]  # Extract YYYY-MM-DD
            print(f"Customer {customer['customer_id']}: registered on {customer_created}")
            
            # Get full customer details
            customer_details = next(
                (c for c in customers_response.data if c["customer_id"] == customer["customer_id"]),
                None
            )
            
            if start_date <= customer_created <= end_date:
                new_customers += 1
                if customer_details:
                    new_customers_list.append(customer_details)
            else:
                returning_customers += 1
                if customer_details:
                    returning_customers_list.append(customer_details)
        
        # Count guest purchases (purchases with null customer_id)
        guest_purchases = sum(1 for p in filtered_purchases if p["customer_id"] is None)
        
        result = {
            "total_customers": total_customers,
            "new_customers": new_customers,
            "returning_customers": returning_customers,
            "guest_purchases": guest_purchases,
            "new_customers_list": new_customers_list,
            "returning_customers_list": returning_customers_list,
            "start_date": start_date,
            "end_date": end_date
        }
        
        print(f"Final result: {result}")
        
        return result
        
    except Exception as e:
        print(f"ERROR in get_customer_activity: {e}")
        return {
            "total_customers": 0,
            "new_customers": 0,
            "returning_customers": 0,
            "guest_purchases": 0,
            "new_customers_list": [],
            "returning_customers_list": [],
            "start_date": start_date,
            "end_date": end_date
        }
