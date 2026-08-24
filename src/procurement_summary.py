from pathlib import Path

import pandas as pd

RECENT_FILE = Path("data/model/recent_7day_summary.csv")
FORECAST_FILE = Path("data/model/forecast_7day.csv")
SIGNAL_FILE = Path("data/model/procurement_signal.csv")
VOLATILITY_FILE = Path("data/model/price_volatility.csv")
ANOMALY_FILE = Path("data/model/anomaly_status.csv")
ATTENTION_FILE = Path("data/model/procurement_attention.csv")

OUTPUT_FILE = Path("data/model/procurement_summary.csv")


def main():
    recent = pd.read_csv(RECENT_FILE)
    forecast = pd.read_csv(FORECAST_FILE)

    signal = pd.read_csv(SIGNAL_FILE).iloc[0]
    volatility = pd.read_csv(VOLATILITY_FILE).iloc[0]
    anomaly = pd.read_csv(ANOMALY_FILE).iloc[0]
    attention = pd.read_csv(ATTENTION_FILE).iloc[0]

    summary = pd.DataFrame([{
        "market": recent["market"].iloc[-1],
        "commodity": recent["commodity"].iloc[-1],
        "latest_date": recent["arrival_date"].iloc[-1],
        "current_modal_price": recent["modal_price"].iloc[-1],
        "recent_7day_min": recent["modal_price"].min(),
        "recent_7day_max": recent["modal_price"].max(),
        "recent_7day_average": round(recent["modal_price"].mean(), 2),
        "forecast_7day_average": round(
            forecast["predicted_modal_price"].mean(), 2
        ),
        "expected_change_pct": signal["expected_change_pct"],
        "procurement_signal": signal["procurement_signal"],
        "volatility_pct": volatility["volatility_pct"],
        "anomaly_status": anomaly["anomaly_status"],
        "attention_score": attention["attention_score"],
        "attention_level": attention["attention_level"],
    }])

    summary.to_csv(OUTPUT_FILE, index=False)

    print("=== PROCUREMENT INTELLIGENCE SUMMARY ===")
    print(summary.to_string(index=False))
    print("\nSaved:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
