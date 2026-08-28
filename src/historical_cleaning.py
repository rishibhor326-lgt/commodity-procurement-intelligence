from pathlib import Path

import pandas as pd

from project_config import (
    CLEANED_HISTORICAL_FILE,
    HISTORICAL_FILE,
    MARKET,
)


def main():
    df = pd.read_csv(
        HISTORICAL_FILE,
        parse_dates=["arrival_date"],
    )

    market_df = df[df["market"] == MARKET].copy()

    if market_df.empty:
        raise ValueError(
            f"No historical data found for market: {MARKET}"
        )

    numeric_cols = [
        "arrivals_mt",
        "min_price",
        "max_price",
        "modal_price",
    ]

    for column in numeric_cols:
        market_df[column] = pd.to_numeric(
            market_df[column],
            errors="coerce",
        )

    q1 = market_df["arrivals_mt"].quantile(0.25)
    q3 = market_df["arrivals_mt"].quantile(0.75)
    iqr = q3 - q1

    extreme_arrival_limit = q3 + (10 * iqr)

    median_max_price = market_df["max_price"].median()
    extreme_price_limit = median_max_price * 5

    suspicious_mask = (
        (market_df["arrivals_mt"] > extreme_arrival_limit)
        | (market_df["max_price"] > extreme_price_limit)
    )

    suspicious_rows = market_df[suspicious_mask]

    cleaned_df = df.drop(
        index=suspicious_rows.index
    ).reset_index(drop=True)

    output_file = Path(CLEANED_HISTORICAL_FILE)
    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    cleaned_df.to_csv(
        output_file,
        index=False,
    )

    print("Historical cleaning complete.")
    print("Selected market:", MARKET)
    print("Original rows:", len(df))
    print("Suspicious rows removed:", len(suspicious_rows))
    print("Cleaned rows:", len(cleaned_df))

    if not suspicious_rows.empty:
        print("\nRemoved suspicious rows:")
        print(
            suspicious_rows[
                [
                    "arrival_date",
                    "arrivals_mt",
                    "min_price",
                    "max_price",
                    "modal_price",
                ]
            ].to_string(index=False)
        )

    print("\nSaved to:", output_file)


if __name__ == "__main__":
    main()
