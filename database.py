import sqlite3

DB_FILE = "dga_app.db"

# ----------------------------------------------------
# Initialize database (create tables if not exist)
# ----------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password BLOB NOT NULL
        )
    """)

    # Sites table
    c.execute("""
        CREATE TABLE IF NOT EXISTS sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Assets table (linked to sites)
    c.execute("""
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES sites(id) ON DELETE CASCADE
        )
    """)

    # DGA results table (linked to assets)
    c.execute("""
        CREATE TABLE IF NOT EXISTS dga_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            h2 REAL,
            ch4 REAL,
            c2h2 REAL,
            c2h4 REAL,
            c2h6 REAL,
            co REAL,
            co2 REAL,
            o2 REAL,
            n2 REAL,
            tdcg REAL,
            FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()

# ----------------------------------------------------
# Utility function for running queries
# ----------------------------------------------------
def query_db(query, params=(), fetchone=False, fetchall=False, commit=False):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(query, params)

    data = None
    if fetchone:
        data = c.fetchone()
    elif fetchall:
        data = c.fetchall()

    if commit:
        conn.commit()

    conn.close()
    return data
