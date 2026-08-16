import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Page Setup
st.set_page_config(page_title="Macro & Markets Dashboard", layout="wide")
st.title("📈 Real-Time Markets & Commodities Dashboard")

# Refresh Rate Control in Sidebar
st.sidebar.header("Dashboard Settings")
auto_refresh = st.sidebar.checkbox("Auto Refresh (30s)", value=False)
if auto_refresh:
    st.empty() # Triggers rerun loop

# Ticker Mappings (NSE stocks require '.NS', Commodities use futures tickers)
TICKERS = {
    "Brent Crude Oil": "BZ=F",
    "Gold (Spot USD)": "GC=F",
    "Nifty 50 Index": "^NSEI",
    "Reliance Industries": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "USD/INR FX": "INR=X"
}

# -------------------------------------------------------------
# 1. TOP METRICS CAROUSEL (Real-Time Snapshots)
# -------------------------------------------------------------
st.subheader("🌐 Global Macro & Market Snapshot")
cols = st.columns(len(TICKERS))

for idx, (name, symbol) in enumerate(TICKERS.items()):
    ticker_data = yf.Ticker(symbol)
    # Fetch fast 1-day history for the latest tick and change
    hist = ticker_data.history(period="2d")
    
    if len(hist) >= 2:
        latest_price = hist['Close'].iloc[-1]
        prev_price = hist['Close'].iloc[-2]
        delta = latest_price - prev_price
        delta_pct = (delta / prev_price) * 100
        
        cols[idx].metric(
            label=name, 
            value=f"{latest_price:,.2f}", 
            delta=f"{delta:+.2f} ({delta_pct:+.2f}%)"
        )

st.markdown("---")

# -------------------------------------------------------------
# 2. CHARTS & DEEP DIVE ANALYSIS
# -------------------------------------------------------------
st.sidebar.subheader("Chart Controls")
selected_asset = st.sidebar.selectbox("Select Asset to Analyze", list(TICKERS.keys()))
time_frame = st.sidebar.selectbox("Timeframe", ["1d", "5d", "1mo", "6mo", "1y", "5y"], index=2)

# Determine interval based on selected timeframe
interval_map = {"1d": "1m", "5d": "5m", "1mo": "1d", "6mo": "1d", "1y": "1wk", "5y": "1mo"}
selected_interval = interval_map[time_frame]

# Download Historical Data
asset_symbol = TICKERS[selected_asset]
df = yf.download(asset_symbol, period=time_frame, interval=selected_interval)

col_chart, col_stats = st.columns([3, 1])

with col_chart:
    st.subheader(f"{selected_asset} — Price Trend ({time_frame.upper()})")
    
    # Interactive Candlestick / Line Chart via Plotly
    fig = go.Figure()
    
    if "Open" in df.columns and len(df) > 0:
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
    if not df.empty:
        high_val = df['High'].max()
        low_val = df['Low'].min()
        vol = df['Volume'].sum() if 'Volume' in df.columns else 0
        
        st.write(f"**Period High:** {high_val:,.2f}")
        st.write(f"**Period Low:** {low_val:,.2f}")
        st.write(f"**Total Volume:** {vol:,.0f}")
