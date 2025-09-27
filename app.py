import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

from database import init_db
from analysis import duval, rogers, keygas, trend
from utils import plot_gas_trends, plot_duval_triangle, export_transformer_pdf, export_fleet_pdf

# Initialize DB
init_db()

# -------------------------------
# Authentication
# -------------------------------
with open("auth_config.yaml") as f:
    config = yaml.load(f, Loader=SafeLoader)

# ✅ Updated: removed deprecated "preauthorized"
authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"]
)

# ✅ Updated: use keyword for location
name, auth_status, username = authenticator.login("Login", location="main")

if auth_status == False:
    st.error("Username/password is incorrect")
elif auth_status == None:
    st.warning("Please enter your username and password")
elif auth_status:

    authenticator.logout("Logout", location="sidebar")
    st.sidebar.success(f"Welcome {name} 👋")

    # -------------------------------
    # Main App Menu
    # -------------------------------
    menu = ["Home", "Fleet Dashboard", "Register Transformer", "Upload DGA Data", "Analysis"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Home":
        st.title("⚡ DGA Analysis App")
        st.write(f"Logged in as **{name}** ({username})")

    elif choice == "Register Transformer":
        st.subheader("Register Transformer")
        name_t = st.text_input("Transformer Name")
        location = st.text_input("Location")
        rating = st.text_input("Rating (e.g. 33kV, 40MVA)")

        if st.button("Register"):
            conn = sqlite3.connect("dga_app.db")
            c = conn.cursor()
            # Ensure user exists
            c.execute("INSERT OR IGNORE INTO users (username, company) VALUES (?, ?)", (username, "Company"))
            conn.commit()
            user_id = c.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()[0]
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
            if st.button("Save"):
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
        df_fleet = pd.read_sql_query(query, conn, params=(username,))
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

            # PDF export fleet
            if st.button("📄 Export Fleet Report (PDF)"):
                buf = export_fleet_pdf(df_fleet, diag_counts, pd.DataFrame(), fig, fig)
                st.download_button("Download Fleet Report", buf, file_name="fleet_report.pdf")
