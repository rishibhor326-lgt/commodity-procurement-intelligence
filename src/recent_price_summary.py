from pathlib import Path

import pandas as pd

from project_config import HISTORICAL_FILE, MARKET

DATA_FILE = Path(HISTORICAL_FILE)
OUTPUT_FILE = Path("data/model/recent_7day_summary.csv")


def main():

    df = pd.read_csv(
        DATA_FILE,
        parse_dates=["arrival_date"],
    )

    df = (
        df[df["market"] == MARKET]
        .sort_values("arrival_date")
        .tail(7)
        .copy()
    )

    if df.empty:
        raise ValueError(
            f"No recent price data found for market: {MARKET}"
        )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("=== LATEST 7-DAY PRICE SUMMARY ===")
    print("Selected market:", MARKET)

    print(
        df[
            [
                "arrival_date",
                "min_price",
                "max_price",
                "modal_price",
                "arrivals_mt",
            ]
        ].to_string(index=False)
    )

    print(
        "\n7-day minimum modal price:",
        df["modal_price"].min(),
    )

    print(
        "7-day maximum modal price:",
        df["modal_price"].max(),
    )

    print(
        "7-day average modal price:",
        round(df["modal_price"].mean(), 2),
    )

    print("Saved:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
