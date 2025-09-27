def analyze(df):
    trends = {}
    for gas in ["H2", "CH4", "C2H2", "C2H4", "C2H6", "CO"]:
        if gas in df.columns and len(df) > 1:
            growth = df[gas].iloc[-1] - df[gas].iloc[-2]
            if growth > 20:
                trends[gas] = f"Rising fast (+{growth} ppm)"
    if not trends:
        return {"Trend": "No alarming growth"}
    return {"Trend Alerts": trends}
