def analyze(df):
    latest = df.iloc[-1]
    thresholds = {
        "H2": 100, "CH4": 120, "C2H2": 35, "C2H4": 65, "C2H6": 65,
        "CO": 700, "CO2": 9000
    }
    alerts = {}
    for gas, limit in thresholds.items():
        if gas in latest and latest[gas] > limit:
            alerts[gas] = f"High ({latest[gas]} ppm > {limit} ppm)"
    if not alerts:
        return {"KeyGas": "All gases within safe limits"}
    return {"KeyGas Alerts": alerts}
