from pathlib import Path

import pandas as pd

INPUT_FILE = Path("data/model/recent_7day_summary.csv")
OUTPUT_FILE = Path("data/model/price_volatility.csv")


def main():
    df = pd.read_csv(INPUT_FILE)

    mean_price = df["modal_price"].mean()
    std_price = df["modal_price"].std()

    volatility_pct = (std_price / mean_price) * 100

    output = pd.DataFrame([{
        "average_modal_price": round(mean_price, 2),
        "price_std_deviation": round(std_price, 2),
        "volatility_pct": round(volatility_pct, 2),
    }])

    output.to_csv(OUTPUT_FILE, index=False)

    print("=== PRICE VOLATILITY ===")
    print(f"Average modal price: {mean_price:.2f}")
    print(f"Price standard deviation: {std_price:.2f}")
    print(f"Volatility: {volatility_pct:.2f}%")
    print("Saved:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
