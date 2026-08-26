from pathlib import Path

import pandas as pd
from fastapi import FastAPI

app = FastAPI(
    title="Commodity Procurement Intelligence API",
    version="1.0.0",
)

SUMMARY_FILE = Path("data/model/procurement_summary.csv")


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Commodity Procurement Intelligence API is running",
    }


@app.get("/summary")
def get_summary():
    df = pd.read_csv(SUMMARY_FILE)
    return df.iloc[0].to_dict()


FORECAST_FILE = Path("data/model/forecast_7day.csv")


@app.get("/forecast")
def get_forecast():
    df = pd.read_csv(FORECAST_FILE)
    return df.to_dict(orient="records")


RECENT_FILE = Path("data/model/recent_7day_summary.csv")


@app.get("/recent")
def get_recent():
    df = pd.read_csv(RECENT_FILE)
    return df.to_dict(orient="records")
