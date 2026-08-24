from pathlib import Path
import pickle

import pandas as pd

DATA_FILE = Path("data/historical/maharashtra_onion_2026_02_to_07.csv")
MODEL_FILE = Path("data/model/linear_regression_model.pkl")
OUTPUT_FILE = Path("data/model/forecast_7day.csv")

MARKET = "Pune(Pimpri) APMC"
FORECAST_DAYS = 7


def main():
    df = pd.read_csv(DATA_FILE, parse_dates=["arrival_date"])

    df = (
        df[df["market"] == MARKET]
        .sort_values("arrival_date")
        .reset_index(drop=True)
        .copy()
    )

    with open(MODEL_FILE, "rb") as file:
        saved = pickle.load(file)

    model = saved["model"]
    features = saved["features"]

    prices = df["modal_price"].tolist()
    arrivals = df["arrivals_mt"].tolist()

    latest_date = df["arrival_date"].max()
    last_arrival = arrivals[-1]

    forecasts = []

    for step in range(1, FORECAST_DAYS + 1):
        forecast_date = latest_date + pd.Timedelta(days=step)

        row = {
            "modal_lag_1": prices[-1],
            "modal_lag_7": prices[-7],
            "modal_lag_14": prices[-14],
            "arrivals_lag_1": arrivals[-1],
            "arrivals_lag_7": arrivals[-7],
            "modal_roll_mean_7": pd.Series(prices[-7:]).mean(),
            "modal_roll_mean_14": pd.Series(prices[-14:]).mean(),
            "day_of_week": forecast_date.dayofweek,
            "day_of_month": forecast_date.day,
            "month": forecast_date.month,
        }

        X = pd.DataFrame([row])[features]

        predicted_price = float(model.predict(X)[0])

        forecasts.append(
            {
                "forecast_date": forecast_date.date(),
                "predicted_modal_price": round(predicted_price, 2),
            }
        )

        prices.append(predicted_price)

        # Future arrivals are unknown, so we temporarily
        # carry forward the latest known arrival quantity.
        arrivals.append(last_arrival)

    forecast_df = pd.DataFrame(forecasts)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    forecast_df.to_csv(OUTPUT_FILE, index=False)

    print("=== 7-DAY PRICE FORECAST ===")
    print(forecast_df.to_string(index=False))
    print("\nSaved:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
