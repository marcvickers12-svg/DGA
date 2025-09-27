import sqlite3

def init_db():
    conn = sqlite3.connect("dga_app.db")
    c = conn.cursor()

    # Users
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            company TEXT
        )
    """)

    # Transformers linked to users
    c.execute("""
        CREATE TABLE IF NOT EXISTS transformers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            location TEXT,
            rating TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # DGA results linked to transformers
    c.execute("""
        CREATE TABLE IF NOT EXISTS dga_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transformer_id INTEGER,
            date TEXT,
            H2 REAL, CH4 REAL, C2H2 REAL, C2H4 REAL, C2H6 REAL,
            CO REAL, CO2 REAL,
            FOREIGN KEY(transformer_id) REFERENCES transformers(id)
        )
    """)
    conn.commit()
    conn.close()
