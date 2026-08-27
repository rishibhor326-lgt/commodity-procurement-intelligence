import os
import subprocess

import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Commodity Procurement Intelligence",
    page_icon="📊",
    layout="wide"
)


st.markdown("""
<style>
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

h1 {
    font-size: 2.4rem !important;
    font-weight: 700 !important;
}

[data-testid="stMetric"] {
    background: #1e222a;
    border: 1px solid #343a46;
    padding: 18px;
    border-radius: 14px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.20);
}

[data-testid="stMetricLabel"] {
    font-weight: 600;
    color: #b7bdc8 !important;
}

[data-testid="stMetricValue"] {
    color: #ffffff !important;
}

div[data-testid="stButton"] > button {
    width: 100%;
    border-radius: 10px;
    font-weight: 600;
}

div[data-testid="stSelectbox"] {
    margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)

st.title("Commodity Procurement Intelligence")
st.caption(
    "Procurement-focused commodity price monitoring, "
    "forecasting and decision intelligence."
)

COMMODITIES = ["Onion", "Tomato", "Potato", "Rice", "Wheat"]

selected_commodity = st.selectbox(
    "Select Commodity",
    COMMODITIES,
)

historical_file = (
    f"data/historical/"
    f"maharashtra_{selected_commodity.lower()}_latest.csv"
)

if not os.path.exists(historical_file):
    env = os.environ.copy()
    env["PROCUREMENT_COMMODITY"] = selected_commodity

    with st.spinner(
        f"Fetching latest {selected_commodity} market data..."
    ):
        subprocess.run(
            ["python", "src/historical_ingestion.py"],
            check=True,
            env=env,
        )

historical_df = pd.read_csv(historical_file)

market_counts = historical_df.groupby("market").size()

MARKETS = sorted(
    market_counts[
        market_counts >= 100
    ].index.tolist()
)

selected_market = st.selectbox(
    "Select Market",
    MARKETS,
)

if st.button("Generate Forecast"):

    with st.spinner(
        f"Generating {selected_commodity} forecast..."
    ):
        env = os.environ.copy()

        env["PROCUREMENT_COMMODITY"] = selected_commodity
        env["PROCUREMENT_MARKET"] = selected_market

        subprocess.run(
            ["python", "src/historical_ingestion.py"],
            check=True,
            env=env,
        )

        subprocess.run(
            ["python", "src/run_pipeline.py"],
            check=True,
            env=env,
        )

    st.success(
        f"Forecast generated for "
        f"{selected_commodity} at {selected_market}"
    )

SUMMARY_URL = "http://127.0.0.1:8000/summary"
FORECAST_URL = "http://127.0.0.1:8000/forecast"
RECENT_URL = "http://127.0.0.1:8000/recent"

try:
    summary_data = requests.get(
        SUMMARY_URL,
        timeout=5
    ).json()

    forecast_df = pd.DataFrame(
        requests.get(
            FORECAST_URL,
            timeout=5
        ).json()
    )

    recent_df = pd.DataFrame(
        requests.get(
            RECENT_URL,
            timeout=5
        ).json()
    )

    st.caption(
        f"{summary_data['market']} — "
        f"{summary_data['commodity']}"
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Current Modal Price (₹/Quintal)",
        f"₹{summary_data['current_modal_price']:,.0f}"
    )

    col2.metric(
        "7-Day Forecast Avg (₹/Quintal)",
        f"₹{summary_data['forecast_7day_average']:,.0f}",
        f"{summary_data['expected_change_pct']:.2f}%"
    )

    st.caption(f"Approx. current price: ₹{summary_data['current_modal_price'] / 100:.2f} per kg")

    col3.metric(
        "Procurement Signal",
        summary_data["procurement_signal"]
    )

    col4.metric(
        "Attention Level",
        summary_data["attention_level"]
    )

    expected_change = summary_data["expected_change_pct"]
    signal = summary_data["procurement_signal"]

    if expected_change > 5:
        insight = (
            f"Prices are expected to rise by {expected_change:.2f}% over the next 7 days. "
            f"Procurement signal: {signal}."
        )
    elif expected_change < -5:
        insight = (
            f"Prices are expected to fall by {abs(expected_change):.2f}% over the next 7 days. "
            f"Procurement signal: {signal}."
        )
    else:
        insight = (
            f"Prices are expected to remain relatively stable, with a "
            f"{expected_change:.2f}% change over the next 7 days. "
            f"Procurement signal: {signal}."
        )

    st.info(insight)

    st.divider()

    st.subheader("Actual + 7-Day Forecast")

    actual_chart = recent_df[
        ["arrival_date", "modal_price"]
    ].copy()

    actual_chart.columns = ["date", "Actual"]

    forecast_chart = forecast_df[
        ["forecast_date", "predicted_modal_price"]
    ].copy()

    forecast_chart.columns = ["date", "Forecast"]

    actual_chart["date"] = pd.to_datetime(
        actual_chart["date"]
    )

    forecast_chart["date"] = pd.to_datetime(
        forecast_chart["date"]
    )

    chart_df = pd.merge(
        actual_chart,
        forecast_chart,
        on="date",
        how="outer"
    ).sort_values("date")

    st.line_chart(
        chart_df.set_index("date")
    )

    st.divider()

    st.subheader("Recent Market Prices")

    recent_display = recent_df.rename(columns={
        "arrival_date": "Date",
        "min_price": "Min Price",
        "max_price": "Max Price",
        "modal_price": "Modal Price",
        "arrivals_mt": "Arrivals (MT)"
    })

    st.dataframe(
        recent_display,
        width="stretch",
        hide_index=True
    )

    st.divider()

    st.subheader("Market Intelligence")

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Volatility",
        f"{summary_data['volatility_pct']:.2f}%"
    )

    c2.metric(
        "Anomaly Status",
        summary_data["anomaly_status"]
    )

    c3.metric(
        "Attention Score",
        summary_data["attention_score"]
    )

except Exception as e:
    st.error(
        f"Could not load dashboard data: {e}"
    )
