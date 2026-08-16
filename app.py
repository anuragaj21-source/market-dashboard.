import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import pandas as pd

# Page Setup
st.set_page_config(page_title="Macro, Commodities & NSE/BSE Sector Dashboard", layout="wide")
st.title("🌐 Real-Time Global Macro, Commodities & NSE/BSE Market Dashboard")

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
    "Nifty 50 Index": "^NSEI",
    "BSE Sensex Index": "^BSESN"
}

# -------------------------------------------------------------
# DYNAMIC NSE & BSE SECTOR / CAP FETCHER
# -------------------------------------------------------------
@st.cache_data(ttl=86400)
def get_live_constituents():
    def load_nse_csv(url, fallback_dict):
        try:
            df = pd.read_csv(url)
            return dict(zip(df['Symbol'] + ".NS", df['Company Name']))
        except Exception:
            return fallback_dict

    # Market Cap Groups
    large_cap = load_nse_csv("https://archives.nseindia.com/content/indices/ind_nifty50list.csv", {"RELIANCE.NS": "Reliance Ind", "TCS.NS": "TCS", "HDFCBANK.NS": "HDFC Bank"})
    mid_cap = load_nse_csv("https://archives.nseindia.com/content/indices/ind_niftymidcap150list.csv", {"PERSISTENT.NS": "Persistent Systems", "POLYCAB.NS": "Polycab"})
    small_cap = load_nse_csv("https://archives.nseindia.com/content/indices/ind_niftysmallcap250list.csv", {"CDSL.NS": "CDSL", "KEI.NS": "KEI Ind"})

    # Sectoral Groups
    nifty_auto = load_nse_csv("https://archives.nseindia.com/content/indices/ind_niftyautolist.csv", {"TATAMOTORS.NS": "Tata Motors", "M&M.NS": "M&M", "MARUTI.NS": "Maruti", "BAJAJ-AUTO.NS": "Bajaj Auto"})
    nifty_bank = load_nse_csv("https://archives.nseindia.com/content/indices/ind_niftybanklist.csv", {"HDFCBANK.NS": "HDFC Bank", "ICICIBANK.NS": "ICICI Bank", "SBIN.NS": "SBI", "KOTAKBANK.NS": "Kotak Bank"})
    nifty_it = load_nse_csv("https://archives.nseindia.com/content/indices/ind_niftyitlist.csv", {"TCS.NS": "TCS", "INFY.NS": "Infosys", "HCLTECH.NS": "HCL Tech", "WIPRO.NS": "Wipro"})
    nifty_pharma = load_nse_csv("https://archives.nseindia.com/content/indices/ind_niftypharmalist.csv", {"SUNPHARMA.NS": "Sun Pharma", "CIPLA.NS": "Cipla", "DRREDDY.NS": "Dr Reddy's"})
    nifty_fmcg = load_nse_csv("https://archives.nseindia.com/content/indices/ind_niftyfmcglist.csv", {"ITC.NS": "ITC", "HINDUNILVR.NS": "Hindustan Unilever", "NESTLEIND.NS": "Nestle India"})
    nifty_metal = load_nse_csv("https://archives.nseindia.com/content/indices/ind_niftymetallist.csv", {"TATASTEEL.NS": "Tata Steel", "JSWSTEEL.NS": "JSW Steel", "HINDALCO.NS": "Hindalco"})
    nifty_energy = load_nse_csv("https://archives.nseindia.com/content/indices/ind_niftyenergylist.csv", {"RELIANCE.NS": "Reliance Ind", "NTPC.NS": "NTPC", "ONGC.NS": "ONGC"})
    nifty_realty = load_nse_csv("https://archives.nseindia.com/content/indices/ind_niftyrealtylist.csv", {"DLF.NS": "DLF", "GODREJPROP.NS": "Godrej Prop", "OBERREALTY.NS": "Oberoi Realty"})
    nifty_fin_service = load_nse_csv("https://archives.nseindia.com/content/indices/ind_niftyfinancialserviceslist.csv", {"BAJFINANCE.NS": "Bajaj Finance", "BAJAJFINSV.NS": "Bajaj Finserv"})

    return {
        "NSE Large Cap (Nifty 50)": large_cap,
        "NSE Mid Cap (Midcap 150)": mid_cap,
        "NSE Small Cap (Smallcap 250)": small_cap,
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

MARKET_GROUPS = get_live_constituents()

# -------------------------------------------------------------
# CACHED DATA HELPERS & BATCH CHUNKING
# -------------------------------------------------------------
@st.cache_data(ttl=300)
def fetch_ticker_data(symbols):
    try:
        return yf.download(tickers=list(symbols), period="5d", auto_adjust=True)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def fetch_heatmap_data(symbol_dict):
    tickers = list(symbol_dict.keys())
    records = []
    
    # Process in chunks of 30 to prevent yfinance batch timeouts and missing data
    chunk_size = 30
    for i in range(0, len(tickers), chunk_size):
        chunk_tickers = tickers[i:i + chunk_size]
        try:
            data = yf.download(tickers=chunk_tickers, period="5d", auto_adjust=True, threads=True, progress=False)
            if data.empty:
                continue

            # MultiIndex Column Handling
            if isinstance(data.columns, pd.MultiIndex):
                close_data = data['Close']
            else:
                close_data = data[['Close']]

            for sym in chunk_tickers:
                try:
                    if sym in close_data.columns:
                        s = close_data[sym].dropna()
                    else:
                        continue
                    
                    if len(s) >= 2:
                        curr_price = float(s.iloc[-1])
                        prev_price = float(s.iloc[-2])
                        if prev_price > 0:
                            pct_change = ((curr_price - prev_price) / prev_price) * 100
                            records.append({
                                "Symbol": sym,
                                "Name": symbol_dict[sym],
                                "Price": curr_price,
                                "Change (%)": pct_change,
                                "Market": "NSE/BSE",
                                "Size": 1
                            })
                except Exception:
                    continue
        except Exception:
            continue

    return pd.DataFrame(records)

@st.cache_data(ttl=300)
def fetch_individual_chart(symbol, period, interval):
    try:
        df = yf.download(tickers=symbol, period=period, interval=interval, auto_adjust=True, progress=False)
        # Column flattening for MultiIndex data frames
        if isinstance(df.columns, pd.MultiIndex):
            df = df.droplevel(level=1, axis=1) if len(df.columns.levels) > 1 else df
            df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
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
# 2. NSE / BSE SECTOR & MARKET CAP HEATMAPS
# -------------------------------------------------------------
st.subheader("🔥 NSE & BSE Sector & Market Cap Heatmaps")

selected_group_name = st.selectbox("Select Sector or Market Cap Category:", list(MARKET_GROUPS.keys()), index=0)

selected_group = MARKET_GROUPS[selected_group_name]
heatmap_df = fetch_heatmap_data(selected_group)

if not heatmap_df.empty:
    fig_heatmap = px.treemap(
        heatmap_df,
        path=['Market', 'Name'],
        values='Size',
        color='Change (%)',
        color_continuous_scale=['#E53935', '#263238', '#43A047'],
        color_continuous_midpoint=0,
        custom_data=['Symbol', 'Price', 'Change (%)']
    )
    fig_heatmap.update_traces(
        hovertemplate="<b>%{label}</b><br>Symbol: %{customdata[0]}<br>Price: ₹%{customdata[1]:,.2f}<br>Change: %{customdata[2]:+.2f}%"
    )
    fig_heatmap.update_layout(height=520, margin=dict(l=5, r=5, t=5, b=5))
    st.plotly_chart(fig_heatmap, use_container_width=True)
else:
    st.info("Loading full constituent heatmap data...")

st.markdown("---")

# -------------------------------------------------------------
# 3. INDIVIDUAL CHART DEEP-DIVE (ENHANCED VISUALS & SUBPLOTS)
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
    custom_input = st.text_input("Or enter ANY Ticker (e.g. TATAMOTORS.NS or RELIANCE.BO):", value="")
    if custom_input.strip():
        chart_symbol = custom_input.strip().upper()

with col_sel3:
    time_frame = st.selectbox("Timeframe", ["1d", "5d", "1mo", "6mo", "1y", "5y"], index=3)

interval_map = {"1d": "5m", "5d": "15m", "1mo": "1d", "6mo": "1d", "1y": "1d", "5y": "1wk"}
chart_df = fetch_individual_chart(chart_symbol, time_frame, interval_map[time_frame])

col_graph, col_stats = st.columns([3.2, 1])

with col_graph:
    if not chart_df.empty and 'Close' in chart_df.columns and len(chart_df) > 0:
        close_series = chart_df['Close'].squeeze()
        open_series = chart_df['Open'].squeeze()
        high_series = chart_df['High'].squeeze()
        low_series = chart_df['Low'].squeeze()
        volume_series = chart_df['Volume'].squeeze() if 'Volume' in chart_df.columns else None

        sma_20 = close_series.rolling(window=20).mean()
        sma_50 = close_series.rolling(window=50).mean()

        fig = make_subplots(
            rows=2, cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.04, 
            row_heights=[0.75, 0.25]
        )

        fig.add_trace(go.Candlestick(
            x=chart_df.index,
            open=open_series,
            high=high_series,
            low=low_series,
            close=close_series,
            name="OHLC",
            increasing_line_color='#26a69a', increasing_fillcolor='#26a69a',
            decreasing_line_color='#ef5350', decreasing_fillcolor='#ef5350'
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=chart_df.index,
            y=sma_20,
            mode='lines',
            name='20 SMA',
            line=dict(color='#FFA726', width=1.5)
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=chart_df.index,
            y=sma_50,
            mode='lines',
            name='50 SMA',
            line=dict(color='#29B6F6', width=1.5)
        ), row=1, col=1)

        if volume_series is not None:
            colors = ['#26a69a' if c >= o else '#ef5350' for c, o in zip(close_series, open_series)]
            fig.add_trace(go.Bar(
                x=chart_df.index,
                y=volume_series,
                name="Volume",
                marker_color=colors,
                opacity=0.6
            ), row=2, col=1)

        fig.update_layout(
            title=f"<b>{selected_asset_label} [{chart_symbol}]</b> — {time_frame.upper()}",
            template="plotly_dark",
            xaxis_rangeslider_visible=False,
            height=520,
            hovermode="x unified",
            margin=dict(l=10, r=10, t=40, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            paper_bgcolor="#0E1117",
            plot_bgcolor="#0E1117"
        )
        
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#1E222D')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#1E222D')
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error(f"No chart data available for '{chart_symbol}'. Append '.NS' for NSE or '.BO' for BSE tickers.")

with col_stats:
    st.subheader("Asset Stats")
    if not chart_df.empty and 'High' in chart_df.columns and len(chart_df) > 0:
        try:
            curr_p = float(close_series.iloc[-1])
            high_p = float(high_series.max())
            low_p = float(low_series.min())
            
            st.metric(label="Current Price", value=f"{curr_p:,.2f}")
            st.write(f"**Period High:** {high_p:,.2f}")
            st.write(f"**Period Low:** {low_p:,.2f}")
            
            if not pd.isna(sma_20.iloc[-1]):
                st.write(f"**20 SMA:** {float(sma_20.iloc[-1]):,.2f}")
            if not pd.isna(sma_50.iloc[-1]):
                st.write(f"**50 SMA:** {float(sma_50.iloc[-1]):,.2f}")
        except Exception:
            st.write("Stats unavailable")
    else:
        st.write("Data loading...")
        
