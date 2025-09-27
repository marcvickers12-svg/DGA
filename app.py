import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import io
import os

from database import init_db
from auth_utils import create_user, authenticate_user, list_users, delete_user
from analysis import duval, rogers, keygas, trend, health
from utils import (
    plot_gas_trends,
    plot_duval_triangle,
    export_transformer_pdf,
    export_fleet_pdf,
    log_asset_event
)

# ------------------------------
# Initialize DB
# ------------------------------
init_db()

# ------------------------------
# Authentication
# ------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None

if not st.session_state.logged_in:
    st.title("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if authenticate_user(username, password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success(f"✅ Welcome {username}!")
            st.experimental_rerun()
        else:
            st.error("❌ Invalid username or password")

    st.stop()

# ------------------------------
# Sidebar Navigation
# ------------------------------
menu = ["Fleet Dashboard", "Sites", "User Management", "Logout"]
choice = st.sidebar.radio("Menu", menu)

# ------------------------------
# Fleet Dashboard
# ------------------------------
if choice == "Fleet Dashboard":
    st.title("📊 Fleet Dashboard")
    st.info("Fleet-level KPIs, trends, and reports will be shown here.")

# ------------------------------
# Sites Page
# ------------------------------
elif choice == "Sites":
    st.title("🏭 Sites")
    st.info("Here you will manage transformer sites and assets.")

# ------------------------------
# User Management Section
# ------------------------------
elif choice == "User Management":
    st.title("👥 User Management")

    tabs = st.tabs(["➕ Add User", "📋 List Users", "🗑 Delete User"])

    # --- Add User ---
    with tabs[0]:
        st.subheader("➕ Add New User")
        new_username = st.text_input("Username")
        new_email = st.text_input("Email")
        new_name = st.text_input("Full Name")
        new_password = st.text_input("Password", type="password")
        new_company = st.text_input("Company")

        if st.button("Create User"):
            if new_username and new_email and new_password:
                create_user(new_username, new_email, new_name, new_password, new_company)
                st.success(f"✅ User `{new_username}` created successfully!")
            else:
                st.error("⚠️ Please fill all fields")

    # --- List Users ---
    with tabs[1]:
        st.subheader("📋 Registered Users")
        users = list_users()
        if users:
            st.table(users)
        else:
            st.info("No users found.")

    # --- Delete User ---
    with tabs[2]:
        st.subheader("🗑 Delete User")
        users = list_users()
        if users:
            usernames = [u["username"] for u in users]
            user_to_delete = st.selectbox("Select User to Delete", usernames)

            if st.button("Delete User"):
                delete_user(user_to_delete)
                st.success(f"✅ User `{user_to_delete}` deleted successfully!")
                st.experimental_rerun()
        else:
            st.info("No users available for deletion.")

# ------------------------------
# Logout
# ------------------------------
elif choice == "Logout":
    st.session_state.logged_in = False
    st.session_state.username = None
    st.success("👋 Logged out successfully!")
    st.experimental_rerun()
