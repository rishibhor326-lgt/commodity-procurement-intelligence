from pathlib import Path

import pandas as pd

SIGNAL_FILE = Path("data/model/procurement_signal.csv")
VOLATILITY_FILE = Path("data/model/price_volatility.csv")
ANOMALY_FILE = Path("data/model/anomaly_status.csv")

OUTPUT_FILE = Path("data/model/procurement_attention.csv")


def main():
    signal = pd.read_csv(SIGNAL_FILE).iloc[0]
    volatility = pd.read_csv(VOLATILITY_FILE).iloc[0]
    anomaly = pd.read_csv(ANOMALY_FILE).iloc[0]

    expected_change = abs(signal["expected_change_pct"])
    volatility_pct = volatility["volatility_pct"]
    anomaly_status = anomaly["anomaly_status"]

    score = 0

    if expected_change >= 5:
        score += 40
    elif expected_change >= 2:
        score += 20

    if volatility_pct >= 10:
        score += 40
    elif volatility_pct >= 5:
        score += 20

    if anomaly_status == "ANOMALY":
        score += 20

    if score >= 60:
        attention = "HIGH"
    elif score >= 30:
        attention = "MEDIUM"
    else:
        attention = "LOW"

    output = pd.DataFrame([{
        "expected_change_pct": expected_change,
        "volatility_pct": volatility_pct,
        "anomaly_status": anomaly_status,
        "attention_score": score,
        "attention_level": attention,
    }])

    output.to_csv(OUTPUT_FILE, index=False)

    print("=== PROCUREMENT ATTENTION ===")
    print(f"Expected change: {expected_change:.2f}%")
    print(f"Volatility: {volatility_pct:.2f}%")
    print("Anomaly status:", anomaly_status)
    print("Attention score:", score)
    print("Attention level:", attention)
    print("Saved:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
