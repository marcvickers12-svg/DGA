import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import io
import os

from database import init_db
from auth_utils import create_user, authenticate_user
from analysis import duval, rogers, keygas, trend, health
from utils import (
    plot_gas_trends,
    plot_duval_triangle,
    export_transformer_pdf,
    export_fleet_pdf,
    log_asset_event
)

# --------------------------------------------------
# Initialize DB
init_db()

# --------------------------------------------------
# Session state setup
if "page" not in st.session_state:
    st.session_state.page = "login"

if "active_site" not in st.session_state:
    st.session_state.active_site = None

if "active_transformer" not in st.session_state:
    st.session_state.active_transformer = None

# --------------------------------------------------
# Login page
def login_page():
    st.title("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = authenticate_user(username, password)
        if user:
            st.session_state.page = "dashboard"
            st.success(f"Welcome {username}!")
        else:
            st.error("Invalid username or password")

# --------------------------------------------------
# Dashboard
def dashboard_page():
    st.sidebar.success("Logged in")
    menu = ["Fleet Dashboard", "Sites", "Logout"]
    choice = st.sidebar.radio("Menu", menu)

    if choice == "Fleet Dashboard":
        st.header("📊 Fleet Dashboard")
        st.info("No transformers registered yet.")

    elif choice == "Sites":
        sites_page()

    elif choice == "Logout":
        st.session_state.page = "login"

# --------------------------------------------------
# Sites page
def sites_page():
    st.header("🏭 Sites")
    st.write("Here you can manage sites and assets (transformers).")

    if st.button("➕ Create Site"):
        st.session_state.page = "create_site"

# --------------------------------------------------
# Create site page
def create_site_page():
    st.header("➕ Create Site")
    site_name = st.text_input("Site Name")
    site_location = st.text_input("Location")

    if st.button("Save Site"):
        if site_name:
            st.success(f"✅ Site '{site_name}' created!")
            st.session_state.page = "dashboard"
        else:
            st.error("Please enter a site name")

    if st.button("⬅️ Back"):
        st.session_state.page = "sites"

# --------------------------------------------------
# Router
if st.session_state.page == "login":
    login_page()
elif st.session_state.page == "dashboard":
    dashboard_page()
elif st.session_state.page == "create_site":
    create_site_page()
