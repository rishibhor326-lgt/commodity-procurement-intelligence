from pathlib import Path

import pandas as pd

ACTUAL_FILE = Path("data/model/recent_7day_summary.csv")
FORECAST_FILE = Path("data/model/forecast_7day.csv")
OUTPUT_FILE = Path("data/model/actual_forecast_view.csv")


def main():
    actual = pd.read_csv(ACTUAL_FILE)

    actual_view = actual[
        ["arrival_date", "modal_price"]
    ].copy()

    actual_view = actual_view.rename(
        columns={
            "arrival_date": "date",
            "modal_price": "price",
        }
    )

    actual_view["type"] = "Actual"

    forecast = pd.read_csv(FORECAST_FILE)

    forecast_view = forecast.rename(
        columns={
            "forecast_date": "date",
            "predicted_modal_price": "price",
        }
    )

    forecast_view["type"] = "Forecast"

    combined = pd.concat(
        [actual_view, forecast_view],
        ignore_index=True,
    )

    combined.to_csv(OUTPUT_FILE, index=False)

    print("=== ACTUAL + FORECAST VIEW ===")
    print(combined.to_string(index=False))
    print("\nSaved:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
