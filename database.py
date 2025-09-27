import sqlite3

DB_FILE = "dga_app.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Users table
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email TEXT,
        name TEXT,
        password TEXT,
        company TEXT
    )
    """)

    # Sites table
    c.execute("""
    CREATE TABLE IF NOT EXISTS sites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        location TEXT
    )
    """)

    # Transformers table
    c.execute("""
    CREATE TABLE IF NOT EXISTS transformers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        site_id INTEGER,
        name TEXT,
        type TEXT,
        FOREIGN KEY (site_id) REFERENCES sites (id)
    )
    """)

    conn.commit()
    conn.close()
