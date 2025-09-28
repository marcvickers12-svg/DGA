import sqlite3

DB_FILE = "dga_app.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # --- Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # --- Sites table
    c.execute('''
        CREATE TABLE IF NOT EXISTS sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    ''')

    # --- Assets (Transformers)
    c.execute('''
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER,
            name TEXT NOT NULL,
            type TEXT,
            FOREIGN KEY (site_id) REFERENCES sites (id)
        )
    ''')

    # --- Readings (DGA results per asset)
    c.execute('''
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id INTEGER,
            date TEXT,
            h2 REAL,
            ch4 REAL,
            c2h2 REAL,
            c2h4 REAL,
            c2h6 REAL,
            co REAL,
            co2 REAL,
            FOREIGN KEY (asset_id) REFERENCES assets (id)
        )
    ''')

    # --- Insert default admin if not exists
    c.execute("SELECT * FROM users WHERE username = ?", ("admin",))
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("admin", "admin123"))
        print("✅ Default admin user created (username: admin, password: admin123)")

    conn.commit()
    conn.close()


def get_connection():
    return sqlite3.connect(DB_FILE)
