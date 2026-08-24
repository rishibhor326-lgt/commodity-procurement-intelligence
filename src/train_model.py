from pathlib import Path
import pickle

import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

TRAIN_FILE = Path("data/model/train.csv")
VALIDATION_FILE = Path("data/model/validation.csv")
MODEL_FILE = Path("data/model/linear_regression_model.pkl")

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


def main():
    train = pd.read_csv(TRAIN_FILE)
    validation = pd.read_csv(VALIDATION_FILE)

    model = LinearRegression()
    model.fit(train[FEATURES], train[TARGET])

    predictions = model.predict(validation[FEATURES])

    mae = mean_absolute_error(validation[TARGET], predictions)
    rmse = root_mean_squared_error(validation[TARGET], predictions)

    with open(MODEL_FILE, "wb") as file:
        pickle.dump(
            {"model": model, "features": FEATURES},
            file,
        )

    print("=== MODEL TRAINING COMPLETE ===")
    print(f"Validation MAE: {mae:.2f}")
    print(f"Validation RMSE: {rmse:.2f}")
    print("Model saved:", MODEL_FILE)


if __name__ == "__main__":
    main()
