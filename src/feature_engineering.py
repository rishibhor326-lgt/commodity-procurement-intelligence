from pathlib import Path

import pandas as pd

from project_config import (
    FEATURE_FILE,
    HISTORICAL_FILE,
    MARKET,
)

INPUT_FILE = Path(HISTORICAL_FILE)
OUTPUT_FILE = Path(FEATURE_FILE)


def main():

    df = pd.read_csv(
        INPUT_FILE,
        parse_dates=["arrival_date"],
    )

    df = (
        df[df["market"] == MARKET]
        .sort_values("arrival_date")
        .reset_index(drop=True)
        .copy()
    )

    if df.empty:
        raise ValueError(
            f"No historical data found for market: {MARKET}"
        )

    df["modal_lag_1"] = df["modal_price"].shift(1)
    df["modal_lag_7"] = df["modal_price"].shift(7)
    df["modal_lag_14"] = df["modal_price"].shift(14)

    df["arrivals_lag_1"] = df["arrivals_mt"].shift(1)
    df["arrivals_lag_7"] = df["arrivals_mt"].shift(7)

    previous_modal = df["modal_price"].shift(1)

    df["modal_roll_mean_7"] = previous_modal.rolling(7).mean()
    df["modal_roll_std_7"] = previous_modal.rolling(7).std()

    df["modal_roll_mean_14"] = previous_modal.rolling(14).mean()
    df["modal_roll_std_14"] = previous_modal.rolling(14).std()

    df["day_of_week"] = df["arrival_date"].dt.dayofweek
    df["day_of_month"] = df["arrival_date"].dt.day
    df["month"] = df["arrival_date"].dt.month

    df["modal_return_1d"] = (
        df["modal_price"]
        .pct_change(fill_method=None)
        .shift(1)
    )

    model_df = df.dropna().reset_index(drop=True)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    model_df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("Feature engineering complete.")
    print("Selected market:", MARKET)
    print("Original observations:", len(df))
    print("Model-ready observations:", len(model_df))
    print("Features:", len(model_df.columns))

    print(
        "Date range:",
        model_df["arrival_date"].min().date(),
        "to",
        model_df["arrival_date"].max().date(),
    )

    print("Saved to:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
