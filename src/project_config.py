import os

COMMODITY_MAP = {
    "Onion": 23,
    "Potato": 24,
    "Tomato": 65,
    "Rice": 3,
    "Wheat": 1,
}

DEFAULT_COMMODITY = "Onion"
DEFAULT_MARKET = "Pune(Pimpri) APMC"

COMMODITY = os.getenv(
    "PROCUREMENT_COMMODITY",
    DEFAULT_COMMODITY,
)

MARKET = os.getenv(
    "PROCUREMENT_MARKET",
    DEFAULT_MARKET,
)

COMMODITY_ID = COMMODITY_MAP[COMMODITY]

HISTORICAL_FILE = (
    f"data/historical/"
    f"maharashtra_{COMMODITY.lower()}_2026_02_to_07.csv"
)

FEATURE_FILE = (
    f"data/processed/"
    f"selected_market_{COMMODITY.lower()}_features.csv"
)
