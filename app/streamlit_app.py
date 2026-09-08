import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from datetime import date

import pandas as pd
import altair as alt
import requests
import streamlit as st

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

st.set_page_config(
    page_title="Commodity Procurement Intelligence",
    page_icon="📊",
    layout="wide"
)


@st.cache_resource
def start_fastapi_backend():
    """Start the existing FastAPI service for single-service Streamlit deployment."""
    try:
        requests.get("http://127.0.0.1:8000/", timeout=1).raise_for_status()
        return True
    except requests.RequestException:
        pass

    import uvicorn
    from api.main import app as fastapi_app

    server = uvicorn.Server(
        uvicorn.Config(
            fastapi_app,
            host="127.0.0.1",
            port=8000,
            log_level="warning",
        )
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    for _ in range(20):
        try:
            requests.get("http://127.0.0.1:8000/", timeout=1).raise_for_status()
            return True
        except requests.RequestException:
            time.sleep(0.25)

    raise RuntimeError("FastAPI backend did not start.")


start_fastapi_backend()


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
    REPOSITORY_ROOT
    / "data"
    / "historical"
    / f"maharashtra_{selected_commodity.lower()}_latest.csv"
)

if not os.path.exists(historical_file):
    env = os.environ.copy()
    env["PROCUREMENT_COMMODITY"] = selected_commodity

    with st.spinner(
        f"Fetching latest {selected_commodity} market data..."
    ):
        ingestion_result = subprocess.run(
            [sys.executable, str(REPOSITORY_ROOT / "src" / "historical_ingestion.py")],
            check=False,
            env=env,
            cwd=REPOSITORY_ROOT,
            capture_output=True,
            text=True,
        )

        if ingestion_result.returncode != 0:
            if historical_file.exists():
                st.warning(
                    "Live AGMARKNET refresh is temporarily unavailable. "
                    "Using the verified historical data stored with the project."
                )
            else:
                st.error("Market data could not be downloaded and no stored data is available.")
                st.stop()

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

        refreshed_today = (
            historical_file.exists()
            and date.fromtimestamp(historical_file.stat().st_mtime) == date.today()
        )

        if refreshed_today:
            ingestion_result = None
        else:
            ingestion_result = subprocess.run(
                [sys.executable, str(REPOSITORY_ROOT / "src" / "historical_ingestion.py")],
                check=False,
                env=env,
                cwd=REPOSITORY_ROOT,
                capture_output=True,
                text=True,
            )

        if ingestion_result is not None and ingestion_result.returncode != 0:
            if historical_file.exists():
                st.warning(
                    "Live AGMARKNET refresh is temporarily unavailable. "
                    "Using the verified historical data stored with the project."
                )
            else:
                st.error("Market data could not be downloaded and no stored data is available.")
                st.stop()

        subprocess.run(
            [sys.executable, str(REPOSITORY_ROOT / "src" / "run_pipeline.py")],
            check=True,
            env=env,
            cwd=REPOSITORY_ROOT,
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
        f"{summary_data['commodity']} | "
        f"Latest available market date: {summary_data['latest_date']}"
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Latest Available Price (₹/Quintal)",
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

    chart_history = pd.read_csv(historical_file, parse_dates=["arrival_date"])
    actual_chart = (
        chart_history[chart_history["market"] == summary_data["market"]]
        .sort_values("arrival_date")
        .groupby("arrival_date", as_index=False)["modal_price"]
        .mean()
        .tail(30)
    )

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

    chart_long = chart_df.melt(
        id_vars=["date"],
        value_vars=["Actual", "Forecast"],
        var_name="Price Type",
        value_name="Price"
    ).dropna()

    price_chart = (
        alt.Chart(chart_long)
        .mark_line(point=True, strokeWidth=3)
        .encode(
            x=alt.X(
                "date:T",
                title="Date",
                axis=alt.Axis(format="%d %b", labelAngle=0)
            ),
            y=alt.Y(
                "Price:Q",
                title="Price (₹/Quintal)",
                scale=alt.Scale(zero=False)
            ),
            color=alt.Color(
                "Price Type:N",
                title=None,
                scale=alt.Scale(
                    domain=["Actual", "Forecast"],
                    range=["#2563EB", "#F97316"],
                ),
            ),
            strokeDash=alt.StrokeDash(
                "Price Type:N",
                title=None,
                scale=alt.Scale(
                    domain=["Actual", "Forecast"],
                    range=[[1, 0], [7, 5]],
                ),
            ),
            tooltip=[
                alt.Tooltip(
                    "date:T",
                    title="Date",
                    format="%d %b %Y"
                ),
                alt.Tooltip(
                    "Price Type:N",
                    title="Type"
                ),
                alt.Tooltip(
                    "Price:Q",
                    title="Price",
                    format=",.0f"
                ),
            ]
        )
        .properties(
            height=440,
            title="30 Most Recent Market Observations + 7-Day Forecast",
        )
        .interactive()
    )

    st.altair_chart(
        price_chart,
        use_container_width=True
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
