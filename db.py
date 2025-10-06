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
    c.execute("SELECT * FROM customers ORDER BY first_name COLLATE NOCASE, last_name COLLATE NOCASE")
    customers = c.fetchall()
    conn.close()
    return customers

def add_customer(first_name, last_name, email):
    conn = None
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("""
            INSERT INTO customers (first_name, last_name, email)
            VALUES (?, ?, ?)
        """, (first_name, last_name, email))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding customer: {e}")
        return False
    finally:
        if conn:
            conn.close()

def delete_customer(customer_id):
    conn = None
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("DELETE FROM customers WHERE customer_id=?", (customer_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting customer: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_customers_paginated(limit, offset, search=None):
    conn = get_db()
    cur = conn.cursor()
    
    if search:
        names = search.split(None, 1)  # split into at most 2 parts
        if len(names) == 2:
            first_pattern = f"{names[0]}%"
            last_pattern = f"{names[1]}%"
            cur.execute("""
                SELECT * FROM customers
                WHERE first_name LIKE ? AND last_name LIKE ?
                ORDER BY first_name COLLATE NOCASE, last_name COLLATE NOCASE
                LIMIT ? OFFSET ?
            """, (first_pattern, last_pattern, limit, offset))
        else:
            pattern = f"{names[0]}%"
            cur.execute("""
                SELECT * FROM customers
                WHERE first_name LIKE ? OR last_name LIKE ? OR email LIKE ?
                ORDER BY first_name COLLATE NOCASE, last_name COLLATE NOCASE
                LIMIT ? OFFSET ?
            """, (pattern, pattern, pattern, limit, offset))
    else:
        cur.execute("""
            SELECT * FROM customers
            ORDER BY first_name COLLATE NOCASE, last_name COLLATE NOCASE
            LIMIT ? OFFSET ?
        """, (limit, offset))
    
    rows = cur.fetchall()
    conn.close()
    return rows



def get_customer_count(search=None):
    conn = get_db()
    cur = conn.cursor()
    if search:
        names = search.split(None, 1)
        if len(names) == 2:
            first_pattern = f"{names[0]}%"
            last_pattern = f"{names[1]}%"
            cur.execute("""
                SELECT COUNT(*) FROM customers
                WHERE first_name LIKE ? AND last_name LIKE ?
            """, (first_pattern, last_pattern))
        else:
            pattern = f"{names[0]}%"
            cur.execute("""
                SELECT COUNT(*) FROM customers
                WHERE first_name LIKE ? OR last_name LIKE ? OR email LIKE ?
            """, (pattern, pattern, pattern))
    else:
        cur.execute("SELECT COUNT(*) FROM customers")
    total = cur.fetchone()[0]
    conn.close()
    return total



# Initialize DB once
init_db()
