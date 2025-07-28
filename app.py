import streamlit as st
import yfinance as yf 
import pandas as pd 
import numpy as np 
import os
from datetime import datetime
import requests

# App config
st.set_page_config(page_title="🇮🇳 Indian Stock Portfolio Tracker", layout="wide") 
st.title("🐂 Bullwalk - Indian Stock Portfolio Tracker with AI Insights")

# Initialize session state
if "portfolio" not in st.session_state:
    st.session_state.portfolio = []

# Telegram Alert Function
def send_telegram_alert(message):
    telegram_token = st.secrets.get("TELEGRAM_TOKEN")
    telegram_chat_id = st.secrets.get("TELEGRAM_CHAT_ID")
    if telegram_token and telegram_chat_id:
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        payload = {"chat_id": telegram_chat_id, "text": message}
        try:
            requests.post(url, data=payload)
        except Exception as e:
            st.error(f"Telegram error: {e}")

# Download stock list CSVs if not available
if not os.path.exists("EQUITY_L.csv"):
    with open("EQUITY_L.csv", "wb") as f:
        f.write(requests.get("https://www1.nseindia.com/content/equities/EQUITY_L.csv", headers={"User-Agent":"Mozilla/5.0"}).content)

# Tabs
tab1, tab2 = st.tabs(["📊 My Portfolio", "📈 Market Movers"])

# ========== Tab 1: Portfolio ==========
with tab1:
    st.subheader("➕ Add Stock to Portfolio")

    with st.form("add_stock_form"):
        col1, col2 = st.columns(2)
        with col1:
            ticker_input = st.text_input("Stock Ticker (e.g., RELIANCE)").upper()
        with col2:
            quantity_input = st.number_input("Quantity", min_value=1, step=1)

        submitted = st.form_submit_button("Add to Portfolio")

        if submitted and ticker_input and quantity_input:
            if "." not in ticker_input:
                ticker_input += ".NS"  # Default to NSE
            st.session_state.portfolio.append({
                "ticker": ticker_input,
                "quantity": quantity_input
            })
            st.success(f"{ticker_input} added!")

    if st.session_state.portfolio:
        st.subheader("📊 Portfolio Summary")
        tickers = [item["ticker"] for item in st.session_state.portfolio]
        data = yf.download(tickers, period="7d", interval="1d", group_by="ticker", threads=True, progress=False)

        total_value = 0
        table = []

        for stock in st.session_state.portfolio:
            ticker = stock["ticker"]
            quantity = stock["quantity"]
            try:
                price_series = data[ticker]["Close"]
                latest_price = price_series.iloc[-1]
                prev_price = price_series.iloc[-2]
                change_pct = ((latest_price - prev_price) / prev_price) * 100
                value = quantity * latest_price
                total_value += value

                # AI Buy/Sell signal (based on EMA)
                ema9 = price_series.ewm(span=9, adjust=False).mean()
                signal = ""
                if latest_price > ema9.iloc[-1] and prev_price < ema9.iloc[-2]:
                    signal = "🟢 Buy Signal"
                    send_telegram_alert(f"BUY signal for {ticker}")
                elif latest_price < ema9.iloc[-1] and prev_price > ema9.iloc[-2]:
                    signal = "🔴 Sell Signal"
                    send_telegram_alert(f"SELL signal for {ticker}")

                table.append({
                    "Ticker": ticker,
                    "Qty": quantity,
                    "Price": f"₹{latest_price:.2f}",
                    "Change %": f"{change_pct:.2f}%",
                    "Value": f"₹{value:,.2f}",
                    "AI Signal": signal
                })
            except Exception as e:
                table.append({"Ticker": ticker, "Qty": quantity, "Error": str(e)})

        df = pd.DataFrame(table)
        st.dataframe(df)

        st.markdown(f"### 💼 Total Portfolio Value: ₹{total_value:,.2f}")
        st.markdown("---")

        # AI summary
        top_mover = max(table, key=lambda x: abs(float(x.get("Change %", "0%")[:-1])) if "Change %" in x else 0)
        st.info(f"Most volatile: **{top_mover['Ticker']}**, moved **{top_mover['Change %']}**")

    else:
        st.warning("Your portfolio is empty. Please add stocks using the form above.")

# ========== Tab 2: Market Movers ==========
with tab2:
    st.subheader("📈 Volume Shockers & Price Gainers (Top NSE Stocks)")

    sample_nse_200 = [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
        "ITC.NS", "SBIN.NS", "LT.NS", "AXISBANK.NS", "ASIANPAINT.NS"
    ]

    mover_data = yf.download(sample_nse_200, period="5d", interval="1d", group_by="ticker", threads=True, progress=False)

    movers = []
    for ticker in sample_nse_200:
        try:
            close = mover_data[ticker]["Close"]
            volume = mover_data[ticker]["Volume"]
            price_change = (close.iloc[-1] - close.iloc[-2]) / close.iloc[-2] * 100
            vol_change = (volume.iloc[-1] - volume.iloc[-2]) / volume.iloc[-2] * 100
            if vol_change > 100 or price_change > 5:
                movers.append({
                    "Ticker": ticker,
                    "Price % Change": f"{price_change:.2f}%",
                    "Volume % Change": f"{vol_change:.2f}%"
                })
        except:
            pass

    if movers:
        st.success("🚀 Top Movers Detected:")
        st.dataframe(pd.DataFrame(movers))
    else:
        st.info("No major movements today.")

st.markdown("---")
st.caption("Built with ❤️ using Streamlit, Yahoo Finance API, and Telegram integration.")
