import numpy as np

def analyze(df):
    latest = df.iloc[-1]
    gases = ["CH4", "C2H2", "C2H4"]
    values = np.array([latest.get(g,0) for g in gases])
    if values.sum() == 0:
        return {"Duval": "No fault detected"}
    norm = values / values.sum() * 100
    CH4, C2H2, C2H4 = norm

    if C2H2 > 40:
        fault = "D2 (High Energy Discharge)"
    elif CH4 > 50:
        fault = "PD (Partial Discharge)"
    elif C2H4 > 40:
        fault = "T3 (Severe Thermal Fault)"
    elif 20 < C2H4 < 40:
        fault = "T2 (Thermal 300-700°C)"
    else:
        fault = "T1 (Thermal <300°C)"

    return {"Duval": fault, "Normalized": {"CH4": CH4, "C2H2": C2H2, "C2H4": C2H4}}
