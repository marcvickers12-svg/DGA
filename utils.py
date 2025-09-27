import matplotlib.pyplot as plt
import pandas as pd
import io
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import plotly.graph_objects as go


# ------------------------------------
# Gas Trends Plot
# ------------------------------------
def plot_gas_trends(df, date_col="date"):
    """Line plot of dissolved gases over time using Matplotlib"""
    if df.empty:
        return None

    gases = ["H2", "CH4", "C2H2", "C2H4", "C2H6", "CO", "CO2"]

    plt.figure(figsize=(10, 5))
    for gas in gases:
        if gas in df.columns:
            plt.plot(df[date_col], df[gas], label=gas)

    plt.xlabel("Date")
    plt.ylabel("Concentration (ppm)")
    plt.title("DGA Gas Trends")
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()

    return plt.gcf()


# ------------------------------------
# Duval Triangle (Plotly version)
# ------------------------------------
def plot_duval_triangle(df, date_col="date"):
    """
    Plot Duval Triangle using Plotly instead of python-ternary.
    Uses gases: CH4, C2H2, C2H4.
    """
    if df.empty or not all(col in df.columns for col in ["CH4", "C2H2", "C2H4"]):
        return None

    # Normalize to 100%
    df = df.copy()
    df["sum"] = df["CH4"] + df["C2H2"] + df["C2H4"]
    df["CH4%"] = df["CH4"] / df["sum"] * 100
    df["C2H2%"] = df["C2H2"] / df["sum"] * 100
    df["C2H4%"] = df["C2H4"] / df["sum"] * 100

    # Build ternary scatter plot
    fig = go.Figure()

    fig.add_trace(go.Scatterternary(
        a=df["C2H2%"],
        b=df["C2H4%"],
        c=df["CH4%"],
        mode="markers+lines",
        marker=dict(size=10, color="red", symbol="circle"),
        text=df[date_col].astype(str).tolist(),
        hovertemplate="Date: %{text}<br>C2H2=%{a:.1f}%<br>C2H4=%{b:.1f}%<br>CH4=%{c:.1f}%<extra></extra>"
    ))

    fig.update_layout(
        title="Duval Triangle (Plotly)",
        ternary=dict(
            sum=100,
            aaxis=dict(title="C2H2 %", min=0, linewidth=2),
            baxis=dict(title="C2H4 %", min=0, linewidth=2),
            caxis=dict(title="CH4 %", min=0, linewidth=2)
        ),
        margin=dict(l=50, r=50, t=50, b=50)
    )

    return fig


# ------------------------------------
# Export Transformer PDF Report
# ------------------------------------
def export_transformer_pdf(name, df, duval_res, rogers_res, keygas_res, trend_res, duval_fig=None, trend_fig=None):
    """Generate PDF report for a transformer"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"Transformer Report: {name}", styles["Title"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("Latest Gas Data:", styles["Heading2"]))
    elements.append(Paragraph(df.tail().to_html(index=False), styles["Normal"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("Analysis Results:", styles["Heading2"]))
    elements.append(Paragraph(f"Duval: {duval_res}", styles["Normal"]))
    elements.append(Paragraph(f"Rogers: {rogers_res}", styles["Normal"]))
    elements.append(Paragraph(f"Key Gas: {keygas_res}", styles["Normal"]))
    elements.append(Paragraph(f"Trend: {trend_res}", styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)
    return buffer


# ------------------------------------
# Export Fleet PDF Report
# ------------------------------------
def export_fleet_pdf(sites, transformers):
    """Export fleet-level summary PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Fleet Report", styles["Title"]))
    elements.append(Spacer(1, 12))

    for site in sites:
        elements.append(Paragraph(f"Site: {site['name']} ({site['location']})", styles["Heading2"]))
        site_transformers = [t for t in transformers if t["site_id"] == site["id"]]
        if site_transformers:
            for tx in site_transformers:
                elements.append(Paragraph(f"- {tx['name']} ({tx['rating']})", styles["Normal"]))
        else:
            elements.append(Paragraph("No transformers yet.", styles["Normal"]))
        elements.append(Spacer(1, 12))

    doc.build(elements)
    buffer.seek(0)
    return buffer

