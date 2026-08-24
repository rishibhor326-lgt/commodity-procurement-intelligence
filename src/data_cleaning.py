from pathlib import Path

import pandas as pd


RAW_FILE = Path("data/raw/mandi_prices_raw.csv")
PROCESSED_DIR = Path("data/processed")
PROCESSED_FILE = PROCESSED_DIR / "mandi_prices_clean.csv"

PRICE_COLUMNS = ["min_price", "max_price", "modal_price"]
TEXT_COLUMNS = [
    "state",
    "district",
    "market",
    "commodity",
    "variety",
    "grade",
]


def clean_mandi_data(df):
    df = df.copy()

    # Remove duplicate records.
    df = df.drop_duplicates()

    # Clean whitespace in text columns.
    for column in TEXT_COLUMNS:
        df[column] = df[column].astype("string").str.strip()

    # Convert arrival date from DD/MM/YYYY into a real datetime value.
    df["arrival_date"] = pd.to_datetime(
        df["arrival_date"],
        format="%d/%m/%Y",
        errors="coerce",
    )

    # Ensure price columns are numeric.
    for column in PRICE_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    # Remove rows missing fields required for price analysis.
    df = df.dropna(
        subset=[
            "state",
            "district",
            "market",
            "commodity",
            "arrival_date",
            "modal_price",
        ]
    )

    # Remove impossible negative prices.
    df = df[
        (df["min_price"] >= 0)
        & (df["max_price"] >= 0)
        & (df["modal_price"] >= 0)
    ]

    return df.reset_index(drop=True)


def main():
    df = pd.read_csv(RAW_FILE)

    print(f"Raw rows: {len(df)}")

    clean_df = clean_mandi_data(df)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    clean_df.to_csv(PROCESSED_FILE, index=False)

    print(f"Clean rows: {len(clean_df)}")
    print(f"Duplicates removed: {len(df) - len(df.drop_duplicates())}")
    print(f"Saved to: {PROCESSED_FILE}")


if __name__ == "__main__":
    main()
