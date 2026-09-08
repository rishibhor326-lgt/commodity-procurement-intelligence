import os
from pathlib import Path

import numpy as np
import pandas as pd
import altair as alt
import streamlit as st
from sklearn.linear_model import LinearRegression

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
COMMODITIES = ["Tomato", "Onion", "Potato", "Rice", "Wheat"]


@st.cache_data
def load_historical(commodity):
    for suffix in ["_latest", "_2026_02_to_07"]:
        path = BASE_DIR / "data" / "historical" / f"maharashtra_{commodity.lower()}{suffix}.csv"
        if path.exists():
            df = pd.read_csv(path, parse_dates=["arrival_date"])
            market_counts = df.groupby("market").size()
            valid_markets = sorted(
                market_counts[market_counts >= 100].index.tolist(),
                key=lambda x: market_counts[x],
                reverse=True,
            )
            return df, valid_markets
    return pd.DataFrame(), []


def clean_market_data(df, market):
    market_df = df[df["market"] == market].copy()

    numeric_cols = ["arrivals_mt", "min_price", "max_price", "modal_price"]
    for col in numeric_cols:
        market_df[col] = pd.to_numeric(market_df[col], errors="coerce")

    market_df = market_df.dropna(subset=["modal_price"]).sort_values("arrival_date")
    market_df = market_df.drop_duplicates(subset=["arrival_date"], keep="last")

    if len(market_df) < 20:
        return market_df

    q1 = market_df["arrivals_mt"].quantile(0.25)
    q3 = market_df["arrivals_mt"].quantile(0.75)
    iqr = q3 - q1
    extreme_arrival_limit = q3 + (10 * iqr)

    median_max_price = market_df["max_price"].median()
    extreme_price_limit = median_max_price * 5

    suspicious_mask = (
        (market_df["arrivals_mt"] > extreme_arrival_limit)
        | (market_df["max_price"] > extreme_price_limit)
    )

    return market_df[~suspicious_mask].reset_index(drop=True)


def engineer_features(df):
    df = df.copy()
    df = df.sort_values("arrival_date").reset_index(drop=True)

    df["lag_1"] = df["modal_price"].shift(1)
    df["lag_7"] = df["modal_price"].shift(7)
    df["rolling_mean_7"] = df["modal_price"].rolling(7).mean()
    df["rolling_mean_30"] = df["modal_price"].rolling(30).mean()

    df["day"] = df["arrival_date"].dt.day
    df["month"] = df["arrival_date"].dt.month
    df["quarter"] = df["arrival_date"].dt.quarter
    df["year"] = df["arrival_date"].dt.year
    df["dayofweek"] = df["arrival_date"].dt.dayofweek
    df["is_weekend"] = (df["dayofweek"] >= 5).astype(int)

    return df.dropna()


def temporal_split(df):
    split_idx = int(len(df) * 0.8)
    return df.iloc[:split_idx], df.iloc[split_idx:]


def train_and_forecast(train_df, test_df, full_df):
    feature_cols = ["lag_1", "lag_7", "rolling_mean_7", "rolling_mean_30",
                    "day", "month", "quarter", "year", "dayofweek", "is_weekend"]

    naive_pred = test_df["lag_1"].values
    naive_mae = np.mean(np.abs(test_df["modal_price"].values - naive_pred))

    ma_pred = test_df["rolling_mean_7"].values
    ma_mae = np.mean(np.abs(test_df["modal_price"].values - ma_pred))

    try:
        model = LinearRegression()
        model.fit(train_df[feature_cols], train_df["modal_price"])
        lr_pred = model.predict(test_df[feature_cols])
        lr_mae = np.mean(np.abs(test_df["modal_price"].values - lr_pred))
    except Exception:
        lr_pred = naive_pred
        lr_mae = float("inf")

    methods = {
        "Naive Baseline": naive_mae,
        "Moving Average": ma_mae,
        "Linear Regression": lr_mae,
    }
    best_method = min(methods, key=methods.get)

    last_row = full_df.iloc[-1]
    last_price = last_row["modal_price"]
    last_date = last_row["arrival_date"]

    forecast_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=7, freq="D")

    if best_method == "Linear Regression":
        forecast_prices = []
        temp_df = full_df.copy()
        for fd in forecast_dates:
            new_row = {
                "lag_1": temp_df["modal_price"].iloc[-1],
                "lag_7": temp_df["modal_price"].iloc[-7] if len(temp_df) >= 7 else last_price,
                "rolling_mean_7": temp_df["modal_price"].tail(7).mean(),
                "rolling_mean_30": temp_df["modal_price"].tail(30).mean() if len(temp_df) >= 30 else temp_df["modal_price"].mean(),
                "day": fd.day,
                "month": fd.month,
                "quarter": (fd.month - 1) // 3 + 1,
                "year": fd.year,
                "dayofweek": fd.dayofweek,
                "is_weekend": int(fd.dayofweek >= 5),
            }
            pred_df = pd.DataFrame([new_row])
            pred_price = max(0, model.predict(pred_df[feature_cols])[0])
            forecast_prices.append(pred_price)
            temp_df = pd.concat([temp_df, pd.DataFrame({"arrival_date": [fd], "modal_price": [pred_price]})], ignore_index=True)
    elif best_method == "Moving Average":
        forecast_prices = [full_df["modal_price"].tail(7).mean()] * 7
    else:
        forecast_prices = [last_price] * 7

    test_actual = test_df["modal_price"].values
    if best_method == "Linear Regression":
        test_pred = lr_pred
    elif best_method == "Moving Average":
        test_pred = ma_pred
    else:
        test_pred = naive_pred

    mae = np.mean(np.abs(test_actual - test_pred))
    rmse = np.sqrt(np.mean((test_actual - test_pred) ** 2))
    mape = np.mean(np.abs((test_actual - test_pred) / np.where(test_actual == 0, 1, test_actual))) * 100

    return {
        "best_method": best_method,
        "mae": mae,
        "rmse": rmse,
        "mape": mape,
        "forecast_dates": forecast_dates,
        "forecast_prices": forecast_prices,
        "all_methods": methods,
    }


def compute_summary(cleaned_df, forecast_result):
    recent_7 = cleaned_df.tail(7)
    current_price = cleaned_df["modal_price"].iloc[-1]

    forecast_avg = np.mean(forecast_result["forecast_prices"])
    expected_change = ((forecast_avg - current_price) / current_price) * 100 if current_price > 0 else 0

    volatility = recent_7["modal_price"].pct_change().std() * np.sqrt(7) * 100 if len(recent_7) > 1 else 0

    mean_price = cleaned_df["modal_price"].tail(30).mean()
    std_price = cleaned_df["modal_price"].tail(30).std()
    if std_price > 0:
        z_score = abs((current_price - mean_price) / std_price)
        if z_score > 3:
            anomaly_status = "ANOMALY"
        elif z_score > 2:
            anomaly_status = "WARNING"
        else:
            anomaly_status = "NORMAL"
    else:
        anomaly_status = "NORMAL"

    if expected_change > 5:
        signal = "WAIT"
    elif expected_change < -5:
        signal = "BUY"
    else:
        signal = "WATCH"

    attention_score = 0
    if volatility > 15:
        attention_score += 40
    elif volatility > 8:
        attention_score += 20
    if anomaly_status != "NORMAL":
        attention_score += 30
    if abs(expected_change) > 10:
        attention_score += 30
    elif abs(expected_change) > 5:
        attention_score += 15

    if attention_score >= 70:
        attention_level = "CRITICAL"
    elif attention_score >= 50:
        attention_level = "HIGH"
    elif attention_score >= 30:
        attention_level = "MEDIUM"
    else:
        attention_level = "LOW"

    return {
        "current_price": current_price,
        "forecast_avg": forecast_avg,
        "expected_change": expected_change,
        "volatility": volatility,
        "anomaly_status": anomaly_status,
        "signal": signal,
        "attention_score": attention_score,
        "attention_level": attention_level,
    }


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

historical_df, valid_markets = load_historical(selected_commodity)

if not valid_markets:
    st.error("No historical data found for this commodity.")
    st.stop()

selected_market = st.selectbox(
    "📍 Select Market",
    valid_markets,
)

if st.button("🔮 Generate Forecast"):

    with st.spinner(f"Generating forecast for {selected_commodity} at {selected_market}..."):

        cleaned = clean_market_data(historical_df, selected_market)

        if len(cleaned) < 20:
            st.warning("Not enough data for this market to generate a reliable forecast.")
            st.stop()

        features = engineer_features(cleaned)

        train_df, test_df = temporal_split(features)

        result = train_and_forecast(train_df, test_df, features)

        summary = compute_summary(cleaned, result)

    st.success(
        f"✅ Forecast generated for {selected_commodity} at {selected_market}"
    )

    st.markdown(f"**{selected_market} — {selected_commodity}**")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "💰 Current Modal Price (₹/Quintal)",
        f"₹{summary['current_price']:,.0f}",
    )

    col2.metric(
        "📈 7-Day Forecast Avg (₹/Quintal)",
        f"₹{summary['forecast_avg']:,.0f}",
        f"{summary['expected_change']:+.2f}%",
    )

    col3.metric(
        "🎯 Procurement Signal",
        summary["signal"],
    )

    col4.metric(
        "⚠️ Attention Level",
        summary["attention_level"],
    )

    st.caption(
        f"Approx. current price: ₹{summary['current_price'] / 100:.2f} per kg"
    )

    expected = summary["expected_change"]
    signal = summary["signal"]

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

    recent = cleaned.tail(7).copy()
    actual_chart = recent[["arrival_date", "modal_price"]].copy()
    actual_chart.columns = ["date", "Actual"]
    actual_chart["date"] = pd.to_datetime(actual_chart["date"])

    forecast_chart = pd.DataFrame({
        "date": result["forecast_dates"],
        "Forecast": result["forecast_prices"],
    })

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
        f"{summary['volatility']:.2f}%",
    )

    c2.metric(
        "🚨 Anomaly Status",
        summary["anomaly_status"],
    )

    c3.metric(
        "⚡ Attention Score",
        f"{summary['attention_score']}",
    )

    st.divider()

    st.subheader("🤖 Forecast Model Details")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Best Method", result["best_method"])
    col2.metric("MAE", f"₹{result['mae']:,.0f}")
    col3.metric("RMSE", f"₹{result['rmse']:,.0f}")
    col4.metric("MAPE", f"{result['mape']:.1f}%")

    with st.expander("📋 Model Comparison (Walk-Forward Validation)"):
        comparison = pd.DataFrame([
            {"Method": m, "Validation MAE": f"₹{v:,.2f}"}
            for m, v in result["all_methods"].items()
        ]).sort_values("Validation MAE")
        st.dataframe(comparison, use_container_width=True, hide_index=True)

    st.divider()
    st.caption("Data source: AGMARKNET | Forecasting: Walk-forward validated ML | Dashboard: Streamlit")
