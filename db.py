import sqlite3

DB_NAME = "store.db"

def get_db():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def get_customers():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM customers")
    customers = c.fetchall()
    conn.close()
    return customers

def add_customer(first_name, last_name, email):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO customers (first_name, last_name, email) VALUES (?,?,?)", (first_name, last_name, email))
    conn.commit()
    conn.close()

def delete_customer(customer_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM customers WHERE customer_id=?", (customer_id,))
    conn.commit()
    conn.close()

# Run this once when the app starts
init_db()
