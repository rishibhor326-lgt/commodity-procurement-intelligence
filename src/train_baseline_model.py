from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

TRAIN_FILE = Path("data/model/train.csv")
VALIDATION_FILE = Path("data/model/validation.csv")

FEATURES = [
    "modal_lag_1",
    "modal_lag_7",
    "modal_lag_14",
    "arrivals_lag_1",
    "arrivals_lag_7",
    "modal_roll_mean_7",
    "modal_roll_std_7",
    "modal_roll_mean_14",
    "modal_roll_std_14",
    "day_of_week",
    "day_of_month",
    "month",
]

TARGET = "modal_price"


def main():
    train = pd.read_csv(TRAIN_FILE)
    validation = pd.read_csv(VALIDATION_FILE)

    X_train = train[FEATURES]
    y_train = train[TARGET]

    X_validation = validation[FEATURES]
    y_validation = validation[TARGET]

    model = RandomForestRegressor(
        n_estimators=200,
        random_state=42,
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_validation)

    mae = mean_absolute_error(y_validation, predictions)
    rmse = root_mean_squared_error(y_validation, predictions)

    print("=== BASELINE MODEL COMPLETE ===")
    print("Train rows:", len(train))
    print("Validation rows:", len(validation))
    print(f"Validation MAE: {mae:.2f}")
    print(f"Validation RMSE: {rmse:.2f}")


if __name__ == "__main__":
    main()
