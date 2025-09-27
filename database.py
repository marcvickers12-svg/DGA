import sqlite3

def init_db():
    conn = sqlite3.connect("dga_app.db")
    c = conn.cursor()

    # -----------------------------
    # Users table
    # -----------------------------
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

    # -----------------------------
    # Sites table
    # -----------------------------
    c.execute("""
        CREATE TABLE IF NOT EXISTS sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            owner TEXT
        )
    """)

    # -----------------------------
    # Transformers table
    # -----------------------------
    c.execute("""
        CREATE TABLE IF NOT EXISTS transformers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER,
            name TEXT NOT NULL,
            rating TEXT,
            location TEXT,
            manufacturer TEXT,
            install_date TEXT,
            notes TEXT,
            FOREIGN KEY(site_id) REFERENCES sites(id)
        )
    """)

    # -----------------------------
    # DGA Results table
    # -----------------------------
    c.execute("""
        CREATE TABLE IF NOT EXISTS dga_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transformer_id INTEGER,
            date TEXT,
            H2 REAL,
            CH4 REAL,
            C2H2 REAL,
            C2H4 REAL,
            C2H6 REAL,
            CO REAL,
            CO2 REAL,
            O2 REAL,
            N2 REAL,
            FOREIGN KEY(transformer_id) REFERENCES transformers(id)
        )
    """)

    # -----------------------------
    # Asset History table
    # -----------------------------
    c.execute("""
        CREATE TABLE IF NOT EXISTS asset_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transformer_id INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            event TEXT,
            details TEXT,
            FOREIGN KEY(transformer_id) REFERENCES transformers(id)
        )
    """)

    conn.commit()
    conn.close()


# -----------------------------
# Helper: Add default master user if missing
# -----------------------------
def add_default_user():
    conn = sqlite3.connect("dga_app.db")
    c = conn.cursor()

    # Check if master user exists
    c.execute("SELECT * FROM users WHERE username=?", ("master_user",))
    if not c.fetchone():
        from auth_utils import hash_password
        hashed_pw = hash_password("master123")
        c.execute("""
            INSERT INTO users (username, email, name, password, company)
            VALUES (?, ?, ?, ?, ?)
        """, ("master_user", "master@example.com", "Master Account", hashed_pw, "Admin"))
        conn.commit()

    conn.close()
