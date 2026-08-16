import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# Page Setup
st.set_page_config(page_title="Macro, Commodities & NSE Sector Dashboard", layout="wide")
st.title("🌐 Real-Time Global Macro, Commodities & NSE Market Dashboard")

# -------------------------------------------------------------
# GLOBAL COMMODITIES & MACRO SNAPSHOT TICKERS
# -------------------------------------------------------------
MACRO_TICKERS = {
    "Brent Crude": "BZ=F",
    "WTI Crude": "CL=F",
    "Gold Spot (USD)": "GC=F",
    "Silver Spot (USD)": "SI=F",
    "Copper Futures": "HG=F",
    "USD/INR FX": "INR=X",
    "Nifty 50 Index": "^NSEI"
}

# -------------------------------------------------------------
# DYNAMIC NSE CAP & SECTOR LIST FETCHER (AUTO-UPDATES IPOS & REBALANCES)
# -------------------------------------------------------------
@st.cache_data(ttl=86400) # Refresh index lists once a day
def get_live_nse_constituents():
    """Fetch official equity lists dynamically from NSE Archives for Market Caps & Sectors."""
    
    # Helper to download and parse NSE CSVs
    def load_nse_csv(url, fallback_dict):
        try:
            df = pd.read_csv(url)
            return dict(zip(df['Symbol'] + ".NS", df['Company Name']))
        except Exception:
            return fallback_dict

    # Market Cap Groups
    large_cap = load_nse_csv(
        "https://archives.nseindia.com/content/indices/ind_nifty50list.csv",
        {"RELIANCE.NS": "Reliance Ind", "TCS.NS": "TCS", "HDFCBANK.NS": "HDFC Bank", "INFY.NS": "Infosys"}
    )
    mid_cap = load_nse_csv(
        "https://archives.nseindia.com/content/indices/ind_niftymidcap150list.csv",
        {"PERSISTENT.NS": "Persistent Systems", "POLYCAB.NS": "Polycab", "COFORGE.NS": "Coforge"}
    )
    small_cap = load_nse_csv(
        "https://archives.nseindia.com/content/indices/ind_niftysmallcap250list.csv",
        {"CDSL.NS": "CDSL", "KEI.NS": "KEI Ind", "ANGELONE.NS": "Angel One"}
    )

    # Sectoral Groups
    nifty_auto = load_nse_csv(
        "https://archives.nseindia.com/content/indices/ind_niftyautolist.csv",
        {"TATAMOTORS.NS": "Tata Motors", "M&M.NS": "Mahindra & Mahindra", "MARUTI.NS": "Maruti Suzuki", "BAJAJ-AUTO.NS": "Bajaj Auto"}
    )
    nifty_bank = load_nse_csv(
        "https://archives.nseindia.com/content/indices/ind_niftybanklist.csv",
        {"HDFCBANK.NS": "HDFC Bank", "ICICIBANK.NS": "ICICI Bank", "SBIN.NS": "State Bank of India", "KOTAKBANK.NS": "Kotak Bank"}
    )
    nifty_it = load_nse_csv(
        "https://archives.nseindia.com/content/indices/ind_niftyitlist.csv",
        {"TCS.NS": "TCS", "INFY.NS": "Infosys", "HCLTECH.NS": "HCL Tech", "WIPRO.NS": "Wipro", "TECHM.NS": "Tech Mahindra"}
    )
    nifty_pharma = load_nse_csv(
        "https://archives.nseindia.com/content/indices/ind_niftypharmalist.csv",
        {"SUNPHARMA.NS": "Sun Pharma", "CIPLA.NS": "Cipla", "DRREDDY.NS": "Dr Reddy's", "DIVISLAB.NS": "Divi's Lab"}
    )
    nifty_fmcg = load_nse_csv(
        "https://archives.nseindia.com/content/indices/ind_niftyfmcglist.csv",
        {"ITC.NS": "ITC", "HINDUNILVR.NS": "Hindustan Unilever", "NESTLEIND.NS": "Nestle India", "BRITANNIA.NS": "Britannia"}
    )
    nifty_metal = load_nse_csv(
        "https://archives.nseindia.com/content/indices/ind_niftymetallist.csv",
        {"TATASTEEL.NS": "Tata Steel", "JSWSTEEL.NS": "JSW Steel", "HINDALCO.NS": "Hindalco", "COALINDIA.NS": "Coal India"}
    )
    nifty_energy = load_nse_csv(
        "https://archives.nseindia.com/content/indices/ind_niftyenergylist.csv",
        {"RELIANCE.NS": "Reliance Ind", "NTPC.NS": "NTPC", "ONGC.NS": "ONGC", "POWERGRID.NS": "Power Grid"}
    )
    nifty_realty = load_nse_csv(
        "https://archives.nseindia.com/content/indices/ind_niftyrealtylist.csv",
        {"DLF.NS": "DLF", "GODREJPROP.NS": "Godrej Prop", "OBERREALTY.NS": "Oberoi Realty", "PHOENIXLTD.NS": "Phoenix Mills"}
    )
    nifty_fin_service = load_nse_csv(
        "https://archives.nseindia.com/content/indices/ind_niftyfinancialserviceslist.csv",
        {"BAJFINANCE.NS": "Bajaj Finance", "BAJAJFINSV.NS": "Bajaj Finserv", "HDFCBANK.NS": "HDFC Bank"}
    )

    return {
        # Market Cap Indices
        "NSE Large Cap (Nifty 50)": large_cap,
        "NSE Mid Cap (Midcap 150)": mid_cap,
        "NSE Small Cap (Smallcap 250)": small_cap,
        # Sectoral Indices
        "Nifty Auto": nifty_auto,
        "Nifty Bank": nifty_bank,
        "Nifty IT": nifty_it,
        "Nifty Pharma": nifty_pharma,
        "Nifty FMCG": nifty_fmcg,
        "Nifty Metal": nifty_metal,
        "Nifty Energy": nifty_energy,
        "Nifty Realty": nifty_realty,
        "Nifty Financial Services": nifty_fin_service
    }

MARKET_GROUPS = get_live_nse_constituents()

# -------------------------------------------------------------
# CACHED DATA FETCHING HELPERS
# -------------------------------------------------------------
@st.cache_data(ttl=300)
def fetch_ticker_data(symbols):
    try:
        return yf.download(tickers=list(symbols), period="2d", auto_adjust=True)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def fetch_heatmap_data(symbol_dict):
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
                        "Size": 1
                    })
            except Exception:
                continue
        return pd.DataFrame(records)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def fetch_individual_chart(symbol, period, interval):
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
# 1. TOP CAROUSEL: MACRO & COMMODITIES SNAPSHOT
# -------------------------------------------------------------
st.subheader("🛢️ Global Energy, Metals & Macro Commodities")
cols = st.columns(len(MACRO_TICKERS))

macro_data = fetch_ticker_data(list(MACRO_TICKERS.values()))

for idx, (name, symbol) in enumerate(MACRO_TICKERS.items()):
    try:
        if not macro_data.empty:
            if isinstance(macro_data.columns, pd.MultiIndex) and symbol in macro_data.columns.levels[0]:
                df_ticker = macro_data[symbol].dropna(subset=['Close'])
            else:
                df_ticker = macro_data.dropna(subset=['Close'])
                
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
        else:
            cols[idx].metric(label=name, value="No Data")
    except Exception:
        cols[idx].metric(label=name, value="Error")

st.markdown("---")

# -------------------------------------------------------------
# 2. NSE SECTOR & MARKET CAP HEATMAPS
# -------------------------------------------------------------
st.subheader("🔥 NSE Sector & Market Cap Heatmaps")

# Dropdown selection for Caps and Sectors
selected_group_name = st.selectbox(
    "Select Category or Sector:", 
    list(MARKET_GROUPS.keys()), 
    index=0
)

selected_group = MARKET_GROUPS[selected_group_name]
heatmap_df = fetch_heatmap_data(selected_group)

if not heatmap_df.empty:
    fig_heatmap = px.treemap(
        heatmap_df,
        path=['Market', 'Name'],
        values='Size',
        color='Change (%)',
        color_continuous_scale=['#FF3333', '#333333', '#33FF33'],
        color_continuous_midpoint=0,
        custom_data=['Symbol', 'Price', 'Change (%)']
    )
    fig_heatmap.update_traces(
        hovertemplate="<b>%{label}</b><br>Symbol: %{customdata[0]}<br>Price: ₹%{customdata[1]:,.2f}<br>Change: %{customdata[2]:+.2f}%"
    )
    fig_heatmap.update_layout(height=480, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_heatmap, use_container_width=True)
else:
    st.info("Fetching real-time sector heatmap data...")

st.markdown("---")

# -------------------------------------------------------------
# 3. INDIVIDUAL CHART DEEP-DIVE WITH MOVING AVERAGES (SMA 20 & SMA 50)
# -------------------------------------------------------------
st.subheader("📈 Interactive Asset Chart Deep Dive")

all_searchable_assets = {}
all_searchable_assets.update({v: k for k, v in MACRO_TICKERS.items()})
for group in MARKET_GROUPS.values():
    for sym, name in group.items():
        all_searchable_assets[f"{name} ({sym})"] = sym

col_sel1, col_sel2, col_sel3 = st.columns([2, 1, 1])

with col_sel1:
    selected_asset_label = st.selectbox("Search Stock or Commodity:", list(all_searchable_assets.keys()))
    chart_symbol = all_searchable_assets[selected_asset_label]

with col_sel2:
    custom_input = st.text_input("Or enter ANY custom Ticker (e.g. TATAMOTORS.NS):", value="")
    if custom_input.strip():
        chart_symbol = custom_input.strip().upper()

with col_sel3:
    time_frame = st.selectbox("Timeframe", ["1d", "5d", "1mo", "6mo", "1y", "5y"], index=3)

interval_map = {"1d": "5m", "5d": "15m", "1mo": "1d", "6mo": "1d", "1y": "1d", "5y": "1wk"}
chart_df = fetch_individual_chart(chart_symbol, time_frame, interval_map[time_frame])

col_graph, col_stats = st.columns([3, 1])

with col_graph:
    if not chart_df.empty and 'Close' in chart_df.columns and len(chart_df) > 0:
        # Calculate Moving Averages
        chart_df['SMA_20'] = chart_df['Close'].rolling(window=20).mean()
        chart_df['SMA_50'] = chart_df['Close'].rolling(window=50).mean()

        fig_candle = go.Figure()
        
        # 1. Candlestick Trace
        fig_candle.add_trace(go.Candlestick(
            x=chart_df.index,
            open=chart_df['Open'],
            high=chart_df['High'],
            low=chart_df['Low'],
            close=chart_df['Close'],
            name="OHLC"
        ))

        # 2. SMA 20 Overlay (Orange)
        fig_candle.add_trace(go.Scatter(
            x=chart_df.index,
            y=chart_df['SMA_20'],
            mode='lines',
            name='20-Day SMA',
            line=dict(color='#FFA500', width=1.5)
        ))

        # 3. SMA 50 Overlay (Cyan)
        fig_candle.add_trace(go.Scatter(
            x=chart_df.index,
            y=chart_df['SMA_50'],
            mode='lines',
            name='50-Day SMA',
            line=dict(color='#00FFFF', width=1.5)
        ))

        fig_candle.update_layout(
            title=f"{selected_asset_label} [{chart_symbol}] — {time_frame.upper()} Candlestick Chart",
            template="plotly_dark",
            xaxis_rangeslider_visible=False,
            height=480,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_candle, use_container_width=True)
    else:
        st.error(f"No chart data available for '{chart_symbol}'. Make sure to append '.NS' for Indian stocks.")

with col_stats:
    st.subheader("Asset Stats")
    if not chart_df.empty and 'High' in chart_df.columns and len(chart_df) > 0:
        try:
            high_p = float(chart_df['High'].max())
            low_p = float(chart_df['Low'].min())
            curr_p = float(chart_df['Close'].iloc[-1])
            st.write(f"**Current Price:** {curr_p:,.2f}")
            st.write(f"**Period High:** {high_p:,.2f}")
            st.write(f"**Period Low:** {low_p:,.2f}")
            
            if 'SMA_20' in chart_df.columns and not pd.isna(chart_df['SMA_20'].iloc[-1]):
                st.write(f"**20 SMA:** {float(chart_df['SMA_20'].iloc[-1]):,.2f}")
            if 'SMA_50' in chart_df.columns and not pd.isna(chart_df['SMA_50'].iloc[-1]):
                st.write(f"**50 SMA:** {float(chart_df['SMA_50'].iloc[-1]):,.2f}")
        except Exception:
            st.write("Stats unavailable")
    else:
        st.write("Data loading...")
