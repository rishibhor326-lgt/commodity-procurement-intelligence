from pathlib import Path

import pandas as pd

ACTUAL_FILE = Path("data/model/recent_7day_summary.csv")
FORECAST_FILE = Path("data/model/forecast_7day.csv")
OUTPUT_FILE = Path("data/model/procurement_signal.csv")


def main():
    actual = pd.read_csv(ACTUAL_FILE)
    forecast = pd.read_csv(FORECAST_FILE)

    current_price = actual["modal_price"].iloc[-1]
    forecast_average = forecast["predicted_modal_price"].mean()

    change_pct = (
        (forecast_average - current_price)
        / current_price
        * 100
    )

    if change_pct >= 5:
        signal = "BUY SOON"
    elif change_pct <= -5:
        signal = "WAIT"
    else:
        signal = "WATCH"

    output = pd.DataFrame([{
        "current_modal_price": round(current_price, 2),
        "forecast_7day_average": round(forecast_average, 2),
        "expected_change_pct": round(change_pct, 2),
        "procurement_signal": signal,
    }])

    output.to_csv(OUTPUT_FILE, index=False)

    print("=== PROCUREMENT SIGNAL ===")
    print(f"Current modal price: {current_price:.2f}")
    print(f"7-day forecast average: {forecast_average:.2f}")
    print(f"Expected change: {change_pct:.2f}%")
    print("Signal:", signal)
    print("Saved:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
