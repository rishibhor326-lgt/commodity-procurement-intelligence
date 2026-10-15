from pathlib import Path
from datetime import timedelta

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "historical"
COMMODITIES = ["Onion", "Tomato", "Potato", "Rice", "Wheat"]
REQUIRED = {"market", "arrival_date", "modal_price", "min_price", "max_price", "arrivals_mt"}

st.set_page_config(page_title="Commodity Procurement Intelligence", page_icon="📊", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.8rem; padding-bottom: 2rem; max-width: 1400px;}
[data-testid="stMetric"] {background: #1e222a; border: 1px solid #343a46; padding: 16px; border-radius: 12px;}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_history(commodity):
    candidates = [
        DATA_DIR / f"maharashtra_{commodity.lower()}_latest.csv",
        DATA_DIR / f"maharashtra_{commodity.lower()}_2026_02_to_07.csv",
    ]
    frames = []
    for path in candidates:
        if path.exists():
            try:
                frame = pd.read_csv(path)
                if REQUIRED.issubset(frame.columns) and not frame.empty:
                    frames.append(frame)
            except (OSError, pd.errors.ParserError, UnicodeDecodeError):
                continue
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    df["arrival_date"] = pd.to_datetime(df["arrival_date"], errors="coerce")
    for col in ["modal_price", "min_price", "max_price", "arrivals_mt"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["market"] = df["market"].astype(str).str.strip()
    df = df.dropna(subset=["arrival_date", "market", "modal_price"])
    df = df[(df["modal_price"] > 0) & (df["market"] != "")]
    # If both archive and latest file exist, retain one record per market/date/commodity/variety.
    keys = [col for col in ["market", "arrival_date", "commodity", "variety"] if col in df.columns]
    if keys:
        df = df.drop_duplicates(subset=keys, keep="last")
    return df.sort_values("arrival_date").reset_index(drop=True)

st.title("Commodity Procurement Intelligence")
st.caption("Explore historical mandi prices, market activity, volatility and a transparent 7-day baseline estimate.")
st.info("Data note: the dashboard uses historical CSVs committed with this project. Live AGMARKNET refresh is not guaranteed. The 7-day estimate is a simple baseline, not a trained machine-learning forecast.")

commodity = st.selectbox("Select commodity", COMMODITIES, index=1)
data = load_history(commodity)
if data.empty:
    st.error(f"No valid historical records found for {commodity}. Check the CSV in data/historical.")
    st.stop()

markets = sorted(data["market"].dropna().unique().tolist())
preferred = "Pune(Pimpri) APMC"
default_index = markets.index(preferred) if preferred in markets else 0
market = st.selectbox("Select market", markets, index=default_index)
market_df = data[data["market"] == market].copy().sort_values("arrival_date")
market_df = market_df.drop_duplicates(subset=["arrival_date"], keep="last").reset_index(drop=True)
if market_df.empty:
    st.warning("There are no valid records for this market.")
    st.stop()

latest = market_df.iloc[-1]
prices = market_df["modal_price"].dropna()
last7 = market_df.tail(7)
last14 = market_df.tail(14)
current_price = float(latest["modal_price"])
baseline = float(last7["modal_price"].mean())
change_pct = ((baseline - current_price) / current_price * 100) if current_price else 0.0
volatility_pct = (float(last14["modal_price"].std(ddof=0)) / float(last14["modal_price"].mean()) * 100) if len(last14) > 1 and last14["modal_price"].mean() else 0.0
rolling_mean = float(last14["modal_price"].mean()) if not last14.empty else current_price
anomaly = "Review price" if rolling_mean and abs(current_price - rolling_mean) > 2 * max(float(last14["modal_price"].std(ddof=0) or 0), 1) else "Within recent range"
signal = "BUY SOON" if change_pct >= 5 else ("WAIT" if change_pct <= -5 else "WATCH")
attention = "High" if abs(change_pct) >= 10 or volatility_pct >= 20 else ("Medium" if abs(change_pct) >= 5 or volatility_pct >= 10 else "Low")
attention_score = min(100, round(abs(change_pct) * 3 + volatility_pct * 1.5))

st.caption(f"{market} · Latest available record: {latest['arrival_date'].strftime('%d %b %Y')} · {len(market_df):,} valid observations")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Latest modal price", f"₹{current_price:,.0f}/quintal")
m2.metric("7-day baseline avg.", f"₹{baseline:,.0f}/quintal", f"{change_pct:+.2f}% vs latest")
m3.metric("Procurement watch", signal)
m4.metric("Attention level", attention)
st.caption(f"Approximate latest price: ₹{current_price / 100:,.2f} per kg. Signals are rule-based indicators, not purchasing advice.")

st.divider()
left, right = st.columns([1.7, 1])
with left:
    st.subheader("Historical prices and 7-day baseline")
    history_chart = market_df.tail(45)[["arrival_date", "modal_price"]].rename(columns={"arrival_date": "Date", "modal_price": "Price"})
    history_chart["Series"] = "Historical modal price"
    future_dates = pd.date_range(latest["arrival_date"] + timedelta(days=1), periods=7, freq="D")
    future_chart = pd.DataFrame({"Date": future_dates, "Price": [baseline] * 7, "Series": ["7-day baseline"] * 7})
    chart_data = pd.concat([history_chart, future_chart], ignore_index=True)
    chart = alt.Chart(chart_data).mark_line(point=True, strokeWidth=2.5).encode(
        x=alt.X("Date:T", title="Date"),
        y=alt.Y("Price:Q", title="Modal price (₹/quintal)", scale=alt.Scale(zero=False)),
        color=alt.Color("Series:N", title="Series"),
        strokeDash=alt.StrokeDash("Series:N", title="Series"),
        tooltip=[alt.Tooltip("Date:T", format="%d %b %Y"), alt.Tooltip("Series:N"), alt.Tooltip("Price:Q", format=",.0f")]
    ).properties(height=360).interactive()
    st.altair_chart(chart, use_container_width=True)
with right:
    st.subheader("Market intelligence")
    st.metric("Price volatility (14 records)", f"{volatility_pct:.1f}%")
    st.metric("Price movement vs baseline", f"{change_pct:+.2f}%")
    st.metric("Attention score", f"{attention_score}/100")
    st.write("**Anomaly screen:**", anomaly)
    st.write("**Rule-based signal:**", signal)
    st.caption("Volatility is the standard deviation divided by mean over the most recent 14 observations. The anomaly screen compares the latest price with the recent mean and standard deviation.")

st.divider()
st.subheader("Recent market observations")
recent = market_df.tail(14).sort_values("arrival_date", ascending=False).copy()
display_cols = [c for c in ["arrival_date", "min_price", "max_price", "modal_price", "arrivals_mt", "variety"] if c in recent.columns]
recent = recent[display_cols].rename(columns={
    "arrival_date": "Date", "min_price": "Min price (₹/quintal)",
    "max_price": "Max price (₹/quintal)", "modal_price": "Modal price (₹/quintal)",
    "arrivals_mt": "Arrivals (MT)", "variety": "Variety"
})
recent["Date"] = pd.to_datetime(recent["Date"]).dt.strftime("%d %b %Y")
st.dataframe(recent, use_container_width=True, hide_index=True)

st.divider()
st.subheader("Compare markets")
comparison = data.groupby("market", as_index=False).agg(
    latest_date=("arrival_date", "max"),
    latest_modal_price=("modal_price", "last"),
    avg_arrivals_mt=("arrivals_mt", "mean"),
    observations=("modal_price", "count"),
)
comparison = comparison.sort_values("latest_date", ascending=False).head(15)
comparison["latest_modal_price"] = comparison["latest_modal_price"].round(2)
comparison["avg_arrivals_mt"] = comparison["avg_arrivals_mt"].round(2)
comparison = comparison.rename(columns={
    "market": "Market", "latest_date": "Latest record",
    "latest_modal_price": "Latest modal price (₹/quintal)",
    "avg_arrivals_mt": "Average arrivals (MT)", "observations": "Records"
})
comparison["Latest record"] = pd.to_datetime(comparison["Latest record"]).dt.strftime("%d %b %Y")
st.dataframe(comparison, use_container_width=True, hide_index=True)

csv = market_df.to_csv(index=False).encode("utf-8")
st.download_button("Download selected market history (CSV)", data=csv, file_name=f"{commodity.lower()}_{market.lower().replace(' ', '_')}_history.csv", mime="text/csv")
st.caption("Built with Python, Pandas, Streamlit and Altair · Historical dataset bundled in the GitHub repository.")
