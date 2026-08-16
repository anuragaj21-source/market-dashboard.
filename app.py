import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

# Page Setup
st.set_page_config(page_title="Macro & Markets Dashboard", layout="wide")
st.title("📈 Real-Time Markets & Commodities Dashboard")

TICKERS = {
    "Brent Crude Oil": "BZ=F",
    "Gold (Spot USD)": "GC=F",
    "Nifty 50 Index": "^NSEI",
    "Reliance Industries": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "USD/INR FX": "INR=X"
}

# -------------------------------------------------------------
# CACHED DATA FETCHING (Prevents Rate Limit Errors)
# -------------------------------------------------------------
@st.cache_data(ttl=300)  # Cache results for 5 minutes (300 seconds)
def fetch_ticker_data(symbols):
    """Fetch 2-day historical data for all metrics at once."""
    return yf.download(list(symbols), period="2d", group_by="ticker", threads=True)

@st.cache_data(ttl=300)
def fetch_chart_data(symbol, period, interval):
    """Fetch custom historical data for the selected chart asset."""
    return yf.download(symbol, period=period, interval=interval)

# Manual refresh button
if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()

# -------------------------------------------------------------
# 1. TOP METRICS CAROUSEL
# -------------------------------------------------------------
st.subheader("🌐 Global Macro & Market Snapshot")
cols = st.columns(len(TICKERS))

# Single batch download for all metrics
all_symbols = list(TICKERS.values())
try:
    batch_data = fetch_ticker_data(all_symbols)
    
    for idx, (name, symbol) in enumerate(TICKERS.items()):
        try:
            # Extract historical dataframe for specific symbol
            if len(all_symbols) > 1:
                df_ticker = batch_data[symbol]
            else:
                df_ticker = batch_data
                
            df_ticker = df_ticker.dropna(subset=['Close'])
            
            if len(df_ticker) >= 2:
                latest_price = float(df_ticker['Close'].iloc[-1])
                prev_price = float(df_ticker['Close'].iloc[-2])
                delta = latest_price - prev_price
                delta_pct = (delta / prev_price) * 100
                
                cols[idx].metric(
                    label=name, 
                    value=f"{latest_price:,.2f}", 
                    delta=f"{delta:+.2f} ({delta_pct:+.2f}%)"
                )
            elif len(df_ticker) == 1:
                latest_price = float(df_ticker['Close'].iloc[-1])
                cols[idx].metric(label=name, value=f"{latest_price:,.2f}", delta="N/A")
            else:
                cols[idx].metric(label=name, value="No Data")
        except Exception:
            cols[idx].metric(label=name, value="Error")

except Exception as e:
    st.error("Rate limit hit or Yahoo Finance connection failed. Tap 'Refresh Data' in sidebar to retry.")

st.markdown("---")

# -------------------------------------------------------------
# 2. CHARTS & DEEP DIVE ANALYSIS
# -------------------------------------------------------------
st.sidebar.subheader("Chart Controls")
selected_asset = st.sidebar.selectbox("Select Asset to Analyze", list(TICKERS.keys()))
time_frame = st.sidebar.selectbox("Timeframe", ["1d", "5d", "1mo", "6mo", "1y", "5y"], index=2)

interval_map = {"1d": "5m", "5d": "15m", "1mo": "1d", "6mo": "1d", "1y": "1wk", "5y": "1mo"}
selected_interval = interval_map[time_frame]
asset_symbol = TICKERS[selected_asset]

df = fetch_chart_data(asset_symbol, time_frame, selected_interval)

col_chart, col_stats = st.columns([3, 1])

with col_chart:
    st.subheader(f"{selected_asset} — Price Trend ({time_frame.upper()})")
    fig = go.Figure()
    
    if not df.empty and 'Close' in df.columns:
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name="OHLC"
        ))
    
    fig.update_layout(
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        height=500,
        margin=dict(l=20, r=20, t=20, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

with col_stats:
    st.subheader("Asset Stats")
    if not df.empty and 'High' in df.columns:
        high_val = float(df['High'].max())
        low_val = float(df['Low'].min())
        st.write(f"**Period High:** {high_val:,.2f}")
        st.write(f"**Period Low:** {low_val:,.2f}")
