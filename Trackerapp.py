import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import numpy as np
st.set_page_config(page_title="AI Stock Portfolio Tracker", layout="wide") 
st.title("📈 AI Stock Portfolio Tracker")

#Session state to store stock portfolio

if "portfolio" not in st.session_state: st.session_state.portfolio = []

#Input form
with st.form("add_stock_form"):
    st.subheader("➕ Add a Stock")
    col1, col2 = st.columns(2)
    with col1:
        ticker = st.text_input("Stock Ticker (e.g., AAPL)").upper()
    with col2:
        quantity = st.number_input("Quantity", min_value=1, step=1)
    add = st.form_submit_button("Add to Portfolio")
if add and ticker and quantity:
    st.session_state.portfolio.append({"ticker": ticker, "quantity": quantity})

#Display portfolio if not empty
if st.session_state.portfolio:
    st.subheader("📊 Portfolio Summary")
    tickers = [item["ticker"] for item in st.session_state.portfolio]
    data = yf.download(
        tickers,
        period="7d",
        interval="1d",
        group_by="ticker",
        threads=True,
        progress=False
    )
rows = []
insights = []
total_value = 0

for item in st.session_state.portfolio:
    ticker = item["ticker"]
    qty = item["quantity"]

    try:
        info = yf.Ticker(ticker).info
        price = info.get("regularMarketPrice")
        prev_close = info.get("previousClose")
        sector = info.get("sector", "N/A")

        value = price * qty
        gain_loss = (price - prev_close) * qty
        change_pct = ((price - prev_close) / prev_close) * 100 if prev_close else 0
        total_value += value

        # Trend detection
        hist = data[ticker]["Close"] if len(tickers) > 1 else data["Close"]
        trend = np.polyfit(range(len(hist)), hist.values, 1)[0]  # slope
        trend_msg = "📈 Uptrend" if trend > 0 else "📉 Downtrend"

        # Risk scoring
        volatility = np.std(hist.pct_change().dropna())
        risk_score = "High" if volatility > 0.03 else "Medium" if volatility > 0.015 else "Low"

        # Store row
        rows.append([ticker, sector, qty, f"${price:.2f}", f"${value:.2f}", f"{change_pct:.2f}%", trend_msg, risk_score])
    except Exception as e:
        st.error(f"Error loading data for {ticker}: {e}")

df = pd.DataFrame(rows, columns=["Ticker", "Sector", "Quantity", "Price", "Value", "% Change", "Trend", "Risk"])
st.dataframe(df, use_container_width=True)
st.success(f"Total Portfolio Value: ${total_value:,.2f}")

# Diversification Check
sector_counts = df["Sector"].value_counts()
if sector_counts.max() > len(df) * 0.6:
    st.warning("⚠️ Your portfolio may be overexposed to one sector. Consider diversifying.")

else: st.info("Add stocks above to begin tracking your portfolio.")

Footer

st.markdown("---")
st.caption("Built with ❤️ using Streamlit and Yahoo Finance API")
