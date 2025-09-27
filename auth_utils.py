import sqlite3
import bcrypt

DB_PATH = "dga_app.db"

def create_user(username: str, email: str, name: str, password: str, company: str = "General"):
    """
    Create a new user in DB with a bcrypt-hashed password.
    Returns True if success, False if username already exists.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Hash password securely
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    try:
        c.execute(
            "INSERT INTO users (username, email, name, password, company) VALUES (?, ?, ?, ?, ?)",
            (username, email, name, hashed_pw, company)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Username already exists
        return False
    finally:
        conn.close()


def authenticate_user(username: str, password: str):
    """
    Authenticate a user by username and password.
    Returns the user's display name if successful, None if failed.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT name, password FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()

    if row:
        name, hashed_pw = row
        if bcrypt.checkpw(password.encode(), hashed_pw.encode()):
            return name
    return None
