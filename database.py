import sqlite3
import bcrypt

DB_PATH = "dga_app.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # ✅ Users table (with username + company fields)
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

    # ✅ Transformers table
    c.execute("""
        CREATE TABLE IF NOT EXISTS transformers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            location TEXT,
            rating TEXT
        )
    """)

    # ✅ DGA results table
    c.execute("""
        CREATE TABLE IF NOT EXISTS dga_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transformer_id INTEGER,
            date TEXT,
            H2 REAL, CH4 REAL, C2H2 REAL, C2H4 REAL, C2H6 REAL,
            CO REAL, CO2 REAL
        )
    """)

    conn.commit()

    # ✅ Seed a master admin if not exists
    c.execute("SELECT * FROM users WHERE username=?", ("master_user",))
    if not c.fetchone():
        hashed_pw = bcrypt.hashpw("master123".encode(), bcrypt.gensalt()).decode()
        c.execute(
            "INSERT INTO users (username, email, name, password, company) VALUES (?, ?, ?, ?, ?)",
            ("master_user", "master@example.com", "Master Account", hashed_pw, "AdminCompany")
        )
        conn.commit()

    conn.close()
