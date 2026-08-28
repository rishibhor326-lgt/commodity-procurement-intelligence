import subprocess

steps = [
    "src/historical_cleaning.py",
    "src/feature_engineering.py",
    "src/temporal_split.py",
    "src/train_model.py",
    "src/evaluate_model.py",
    "src/generate_predictions.py",
    "src/forecast_7day.py",
    "src/validate_forecast.py",
    "src/recent_price_summary.py",
    "src/combine_actual_forecast.py",
    "src/procurement_signal.py",
    "src/price_volatility.py",
    "src/anomaly_detection.py",
    "src/procurement_attention.py",
    "src/procurement_summary.py",
]

for step in steps:
    print(f"\n=== RUNNING {step} ===")
    subprocess.run(["python", step], check=True)

print("\n=== FULL PIPELINE COMPLETE ===")
