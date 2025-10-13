from supabase import create_client, Client
from dotenv import load_dotenv
from flask import Flask, request, jsonify
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def init_db():
    print("Table created in Supabase dashboard")

#  In Supabase there is not Create method, to make a new table, you need to go on the Supabase dashboard online.
def get_customers():
    try:
        response = supabase.table("customers").select("*").order("created_at", desc=True).execute()
        customers = []
        for item in response.data:
            customers.append((
                item['customer_id'],
                item['first_name'],
                item['last_name'],
                item['email'],
                item['phone_num'],
                item['created_at'],
            ))
        return customers
    except Exception as e:
        print("Error fetching Customers: {e}")
        return []

