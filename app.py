import os
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Commodity Procurement Intelligence",
    page_icon="🌽",
    layout="wide",
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


@st.cache_data
def load_all_summary():
    path = BASE_DIR / "data" / "model" / "all_commodities_summary.csv"
    return pd.read_csv(path)


st.sidebar.title("🌽 Navigation")

page = st.sidebar.radio(
    "Select Dashboard",
    [
        "📊 Executive Overview",
        "📈 Forecast View",
        "🔍 Recent Market Prices",
        "⚠️ Procurement Signals",
    ],
)

COMMODITIES = ["Tomato", "Onion", "Potato", "Rice", "Wheat"]

if page == "📊 Executive Overview":

    st.title("🌽 Commodity Procurement Intelligence")
    st.caption(
        "Procurement-focused commodity price monitoring, "
        "forecasting and decision intelligence."
    )

    st.markdown("---")

    all_summary = load_all_summary()

    col1, col2, col3, col4, col5 = st.columns(5)

    for idx, row in all_summary.iterrows():
        cols = [col1, col2, col3, col4, col5]
        with cols[idx]:
            price = row["current_modal_price"]
            signal = row["procurement_signal"]
            commodity = row["commodity"]
            emoji = {"BUY": "🟢", "WAIT": "🟡", "WATCH": "🔵"}.get(signal, "⚪")
            cols[idx].metric(
                f"{commodity} {emoji}",
                f"₹{price:,.0f}",
                f"{row['expected_change_pct']:+.1f}%",
            )

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📋 All Commodities Summary")
        display_df = all_summary[
            [
                "commodity",
                "market",
                "current_modal_price",
                "forecast_7day_average",
                "expected_change_pct",
                "procurement_signal",
                "volatility_pct",
                "anomaly_status",
                "attention_level",
            ]
        ].rename(columns={
            "commodity": "Commodity",
            "market": "Market",
            "current_modal_price": "Current Price (₹)",
            "forecast_7day_average": "7-Day Forecast Avg (₹)",
            "expected_change_pct": "Expected Change (%)",
            "procurement_signal": "Signal",
            "volatility_pct": "Volatility (%)",
            "anomaly_status": "Anomaly",
            "attention_level": "Attention",
        })
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    with col2:
        st.subheader("💹 Current Price Comparison")
        import plotly.express as px
        fig = px.bar(
            all_summary,
            x="commodity",
            y="current_modal_price",
            color="procurement_signal",
            title="Current Modal Price by Commodity",
            color_discrete_map={"BUY": "#2ecc71", "WAIT": "#f1c40f", "WATCH": "#3498db"},
            text="current_modal_price",
        )
        fig.update_traces(texttemplate="₹%{y:,.0f}", textposition="outside")
        fig.update_layout(
            yaxis_title="Price (₹/Quintal)",
            xaxis_title="Commodity",
            showlegend=False,
            height=350,
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.caption("Data source: AGMARKNET | Forecasting: Walk-forward validated ML | Dashboard: Streamlit")


elif page == "📈 Forecast View":

    st.title("📈 7-Day Price Forecast")

    selected = st.selectbox("Select Commodity", COMMODITIES)

    summary = load_summary(selected)
    view = load_view(selected)
    forecast = load_forecast(selected)

    row = summary.iloc[0]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Current Modal Price",
        f"₹{row['current_modal_price']:,.0f}",
    )

    col2.metric(
        "7-Day Forecast Avg",
        f"₹{row['forecast_7day_average']:,.0f}",
        f"{row['expected_change_pct']:+.1f}%",
    )

    col3.metric(
        "Procurement Signal",
        row["procurement_signal"],
    )

    col4.metric(
        "Volatility",
        f"{row['volatility_pct']:.1f}%",
    )

    st.markdown("---")

    st.subheader(f"Actual vs Forecast — {selected} at {row['market']}")

    import plotly.express as px

    fig = px.line(
        view,
        x="date",
        y="price",
        color="type",
        title=f"{selected} — Actual vs 7-Day Forecast",
        color_discrete_map={"Actual": "#3498db", "Forecast": "#e74c3c"},
    )
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Price (₹/Quintal)",
        height=450,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("7-Day Forecast Detail")
        forecast_display = forecast.rename(columns={
            "forecast_date": "Date",
            "predicted_modal_price": "Predicted Price (₹)",
        })
        forecast_display["Predicted Price (₹)"] = forecast_display["Predicted Price (₹)"].apply(
            lambda x: f"₹{x:,.0f}"
        )
        st.dataframe(forecast_display, use_container_width=True, hide_index=True)

    with col2:
        expected = row["expected_change_pct"]
        signal = row["procurement_signal"]

        if expected > 5:
            insight = (
                f"Prices are expected to rise by **{expected:.1f}%** over the next 7 days. "
                f"Procurement signal: **{signal}.**"
            )
        elif expected < -5:
            insight = (
                f"Prices are expected to fall by **{abs(expected):.1f}%** over the next 7 days. "
                f"Procurement signal: **{signal}.**"
            )
        else:
            insight = (
                f"Prices are expected to remain relatively stable "
                f"({expected:+.1f}%). Procurement signal: **{signal}.**"
            )

        st.info(insight)


elif page == "🔍 Recent Market Prices":

    st.title("🔍 Recent Market Prices")

    selected = st.selectbox("Select Commodity", COMMODITIES)

    recent = load_recent(selected)
    summary = load_summary(selected)
    row = summary.iloc[0]

    st.caption(f"{selected} at {row['market']} — Last 7 days")

    display = recent.rename(columns={
        "arrival_date": "Date",
        "arrivals_mt": "Arrivals (MT)",
        "min_price": "Min Price (₹)",
        "max_price": "Max Price (₹)",
        "modal_price": "Modal Price (₹)",
    })

    display["Date"] = display["Date"].dt.strftime("%d %b %Y")
    for col in ["Min Price (₹)", "Max Price (₹)", "Modal Price (₹)"]:
        display[col] = display[col].apply(lambda x: f"₹{x:,.0f}")
    display["Arrivals (MT)"] = display["Arrivals (MT)"].apply(lambda x: f"{x:.1f}")

    st.dataframe(display, use_container_width=True, hide_index=True)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        import plotly.express as px
        fig = px.line(
            recent,
            x="arrival_date",
            y="modal_price",
            title="Modal Price Trend (Last 7 Days)",
            markers=True,
        )
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Modal Price (₹)",
            height=350,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.bar(
            recent,
            x="arrival_date",
            y="arrivals_mt",
            title="Arrivals Volume (MT)",
        )
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Arrivals (MT)",
            height=350,
        )
        st.plotly_chart(fig, use_container_width=True)


elif page == "⚠️ Procurement Signals":

    st.title("⚠️ Procurement Intelligence")

    all_summary = load_all_summary()

    col1, col2, col3 = st.columns(3)

    avg_risk = all_summary["attention_score"].mean()
    high_risk = all_summary[all_summary["attention_level"].isin(["HIGH", "CRITICAL"])]
    buy_signals = all_summary[all_summary["procurement_signal"] == "BUY"]

    col1.metric("Avg Attention Score", f"{avg_risk:.0f}")
    col2.metric("High-Risk Commodities", len(high_risk))
    col3.metric("Buy Signals", len(buy_signals))

    st.markdown("---")

    st.subheader("Procurement Decision Matrix")

    display = all_summary[[
        "commodity",
        "market",
        "current_modal_price",
        "forecast_7day_average",
        "expected_change_pct",
        "procurement_signal",
        "volatility_pct",
        "anomaly_status",
        "attention_score",
        "attention_level",
    ]].rename(columns={
        "commodity": "Commodity",
        "market": "Market",
        "current_modal_price": "Current (₹)",
        "forecast_7day_average": "Forecast Avg (₹)",
        "expected_change_pct": "Change (%)",
        "procurement_signal": "Signal",
        "volatility_pct": "Volatility (%)",
        "anomaly_status": "Anomaly",
        "attention_score": "Attention Score",
        "attention_level": "Attention Level",
    })

    st.dataframe(display, use_container_width=True, hide_index=True)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        import plotly.express as px
        fig = px.bar(
            all_summary,
            x="commodity",
            y="attention_score",
            color="attention_level",
            title="Attention Score by Commodity",
            color_discrete_map={"LOW": "#2ecc71", "MEDIUM": "#f1c40f", "HIGH": "#e74c3c", "CRITICAL": "#c0392b"},
        )
        fig.update_layout(height=350, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.scatter(
            all_summary,
            x="expected_change_pct",
            y="volatility_pct",
            size="attention_score",
            color="commodity",
            title="Expected Change vs Volatility",
            hover_data=["market"],
        )
        fig.update_layout(
            xaxis_title="Expected Price Change (%)",
            yaxis_title="Volatility (%)",
            height=350,
        )
        st.plotly_chart(fig, use_container_width=True)


st.markdown("---")
st.caption("Commodity Procurement Intelligence — Built with Python, Pandas, Scikit-learn, and Streamlit")
