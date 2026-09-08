## 🌽 Commodity Procurement Intelligence

### A Procurement-Focused Analytics Platform for Agricultural Market Price Monitoring, Forecasting & Decision Intelligence

**Descriptive → Diagnostic → Predictive → Prescriptive Analytics for Commodity Procurement**

**🚀 [Launch Live Dashboard](https://commodity-procurement-intelligence-48akig8fh5z6cmmcwmnlmj.streamlit.app/)**

---

## What Problem Does It Solve?

Commodity buyers need more than historical prices.

They need to know:

- What is the current market price?
- What could prices look like over the next 7 days?
- Is the market volatile?
- Is the latest price unusual?
- Should procurement teams buy soon, wait, or continue watching?

This project turns raw mandi price data into decision-oriented procurement intelligence.

## Key Features

- Real agricultural market data from AGMARKNET
- Multiple commodities and Maharashtra APMC markets
- Historical data cleaning and anomaly handling
- Time-series feature engineering
- Chronological train/validation/test splitting
- Walk-forward validation
- Automatic forecast-method selection
- 7-day price forecasting
- Procurement signals
- Volatility analysis
- Price anomaly detection
- Procurement attention scoring
- Interactive Streamlit dashboard

## Forecasting Methods

The project compares:

- Naive Baseline
- 7-Period Moving Average
- Trend Baseline
- Linear Regression

Forecast methods are compared using walk-forward validation.

The final test dataset is kept separate from model selection.

This allows the system to select the method that performs best instead of automatically choosing the most complex ML model.

## Example: Tomato — Akluj APMC

Walk-forward validation selected the **Naive Baseline** as the most reliable forecasting method.

| Method | Validation MAE | Test MAE |
| --- | --- | --- |
| **Naive Baseline** | **327.45** | **65.22** |
| Moving Average | 343.70 | 158.39 |
| Trend Baseline | 377.78 | 89.13 |
| Linear Regression | 423.49 | 327.11 |

## Procurement Intelligence Example

For Tomato — Akluj APMC:

| Metric | Result |
| --- | --- |
| Current Modal Price | ₹800 / Quintal |
| Recent 7-Day Minimum | ₹800 |
| Recent 7-Day Maximum | ₹1,000 |
| Recent 7-Day Average | ₹828.57 |
| Forecast 7-Day Average | ₹800 |
| Expected Change | 0.00% |
| Procurement Signal | **WATCH** |
| Volatility | 9.12% |
| Anomaly Status | NORMAL |
| Attention Score | 20 |
| Attention Level | **LOW** |

## Dashboard

![Commodity Procurement Intelligence Dashboard](docs/screenshots/dashboard-overview.png)

The Streamlit dashboard lets users select a commodity and market and view:

- Current modal price
- 7-day forecast
- Expected price movement
- Procurement signal
- Volatility
- Anomaly status
- Attention score
- Recent prices
- Actual vs forecast chart

### Forecast View

![7-Day Forecast](docs/screenshots/dashboard-forecast.png)

### Recent Market Prices

![Recent Market Prices](docs/screenshots/recent-market-prices.png)


## Tech Stack

| Area | Technologies |
| --- | --- |
| Programming & Data | Python, Pandas, NumPy |
| Machine Learning | Scikit-learn (Linear Regression, Random Forest) |
| Visualization | Altair, Streamlit |
| Dashboard Deployment | Streamlit Community Cloud |
| Data Source | AGMARKNET |
| Version Control | Git, GitHub |

## Project Pipeline

```text
AGMARKNET Data
      → Data Cleaning
      → Feature Engineering
      → Chronological Split
      → Walk-Forward Validation
      → Forecast Method Selection
      → Final Test Evaluation
      → 7-Day Forecast
      → Procurement Signal
      → Volatility + Anomaly Detection
      → Attention Score
      → Streamlit Dashboard
```

## Run Locally

```bash
git clone https://github.com/rishibhor326-lgt/commodity-procurement-intelligence.git
cd commodity-procurement-intelligence

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

Run the Streamlit application:

```bash
streamlit run app.py
```

The dashboard will be available at `http://localhost:8501`.

## Why This Project Is Strong

- Uses real-world agricultural market data
- Solves a business-oriented procurement problem
- Benchmarks ML against simpler baselines
- Uses walk-forward validation
- Avoids test-set leakage
- Includes forecasting, API, and dashboard layers
- Converts technical predictions into procurement decisions

## Future Improvements

- Weather integration
- More commodities and states
- Additional time-series models
- Cloud deployment
- Database storage
- Automated retraining
- Procurement alerts

## Disclaimer

This project is built for analytics, learning, and portfolio demonstration purposes. Forecasts should not be treated as guaranteed commercial or financial outcomes.

---

<div align="center">

**🚀 [Launch Live Dashboard](https://commodity-procurement-intelligence-48akig8fh5z6cmmcwmnlmj.streamlit.app/)**

Built with ❤️ by **Rishi Bhor** — [LinkedIn](https://www.linkedin.com/in/rishi-bhor-02a23b289) | [GitHub](https://github.com/rishibhor326-lgt)

</div>
