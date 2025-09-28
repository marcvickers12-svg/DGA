import streamlit as st
import sqlite3
import pandas as pd
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

# ----------------------------------------------------
# Initialize database
# ----------------------------------------------------
init_db()

# ----------------------------------------------------
# Session state initialization
# ----------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = None
if "page" not in st.session_state:
    st.session_state.page = "login"
if "active_site" not in st.session_state:
    st.session_state.active_site = None
if "active_transformer" not in st.session_state:
    st.session_state.active_transformer = None

# ----------------------------------------------------
# Sidebar Navigation
# ----------------------------------------------------
def sidebar_menu():
    if st.session_state.authenticated:
        st.sidebar.success(f"Logged in as {st.session_state.username}")
        if st.sidebar.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.page = "login"
            st.experimental_rerun()

        st.sidebar.markdown("### Menu")
        options = [
            "Fleet Dashboard",
            "Sites",
            "Add Transformer",
            "Upload DGA",
            "Analysis",
            "Reports",
            "User Management",
            "IoT Integration (Coming Soon)"
        ]
        choice = st.sidebar.radio("Navigate", options)
        return choice
    return None

# ----------------------------------------------------
# Login Page
# ----------------------------------------------------
def login_page():
    st.title("🔐 GridGuard Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if authenticate_user(username, password):
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.page = "dashboard"
            st.success(f"Welcome {username}!")
            st.experimental_rerun()
        else:
            st.error("Invalid username or password")

# ----------------------------------------------------
# Fleet Dashboard
# ----------------------------------------------------
def fleet_dashboard():
    st.title("📊 Fleet Dashboard")
    st.info("Overview of all registered transformers across sites.")
    conn = sqlite3.connect("dga_app.db")
    df = pd.read_sql("SELECT * FROM transformers", conn)
    conn.close()
    if df.empty:
        st.warning("No transformers registered yet.")
    else:
        st.dataframe(df)

# ----------------------------------------------------
# Sites Page
# ----------------------------------------------------
def sites_page():
    st.title("🏭 Sites")
    st.info("Create and manage sites. Each site can have multiple transformers.")
    conn = sqlite3.connect("dga_app.db")
    c = conn.cursor()

    # Add new site
    with st.form("add_site_form"):
        site_name = st.text_input("Site Name")
        site_location = st.text_input("Location")
        submit = st.form_submit_button("Add Site")
        if submit and site_name:
            c.execute("INSERT INTO sites (name, location) VALUES (?, ?)", (site_name, site_location))
            conn.commit()
            st.success(f"Site '{site_name}' added.")

    # Show sites
    df = pd.read_sql("SELECT * FROM sites", conn)
    if not df.empty:
        site_choice = st.selectbox("Select a Site", df["name"].tolist())
        site_id = df[df["name"] == site_choice]["id"].values[0]
        st.session_state.active_site = site_id
        st.write(f"Selected Site: **{site_choice}**")

        # Show transformers at site
        tdf = pd.read_sql("SELECT * FROM transformers WHERE site_id=?", conn, params=(site_id,))
        if not tdf.empty:
            st.subheader("Transformers at this Site")
            st.dataframe(tdf)
        else:
            st.warning("No transformers at this site yet.")

    conn.close()

# ----------------------------------------------------
# Add Transformer
# ----------------------------------------------------
def add_transformer_page():
    st.title("➕ Add Transformer")
    if st.session_state.active_site is None:
        st.warning("Please select a Site first in the 'Sites' page.")
        return

    with st.form("add_transformer_form"):
        name = st.text_input("Transformer Name")
        rating = st.text_input("Rating (MVA)")
        manufacturer = st.text_input("Manufacturer")
        submit = st.form_submit_button("Add Transformer")
        if submit and name:
            conn = sqlite3.connect("dga_app.db")
            c = conn.cursor()
            c.execute(
                "INSERT INTO transformers (site_id, name, rating, manufacturer) VALUES (?, ?, ?, ?)",
                (st.session_state.active_site, name, rating, manufacturer)
            )
            conn.commit()
            conn.close()
            st.success(f"Transformer '{name}' added.")

# ----------------------------------------------------
# Upload DGA
# ----------------------------------------------------
def upload_dga_page():
    st.title("📤 Upload DGA Results")
    uploaded_file = st.file_uploader("Upload CSV", type="csv")
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.write("Uploaded Data:")
        st.dataframe(df)
        # Save to DB (simplified)
        conn = sqlite3.connect("dga_app.db")
        df.to_sql("dga_results", conn, if_exists="append", index=False)
        conn.close()
        st.success("DGA Results uploaded successfully.")

# ----------------------------------------------------
# Analysis
# ----------------------------------------------------
def analysis_page():
    st.title("🔎 Analysis")
    st.info("Run DGA diagnostics: Duval, Rogers, Key Gas, Trends, Health.")
    conn = sqlite3.connect("dga_app.db")
    df = pd.read_sql("SELECT * FROM dga_results", conn)
    conn.close()
    if df.empty:
        st.warning("No DGA data available.")
        return
    st.subheader("Gas Trends")
    st.plotly_chart(plot_gas_trends(df))
    st.subheader("Duval Triangle")
    st.plotly_chart(plot_duval_triangle(df))

# ----------------------------------------------------
# Reports
# ----------------------------------------------------
def reports_page():
    st.title("📑 Reports")
    if st.button("Export Fleet Report (PDF)"):
        pdf = export_fleet_pdf()
        st.download_button("Download Fleet Report", data=pdf, file_name="fleet_report.pdf")

# ----------------------------------------------------
# User Management
# ----------------------------------------------------
def user_management_page():
    st.title("👥 User Management")
    st.subheader("Add New User")
    with st.form("add_user_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Create User")
        if submit and username:
            create_user(username, password)
            st.success(f"User {username} created.")

    st.subheader("Existing Users")
    users = list_users()
    if users:
        st.write(users)
        del_user = st.selectbox("Select User to Delete", users)
        if st.button("Delete User"):
            delete_user(del_user)
            st.success(f"User {del_user} deleted.")

# ----------------------------------------------------
# IoT Integration (Placeholder)
# ----------------------------------------------------
def iot_integration_page():
    st.title("📡 IoT Integration")
    st.info("Coming Soon: Live data via MQTT from transformer sensors (Modbus-to-MQTT gateway).")

# ----------------------------------------------------
# App Routing
# ----------------------------------------------------
if st.session_state.page == "login":
    login_page()
else:
    page = sidebar_menu()
    if page == "Fleet Dashboard":
        fleet_dashboard()
    elif page == "Sites":
        sites_page()
    elif page == "Add Transformer":
        add_transformer_page()
    elif page == "Upload DGA":
        upload_dga_page()
    elif page == "Analysis":
        analysis_page()
    elif page == "Reports":
        reports_page()
    elif page == "User Management":
        user_management_page()
    elif page == "IoT Integration (Coming Soon)":
        iot_integration_page()
