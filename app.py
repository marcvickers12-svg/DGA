import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import io
import os

from database import init_db
from auth_utils import create_user, authenticate_user
from analysis import duval, rogers, keygas, trend, health
from utils import plot_gas_trends, plot_duval_triangle, export_transformer_pdf, export_fleet_pdf, log_asset_event

# -------------------------------
# PAGE CONFIG + BRANDING
# -------------------------------
st.set_page_config(page_title="GridGuard – Transformer DGA & Fleet Monitoring", layout="wide")
st.markdown("<h1 style='text-align: center; color: #2E86C1;'>⚡ GridGuard</h1>", unsafe_allow_html=True)
st.caption("Advanced Transformer DGA Analysis & Fleet Health Monitoring")

# -------------------------------
# Database Initialization
# -------------------------------
DB_PATH = "dga_app.db"

if not os.path.exists(DB_PATH):
    st.warning("⚠️ Database not found. Creating a fresh one...")
    init_db()
else:
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in c.fetchall()]
        conn.close()
        if "sites" not in tables:
            st.warning("⚠️ Old database schema detected. Resetting DB...")
            os.remove(DB_PATH)
            init_db()
    except Exception as e:
        st.error(f"❌ DB check failed: {e}")
        os.remove(DB_PATH)
        init_db()

# -------------------------------
# Session State
# -------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.name = None

if "page" not in st.session_state:
    st.session_state.page = "fleet"

if "active_site" not in st.session_state:
    st.session_state.active_site = None

if "active_transformer" not in st.session_state:
    st.session_state.active_transformer = None

# -------------------------------
# Helper: Breadcrumbs
# -------------------------------
def render_breadcrumbs():
    parts = ["🏭 Fleet"]
    if st.session_state.page in ["site", "asset"] and st.session_state.active_site:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT name FROM sites WHERE id=?", (st.session_state.active_site,))
        site_name = c.fetchone()[0]
        conn.close()
        parts.append(f"📍 {site_name}")
    if st.session_state.page == "asset" and st.session_state.active_transformer:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT name FROM transformers WHERE id=?", (st.session_state.active_transformer,))
        tx_name = c.fetchone()[0]
        conn.close()
        parts.append(f"⚡ {tx_name}")
    st.markdown(" ➡️ ".join(parts))

# -------------------------------
# LOGIN SCREEN
# -------------------------------
if not st.session_state.logged_in:
    st.subheader("🔐 Login to GridGuard")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        name = authenticate_user(username, password)
        if name:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.name = name
            st.success(f"✅ Welcome {name}!")
            st.rerun()
        else:
            st.error("❌ Invalid username or password")

    st.markdown("---")
    st.subheader("👤 Create New Account")
    new_username = st.text_input("New Username")
    new_email = st.text_input("New Email")
    new_name = st.text_input("Full Name")
    new_password = st.text_input("New Password", type="password")
    company = st.text_input("Company", value="General")

    if st.button("Create Account"):
        if create_user(new_username, new_email, new_name, new_password, company):
            st.success("✅ Account created! You can now log in.")
        else:
            st.error("❌ Username already exists")

# -------------------------------
# MAIN APP (after login)
# -------------------------------
else:
    with st.sidebar:
        st.markdown("## ⚡ GridGuard")
        st.caption("Fleet Transformer Monitoring")

        st.success(f"Logged in as {st.session_state.name}")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.name = None
            st.session_state.page = "fleet"
            st.session_state.active_site = None
            st.session_state.active_transformer = None
            st.rerun()

        st.title("📋 Navigation")
        if st.button("🏭 Fleet Dashboard"):
            st.session_state.page = "fleet"
            st.session_state.active_site = None
            st.session_state.active_transformer = None
            st.rerun()
        if st.button("➕ Register Site"):
            st.session_state.page = "register_site"
            st.session_state.active_site = None
            st.rerun()

    # -------------------------------
    # ASSET PAGE (Transformer analysis + history + alarms)
    # -------------------------------
    elif st.session_state.page == "asset" and st.session_state.active_transformer:
        render_breadcrumbs()
        t_id = st.session_state.active_transformer

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT name, rating, site_id FROM transformers WHERE id=?", (t_id,))
        t_row = c.fetchone()
        df = pd.read_sql_query("SELECT * FROM dga_results WHERE transformer_id=?", conn, params=(t_id,))
        conn.close()

        if not t_row:
            st.error("❌ Transformer not found")
        else:
            if st.button("⬅️ Back to Site"):
                st.session_state.page = "site"
                st.session_state.active_transformer = None
                st.session_state.active_site = t_row[2]
                st.rerun()

            st.title(f"⚡ {t_row[0]}")
            st.caption(f"{t_row[1]}")

            # Upload new DGA data
            st.subheader("📤 Upload New DGA Data")
            sample_csv = io.StringIO()
            sample_csv.write("date,H2,CH4,C2H2,C2H4,C2H6,CO,CO2\n")
            sample_csv.write("2024-01-01,120,35,2,18,50,350,3200\n")
            st.download_button("📥 Download Sample CSV", sample_csv.getvalue(),
                               file_name="sample_dga.csv", mime="text/csv")

            file = st.file_uploader("Upload File", type=["csv", "xlsx"])
            if file:
                df_new = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
                required_cols = ["date", "H2", "CH4", "C2H2", "C2H4", "C2H6", "CO", "CO2"]
                if not all(col in df_new.columns for col in required_cols):
                    st.error(f"❌ Invalid file format. Required: {', '.join(required_cols)}")
                else:
                    if st.button("Save Data"):
                        conn = sqlite3.connect(DB_PATH)
                        df_new["transformer_id"] = t_id
                        df_new.to_sql("dga_results", conn, if_exists="append", index=False)
                        conn.close()
                        log_asset_event(t_id, "DGA Data Uploaded", f"{len(df_new)} new records added")
                        st.success("✅ Data uploaded!")
                        st.rerun()

            # Show analysis if data exists
            if not df.empty:
                df["date"] = pd.to_datetime(df["date"], errors="coerce")
                st.subheader("📊 Latest Data")
                st.dataframe(df.tail())

                # --- Health Indicator ---
                st.write("### 🩺 Transformer Health")
                health_res = health.calculate_health(df)
                if health_res["status"] == "Healthy":
                    st.success(f"🟢 Healthy (Score {health_res['score']})")
                elif health_res["status"] == "Warning":
                    st.warning(f"🟡 Warning (Score {health_res['score']})")
                    log_asset_event(t_id, "Alarm: Health Warning", f"Score {health_res['score']}")
                elif health_res["status"] == "Critical":
                    st.error(f"🔴 Critical (Score {health_res['score']})")
                    log_asset_event(t_id, "Alarm: Health Critical", f"Score {health_res['score']}")

                # --- Analysis Results ---
                st.write("### 🔬 Diagnostic Analysis")
                analyses = {
                    "Duval Triangle": duval.analyze(df),
                    "Rogers Ratios": rogers.analyze(df),
                    "Key Gas Method": keygas.analyze(df),
                    "Trend Analysis": trend.analyze(df),
                }
                for method, result in analyses.items():
                    with st.container():
                        st.markdown(f"**{method}**")
                        if isinstance(result, dict):
                            st.table(pd.DataFrame(result.items(), columns=["Parameter", "Result"]))
                            # Alarm logging if critical
                            if "fault" in str(result).lower():
                                log_asset_event(t_id, f"Alarm: {method}", str(result))
                        else:
                            st.info(str(result))

            # --- IoT Integration Coming Soon ---
            st.markdown("---")
            st.subheader("📡 IoT Integration (Coming Soon)")
            st.info("Live transformer monitoring via MQTT and IoT sensors is under development. "
                    "This feature will allow automatic data streaming into GridGuard for real-time analytics.")
            st.checkbox("Enable IoT Streaming (coming soon)", value=False, disabled=True)

            # --- Asset History ---
            st.markdown("---")
            st.subheader("📜 Asset History")
            conn = sqlite3.connect(DB_PATH)
            history_df = pd.read_sql_query(
                "SELECT timestamp, event, details FROM asset_history WHERE transformer_id=? ORDER BY timestamp DESC",
                conn, params=(t_id,)
            )
            conn.close()
            if history_df.empty:
                st.info("No history available yet for this asset.")
            else:
                st.dataframe(history_df, use_container_width=True, height=300)
