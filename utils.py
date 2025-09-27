import matplotlib.pyplot as plt
import ternary
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

DUVAL_ZONES = {
    "PD": [(0,100,0),(0,90,10),(10,90,0)],
    "D1": [(20,70,10),(30,60,10),(25,65,10)],
    "D2": [(80,20,0),(90,10,0),(100,0,0)],
    "T1": [(0,20,80),(0,10,90),(10,10,80)],
    "T2": [(0,30,70),(0,20,80),(10,20,70)],
    "T3": [(0,0,100),(0,10,90),(10,0,90)]
}

def plot_gas_trends(df):
    fig, ax = plt.subplots()
    for gas in ["H2", "CH4", "C2H2", "C2H4", "C2H6", "CO"]:
        if gas in df.columns:
            ax.plot(df["date"], df[gas], label=gas)
    ax.set_title("Gas Trends Over Time")
    ax.set_xlabel("Date")
    ax.set_ylabel("Concentration (ppm)")
    ax.legend()
    return fig

def plot_duval_triangle(df, date_col="date"):
    required = ["CH4", "C2H2", "C2H4"]
    if not all(g in df.columns for g in required):
        return None
    samples, labels = [], []
    for _, row in df.iterrows():
        CH4, C2H2, C2H4 = row["CH4"], row["C2H2"], row["C2H4"]
        total = CH4 + C2H2 + C2H4
        if total == 0: continue
        samples.append((C2H2/total*100, C2H4/total*100, CH4/total*100))
        labels.append(str(row[date_col]) if date_col in df.columns else "")
    if not samples:
        return None
    scale = 100
    fig, tax = ternary.figure(scale=scale)
    fig.set_size_inches(7, 7)
    tax.boundary(linewidth=2.0)
    tax.gridlines(color="black", multiple=10)
    tax.left_axis_label("C2H2 (%)", fontsize=12, offset=0.14)
    tax.right_axis_label("C2H4 (%)", fontsize=12, offset=0.14)
    tax.bottom_axis_label("CH4 (%)", fontsize=12, offset=0.06)
    for label, points in DUVAL_ZONES.items():
        tax.fill(points, alpha=0.15, label=label)
    tax.scatter(samples, marker="o", color="blue", s=40, label="Samples")
    tax.line(samples, linewidth=1.5, color="blue")
    tax.scatter([samples[-1]], marker="o", color="red", s=80, label="Latest Sample")
    for (x,y,z), label in zip(samples, labels):
        if label: tax.annotate(label, (x,y,z), fontsize=8, ha="center")
    tax.legend()
    tax.ticks(axis="lbr", multiple=20, linewidth=1)
    tax.clear_matplotlib_ticks()
    return fig

def export_transformer_pdf(name, df, duval_res, rogers_res, keygas_res, trend_res, duval_fig, trend_fig):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height-50, f"DGA Report - Transformer: {name}")
    latest = df.iloc[-1].to_dict()
    y = height-100
    for k,v in latest.items():
        c.drawString(60, y, f"{k}: {v}")
        y -= 15
    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Diagnostics")
    y -= 15
    c.setFont("Helvetica", 11)
    c.drawString(60, y, f"Duval: {duval_res['Duval']}")
    y -= 15
    c.drawString(60, y, f"Rogers: {rogers_res['Rogers']}")
    y -= 15
    c.drawString(60, y, f"Key Gas: {keygas_res}")
    y -= 15
    c.drawString(60, y, f"Trend: {trend_res}")
    def embed_plot(fig, x, y, w=250, h=250):
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight")
        buf.seek(0)
        img = ImageReader(buf)
        c.drawImage(img, x, y, width=w, height=h)
        buf.close()
    y = 250
    embed_plot(duval_fig, 50, y)
    embed_plot(trend_fig, 320, y)
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

def export_fleet_pdf(df_fleet, diag_counts, bench_df, heatmap_fig, pie_fig):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height-50, "Fleet DGA Report")
    c.setFont("Helvetica", 12)
    total = len(df_fleet)
    c.drawString(50, height-80, f"Total Transformers: {total}")
    def embed_plot(fig, x, y, w=250, h=250):
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight")
        buf.seek(0)
        img = ImageReader(buf)
        c.drawImage(img, x, y, width=w, height=h)
        buf.close()
    y = 250
    embed_plot(pie_fig, 50, y)
    embed_plot(heatmap_fig, 320, y)
    c.showPage()
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height-50, "Fleet Benchmarking vs IEC Limits")
    y = height-80
    c.setFont("Helvetica", 11)
    if not bench_df.empty:
        for idx, row in bench_df.iterrows():
            c.drawString(50, y, f"{idx}: Avg={row['Fleet Avg (ppm)']:.1f}, Limit={row['IEC/IEEE Limit']}")
            y -= 15
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer
