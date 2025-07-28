import streamlit as st
import yfinance as yf 
import pandas as pd 
import numpy as np 
from datetime import datetime 
import requests

st.set_page_config(page_title="🇮🇳 Indian Stock Portfolio Tracker", layout="wide") 
st.title("📈 Indian Stock Portfolio Tracker with AI Insights")

#Initialize portfolio state

if "portfolio" not in st.session_state: st.session_state.portfolio = []

#Function to send Telegram alert

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

#Tabs for portfolio and market movers

tab1, tab2 = st.tabs(["📊 My Portfolio", "📈 Market Movers"])

with tab1: # Sidebar - Add a stock with st.sidebar: st.header("➕ Add Stock to Portfolio") ticker_input = st.text_input("Stock Ticker (e.g., RELIANCE for NSE, SBIN.BO for BSE)").upper() quantity_input = st.number_input("Quantity", min_value=1, step=1)

# Auto append .NS for NSE if no suffix is given
    # Input field
ticker_input = st.text_input("Enter Stock Ticker (e.g., RELIANCE, TCS, HDFCBANK)").upper()

# Only process if ticker is valid and not an index like NIFTY.BE
if ticker_input and "." not in ticker_input:
    # Do something with the ticker
    st.write(f"Looking up data for {ticker_input}")
    if ticker_input and "." not in ticker_input:
        ticker_input += ".NS"

    if st.button("Add Stock"):
        st.session_state.portfolio.append({
            "ticker": ticker_input,
            "quantity": quantity_input
        })

# Display current portfolio
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
            latest_price = data[ticker]["Close"].iloc[-1]
            change_pct = ((data[ticker]["Close"].iloc[-1] - data[ticker]["Close"].iloc[-2]) / data[ticker]["Close"].iloc[-2]) * 100
            value = quantity * latest_price
            total_value += value
            table.append({
                "Ticker": ticker,
                "Qty": quantity,
                "Price": f"₹{latest_price:.2f}",
                "Change %": f"{change_pct:.2f}%",
                "Value": f"₹{value:,.2f}"
            })
        except Exception as e:
            table.append({"Ticker": ticker, "Qty": quantity, "Error": str(e)})

    df = pd.DataFrame(table)
    st.dataframe(df)

    st.markdown(f"### 💼 Total Portfolio Value: ₹{total_value:,.2f}")

    # AI Insight (mocked example)
    st.markdown("---")
    st.subheader("🤖 AI Insights")
    top_mover = max(table, key=lambda x: abs(float(x.get("Change %", "0%")[:-1])) if "Change %" in x else 0)
    st.info(f"Your most volatile stock today is **{top_mover['Ticker']}**, moving **{top_mover['Change %']}**")

else:
    st.warning("Your portfolio is empty. Please add stocks from the sidebar.")

with tab2: st.subheader("📈 Volume Shockers & Price Gainers (Top NSE Stocks)")

# NSE 200 sample list
sample_nse_200 = ["RELIANCE.NS", "HDFCBANK.NS", "INFY.NS", "TCS.NS", "ITC.NS", "LT.NS", "SBIN.NS", "ICICIBANK.NS", "KOTAKBANK.NS", "AXISBANK.NS",
                  "WIPRO.NS", "HINDUNILVR.NS", "BAJFINANCE.NS", "BHARTIARTL.NS", "ADANIENT.NS", "ASIANPAINT.NS", "MARUTI.NS", "SUNPHARMA.NS"]

data = yf.download(sample_nse_200, period="5d", interval="1d", group_by="ticker", threads=True, progress=False)

movers = []
alert_msgs = []

for ticker in sample_nse_200:
    try:
        vol_today = data[ticker]["Volume"].iloc[-1]
        vol_avg = data[ticker]["Volume"].mean()
        close_today = data[ticker]["Close"].iloc[-1]
        close_prev = data[ticker]["Close"].iloc[-2]
        price_change = ((close_today - close_prev) / close_prev) * 100

        if vol_today > 2 * vol_avg or price_change > 2:
            movers.append({
                "Ticker": ticker,
                "Volume": vol_today,
                "Avg Volume": int(vol_avg),
                "Price": f"₹{close_today:.2f}",
                "Change %": f"{price_change:.2f}%"
            })
            alert_msgs.append(f"{ticker}: Price {price_change:.2f}%, Volume {vol_today:,}")
    except:
        continue

if movers:
    df_movers = pd.DataFrame(movers)
    st.dataframe(df_movers)

    # Send Telegram Alert
    st.success("Sending alert to Telegram...")
    alert_text = "📢 Volume/Price Alerts:\n" + "\n".join(alert_msgs)
    send_telegram_alert(alert_text)
else:
    st.info("No major volume or price shocks detected today.")

st.markdown("---") 
st.caption("Built with ❤️ using Streamlit, Yahoo Finance & Telegram")
