import pandas as pd
import numpy as np

def calculate_health(df):
    """
    Simple health indicator for transformer based on latest DGA reading.
    Uses thresholds for key gases (ppm).
    """

    if df.empty:
        return {"status": "No Data", "score": 0, "details": {}}

    latest = df.sort_values("date").iloc[-1]

    # IEEE C57.104 thresholds (simplified)
    limits = {
        "H2": [100, 700],
        "CH4": [120, 1000],
        "C2H2": [35, 50],
        "C2H4": [50, 200],
        "C2H6": [65, 100],
        "CO": [350, 570],
        "CO2": [2500, 10000],
    }

    status = "Healthy"
    score = 100
    details = {}

    for gas, (warn, crit) in limits.items():
        val = latest.get(gas, np.nan)
        if pd.isna(val):
            continue

        if val >= crit:
            status = "Critical"
            score -= 50
        elif val >= warn and status != "Critical":
            status = "Warning"
            score -= 25

        details[gas] = float(val)

    return {"status": status, "score": max(score, 0), "details": details}
