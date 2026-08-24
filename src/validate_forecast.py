from pathlib import Path

import pandas as pd

FORECAST_FILE = Path("data/model/forecast_7day.csv")


def main():
    df = pd.read_csv(FORECAST_FILE)

    minimum = df["predicted_modal_price"].min()
    maximum = df["predicted_modal_price"].max()
    average = df["predicted_modal_price"].mean()

    change = (
        df["predicted_modal_price"].iloc[-1]
        - df["predicted_modal_price"].iloc[0]
    )

    print("=== FORECAST VALIDATION ===")
    print(f"Minimum forecast: {minimum:.2f}")
    print(f"Maximum forecast: {maximum:.2f}")
    print(f"Average forecast: {average:.2f}")
    print(f"7-day change: {change:.2f}")
    print("All prices positive:", (df["predicted_modal_price"] > 0).all())
    print("Forecast rows:", len(df))


if __name__ == "__main__":
    main()
