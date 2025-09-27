import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import io

from database import init_db
from auth_utils import create_user, authenticate_user
from analysis import duval, rogers, keygas, trend
from utils import plot_gas_trends, plot_duval_triangle, export_transformer_pdf, export_fleet_pdf

# Initialize DB
init_db()

# -------------------------------
# Session State
# -------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.name = None

if "page" not in st.session_state:
    st.session_state.page = "fleet"  # default = fleet dashboard

if "active_transformer" not in st.session_state:
    st.session_state.active_transformer = None

# -------------------------------
# LOGIN SCREEN
# -------------------------------
if not st.session_state.logged_in:
    st.title("🔐 Login")

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
        st.success(f"Logged in as {st.session_state.name}")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.name = None
            st.session_state.page = "fleet"
            st.session_state.active_transformer = None
            st.rerun()

        st.title("📋 Navigation")
        if st.button("🏭 Fleet Dashboard"):
            st.session_state.page = "fleet"
            st.session_state.active_transformer = None
            st.rerun()
        if st.button("➕ Register Asset"):
            st.session_state.page = "register"
            st.session_state.active_transformer = None
            st.rerun()

    # -------------------------------
    # FLEET DASHBOARD
    # -------------------------------
    if st.session_state.page == "fleet":
        st.title("🏭 Fleet Dashboard")

        conn = sqlite3.connect("dga_app.db")
        query = """
        SELECT t.id as transformer_id, t.name, t.location, t.rating,
               d.date, d.H2, d.CH4, d.C2H2, d.C2H4, d.C2H6, d.CO, d.CO2
        FROM transformers t
        LEFT JOIN (
            SELECT transformer_id, MAX(date) as latest_date
            FROM dga_results
            GROUP BY transformer_id
        ) latest ON t.id = latest.transformer_id
        LEFT JOIN dga_results d ON t.id = d.transformer_id AND d.date = latest.latest_date
        WHERE t.user_id = (SELECT id FROM users WHERE username=?)
        """
        df_fleet = pd.read_sql_query(query, conn, params=(st.session_state.username,))
        conn.close()

        if df_fleet.empty:
            st.warning("No transformers registered yet.")
        else:
            st.subheader("Your Transformers")
            for _, row in df_fleet.iterrows():
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.write(f"**{row['name']}** ({row['rating']})")
                    st.caption(f"{row['location']}")
                with col2:
                    st.write("Last Sample:", row["date"] if row["date"] else "No Data")
                with col3:
                    if st.button(f"View ➡️", key=f"view_{row['transformer_id']}"):
                        st.session_state.page = "asset"
                        st.session_state.active_transformer = row["transformer_id"]
                        st.rerun()

    # -------------------------------
    # REGISTER ASSET
    # -------------------------------
    elif st.session_state.page == "register":
        st.title("➕ Register New Transformer")

        name_t = st.text_input("Transformer Name")
        location = st.text_input("Location")
        rating = st.text_input("Rating (e.g. 33kV, 40MVA)")

        if st.button("Register Transformer"):
            conn = sqlite3.connect("dga_app.db")
            c = conn.cursor()
            c.execute("SELECT id FROM users WHERE username=?", (st.session_state.username,))
            user_id = c.fetchone()[0]
            c.execute("INSERT INTO transformers (user_id, name, location, rating) VALUES (?,?,?,?)",
                      (user_id, name_t, location, rating))
            conn.commit()
            conn.close()
            st.success("✅ Transformer registered!")
            st.session_state.page = "fleet"
            st.rerun()

    # -------------------------------
    # ASSET PAGE
    # -------------------------------
    elif st.session_state.page == "asset" and st.session_state.active_transformer:
        t_id = st.session_state.active_transformer

        # Fetch transformer details
        conn = sqlite3.connect("dga_app.db")
        c = conn.cursor()
        c.execute("SELECT name, location, rating FROM transformers WHERE id=?", (t_id,))
        t_row = c.fetchone()
        df = pd.read_sql_query("SELECT * FROM dga_results WHERE transformer_id=?", conn, params=(t_id,))
        conn.close()

        if not t_row:
            st.error("❌ Transformer not found")
        else:
            st.title(f"⚡ {t_row[0]}")
            st.caption(f"{t_row[1]} • {t_row[2]}")

            # Upload new DGA data
            st.subheader("📤 Upload New DGA Data")
            sample_csv = io.StringIO()
            sample_csv.write("date,H2,CH4,C2H2,C2H4,C2H6,CO,CO2\n")
            sample_csv.write("2024-01-01,120,35,2,18,50,350,3200\n")
            sample_csv.write("2024-02-01,130,40,3,20,55,360,3300\n")
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
                        conn = sqlite3.connect("dga_app.db")
                        df_new["transformer_id"] = t_id
                        df_new.to_sql("dga_results", conn, if_exists="append", index=False)
                        conn.close()
                        st.success("✅ Data uploaded!")
                        st.rerun()

            # Show analysis if data exists
            if not df.empty:
                df["date"] = pd.to_datetime(df["date"], errors="coerce")
                st.subheader("📊 Latest Data")
                st.dataframe(df.tail())

                st.write("### Gas Trends")
                fig_trend = plot_gas_trends(df)
                st.pyplot(fig_trend)

                st.write("### Duval Triangle")
                fig_duval = plot_duval_triangle(df, date_col="date")
                if fig_duval:
                    st.plotly_chart(fig_duval, use_container_width=True)

                st.write("### Analysis Results")
                st.json({
                    "Duval": duval.analyze(df),
                    "Rogers": rogers.analyze(df),
                    "Key Gas": keygas.analyze(df),
                    "Trend": trend.analyze(df),
                })

                if st.button("📄 Export Transformer Report (PDF)"):
                    buf = export_transformer_pdf(
                        name=f"{t_row[0]}",
                        df=df,
                        duval_res=duval.analyze(df),
                        rogers_res=rogers.analyze(df),
                        keygas_res=keygas.analyze(df),
                        trend_res=trend.analyze(df),
                        duval_fig=fig_duval,
                        trend_fig=fig_trend
                    )
                    st.download_button("Download Report", buf, file_name=f"{t_row[0]}_report.pdf")
