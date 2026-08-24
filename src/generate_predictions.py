from pathlib import Path
import pickle

import pandas as pd

MODEL_FILE = Path("data/model/linear_regression_model.pkl")
TEST_FILE = Path("data/model/test.csv")
OUTPUT_FILE = Path("data/model/test_predictions.csv")


def main():
    with open(MODEL_FILE, "rb") as file:
        saved = pickle.load(file)

    model = saved["model"]
    features = saved["features"]

    test = pd.read_csv(TEST_FILE)

    test["predicted_modal_price"] = model.predict(test[features])

    test["prediction_error"] = (
        test["modal_price"] - test["predicted_modal_price"]
    )

    test["absolute_error"] = test["prediction_error"].abs()

    test.to_csv(OUTPUT_FILE, index=False)

    print("=== PREDICTIONS GENERATED ===")
    print("Rows:", len(test))
    print("Saved:", OUTPUT_FILE)
    print("Largest absolute error:", round(test["absolute_error"].max(), 2))


if __name__ == "__main__":
    main()
