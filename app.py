import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import sqlite3
import io
from fpdf import FPDF   # from fpdf2
from datetime import datetime

from analysis import duval, rogers, keygas, trend

# -------------------------------
# Plot Gas Trends
# -------------------------------
def plot_gas_trends(df, date_col="date"):
    if df.empty:
        return None
    fig = px.line(
        df,
        x=date_col,
        y=["H2", "CH4", "C2H2", "C2H4", "C2H6", "CO", "CO2"],
        title="Gas Trends Over Time"
    )
    return fig

# -------------------------------
# Duval Triangle (Plotly)
# -------------------------------
def plot_duval_triangle(df, date_col="date"):
    if df.empty:
        return None
    latest = df.iloc[-1]
    fig = px.scatter_ternary(
        latest.to_frame().T,
        a="CH4", b="C2H2", c="C2H4",
        hover_name=date_col,
        title="Duval Triangle"
    )
    return fig

# -------------------------------
# Export Transformer Report (PDF)
# -------------------------------
def export_transformer_pdf(transformer_name, df, analyses, health_res):
    buffer = io.BytesIO()
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt=f"Transformer Report: {transformer_name}", ln=True, align="C")

    # Health
    pdf.cell(200, 10, txt=f"Health Status: {health_res['status']} (Score {health_res['score']})", ln=True)

    # Analyses
    pdf.cell(200, 10, txt="Analyses:", ln=True)
    for k, v in analyses.items():
        pdf.cell(200, 10, txt=f"{k}: {str(v)}", ln=True)

    pdf.output(buffer)
    buffer.seek(0)
    return buffer

# -------------------------------
# Export Fleet Report (PDF)
# -------------------------------
def export_fleet_pdf(username, fleet_summary):
    buffer = io.BytesIO()
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt=f"Fleet Report for {username}", ln=True, align="C")
    pdf.cell(200, 10, txt=str(fleet_summary), ln=True)

    pdf.output(buffer)
    buffer.seek(0)
    return buffer

# -------------------------------
# Asset History Logging
# -------------------------------
def log_asset_event(transformer_id, event, details):
    conn = sqlite3.connect("dga_app.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO asset_history (transformer_id, event, details) VALUES (?, ?, ?)",
        (transformer_id, event, details)
    )
    conn.commit()
    conn.close()
