from pathlib import Path
import pickle

import pandas as pd
from sklearn.metrics import mean_absolute_error, root_mean_squared_error


MODEL_FILE = Path(
    "data/model/linear_regression_model.pkl"
)

TEST_FILE = Path(
    "data/model/test.csv"
)

SELECTION_FILE = Path(
    "data/model/model_selection.csv"
)

EVALUATION_FILE = Path(
    "data/model/final_evaluation.csv"
)


def main():
    with open(MODEL_FILE, "rb") as file:
        saved = pickle.load(file)

    model = saved["model"]
    features = saved["features"]

    test = pd.read_csv(TEST_FILE)

    selection = pd.read_csv(SELECTION_FILE)

    selected_rows = selection[
        selection["selected"] == True
    ]

    if selected_rows.empty:
        raise ValueError(
            "No selected forecasting method found."
        )

    selected_method = selected_rows.iloc[0]["method"]

    actual = test["modal_price"]

    predictions = {
        "naive_baseline": test["modal_lag_1"],
        "moving_average_7": test["modal_roll_mean_7"],
        "trend_baseline": (
            test["modal_lag_1"]
            + (
                test["modal_lag_1"]
                - test["modal_lag_7"]
            ) / 6
        ).clip(lower=0),
        "linear_regression": model.predict(
            test[features]
        ),
    }

    rows = []

    for method, prediction in predictions.items():
        mae = mean_absolute_error(
            actual,
            prediction,
        )

        rmse = root_mean_squared_error(
            actual,
            prediction,
        )

        rows.append(
            {
                "method": method,
                "test_mae": round(mae, 2),
                "test_rmse": round(rmse, 2),
                "selected_method": (
                    method == selected_method
                ),
            }
        )

    evaluation = pd.DataFrame(rows)

    EVALUATION_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    evaluation.to_csv(
        EVALUATION_FILE,
        index=False,
    )

    selected_result = evaluation[
        evaluation["selected_method"]
    ].iloc[0]

    print("=== FINAL TEST EVALUATION ===")

    print(
        evaluation.to_string(index=False)
    )

    print(
        "\nMethod selected using validation:",
        selected_method,
    )

    print(
        "Final selected-method Test MAE:",
        selected_result["test_mae"],
    )

    print(
        "Final selected-method Test RMSE:",
        selected_result["test_rmse"],
    )

    print(
        "Saved:",
        EVALUATION_FILE,
    )


if __name__ == "__main__":
    main()
