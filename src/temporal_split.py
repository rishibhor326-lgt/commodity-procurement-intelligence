from pathlib import Path

import pandas as pd

from project_config import FEATURE_FILE

INPUT_FILE = Path(FEATURE_FILE)
OUTPUT_DIR = Path("data/model")


def main():

    df = pd.read_csv(
        INPUT_FILE,
        parse_dates=["arrival_date"],
    )

    df = df.sort_values(
        "arrival_date"
    ).reset_index(drop=True)

    n = len(df)

    train_end = int(n * 0.70)
    validation_end = int(n * 0.85)

    train = df.iloc[:train_end].copy()
    validation = df.iloc[train_end:validation_end].copy()
    test = df.iloc[validation_end:].copy()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    train.to_csv(
        OUTPUT_DIR / "train.csv",
        index=False,
    )

    validation.to_csv(
        OUTPUT_DIR / "validation.csv",
        index=False,
    )

    test.to_csv(
        OUTPUT_DIR / "test.csv",
        index=False,
    )

    print("=== TEMPORAL SPLIT COMPLETE ===")

    print("\nTRAIN")
    print("Rows:", len(train))
    print(
        "Dates:",
        train["arrival_date"].min().date(),
        "to",
        train["arrival_date"].max().date(),
    )

    print("\nVALIDATION")
    print("Rows:", len(validation))
    print(
        "Dates:",
        validation["arrival_date"].min().date(),
        "to",
        validation["arrival_date"].max().date(),
    )

    print("\nTEST")
    print("Rows:", len(test))
    print(
        "Dates:",
        test["arrival_date"].min().date(),
        "to",
        test["arrival_date"].max().date(),
    )

    chronological = (
        train["arrival_date"].max()
        < validation["arrival_date"].min()
        < test["arrival_date"].min()
    )

    print(
        "\nChronological order valid:",
        chronological,
    )

    print(
        "Total rows:",
        len(train) + len(validation) + len(test),
    )


if __name__ == "__main__":
    main()
