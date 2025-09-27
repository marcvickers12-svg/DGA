import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

from database import init_db
from auth_utils import create_user, authenticate_user
from analysis import duval, rogers, keygas, trend
from utils import plot_gas_trends, plot_duval_triangle, export_transformer_pdf, export_fleet_pdf

# Initialize DB + seed master user
init_db()

# -------------------------------
# Session State for Login
# -------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.name = None

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
            st.rerun()   # 🔄 NEW (fix for experimental_rerun)
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
    st.sidebar.success(f"Logged in as {st.session_state.name} ({st.session_state.username})")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.name = None
        st.rerun()   # 🔄 NEW (fix for experimental_rerun)

    # -------------------------------
    # Main App Menu
    # -------------------------------
    menu = ["Home", "Fleet Dashboard", "Register Transformer", "Upload DGA Data", "Analysis"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Home":
        st.title("⚡ DGA Analysis App")
        st.write(f"Logged in as **{st.session_state.name}** ({st.session_state.username})")

    elif choice == "Register Transformer":
        st.subheader("Register Transformer")
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
            st.success("Transformer registered!")

    elif choice == "Upload DGA Data":
        st.subheader("Upload DGA CSV/Excel")
        file = st.file_uploader("Upload File", type=["csv", "xlsx"])
        if file:
            df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
            st.write("Preview:", df.head())

            t_id = st.number_input("Transformer ID", min_value=1)
            if st.button("Save Data"):
                conn = sqlite3.connect("dga_app.db")
                df["transformer_id"] = t_id
                df.to_sql("dga_results", conn, if_exists="append", index=False)
                conn.close()
                st.success("Data uploaded!")

    elif choice == "Analysis":
        st.subheader("Run DGA Analysis")
        t_id = st.number_input("Transformer ID", min_value=1)

        conn = sqlite3.connect("dga_app.db")
        df = pd.read_sql_query(f"SELECT * FROM dga_results WHERE transformer_id={t_id}", conn)
        conn.close()

        if df.empty:
            st.warning("No data found")
        else:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            st.write("Latest Data", df.tail())

            st.write("### Gas Trends")
            fig_trend = plot_gas_trends(df)
            st.pyplot(fig_trend)

            st.write("### Duval Triangle")
            fig_duval = plot_duval_triangle(df, date_col="date")
            if fig_duval:
                st.plotly_chart(fig_duval, use_container_width=True)

            st.write("### Duval Analysis")
            duval_res = duval.analyze(df)
            st.json(duval_res)

            st.write("### Rogers")
            rogers_res = rogers.analyze(df)
            st.json(rogers_res)

            st.write("### Key Gas")
            keygas_res = keygas.analyze(df)
            st.json(keygas_res)

            st.write("### Trend")
            trend_res = trend.analyze(df)
            st.json(trend_res)

            if st.button("📄 Export Transformer Report (PDF)"):
                buf = export_transformer_pdf(
                    name=f"Transformer {t_id}",
                    df=df,
                    duval_res=duval_res,
                    rogers_res=rogers_res,
                    keygas_res=keygas_res,
                    trend_res=trend_res,
                    duval_fig=fig_duval,
                    trend_fig=fig_trend
                )
                st.download_button("Download Report", buf, file_name=f"transformer_{t_id}_report.pdf")

    elif choice == "Fleet Dashboard":
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
            st.subheader("Transformer Overview")
            st.dataframe(df_fleet)

            # Fault Distribution
            from analysis import duval
            diagnoses = []
            for _, row in df_fleet.iterrows():
                if pd.notnull(row["C2H2"]):
                    temp_df = pd.DataFrame([row])
                    res = duval.analyze(temp_df)
                    diagnoses.append(res["Duval"])
            if diagnoses:
                diag_counts = pd.Series(diagnoses).value_counts()
                fig, ax = plt.subplots()
                ax.pie(diag_counts, labels=diag_counts.index, autopct="%1.1f%%")
                st.pyplot(fig)

            if st.button("📄 Export Fleet Report (PDF)"):
                buf = export_fleet_pdf(df_fleet, diag_counts, pd.DataFrame(), fig, fig)
                st.download_button("Download Fleet Report", buf, file_name="fleet_report.pdf")
