# app.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from models.lstm_model import predict_next_day_price
from models.gemini_recommender import generate_recommendation
from models.pdf_report import create_pdf_report
import os

st.set_page_config(page_title="Market Eye", layout="wide")

# Load cleaned stock data
DATA_PATH = os.path.join("data", "cleaned_stock_data.csv")
if not os.path.exists(DATA_PATH):
    st.error("❌ Data file not found. Please run the data cleaning script first.")
    st.stop()

df = pd.read_csv(DATA_PATH, parse_dates=["Date"])

# Sidebar: Login or Signup
st.sidebar.header("User Access")
action = st.sidebar.radio("Select Action", ["Login", "Sign Up"])

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

credentials_path = os.path.join("data", "credentials.csv")
if os.path.exists(credentials_path):
    credentials_df = pd.read_csv(credentials_path)
else:
    credentials_df = pd.DataFrame(columns=["Username", "Password"])
    credentials_df.to_csv(credentials_path, index=False)

if action == "Login":
    st.subheader("🔐 Login to Market Eye")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if "Username" in credentials_df.columns and "Password" in credentials_df.columns:
            match = credentials_df[
                (credentials_df["Username"] == username) & (credentials_df["Password"] == password)
            ]
            if not match.empty:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(f"Logged in as: {username}")
                st.experimental_rerun()
            else:
                st.error("Invalid credentials.")
        else:
            st.error("⚠️ Credentials file is missing required columns.")
elif action == "Sign Up":
    st.subheader("📝 Sign Up")
    new_user = st.text_input("New Username")
    new_pass = st.text_input("New Password", type="password")
    if st.button("Register"):
        if new_user and new_pass:
            if "Username" in credentials_df.columns and new_user in credentials_df["Username"].values:
                st.warning("Username already exists.")
            else:
                new_entry = pd.DataFrame([[new_user, new_pass]], columns=["Username", "Password"])
                credentials_df = pd.concat([credentials_df, new_entry], ignore_index=True)
                credentials_df.to_csv(credentials_path, index=False)
                st.success("User registered! Please log in.")
                st.experimental_rerun()
        else:
            st.warning("Please enter both username and password.")

# Logout
if st.session_state.logged_in:
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.experimental_rerun()

# Main Dashboard
if st.session_state.logged_in:
    st.title("📊 Market Eye Dashboard")

    tickers = df["Ticker"].unique()
    selected_ticker = st.selectbox("Select a stock ticker:", tickers)

    ticker_df = df[df["Ticker"] == selected_ticker].sort_values("Date", ascending=False)

    st.subheader(f"🗃️ Recent Data for {selected_ticker}")
    st.dataframe(ticker_df[["Date", "Close"]].head(10), use_container_width=True)

    st.subheader("📉 Closing Price Over Time")
    fig, ax = plt.subplots()
    ax.plot(ticker_df["Date"], ticker_df["Close"], color="blue")
    ax.set_title(f"{selected_ticker} Closing Price History")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price ($)")
    st.pyplot(fig)

    # Save chart as image for PDF
    chart_path = os.path.join("reports", f"{selected_ticker}_chart.png")
    os.makedirs("reports", exist_ok=True)
    fig.savefig(chart_path)

    st.subheader("📊 Quick Stats")
    max_close = ticker_df["Close"].max()
    min_close = ticker_df["Close"].min()
    avg_close = ticker_df["Close"].mean()
    st.markdown(f"**Max Close:** ${max_close:.2f}")
    st.markdown(f"**Min Close:** ${min_close:.2f}")
    st.markdown(f"**Average Close:** ${avg_close:.2f}")

    st.subheader("🧠 LSTM Forecast (Next Day Closing Price)")
    predicted_price = predict_next_day_price(ticker_df)
    st.success(f"✅ Predicted Next Close: ${predicted_price:.2f}")

    st.subheader("💬 Gemini Recommendation")
    recommendation = generate_recommendation(
        ticker=selected_ticker,
        max_price=max_close,
        min_price=min_close,
        average_price=avg_close,
        predicted_price=predicted_price
    )
    if "Gemini API failed" in recommendation:
        st.error(recommendation)
    else:
        st.info(recommendation)

    st.subheader("📄 Downloadable PDF Report")
    if st.button("Generate PDF Report"):
        pdf_path = create_pdf_report(
            ticker=selected_ticker,
            max_price=max_close,
            min_price=min_close,
            average_price=avg_close,
            predicted_price=predicted_price,
            recommendation=recommendation,
            chart_image_path=chart_path
        )
        if pdf_path:
            with open(pdf_path, "rb") as f:
                st.download_button("📥 Download PDF", f, file_name=os.path.basename(pdf_path))
        else:
            st.error("Failed to generate PDF.")
