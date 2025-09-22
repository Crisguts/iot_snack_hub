import sqlite3

DB_NAME = "store.db"

def get_db():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()

def get_items():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM items")
    items = c.fetchall()
    conn.close()
    return items

def add_item(name):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO items (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()

def delete_item(item_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM items WHERE id=?", (item_id,))
    conn.commit()
    conn.close()

# Run this once when the app starts
init_db()
