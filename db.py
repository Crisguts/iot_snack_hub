from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def init_db():
    print("Table managed in Supabase dashboard (no local creation needed)")


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
            ))
        return customers
    except Exception as e:
        print(f"Error fetching customers: {e}")
        return []


def add_customer(first_name, last_name, email, phone_num=None):
    try:
        data = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone_num": phone_num,
        }
        response = supabase.table("customers").insert(data).execute()
        print("Insert response:", response)
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
            .eq("customer_id", customer_id)
            .execute()
        )
        print("Update response:", response)
        return True
    except Exception as e:
        print(f"Error updating customer: {e}")
        return False


def delete_customer(customer_id):
    try:
        response = supabase.table("customers").delete().eq("customer_id", customer_id).execute()
        print("Delete response:", response)
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
                row["customer_id"],        # 0: customer_id
                row["first_name"],         # 1: first_name
                row["last_name"],          # 2: last_name
                row["email"],              # 3: email
                row.get("phone_num", "N/A"),   # 4: phone number
                row.get("created_at", "N/A")   # 5: created_at
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

