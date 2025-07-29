import streamlit as st
import yfinance as yf 
import pandas as pd
import numpy as np 
from datetime import datetime 
import requests 
import os 
from sklearn.ensemble import RandomForestClassifier 
from ta.momentum import RSIIndicator 
from ta.trend import MACD, EMAIndicator 
import matplotlib.pyplot as plt

st.set_page_config(page_title="🇮🇳 Indian Stock Portfolio Tracker", layout="wide") 
st.title(":chart_with_upwards_trend: Indian Stock Portfolio Tracker with AI Insights")

#Initialize portfolio

if "portfolio" not in st.session_state: 
    st.session_state.portfolio = []

#Telegram Alert

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

#AI Model
@st.cache_data 
def generate_features(df): 
    df = df.copy() 
    df["EMA9"] = EMAIndicator(df["Close"], window=9).ema_indicator() 
    df["EMA21"] = EMAIndicator(df["Close"], window=21).ema_indicator() 
    df["RSI"] = RSIIndicator(df["Close"]).rsi() 
    macd = MACD(df["Close"]) 
    df["MACD"] = macd.macd() 
    df["Signal"] = macd.macd_signal() 
    df.dropna(inplace=True) 
    return df

@st.cache_resource 
def train_model(df): 
    df["Target"] = np.where(df["Close"].shift(-1) > df["Close"], 1, 0) 
    features = df[["EMA9", "EMA21", "RSI", "MACD", "Signal"]] 
    target = df["Target"] 
    model = RandomForestClassifier(n_estimators=100, random_state=42) 
    model.fit(features, target) 
    return model

#Tabs

tab1, tab2 = st.tabs(["My Portfolio", "Market Movers"])

with tab1: 
    
    with st.form("add_stock_form"):
         st.subheader("Add Stock to Portfolio") 
         col1, col2 = st.columns(2) 
    
    with col1: 
        ticker_input = st.text_input("Stock Ticker (e.g., RELIANCE)").upper() 
        
    with col2: 
        quantity_input = st.number_input("Quantity", min_value=1, step=1) 
        submit = st.form_submit_button("Add")
            if submit and ticker_input and quantity_input:
             if "." not in ticker_input: 
                    ticker_input += ".NS"
                    st.session_state.portfolio.append({ 
                        "ticker": ticker_input, 
                        "quantity": quantity_input 
                    })

if st.session_state.portfolio:
    st.subheader("Portfolio Summary")
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

            # AI Signal
            history = yf.download(ticker, period="6mo", interval="1d", progress=False)
            features_df = generate_features(history)
            model = train_model(features_df)
            latest = features_df.iloc[-1][["EMA9", "EMA21", "RSI", "MACD", "Signal"]].values.reshape(1, -1)
            prediction = model.predict(latest)[0]
            signal = "🟢 Buy" if prediction == 1 else "🔴 Sell"

            # Telegram
            send_telegram_alert(f"{signal} Signal for {ticker}")

            table.append({
                "Ticker": ticker,
                "Qty": quantity,
                "Price": f"₹{latest_price:.2f}",
                "Change %": f"{change_pct:.2f}%",
                "Value": f"₹{value:,.2f}",
                "AI Signal": signal
            })

            # Plot
            st.markdown(f"#### {ticker} - AI Signal: {signal}")
            st.line_chart(history[["Close"]])

        except Exception as e:
            table.append({"Ticker": ticker, "Qty": quantity, "Error": str(e)})

    df = pd.DataFrame(table)
    st.dataframe(df)
    st.markdown(f"### Total Portfolio Value: ₹{total_value:,.2f}")

else:
    st.warning("Your portfolio is empty. Please add stocks.")

with tab2: st.subheader("Volume Shockers & Gainers Coming Soon...")

