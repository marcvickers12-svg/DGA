def init_db():
    conn = sqlite3.connect("dga_app.db")
    c = conn.cursor()

    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # Sites table
    c.execute('''
        CREATE TABLE IF NOT EXISTS sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    ''')

    # Assets table
    c.execute('''
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER,
            name TEXT NOT NULL,
            type TEXT,
            FOREIGN KEY (site_id) REFERENCES sites (id)
        )
    ''')

    # Readings table
    c.execute('''
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id INTEGER,
            date TEXT,
            h2 REAL, ch4 REAL, c2h2 REAL, c2h4 REAL, c2h6 REAL, co REAL, co2 REAL,
            FOREIGN KEY (asset_id) REFERENCES assets (id)
        )
    ''')

    # Insert default admin user if not exists
    c.execute("SELECT * FROM users WHERE username = ?", ("admin",))
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("admin", "admin123"))

    conn.commit()
    conn.close()
