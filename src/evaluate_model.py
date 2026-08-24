from pathlib import Path
import pickle

import pandas as pd
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

MODEL_FILE = Path("data/model/linear_regression_model.pkl")
TEST_FILE = Path("data/model/test.csv")


def main():
    with open(MODEL_FILE, "rb") as file:
        saved = pickle.load(file)

    model = saved["model"]
    features = saved["features"]

    test = pd.read_csv(TEST_FILE)

    actual = test["modal_price"]
    predictions = model.predict(test[features])
    naive_predictions = test["modal_lag_1"]

    model_mae = mean_absolute_error(actual, predictions)
    model_rmse = root_mean_squared_error(actual, predictions)

    naive_mae = mean_absolute_error(actual, naive_predictions)
    naive_rmse = root_mean_squared_error(actual, naive_predictions)

    print("=== FINAL MODEL EVALUATION ===")
    print(f"Model MAE: {model_mae:.2f}")
    print(f"Model RMSE: {model_rmse:.2f}")
    print(f"Naive MAE: {naive_mae:.2f}")
    print(f"Naive RMSE: {naive_rmse:.2f}")
    print("Model beats naive baseline:", model_mae < naive_mae)


if __name__ == "__main__":
    main()
