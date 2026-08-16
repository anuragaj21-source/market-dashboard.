import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# Page Setup
st.set_page_config(page_title="NSE Market Heatmaps & Dashboards", layout="wide")
st.title("📊 NSE India — Market Heatmaps & Deep-Dive Charts")

# Define Market Segment Groups (NSE Tickers require '.NS')
MARKET_GROUPS = {
    "NSE Large Cap (Nifty Top Holdings)": {
        "RELIANCE.NS": "Reliance Ind",
        "TCS.NS": "TCS",
        "HDFCBANK.NS": "HDFC Bank",
        "INFY.NS": "Infosys",
        "ICICIBANK.NS": "ICICI Bank",
        "BHARTIARTL.NS": "Bharti Airtel",
        "ITC.NS": "ITC",
        "LT.NS": "Larsen & Toubro",
        "HINDUNILVR.NS": "Hindustan Unilever",
        "SBIN.NS": "State Bank of India"
    },
    "NSE Mid Cap": {
        "PERSISTENT.NS": "Persistent Systems",
        "POLYCAB.NS": "Polycab",
        "COFORGE.NS": "Coforge",
        "MPHASIS.NS": "Mphasis",
        "DIXON.NS": "Dixon Tech",
        "TATACOMM.NS": "Tata Comm",
        "FEDERALBNK.NS": "Federal Bank",
        "ASTRAL.NS": "Astral"
    },
    "NSE Small Cap": {
        "CDSL.NS": "CDSL",
        "KEI.NS": "KEI Ind",
        "KAYNES.NS": "Kaynes Tech",
        "ANGELONE.NS": "Angel One",
        "BSOFT.NS": "Birlasoft",
        "CYIENT.NS": "Cyient",
        "MAPMYINDIA.NS": "MapmyIndia"
    }
}

# -------------------------------------------------------------
# DATA FETCHING HELPERS
# -------------------------------------------------------------
@st.cache_data(ttl=300)
def fetch_heatmap_data(symbol_dict):
    """Fetch 2-day historical data to compute daily percentage returns."""
    tickers = list(symbol_dict.keys())
    try:
        data = yf.download(tickers=tickers, period="2d", auto_adjust=True)
        records = []
        
        for sym, name in symbol_dict.items():
            try:
                if isinstance(data.columns, pd.MultiIndex):
                    close_series = data['Close'][sym].dropna()
                else:
                    close_series = data['Close'].dropna()
                
                if len(close_series) >= 2:
                    curr_price = float(close_series.iloc[-1])
                    prev_price = float(close_series.iloc[-2])
                    pct_change = ((curr_price - prev_price) / prev_price) * 100
                    records.append({
                        "Symbol": sym,
                        "Name": name,
                        "Price": curr_price,
                        "Change (%)": pct_change,
                        "Market": "NSE",
                        "Size": 1  # Equal tile sizing (can be mapped to market cap)
                    })
            except Exception:
                continue
        return pd.DataFrame(records)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def fetch_individual_chart(symbol, period, interval):
    """Fetch candlestick chart data for an individual stock."""
    try:
        df = yf.download(tickers=symbol, period=period, interval=interval, auto_adjust=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception:
        return pd.DataFrame()

# Manual Refresh Control
if st.sidebar.button("🔄 Refresh Market Data"):
    st.cache_data.clear()

# -------------------------------------------------------------
# 1. MARKET HEATMAP SECTION
# -------------------------------------------------------------
st.subheader("🔥 NSE Market Heatmaps by Cap Size")
selected_group_name = st.radio(
    "Select Market Category:", 
    list(MARKET_GROUPS.keys()), 
    horizontal=True
)

selected_group = MARKET_GROUPS[selected_group_name]
heatmap_df = fetch_heatmap_data(selected_group)

if not heatmap_df.empty:
    # Create Treemap Visualization using Plotly
    fig_heatmap = px.treemap(
        heatmap_df,
        path=['Market', 'Name'],
        values='Size',
        color='Change (%)',
        color_continuous_scale=['#FF3333', '#333333', '#33FF33'], # Red -> Gray -> Green
        color_continuous_midpoint=0,
        custom_data=['Symbol', 'Price', 'Change (%)']
    )
    
    fig_heatmap.update_traces(
        hovertemplate="<b>%{label}</b><br>Symbol: %{customdata[0]}<br>Price: ₹%{customdata[1]:,.2f}<br>Change: %{customdata[2]:+.2f}%"
    )
    fig_heatmap.update_layout(height=450, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_heatmap, use_container_width=True)
else:
    st.warning("Fetching market heatmap data. If off-hours, tap 'Refresh Market Data'.")

st.markdown("---")

# -------------------------------------------------------------
# 2. INDIVIDUAL STOCK CHART DEEP-DIVE
# -------------------------------------------------------------
st.subheader("📈 Individual Stock Chart Analysis")

all_symbols_flat = {}
for g in MARKET_GROUPS.values():
    all_symbols_flat.update(g)

col_sel1, col_sel2 = st.columns([2, 2])
with col_sel1:
    chart_stock_name = st.selectbox(
        "Select Stock for Deep Dive:", 
        options=list(all_symbols_flat.values())
    )
    # Reverse lookup ticker symbol
    chart_symbol = [k for k, v in all_symbols_flat.items() if v == chart_stock_name][0]

with col_sel2:
    time_frame = st.selectbox("Timeframe", ["1d", "5d", "1mo", "6mo", "1y", "5y"], index=2)

interval_map = {"1d": "5m", "5d": "15m", "1mo": "1d", "6mo": "1d", "1y": "1wk", "5y": "1mo"}
chart_df = fetch_individual_chart(chart_symbol, time_frame, interval_map[time_frame])

col_graph, col_info = st.columns([3, 1])

with col_graph:
    if not chart_df.empty and 'Close' in chart_df.columns and len(chart_df) > 0:
        fig_candle = go.Figure()
        fig_candle.add_trace(go.Candlestick(
            x=chart_df.index,
            open=chart_df['Open'],
            high=chart_df['High'],
            low=chart_df['Low'],
            close=chart_df['Close'],
            name=chart_stock_name
        ))
        fig_candle.update_layout(
            title=f"{chart_stock_name} ({chart_symbol}) — {time_frame.upper()} Candlestick Chart",
            template="plotly_dark",
            xaxis_rangeslider_visible=False,
            height=450
        )
        st.plotly_chart(fig_candle, use_container_width=True)
    else:
        st.error("Could not load chart data for this stock.")

with col_stats:
    st.subheader("Stock Summary")
    if not chart_df.empty and 'High' in chart_df.columns:
        high_p = float(chart_df['High'].max())
        low_p = float(chart_df['Low'].min())
        curr_p = float(chart_df['Close'].iloc[-1])
        st.write(f"**Current:** ₹{curr_p:,.2f}")
        st.write(f"**Period High:** ₹{high_p:,.2f}")
        st.write(f"**Period Low:** ₹{low_p:,.2f}")
