from pathlib import Path

import pandas as pd

INPUT_FILE = Path("data/model/recent_7day_summary.csv")
OUTPUT_FILE = Path("data/model/anomaly_status.csv")


def main():
    df = pd.read_csv(INPUT_FILE)

    latest_price = df["modal_price"].iloc[-1]
    mean_price = df["modal_price"].mean()
    std_price = df["modal_price"].std()

    z_score = (latest_price - mean_price) / std_price

    if abs(z_score) >= 2:
        status = "ANOMALY"
    else:
        status = "NORMAL"

    output = pd.DataFrame([{
        "latest_modal_price": round(latest_price, 2),
        "recent_average_price": round(mean_price, 2),
        "z_score": round(z_score, 2),
        "anomaly_status": status,
    }])

    output.to_csv(OUTPUT_FILE, index=False)

    print("=== PRICE ANOMALY CHECK ===")
    print(f"Latest modal price: {latest_price:.2f}")
    print(f"7-day average: {mean_price:.2f}")
    print(f"Z-score: {z_score:.2f}")
    print("Status:", status)
    print("Saved:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
