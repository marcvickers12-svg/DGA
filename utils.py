import plotly.express as px
import sqlite3
from fpdf import FPDF
from datetime import datetime

DB_FILE = "dga_app.db"

def plot_gas_trends(df, date_col="date"):
    fig = px.line(df, x=date_col, y=df.columns.drop(date_col), title="Gas Trends")
    return fig

def plot_duval_triangle(df, date_col="date"):
    fig = px.scatter_ternary(df,
        a="CH4", b="C2H4", c="C2H2",
        color=date_col,
        title="Duval Triangle"
    )
    return fig

def export_transformer_pdf(transformer_id):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Transformer Report {transformer_id}", ln=True)
    filename = f"transformer_{transformer_id}_report.pdf"
    pdf.output(filename)
    return filename

def export_fleet_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Fleet Report", ln=True)
    filename = "fleet_report.pdf"
    pdf.output(filename)
    return filename

def log_asset_event(asset_id, message):
    print(f"[{datetime.now()}] Asset {asset_id}: {message}")
