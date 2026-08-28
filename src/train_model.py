from pathlib import Path
import pickle

import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, root_mean_squared_error


TRAIN_FILE = Path("data/model/train.csv")
VALIDATION_FILE = Path("data/model/validation.csv")
MODEL_FILE = Path("data/model/linear_regression_model.pkl")
SELECTION_FILE = Path("data/model/model_selection.csv")
ROLLING_FILE = Path("data/model/rolling_validation_results.csv")

FEATURES = [
    "modal_lag_1",
    "modal_lag_7",
    "modal_lag_14",
    "arrivals_lag_1",
    "arrivals_lag_7",
    "modal_roll_mean_7",
    "modal_roll_mean_14",
    "day_of_week",
    "day_of_month",
    "month",
]

TARGET = "modal_price"
N_FOLDS = 3


def get_predictions(model, validation):
    return {
        "naive_baseline": validation["modal_lag_1"],
        "moving_average_7": validation["modal_roll_mean_7"],
        "trend_baseline": (
            validation["modal_lag_1"]
            + (
                validation["modal_lag_1"]
                - validation["modal_lag_7"]
            ) / 6
        ).clip(lower=0),
        "linear_regression": model.predict(
            validation[FEATURES]
        ),
    }


def main():
    train = pd.read_csv(
        TRAIN_FILE,
        parse_dates=["arrival_date"],
    )

    validation = pd.read_csv(
        VALIDATION_FILE,
        parse_dates=["arrival_date"],
    )

    # Everything before the untouched final test set.
    development = (
        pd.concat(
            [train, validation],
            ignore_index=True,
        )
        .sort_values("arrival_date")
        .reset_index(drop=True)
    )

    n = len(development)

    # First 60% is the initial training history.
    initial_train_end = int(n * 0.60)

    remaining = n - initial_train_end
    fold_size = max(
        1,
        remaining // N_FOLDS,
    )

    rolling_results = []

    for fold in range(N_FOLDS):
        validation_start = (
            initial_train_end
            + fold * fold_size
        )

        if fold == N_FOLDS - 1:
            validation_end = n
        else:
            validation_end = min(
                n,
                validation_start + fold_size,
            )

        fold_train = development.iloc[
            :validation_start
        ].copy()

        fold_validation = development.iloc[
            validation_start:validation_end
        ].copy()

        if fold_validation.empty:
            continue

        model = LinearRegression()

        model.fit(
            fold_train[FEATURES],
            fold_train[TARGET],
        )

        predictions = get_predictions(
            model,
            fold_validation,
        )

        actual = fold_validation[TARGET]

        for method, prediction in predictions.items():
            mae = mean_absolute_error(
                actual,
                prediction,
            )

            rmse = root_mean_squared_error(
                actual,
                prediction,
            )

            rolling_results.append(
                {
                    "fold": fold + 1,
                    "method": method,
                    "train_rows": len(
                        fold_train
                    ),
                    "validation_rows": len(
                        fold_validation
                    ),
                    "validation_start": (
                        fold_validation[
                            "arrival_date"
                        ]
                        .min()
                        .date()
                    ),
                    "validation_end": (
                        fold_validation[
                            "arrival_date"
                        ]
                        .max()
                        .date()
                    ),
                    "mae": round(
                        mae,
                        2,
                    ),
                    "rmse": round(
                        rmse,
                        2,
                    ),
                }
            )

    rolling_df = pd.DataFrame(
        rolling_results
    )

    if rolling_df.empty:
        raise ValueError(
            "Rolling validation produced no folds."
        )

    summary = (
        rolling_df
        .groupby(
            "method",
            as_index=False,
        )
        .agg(
            validation_mae=(
                "mae",
                "mean",
            ),
            validation_rmse=(
                "rmse",
                "mean",
            ),
            validation_mae_std=(
                "mae",
                "std",
            ),
            folds=(
                "fold",
                "count",
            ),
        )
    )

    summary[
        "validation_mae"
    ] = summary[
        "validation_mae"
    ].round(2)

    summary[
        "validation_rmse"
    ] = summary[
        "validation_rmse"
    ].round(2)

    summary[
        "validation_mae_std"
    ] = (
        summary[
            "validation_mae_std"
        ]
        .fillna(0)
        .round(2)
    )

    summary = summary.sort_values(
        [
            "validation_mae",
            "validation_rmse",
        ]
    ).reset_index(drop=True)

    selected_method = summary.loc[
        0,
        "method",
    ]

    summary["selected"] = (
        summary["method"]
        == selected_method
    )

    # Refit Linear Regression using ALL data
    # available before the final test set.
    final_model = LinearRegression()

    final_model.fit(
        development[FEATURES],
        development[TARGET],
    )

    with open(
        MODEL_FILE,
        "wb",
    ) as file:
        pickle.dump(
            {
                "model": final_model,
                "features": FEATURES,
            },
            file,
        )

    SELECTION_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    rolling_df.to_csv(
        ROLLING_FILE,
        index=False,
    )

    summary.to_csv(
        SELECTION_FILE,
        index=False,
    )

    print(
        "=== WALK-FORWARD VALIDATION ==="
    )

    print(
        rolling_df.to_string(
            index=False
        )
    )

    print(
        "\n=== FORECAST METHOD RANKING ==="
    )

    print(
        summary.to_string(
            index=False
        )
    )

    print(
        "\nSelected forecast method:",
        selected_method,
    )

    print(
        "Linear Regression refitted on",
        len(development),
        "pre-test rows.",
    )

    print(
        "Saved:",
        SELECTION_FILE,
    )

    print(
        "Saved:",
        ROLLING_FILE,
    )

    print(
        "Saved:",
        MODEL_FILE,
    )


if __name__ == "__main__":
    main()
