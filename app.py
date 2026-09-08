import os
from pathlib import Path

import pandas as pd
import altair as alt
import streamlit as st

st.set_page_config(
    page_title="Commodity Procurement Intelligence",
    page_icon="🌽",
    layout="wide",
)

st.markdown(
    """
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
""",
    unsafe_allow_html=True,
)

BASE_DIR = Path(__file__).resolve().parent


@st.cache_data
def load_summary(commodity):
    path = BASE_DIR / "data" / "model" / f"procurement_summary_{commodity.lower()}.csv"
    return pd.read_csv(path)


@st.cache_data
def load_forecast(commodity):
    path = BASE_DIR / "data" / "model" / f"forecast_7day_{commodity.lower()}.csv"
    return pd.read_csv(path, parse_dates=["forecast_date"])


@st.cache_data
def load_view(commodity):
    path = BASE_DIR / "data" / "model" / f"actual_forecast_view_{commodity.lower()}.csv"
    df = pd.read_csv(path, parse_dates=["date"])
    return df


@st.cache_data
def load_recent(commodity):
    path = BASE_DIR / "data" / "model" / f"recent_7day_summary_{commodity.lower()}.csv"
    return pd.read_csv(path, parse_dates=["arrival_date"])


COMMODITIES = ["Tomato", "Onion", "Potato", "Rice", "Wheat"]

st.title("🌽 Commodity Procurement Intelligence")
st.caption(
    "Procurement-focused commodity price monitoring, "
    "forecasting and decision intelligence."
)

st.markdown("---")

selected_commodity = st.selectbox(
    "🌾 Select Commodity",
    COMMODITIES,
)

summary = load_summary(selected_commodity)
market_name = summary.iloc[0]["market"].strip()
selected_market = st.selectbox(
    "📍 Select Market",
    [market_name],
)

if st.button("🔮 Generate Forecast"):

    forecast = load_forecast(selected_commodity)
    view = load_view(selected_commodity)
    recent = load_recent(selected_commodity)
    row = summary.iloc[0]

    st.success(
        f"✅ Forecast generated for {selected_commodity} at {selected_market}"
    )

    st.markdown(f"**{selected_market} — {selected_commodity}**")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "💰 Current Modal Price (₹/Quintal)",
        f"₹{row['current_modal_price']:,.0f}",
    )

    col2.metric(
        "📈 7-Day Forecast Avg (₹/Quintal)",
        f"₹{row['forecast_7day_average']:,.0f}",
        f"{row['expected_change_pct']:+.2f}%",
    )

    col3.metric(
        "🎯 Procurement Signal",
        row["procurement_signal"],
    )

    col4.metric(
        "⚠️ Attention Level",
        row["attention_level"],
    )

    st.caption(
        f"Approx. current price: ₹{row['current_modal_price'] / 100:.2f} per kg"
    )

    expected = row["expected_change_pct"]
    signal = row["procurement_signal"]

    if expected > 5:
        insight = (
            f"Prices are expected to rise by {expected:.1f}% over the next 7 days. "
            f"Procurement signal: {signal}."
        )
    elif expected < -5:
        insight = (
            f"Prices are expected to fall by {abs(expected):.1f}% over the next 7 days. "
            f"Procurement signal: {signal}."
        )
    else:
        insight = (
            f"Prices are expected to remain relatively stable, "
            f"with a {expected:+.2f}% change over the next 7 days. "
            f"Procurement signal: {signal}."
        )

    st.info(insight)

    st.divider()

    st.subheader("📊 Actual + 7-Day Forecast")

    actual_chart = recent[["arrival_date", "modal_price"]].copy()
    actual_chart.columns = ["date", "Actual"]
    actual_chart["date"] = pd.to_datetime(actual_chart["date"])

    forecast_chart = forecast.copy()
    forecast_chart.columns = ["date", "Forecast"]

    chart_df = pd.merge(
        actual_chart,
        forecast_chart,
        on="date",
        how="outer",
    ).sort_values("date")

    chart_long = chart_df.melt(
        id_vars=["date"],
        value_vars=["Actual", "Forecast"],
        var_name="Type",
        value_name="Price",
    )

    chart_long = chart_long.dropna(subset=["Price"])

    price_chart = (
        alt.Chart(chart_long)
        .mark_line(point=True, strokeWidth=3)
        .encode(
            x=alt.X(
                "date:T",
                title="Date",
                axis=alt.Axis(format="%d %b"),
            ),
            y=alt.Y(
                "Price:Q",
                title="Price (₹/Quintal)",
                scale=alt.Scale(zero=False),
            ),
            color=alt.Color(
                "Type:N",
                title=None,
            ),
            tooltip=[
                alt.Tooltip("date:T", title="Date", format="%d %b %Y"),
                alt.Tooltip("Type:N", title="Type"),
                alt.Tooltip("Price:Q", title="Price", format=",.0f"),
            ],
        )
        .properties(height=420)
        .interactive()
    )

    st.altair_chart(price_chart, use_container_width=True)

    st.divider()

    st.subheader("📋 Recent Market Prices")

    recent_display = recent.rename(
        columns={
            "arrival_date": "Date",
            "arrivals_mt": "Arrivals (MT)",
            "min_price": "Min Price",
            "max_price": "Max Price",
            "modal_price": "Modal Price",
        }
    )

    recent_display["Date"] = recent_display["Date"].dt.strftime("%Y-%m-%d")
    recent_display["Arrivals (MT)"] = recent_display["Arrivals (MT)"].apply(
        lambda x: f"{x:.1f}"
    )

    st.dataframe(
        recent_display[
            [
                "state",
                "market",
                "commodity",
                "Date",
                "variety",
                "Arrivals (MT)",
                "Min Price",
                "Max Price",
                "Modal Price",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.subheader("🔍 Market Intelligence")

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "📊 Volatility",
        f"{row['volatility_pct']:.2f}%",
    )

    c2.metric(
        "🚨 Anomaly Status",
        row["anomaly_status"],
    )

    c3.metric(
        "⚡ Attention Score",
        f"{row['attention_score']}",
    )
