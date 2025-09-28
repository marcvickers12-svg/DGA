import streamlit as st
import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import io

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

# ----------------------------------------------------
# INITIAL SETUP
# ----------------------------------------------------
st.set_page_config(page_title="GridGuard DGA", layout="wide")
init_db()

if "page" not in st.session_state:
    st.session_state.page = "login"

if "user" not in st.session_state:
    st.session_state.user = None

# ----------------------------------------------------
# LOGIN PAGE
# ----------------------------------------------------
if st.session_state.page == "login":
    st.title("🔐 GridGuard Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if authenticate_user(username, password):
            st.session_state.user = username
            st.session_state.page = "fleet"
            st.success(f"✅ Welcome, {username}!")
        else:
            st.error("❌ Invalid username or password")

# ----------------------------------------------------
# SIDEBAR NAVIGATION
# ----------------------------------------------------
if st.session_state.user:
    with st.sidebar:
        st.success(f"Logged in as {st.session_state.user}")
        if st.button("Logout"):
            st.session_state.user = None
            st.session_state.page = "login"
        st.header("Menu")
        page_choice = st.radio(
            "Navigate",
            ["Fleet Dashboard", "Sites", "Manage Users"],
            index=0 if st.session_state.page == "fleet" else 1
        )
        if page_choice == "Fleet Dashboard":
            st.session_state.page = "fleet"
        elif page_choice == "Sites":
            st.session_state.page = "sites"
        elif page_choice == "Manage Users":
            st.session_state.page = "users"

# ----------------------------------------------------
# MANAGE USERS PAGE
# ----------------------------------------------------
if st.session_state.page == "users" and st.session_state.user:
    st.title("👤 Manage Users")

    # --- Create new user
    st.subheader("Add New User")
    new_username = st.text_input("New Username")
    new_password = st.text_input("New Password", type="password")
    if st.button("Create User"):
        if new_username and new_password:
            if create_user(new_username, new_password):
                st.success(f"✅ User '{new_username}' created successfully.")
            else:
                st.error("⚠️ Username already exists.")
        else:
            st.warning("Please provide both username and password.")

    st.divider()

    # --- List existing users
    st.subheader("Existing Users")
    users = list_users()
    if users:
        for user_id, username in users:
            col1, col2 = st.columns([3, 1])
            col1.write(f"👤 {username}")
            if col2.button("Delete", key=f"del_{user_id}"):
                if delete_user(user_id):
                    st.success(f"✅ User '{username}' deleted.")
                    st.experimental_rerun()
    else:
        st.info("No users found.")

# ----------------------------------------------------
# PLACEHOLDER FOR OTHER PAGES (Fleet, Sites, etc.)
# ----------------------------------------------------
if st.session_state.page == "fleet" and st.session_state.user:
    st.title("📊 Fleet Dashboard")
    st.info("Fleet overview will go here.")

if st.session_state.page == "sites" and st.session_state.user:
    st.title("🏭 Sites Management")
    st.info("Sites and assets management will go here.")
