from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def init_db():
    print("Table managed in Supabase dashboard (no local creation needed)")


#  In Supabase there is not Create method, to make a new table, you need to go on the Supabase dashboard online.
def get_customers():
    try:
        response = (
            supabase.table("customers")
            .select("*")
            .order("first_name", desc=False)
            .order("last_name", desc=False)
            .execute()
        )

        customers = []
        for item in response.data:
            customers.append((
                item.get('customer_id'),
                item.get('first_name'),
                item.get('last_name'),
                item.get('email'),
                item.get('phone_num'),
                item.get('created_at'),
                item.get('date_of_birth')
            ))
        return customers
    except Exception as e:
        print(f"Error fetching customers: {e}")
        return []


def add_customer(first_name, last_name, email, dob, phone_num=None):
    try:
        data = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone_num": phone_num,
            "date_of_birth": dob
        }
        response = supabase.table("customers").insert(data).execute()

        # Check for 204 No Content
        if response.status_code == 204:
            print("Insert successful with no content returned.")
            return True
        print("Insert response:", response)
        return True
    except ValueError as ve:
        # Handle empty response body
        print("Insert successful, but received empty response body.")
        return True
    except Exception as e:
        print(f"Error adding customer: {e}")
        return False


def update_customer(customer_id, first_name, last_name, email, phone_num=None):
    try:
        response = (
            supabase.table("customers")
            .update({
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "phone_num": phone_num,
            })
            .filter("customer_id", "eq", customer_id)
            .execute()
        )
        print("Update response:", response)
        return True
    except ValueError as ve:
        # Handle empty response body
        print("Update successful, but received empty response body.")
        return True 
    except Exception as e:
        print(f"Error updating customer: {e}")
        return False


def delete_customer(customer_id):
    try:
        response = supabase.table("customers").delete().filter("customer_id", "eq", customer_id).execute()
        print("Delete response:", response)

           # Check for 204 No Content
        if response.status_code == 204:
            print("Delete successful with no content returned.")
            return True
        
        return True
    except ValueError as ve:
        # Handle empty response body
        print("Delete successful, but received empty response body.")
        return True
    except Exception as e:
        print(f"Error deleting customer: {e}")
        return False

def get_customers_paginated(limit, offset, search=None):
    try:
        query = supabase.table("customers").select("*")

        if search:
            names = search.split(None, 1)
            if len(names) == 2:
                first_pattern = names[0]
                last_pattern = names[1]
                query = (
                    query.ilike("first_name", f"{first_pattern}%")
                         .ilike("last_name", f"{last_pattern}%")
                )
            else:
                pattern = names[0]
                query = query.or_(
                    f"first_name.ilike.%{pattern}%,last_name.ilike.%{pattern}%,email.ilike.%{pattern}%"
                )

        response = (
            query.order("first_name")
                 .order("last_name")
                 .range(offset, offset + limit - 1)
                 .execute()
        )

        # Convert dictionaries to tuple format expected by template
        rows = response.data or []
        return [
            (
                row["customer_id"],        
                row["first_name"],         
                row["last_name"],         
                row["email"],           
                row.get("phone_num", "N/A"),  
                row.get("date_of_birth", "N/A"),
                row.get("created_at", "N/A")   
            )
            for row in rows
        ]

    except Exception as e:
        print(f"Error fetching paginated customers: {e}")
        return []



def get_customer_count(search=None):
    try:
        query = supabase.table("customers").select("customer_id", count="exact")

        if search:
            names = search.split(None, 1)
            if len(names) == 2:
                first_pattern = names[0]
                last_pattern = names[1]
                query = (
                    query.ilike("first_name", f"{first_pattern}%")
                         .ilike("last_name", f"{last_pattern}%")
                )
            else:
                pattern = names[0]
                query = query.or_(
                    f"first_name.ilike.%{pattern}%,last_name.ilike.%{pattern}%,email.ilike.%{pattern}%"
                )

        response = query.execute()

        # Supabase sync client returns a dict with 'count' if count="exact" is used
        if hasattr(response, "count") and response.count is not None:
            return response.count
        else:
            # fallback if count not provided
            return len(response.data or [])

    except Exception as e:
        print(f"Error counting customers: {e}")
        return 0

# For the temperature reading
def get_latest_temperature_readings(fridge_id):
    try:
        print(f"get_latest_temperature_readings called with fridge_id={fridge_id} ({type(fridge_id)})")
        fridge_id = int(fridge_id)
        response = (
            supabase.table("temperature_readings")
            .select("*")
            .filter("fridge_id", "eq", fridge_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        # Debug: print raw response info
        print("Supabase response (latest):", getattr(response, "status_code", None), getattr(response, "data", None))
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error fetching temperature: {e}")
        return None

def get_temperature_history(fridge_id, limit=50):
    try:
        print(f"get_temperature_history called with fridge_id={fridge_id} ({type(fridge_id)}) limit={limit}")
        fridge_id = int(fridge_id)
        response = (
            supabase.table("temperature_readings")
            .select("*")
            .filter("fridge_id", "eq", fridge_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        print("Supabase response (history):", getattr(response, "status_code", None), getattr(response, "data", None))
        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching temperature history: {e}")
        return []

def get_fridge_threshold(fridge_id):
    try:
        response = supabase.table("refrigerators")\
            .select("temperature_threshold")\
            .eq("fridge_id", fridge_id)\
            .execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0].get("temperature_threshold", 25.0)
        return 25.0
        
    except Exception as e:
        print(f"Error fetching threshold: {e}")
        return 25.0

def update_fridge_threshold(fridge_id, new_threshold):
    try:
        response = supabase.table("refrigerators")\
            .update({"temperature_threshold": new_threshold})\
            .eq("fridge_id", fridge_id)\
            .execute()
        return True
    except Exception as e:
        print(f"Error updating threshold: {e}")
        return False