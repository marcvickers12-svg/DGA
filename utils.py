import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import sqlite3
import io
from fpdf import FPDF  
from datetime import datetime

from dga.analysis import duval, rogers, keygas, trend


# -------------------------------
# Plot Gas Trends
# -------------------------------
def plot_gas_trends(df, date_col="date"):
    """Generate a line plot of gas concentrations over time."""
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    fig = px.line(
        df,
        x=date_col,
        y=["H2", "CH4", "C2H2", "C2H4", "C2H6", "CO", "CO2"],
        markers=True,
        title="Gas Concentration Trends",
    )
    return fig


# -------------------------------
# Plot Duval Triangle (Plotly Approximation)
# -------------------------------
def plot_duval_triangle(df, date_col="date"):
    """Plot a simplified Duval Triangle using plotly scatter ternary."""
    if df.empty:
        return None

    latest = df.iloc[-1]
    total = latest["CH4"] + latest["C2H2"] + latest["C2H4"]
    if total == 0:
        return None

    fig = px.scatter_ternary(
        a=[latest["CH4"] / total],
        b=[latest["C2H2"] / total],
        c=[latest["C2H4"] / total],
        title="Duval Triangle (Simplified)",
    )
    return fig


# -------------------------------
# PDF Export - Transformer Report
# -------------------------------
def export_transformer_pdf(name, df, duval_res, rogers_res, keygas_res, trend_res, duval_fig, trend_fig):
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, f"Transformer Report: {name}", ln=True, align="C")

    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="L")

    pdf.ln(10)
    pdf.cell(200, 10, "Diagnostic Results:", ln=True, align="L")

    def write_dict(title, res):
        pdf.set_font("Arial", "B", 12)
        pdf.cell(200, 8, f"- {title}", ln=True, align="L")
        pdf.set_font("Arial", size=11)
        if isinstance(res, dict):
            for k, v in res.items():
                pdf.cell(200, 8, f"   {k}: {v}", ln=True)
        else:
            pdf.cell(200, 8, str(res), ln=True)

    write_dict("Duval Triangle", duval_res)
    write_dict("Rogers Ratios", rogers_res)
    write_dict("Key Gas Method", keygas_res)
    write_dict("Trend Analysis", trend_res)

    # Save gas trends chart
    if trend_fig:
        buf = io.BytesIO()
        trend_fig.write_image(buf, format="PNG")
        buf.seek(0)
        pdf.image(buf, x=10, y=None, w=180)

    output = io.BytesIO()
    pdf.output(output)
    output.seek(0)
    return output


# -------------------------------
# PDF Export - Fleet Report
# -------------------------------
def export_fleet_pdf(sites):
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, f"Fleet Report", ln=True, align="C")

    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="L")

    pdf.ln(10)
    pdf.cell(200, 10, "Sites & Transformers:", ln=True, align="L")

    for site in sites:
        pdf.set_font("Arial", "B", 12)
        pdf.cell(200, 8, f"📍 {site['name']} - {site['location']}", ln=True, align="L")
        pdf.set_font("Arial", size=11)
        for tx in site.get("transformers", []):
            pdf.cell(200, 8, f"   ⚡ {tx['name']} ({tx['rating']})", ln=True)

    output = io.BytesIO()
    pdf.output(output)
    output.seek(0)
    return output


# -------------------------------
# Asset Event Logging
# -------------------------------
def log_asset_event(transformer_id, event, details=""):
    conn = sqlite3.connect("dga_app.db")
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO asset_history (transformer_id, event, details, timestamp)
        VALUES (?, ?, ?, ?)
        """,
        (transformer_id, event, details, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()
    conn.close()
