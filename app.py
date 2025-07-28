import os 
import requests 
import zipfile 
import io 
import streamlit as st 
import yfinance as yf 
import pandas as pd 
from datetime import datetime

st.set_page_config(page_title="🇮🇳 Bullwalk: Indian Stock Tracker", layout="wide") 
st.title("🐂 Bullwalk - NSE/BSE Stock Tracker with AI Buy/Sell Signals")

@st.cache_data(show_spinner=True) def fetch_nse_tickers(): url = "https://www1.nseindia.com/content/equities/EQUITY_L.csv" headers = {"User-Agent": "Mozilla/5.0"} response = requests.get(url, headers=headers) if response.ok: with open("EQUITY_L.csv", "wb") as f: f.write(response.content) df = pd.read_csv("EQUITY_L.csv") return df["SYMBOL"].dropna().astype(str).tolist() else: st.error("❌ Failed to fetch NSE stock list.") return []

@st.cache_data(show_spinner=True) def fetch_bse_tickers(): today = datetime.now().strftime("%d%m%y") zip_url = f"https://www.bseindia.com/download/BhavCopy/Equity/EQ{today}_CSV.ZIP" headers = {"User-Agent": "Mozilla/5.0"} response = requests.get(zip_url, headers=headers) if response.ok: z = zipfile.ZipFile(io.BytesIO(response.content)) csv_filename = [name for name in z.namelist() if name.endswith('.CSV')][0] z.extract(csv_filename) df = pd.read_csv(csv_filename) return df["SC_CODE"].dropna().astype(str).tolist() else: st.error("❌ Failed to fetch BSE Bhavcopy.") return []

Load tickers

nse_tickers = fetch_nse_tickers() bse_tickers = fetch_bse_tickers()

all_indian_tickers = [f"{symbol}.NS" for symbol in nse_tickers] + [f"{code}.BO" for code in bse_tickers]

User input

st.sidebar.header("Search a Stock") user_ticker = st.sidebar.text_input("Enter Stock Ticker (e.g., RELIANCE, 500325)").upper()

if user_ticker: full_ticker = user_ticker + (".NS" if user_ticker in nse_tickers else ".BO") data = yf.download(full_ticker, period="1mo", interval="1d", progress=False)

if not data.empty:
    st.subheader(f"📊 Analysis for {full_ticker}")
    data["9EMA"] = data["Close"].ewm(span=9, adjust=False).mean()
    data["Signal"] = ["BUY" if c > e else "SELL" for c, e in zip(data["Close"], data["9EMA"])]

    st.line_chart(data[["Close", "9EMA"]])
    st.write(data.tail())

    latest_signal = data["Signal"].iloc[-1]
    st.success(f"🔔 AI Signal: **{latest_signal}**")
else:
    st.warning("No data found for the ticker.")

st.sidebar.markdown("---") 
st.sidebar.caption("Made with ❤️ for Indian investors")
