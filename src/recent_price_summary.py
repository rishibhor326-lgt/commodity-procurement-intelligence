from pathlib import Path

import pandas as pd

DATA_FILE = Path("data/historical/maharashtra_onion_2026_02_to_07.csv")
OUTPUT_FILE = Path("data/model/recent_7day_summary.csv")

MARKET = "Pune(Pimpri) APMC"


def main():
    df = pd.read_csv(DATA_FILE, parse_dates=["arrival_date"])

    df = (
        df[df["market"] == MARKET]
        .sort_values("arrival_date")
        .tail(7)
        .copy()
    )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)

    print("=== LATEST 7-DAY PRICE SUMMARY ===")
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

    print("\n7-day minimum modal price:", df["modal_price"].min())
    print("7-day maximum modal price:", df["modal_price"].max())
    print("7-day average modal price:", round(df["modal_price"].mean(), 2))
    print("Saved:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
