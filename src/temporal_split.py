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

    if n < 3:
        raise ValueError(
            f"Not enough feature rows for a train/validation/test split: {n}. "
            "Check that the selected market has sufficient historical observations."
        )

    train_end = max(1, int(n * 0.70))
    validation_end = max(train_end + 1, int(n * 0.85))
    validation_end = min(validation_end, n - 1)

    train = df.iloc[:train_end].copy()
    validation = df.iloc[train_end:validation_end].copy()
    test = df.iloc[validation_end:].copy()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    train.to_csv(OUTPUT_DIR / "train.csv", index=False)
    validation.to_csv(OUTPUT_DIR / "validation.csv", index=False)
    test.to_csv(OUTPUT_DIR / "test.csv", index=False)

    print("=== TEMPORAL SPLIT COMPLETE ===")

    for name, part in (("TRAIN", train), ("VALIDATION", validation), ("TEST", test)):
        print(f"\\n{name}")
        print("Rows:", len(part))
        if not part.empty and part["arrival_date"].notna().any():
            dates = part["arrival_date"].dropna()
            print("Dates:", dates.min().date(), "to", dates.max().date())
        else:
            print("Dates: unavailable (no rows with valid dates)")

    chronological = (
        not train.empty
        and not validation.empty
        and not test.empty
        and train["arrival_date"].max()
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
