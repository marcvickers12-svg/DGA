import sqlite3
import bcrypt
from database import DB_FILE

# ----------------------------------------------------
# Create a new user
# ----------------------------------------------------
def create_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Username already exists
    finally:
        conn.close()

# ----------------------------------------------------
# Authenticate user (login)
# ----------------------------------------------------
def authenticate_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()

    if result:
        stored_password = result[0]
        return bcrypt.checkpw(password.encode(), stored_password)
    return False

# ----------------------------------------------------
# List all users
# ----------------------------------------------------
def list_users():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, username FROM users")
    users = c.fetchall()
    conn.close()
    return users

# ----------------------------------------------------
# Delete user by ID
# ----------------------------------------------------
def delete_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return True
