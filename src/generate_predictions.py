from pathlib import Path
import pickle

import pandas as pd


MODEL_FILE = Path(
    "data/model/linear_regression_model.pkl"
)

TEST_FILE = Path(
    "data/model/test.csv"
)

SELECTION_FILE = Path(
    "data/model/model_selection.csv"
)

OUTPUT_FILE = Path(
    "data/model/test_predictions.csv"
)


def main():
    with open(MODEL_FILE, "rb") as file:
        saved = pickle.load(file)

    model = saved["model"]
    features = saved["features"]

    test = pd.read_csv(
        TEST_FILE,
        parse_dates=["arrival_date"],
    )

    selection = pd.read_csv(
        SELECTION_FILE
    )

    selected = selection[
        selection["selected"] == True
    ]

    if selected.empty:
        raise ValueError(
            "No selected forecast method found."
        )

    method = selected.iloc[0]["method"]

    if method == "naive_baseline":
        predictions = test["modal_lag_1"]

    elif method == "moving_average_7":
        predictions = test[
            "modal_roll_mean_7"
        ]

    elif method == "trend_baseline":
        predictions = (
            test["modal_lag_1"]
            + (
                test["modal_lag_1"]
                - test["modal_lag_7"]
            ) / 6
        ).clip(lower=0)

    elif method == "linear_regression":
        predictions = model.predict(
            test[features]
        )

    else:
        raise ValueError(
            f"Unknown forecast method: {method}"
        )

    output = pd.DataFrame(
        {
            "arrival_date": test[
                "arrival_date"
            ],
            "actual_modal_price": test[
                "modal_price"
            ],
            "predicted_modal_price": predictions,
        }
    )

    output["absolute_error"] = (
        output["actual_modal_price"]
        - output["predicted_modal_price"]
    ).abs()

    output["forecast_method"] = method

    output.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("=== PREDICTIONS GENERATED ===")

    print(
        "Forecast method:",
        method,
    )

    print(
        "Rows:",
        len(output),
    )

    print(
        "Largest absolute error:",
        round(
            output["absolute_error"].max(),
            2,
        ),
    )

    print(
        "Saved:",
        OUTPUT_FILE,
    )


if __name__ == "__main__":
    main()
