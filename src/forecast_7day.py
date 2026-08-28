from pathlib import Path
import pickle

import pandas as pd

from project_config import (
    CLEANED_HISTORICAL_FILE,
    MARKET,
)


DATA_FILE = Path(
    CLEANED_HISTORICAL_FILE
)

MODEL_FILE = Path(
    "data/model/linear_regression_model.pkl"
)

SELECTION_FILE = Path(
    "data/model/model_selection.csv"
)

OUTPUT_FILE = Path(
    "data/model/forecast_7day.csv"
)

FORECAST_DAYS = 7


def main():
    df = pd.read_csv(
        DATA_FILE,
        parse_dates=["arrival_date"],
    )

    df = (
        df[df["market"] == MARKET]
        .sort_values("arrival_date")
        .reset_index(drop=True)
        .copy()
    )

    if len(df) < 14:
        raise ValueError(
            f"Not enough historical data for market: {MARKET}"
        )

    selection = pd.read_csv(
        SELECTION_FILE
    )

    selected = selection[
        selection["selected"] == True
    ]

    if selected.empty:
        raise ValueError(
            "No selected forecasting method found."
        )

    selected_method = selected.iloc[0][
        "method"
    ]

    prices = (
        df["modal_price"]
        .astype(float)
        .tolist()
    )

    arrivals = (
        df["arrivals_mt"]
        .astype(float)
        .tolist()
    )

    latest_date = df[
        "arrival_date"
    ].max()

    last_arrival = arrivals[-1]

    forecasts = []

    if selected_method == "linear_regression":
        with open(MODEL_FILE, "rb") as file:
            saved = pickle.load(file)

        model = saved["model"]
        features = saved["features"]

    for step in range(
        1,
        FORECAST_DAYS + 1,
    ):
        forecast_date = (
            latest_date
            + pd.Timedelta(days=step)
        )

        if selected_method == "naive_baseline":
            predicted_price = float(
                prices[-1]
            )

        elif selected_method == "moving_average_7":
            predicted_price = float(
                pd.Series(
                    prices[-7:]
                ).mean()
            )

        elif selected_method == "trend_baseline":
            recent_prices = prices[-7:]

            if len(recent_prices) >= 7:
                slope = (
                    recent_prices[-1]
                    - recent_prices[0]
                ) / 6
            else:
                slope = 0

            predicted_price = max(
                0.0,
                float(
                    prices[-1] + slope
                ),
            )

        elif selected_method == "linear_regression":
            row = {
                "modal_lag_1": prices[-1],
                "modal_lag_7": prices[-7],
                "modal_lag_14": prices[-14],
                "arrivals_lag_1": arrivals[-1],
                "arrivals_lag_7": arrivals[-7],
                "modal_roll_mean_7": pd.Series(
                    prices[-7:]
                ).mean(),
                "modal_roll_mean_14": pd.Series(
                    prices[-14:]
                ).mean(),
                "day_of_week": forecast_date.dayofweek,
                "day_of_month": forecast_date.day,
                "month": forecast_date.month,
            }

            X = pd.DataFrame(
                [row]
            )[features]

            predicted_price = max(
                0.0,
                float(
                    model.predict(X)[0]
                ),
            )

        else:
            raise ValueError(
                f"Unknown forecast method: {selected_method}"
            )

        forecasts.append(
            {
                "forecast_date": (
                    forecast_date.date()
                ),
                "predicted_modal_price": round(
                    predicted_price,
                    2,
                ),
            }
        )

        prices.append(
            predicted_price
        )

        arrivals.append(
            last_arrival
        )

    forecast_df = pd.DataFrame(
        forecasts
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    forecast_df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print(
        "=== 7-DAY PRICE FORECAST ==="
    )

    print(
        "Selected market:",
        MARKET,
    )

    print(
        "Forecast method:",
        selected_method,
    )

    print(
        forecast_df.to_string(
            index=False
        )
    )

    print(
        "\nSaved:",
        OUTPUT_FILE,
    )


if __name__ == "__main__":
    main()
