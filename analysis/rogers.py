def analyze(df):
    latest = df.iloc[-1]
    try:
        R1 = latest["CH4"] / latest["H2"] if latest["H2"] > 0 else 0
        R2 = latest["C2H2"] / latest["C2H4"] if latest["C2H4"] > 0 else 0
        R3 = latest["C2H4"] / latest["C2H6"] if latest["C2H6"] > 0 else 0
        if R1 < 0.1 and R2 < 0.5:
            fault = "PD (Partial Discharge)"
        elif R1 > 1 and R3 > 1:
            fault = "T2/T3 (Thermal Fault)"
        elif R2 > 1:
            fault = "D1/D2 (Discharge)"
        else:
            fault = "Normal/Unclassified"
    except Exception:
        fault = "Insufficient data"
    return {"Rogers": fault, "Ratios": {"R1": R1, "R2": R2, "R3": R3}}
