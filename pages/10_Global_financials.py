import streamlit as st
import pandas as pd
import yfinance as yf
from tradingview_screener import Query
from datetime import datetime, date

st.set_page_config(
    page_title="Index Max Return",
    page_icon="",
    layout="centered",
    initial_sidebar_state="auto"
)

st.markdown("""
<div style='display:flex;align-items:center;justify-content:center;margin-bottom:0.5em;'>
  <svg xmlns='http://www.w3.org/2000/svg' width='48' height='48' viewBox='0 0 48 48' fill='none' style='margin-right:16px;'>
    <rect width='48' height='48' rx='12' fill='url(#gf-bg)'/>
    <polyline points='12,32 22,22 30,28 38,14' stroke='#47d16c' stroke-width='4' fill='none' stroke-linecap='round' stroke-linejoin='round'/>
    <circle cx='12' cy='32' r='3' fill='#47d16c'/>
    <circle cx='22' cy='22' r='3' fill='#47d16c'/>
    <circle cx='30' cy='28' r='3' fill='#47d16c'/>
    <circle cx='38' cy='14' r='3' fill='#47d16c'/>
    <defs>
      <linearGradient id='gf-bg' x1='0' y1='0' x2='48' y2='48' gradientUnits='userSpaceOnUse'>
        <stop stop-color='#23272F'/>
        <stop offset='1' stop-color='#181A20'/>
      </linearGradient>
    </defs>
  </svg>
  <span style='font-size:2.5rem;font-weight:700;color:#fff;'>Global Financials</span>
</div>
<p style='text-align:center;margin-top:-0.75em;margin-bottom:2em;color:#aaa;font-size:1.1rem;'>Explore and analyze global company financials and SEC filings</p>
""", unsafe_allow_html=True)


# --- UI Toggles for All Components ---
st.sidebar.header('Dashboard Components')
show_markets = st.sidebar.toggle('Show Global Markets Dashboard', value=False)
show_returns = st.sidebar.toggle('Show Max Return Calculator', value=False)
show_financials = st.sidebar.toggle('Show Stock Financials Search', value=True)

# --- Compact Glassmorphism Global Markets Dashboard ---
if show_markets:
    st.markdown("""
        <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@500;700&display=swap" rel="stylesheet">
        <style>
        body, .stApp {
            font-family: 'Roboto', sans-serif;
            background: #18191A;
            color: #F0F2F6;
        }
        .market-dashboard-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            margin-bottom: 1.5em;
        }
        .market-cards-row {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 1.2em;
            width: 100%;
            max-width: 700px;
        }
        .market-column {
            display: flex;
            flex-direction: column;
            gap: 1.2em;
            flex: 1 1 0;
            min-width: 0;
        }
        .market-card {
            background: rgba(35, 39, 47, 0.65);
            border-radius: 18px;
            box-shadow: 0 4px 24px 0 rgba(0,0,0,0.18);
            backdrop-filter: blur(8px) saturate(120%);
            border: 1.5px solid rgba(255,255,255,0.08);
            padding: 0.7em 0.7em 0.5em 0.7em;
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            min-width: 120px;
            max-width: 160px;
            min-height: 90px;
            transition: box-shadow 0.2s, background 0.3s;
            animation: flicker 1.2s infinite alternate;
        }
        @keyframes flicker {
            0% { background: rgba(35, 39, 47, 0.65); }
            40% { background: rgba(35, 39, 47, 0.80); }
            60% { background: rgba(35, 39, 47, 0.60); }
            100% { background: rgba(35, 39, 47, 0.65); }
        }
        .market-card:hover {
            box-shadow: 0 6px 32px 0 rgba(0,0,0,0.22);
            border: 1.5px solid rgba(255,255,255,0.18);
        }
        .market-title {
            font-size: 1em;
            font-weight: 700;
            margin-bottom: 0.1em;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 120px;
        }
        .market-price {
            font-size: 1.2em;
            font-weight: 700;
            margin-bottom: 0.1em;
            letter-spacing: 0.01em;
        }
        .market-delta {
            font-size: 0.9em;
            margin-bottom: 0.1em;
        }
        .market-delta.positive { color: #4CAF50; }
        .market-delta.negative { color: #F44336; }
        .market-region-tabs {
            margin-bottom: 0.5em;
        }
        </style>
    """, unsafe_allow_html=True)

    # --- Asset Class Categories ---
    CATEGORIES = [
        "US", "Europe", "Asia", "Rates", "Commodities", "Currencies", "Cryptocurrencies"
    ]

    CATEGORY_SYMBOLS = {
        "US": {
            'S&P 500': '^GSPC',
            'Dow 30': '^DJI',
            'Nasdaq': '^IXIC',
            'Russell 2000': '^RUT',
            'VIX': '^VIX',
        },
        "Europe": {
            'FTSE 100': '^FTSE',
            'DAX': '^GDAXI',
            'CAC 40': '^FCHI',
            'Euro Stoxx 50': '^STOXX50E',
            'FTSE MIB': 'FTSEMIB.MI',
        },
        "Asia": {
            'Nikkei 225': '^N225',
            'Hang Seng': '^HSI',
            'Shanghai': '000001.SS',
            'Nifty 50': '^NSEI',
            'Sensex': '^BSESN',
        },
        "Rates": {
            'US 10Y Treasury': '^TNX',
            'US 2Y Treasury': '^IRX',
            'US 30Y Treasury': '^TYX',
            'Germany 10Y Bund': 'DE10YB=RR',
            'India 10Y Bond': 'IN10YT=RR',
            'Japan 10Y JGB': 'JP10YB=RR',
        },
        "Commodities": {
            'Gold': 'GC=F',
            'Silver': 'SI=F',
            'Crude Oil WTI': 'CL=F',
            'Crude Oil Brent': 'BZ=F',
            'Natural Gas': 'NG=F',
            'Copper': 'HG=F',
        },
        "Currencies": {
            'USD/EUR': 'EURUSD=X',
            'USD/JPY': 'JPY=X',
            'USD/GBP': 'GBPUSD=X',
            'USD/INR': 'INR=X',
            'USD/CNY': 'CNY=X',
            'USD/CHF': 'CHF=X',
        },
        "Cryptocurrencies": {
            'Bitcoin': 'BTC-USD',
            'Ethereum': 'ETH-USD',
            'Binance Coin': 'BNB-USD',
            'Solana': 'SOL-USD',
            'Ripple': 'XRP-USD',
            'Dogecoin': 'DOGE-USD',
        },
    }

    # --- Auto-refresh for live price flicker ---
    refresh_interval = 10  # seconds
    if 'last_refresh' not in st.session_state or (datetime.now() - st.session_state.get('last_refresh', datetime.min)).total_seconds() > refresh_interval:
        st.session_state['last_refresh'] = datetime.now()
        st.rerun()

    tab_objs = st.tabs(CATEGORIES)
    for i, cat in enumerate(CATEGORIES):
        with tab_objs[i]:
            symbols = CATEGORY_SYMBOLS[cat]
            data = yf.download(list(symbols.values()), period='2d', interval='1d', group_by='ticker', progress=False)
            st.markdown('<div class="market-dashboard-container">', unsafe_allow_html=True)
            st.markdown('<div class="market-cards-row">', unsafe_allow_html=True)
            # Split the items into two columns (left/right)
            items = list(symbols.items())
            mid = (len(items) + 1) // 2
            left_items = items[:mid]
            right_items = items[mid:]
            st.markdown('<div class="market-column">', unsafe_allow_html=True)
            for name, symbol in left_items:
                try:
                    last = data[symbol]['Close'].dropna().iloc[-1]
                    prev = data[symbol]['Close'].dropna().iloc[-2]
                    change = last - prev
                    pct = (change / prev) * 100 if prev != 0 else 0
                    delta_class = "positive" if change >= 0 else "negative"
                    st.markdown(
                        f'''
                        <div class="market-card">
                            <div class="market-title">{name}</div>
                            <div class="market-price">{last:,.2f}</div>
                            <div class="market-delta {delta_class}">
                                {change:+.2f} ({pct:+.2f}%)
                            </div>
                        </div>
                        ''', unsafe_allow_html=True
                    )
                except Exception:
                    st.markdown(
                        f'''
                        <div class="market-card">
                            <div class="market-title">{name}</div>
                            <div class="market-price">N/A</div>
                            <div class="market-delta">N/A</div>
                        </div>
                        ''', unsafe_allow_html=True
                    )
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('<div class="market-column">', unsafe_allow_html=True)
            for name, symbol in right_items:
                try:
                    last = data[symbol]['Close'].dropna().iloc[-1]
                    prev = data[symbol]['Close'].dropna().iloc[-2]
                    change = last - prev
                    pct = (change / prev) * 100 if prev != 0 else 0
                    delta_class = "positive" if change >= 0 else "negative"
                    st.markdown(
                        f'''
                        <div class="market-card">
                            <div class="market-title">{name}</div>
                            <div class="market-price">{last:,.2f}</div>
                            <div class="market-delta {delta_class}">
                                {change:+.2f} ({pct:+.2f}%)
                            </div>
                        </div>
                        ''', unsafe_allow_html=True
                    )
                except Exception:
                    st.markdown(
                        f'''
                        <div class="market-card">
                            <div class="market-title">{name}</div>
                            <div class="market-price">N/A</div>
                            <div class="market-delta">N/A</div>
                        </div>
                        ''', unsafe_allow_html=True
                    )
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div></div>', unsafe_allow_html=True)

    # --- Global Market Live Feed Toggle (top right, independent) ---
    col1, col2 = st.columns([1, 5])
    with col2:
        global_feed = st.toggle("Show Global Market Live Feed", key="global_feed_toggle")
    if global_feed:
        indices = {
            'S&P 500': '^GSPC',
            'Dow Jones': '^DJI',
            'Nasdaq': '^IXIC',
            'FTSE 100': '^FTSE',
            'DAX': '^GDAXI',
            'CAC 40': '^FCHI',
            'Nikkei 225': '^N225',
            'Hang Seng': '^HSI',
            'Nifty 50': '^NSEI',
            'Sensex': '^BSESN',
        }
        data = yf.download(list(indices.values()), period='1d', interval='1m', group_by='ticker', progress=False)
        for name, symbol in indices.items():
            try:
                last = data[symbol]['Close'].dropna().iloc[-1]
                st.write(f"{name} ({symbol}): {last}")
            except Exception:
                st.write(f"{name} ({symbol}): Data not available")

# --- Max Return Calculator ---
if show_returns:
    st.title("Index Maximum Potential Return by Year")
    st.markdown("""
    This tool calculates the **maximum potential return (%)** for selected indices for each year, based on historical price data.

    - **Maximum Potential Return (%)** = (Max Price - Min Price) / Min Price × 100
    - Data is fetched via TradingView API (subject to available index data).
    """)

    # Example indices with Yahoo Finance-compatible symbols for Indian indices
    INDICES = [
        ("Nifty 50", "^NSEI"),
    ]

    index_names = [name for name, _ in INDICES]
    selected_indices = st.multiselect("Select Indices", index_names, default=index_names)

    start_year = st.number_input("Start Year", min_value=2000, max_value=datetime.now().year-1, value=2020)
    end_year = st.number_input("End Year", min_value=start_year, max_value=datetime.now().year, value=datetime.now().year)
    years = list(range(start_year, end_year+1))

    # --- yfinance-based fetching strictly per official documentation ---
    def fetch_yfinance_data(symbol, start, end):
        import yfinance as yf
        # As per docs: use yf.download for historical market data
        return yf.download(symbol, start=start, end=end, progress=False)

    if st.button("Calculate Maximum Potential Returns"):
        results = []
        for idx_name, idx_symbol in INDICES:
            if idx_name not in selected_indices:
                continue
            row = {"Index": idx_name}
            for year in years:
                if idx_symbol == '^NSEI':
                    # Fetch using yfinance strictly per docs
                    start_date = f"{year}-01-01"
                    # If year is current year, set end_date as today; else, Dec 31
                    if year == datetime.now().year:
                        end_date = datetime.now().strftime("%Y-%m-%d")
                    else:
                        end_date = f"{year}-12-31"
                    nsei_df = fetch_yfinance_data(idx_symbol, start=start_date, end=end_date)
                    if nsei_df.empty:
                        row[f"{year}"] = 'NA'
                        row[f"{year} Close Return"] = 'NA'
                        continue
                    # Max potential return (intrayear)
                    min_price = nsei_df['Low'].min()
                    max_price = nsei_df['High'].max()
                    if hasattr(min_price, 'item') and not isinstance(min_price, float):
                        min_price = min_price.item()
                    if hasattr(max_price, 'item') and not isinstance(max_price, float):
                        max_price = max_price.item()
                    if pd.isna(min_price) or pd.isna(max_price) or min_price == 0.0:
                        row[f"{year}"] = 'NA'
                    else:
                        max_return = (max_price - min_price) / min_price * 100
                        row[f"{year}"] = f"{round(max_return, 1)}%"
                    # Jan 1 to Dec 31 (or today if current year) close-to-close return
                    jan1 = nsei_df.iloc[0]['Close'] if not nsei_df.empty else None
                    dec31 = nsei_df.iloc[-1]['Close'] if not nsei_df.empty else None
                    # Defensive: ensure jan1 and dec31 are scalars
                    if hasattr(jan1, 'item') and not isinstance(jan1, float):
                        jan1 = jan1.item()
                    if hasattr(dec31, 'item') and not isinstance(dec31, float):
                        dec31 = dec31.item()
                    if jan1 is None or dec31 is None or pd.isna(jan1) or pd.isna(dec31) or float(jan1) == 0.0:
                        row[f"{year} Close Return"] = 'NA'
                    else:
                        close_return = (dec31 - jan1) / jan1 * 100
                        if year == datetime.now().year:
                            row[f"{year} Close Return"] = f"{round(close_return, 1)}% (YTD)"
                        else:
                            row[f"{year} Close Return"] = f"{round(close_return, 1)}%"
                else:
                    # Fallback to TradingView or other logic for non-NSEI indices
                    try:
                        q = Query().select('close').where('ticker', idx_symbol)
                        q.query['range'] = {'from': f'{year}-01-01', 'to': f'{year}-12-31'}
                        count, df = q.get_scanner_data()
                        if df.empty or 'close' not in df.columns:
                            row[f"{year}"] = 'NA'
                            row[f"{year} Close Return"] = 'NA'
                            continue
                        min_price = df['close'].min()
                        max_price = df['close'].max()
                        # Defensive check for scalar values as per pandas/yfinance API docs
                        if hasattr(min_price, 'item') and not isinstance(min_price, float):
                            min_price = min_price.item()
                        if hasattr(max_price, 'item') and not isinstance(max_price, float):
                            max_price = max_price.item()
                        if pd.isna(min_price) or pd.isna(max_price) or min_price == 0.0:
                            row[f"{year}"] = 'NA'
                        else:
                            max_return = (max_price - min_price) / min_price * 100
                            row[f"{year}"] = f"{round(max_return, 1)}%"
                        # Jan 1 to Dec 31 close-to-close return
                        jan1 = df.iloc[0]['close'] if not df.empty else None
                        dec31 = df.iloc[-1]['close'] if not df.empty else None
                        if jan1 is None or dec31 is None or jan1 == 0.0:
                            row[f"{year} Close Return"] = 'NA'
                        else:
                            close_return = (dec31 - jan1) / jan1 * 100
                            row[f"{year} Close Return"] = f"{round(close_return, 1)}%"
                    except Exception as e:
                        row[f"{year}"] = 'NA'
                        row[f"{year} Close Return"] = 'NA'
            results.append(row)

        result_df = pd.DataFrame(results)
        st.dataframe(result_df, use_container_width=True)
        st.caption("*NA = Data not available for the selected index/year.")
    else:
        st.info("Select indices and years, then click 'Calculate Maximum Potential Returns'.")

# --- Financials Toggle and Stock Search ---
if show_financials:
    with st.expander("🔎 Show Stock Financials (Global)", expanded=True):
        stock_query = st.text_input("Enter a stock symbol (any market supported by Yahoo Finance):", "AAPL")
        # Statement selection
        available_statements = [
            "get_income_stmt", "income_stmt", "quarterly_income_stmt", "ttm_income_stmt",
            "get_balance_sheet", "balance_sheet",
            "get_cashflow", "cashflow", "quarterly_cashflow", "ttm_cashflow",
            "get_earnings", "earnings"
        ]
        statement_labels = {
            "get_income_stmt": "Income Statement (Function)",
            "income_stmt": "Income Statement (Annual)",
            "quarterly_income_stmt": "Income Statement (Quarterly)",
            "ttm_income_stmt": "Income Statement (TTM)",
            "get_balance_sheet": "Balance Sheet (Function)",
            "balance_sheet": "Balance Sheet (Annual)",
            "get_cashflow": "Cashflow (Function)",
            "cashflow": "Cashflow (Annual)",
            "quarterly_cashflow": "Cashflow (Quarterly)",
            "ttm_cashflow": "Cashflow (TTM)",
            "get_earnings": "Earnings (Function)",
            "earnings": "Earnings (Annual)"
        }
        selected_statement = st.selectbox("Select Financial Statement to Show", [statement_labels[k] for k in available_statements])
        if st.button("Show Financials"):
            try:
                ticker = yf.Ticker(stock_query)
                st.subheader(f"Financials for {stock_query.upper()}")
                key = [k for k, v in statement_labels.items() if v == selected_statement][0]

                def convert_to_billions(df):
                    import pandas as pd
                    def to_billion(x):
                        try:
                            if pd.notnull(x) and abs(float(x)) >= 1e9:
                                return f"{int(round(float(x)/1e9))} billion"
                        except Exception:
                            pass
                        return x
                    if isinstance(df, pd.DataFrame):
                        df_b = df.copy()
                        # Apply to numeric columns
                        for col in df_b.columns:
                            if pd.api.types.is_numeric_dtype(df_b[col]):
                                df_b[col] = df_b[col].apply(to_billion)
                        # If index is numeric, apply to index too
                        if pd.api.types.is_numeric_dtype(df_b.index):
                            df_b.index = [to_billion(x) for x in df_b.index]
                        # If all columns are not numeric, try to apply to all cells (for transposed dfs)
                        if not any(pd.api.types.is_numeric_dtype(df_b[col]) for col in df_b.columns):
                            df_b = df_b.applymap(to_billion)
                        return df_b
                    elif isinstance(df, pd.Series):
                        return df.apply(to_billion)
                    return df

                if key == "get_income_stmt":
                    st.markdown("**get_income_stmt ([proxy, as_dict, pretty, freq])**")
                    df = ticker.get_income_stmt()
                    st.dataframe(convert_to_billions(df), use_container_width=True)
                elif key == "income_stmt":
                    st.markdown("**income_stmt**")
                    df = ticker.income_stmt
                    st.dataframe(convert_to_billions(df), use_container_width=True)
                elif key == "quarterly_income_stmt":
                    st.markdown("**quarterly_income_stmt**")
                    df = ticker.quarterly_income_stmt
                    st.dataframe(convert_to_billions(df), use_container_width=True)
                elif key == "ttm_income_stmt":
                    st.markdown("**ttm_income_stmt**")
                    df = ticker.ttm_income_stmt
                    st.dataframe(convert_to_billions(df), use_container_width=True)
                elif key == "get_balance_sheet":
                    st.markdown("**get_balance_sheet ([proxy, as_dict, pretty, freq])**")
                    df = ticker.get_balance_sheet()
                    st.dataframe(convert_to_billions(df), use_container_width=True)
                elif key == "balance_sheet":
                    st.markdown("**balance_sheet**")
                    df = ticker.balance_sheet
                    st.dataframe(convert_to_billions(df), use_container_width=True)
                elif key == "get_cashflow":
                    st.markdown("**get_cashflow ([proxy, as_dict, pretty, freq])**")
                    df = ticker.get_cashflow()
                    st.dataframe(convert_to_billions(df), use_container_width=True)
                elif key == "cashflow":
                    st.markdown("**cashflow**")
                    df = ticker.cashflow
                    st.dataframe(convert_to_billions(df), use_container_width=True)
                elif key == "quarterly_cashflow":
                    st.markdown("**quarterly_cashflow**")
                    df = ticker.quarterly_cashflow
                    st.dataframe(convert_to_billions(df), use_container_width=True)
                elif key == "ttm_cashflow":
                    st.markdown("**ttm_cashflow**")
                    df = ticker.ttm_cashflow
                    st.dataframe(convert_to_billions(df), use_container_width=True)
                elif key == "get_earnings":
                    st.markdown("**get_earnings ([proxy, as_dict, freq])**")
                    df = ticker.get_earnings()
                    st.dataframe(convert_to_billions(df), use_container_width=True)
                elif key == "earnings":
                    st.markdown("**earnings**")
                    df = ticker.earnings
                    st.dataframe(convert_to_billions(df), use_container_width=True)

                # --- Show SEC Filings if available ---
                st.markdown('**SEC Filings:**')
                try:
                    filings = None
                    if hasattr(ticker, 'get_sec_filings'):
                        filings = ticker.get_sec_filings()
                    elif hasattr(ticker, 'sec_filings'):
                        filings = ticker.sec_filings
                    import json
                    import pandas as pd
                    # If filings is a list of dicts, display as table
                    if filings and isinstance(filings, list) and all(isinstance(x, dict) for x in filings):
                        if len(filings) > 0:
                            filings_df = pd.DataFrame(filings)
                            cols = [c for c in ['date', 'type', 'title', 'edgarUrl'] if c in filings_df.columns]
                            if cols:
                                filings_df = filings_df[cols]
                            if 'edgarUrl' in filings_df.columns:
                                filings_df['edgarUrl'] = filings_df['edgarUrl'].apply(lambda x: f'<a href="{x}" target="_blank">{x}</a>' if pd.notnull(x) else x)
                                custom_table_style = '''
                                <style>
                                .sec-filings-table-wrapper {
                                    margin: 2em 0 2.5em 0;
                                }
                                .sec-filings-table {
                                    border-collapse: separate;
                                    border-spacing: 0;
                                    width: 100%;
                                    font-size: 1.08rem;
                                    font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
                                    background: #181b22;
                                    border-radius: 14px;
                                    overflow: hidden;
                                    box-shadow: 0 2px 14px 0 rgba(0,0,0,0.18);
                                }
                                .sec-filings-table th {
                                    background: linear-gradient(90deg, #23272f 60%, #1e2230 100%);
                                    font-weight: 600;
                                    white-space: nowrap;
                                    min-width: 80px;
                                    padding: 14px 16px 14px 14px;
                                    color: #f2f2f2;
                                    border: none;
                                    font-size: 1.06rem;
                                }
                                .sec-filings-table td {
                                    border: none;
                                    padding: 13px 16px 13px 14px;
                                    text-align: left;
                                    vertical-align: top;
                                    background: #191c22;
                                    color: #e0e0e0;
                                    max-width: 440px;
                                    overflow: hidden;
                                    text-overflow: ellipsis;
                                    white-space: nowrap;
                                    position: relative;
                                }
                                .sec-filings-table td:hover {
                                    white-space: normal;
                                    overflow: visible;
                                    z-index: 2;
                                    background: #23272f;
                                }
                                .sec-filings-table td[title] {
                                    cursor: help;
                                }
                                .sec-filings-table td:nth-child(1), .sec-filings-table th:nth-child(1) {
                                    min-width: 100px;
                                }
                                .sec-filings-table td:nth-child(2), .sec-filings-table th:nth-child(2) {
                                    min-width: 60px;
                                }
                                .sec-filings-table td a {
                                    color: #4ea1ff;
                                    text-decoration: underline;
                                    word-break: break-all;
                                }
                                .sec-filings-table tr:nth-child(even) {background: #21242d;}
                                .sec-filings-table tr:hover td {
                                    background: #29304a !important;
                                    transition: background 0.2s;
                                }
                                @media (max-width: 900px) {
                                    .sec-filings-table th, .sec-filings-table td {
                                        font-size: 0.97rem;
                                        padding: 9px 7px;
                                    }
                                    .sec-filings-table td {
                                        max-width: 180px;
                                    }
                                }
                                </style>
                                '''
                                st.markdown(custom_table_style, unsafe_allow_html=True)
                                st.markdown('<div class="sec-filings-table-wrapper">' + filings_df.to_html(classes='sec-filings-table', escape=False, index=False) + '</div>', unsafe_allow_html=True)
                            else:
                                st.dataframe(filings_df)
                        else:
                            st.info('No SEC filings found for this ticker (empty list).')
                    else:
                        st.info('No SEC filings found or not in expected format.')
                        st.write(f"Type: {type(filings)}")
                        st.code(repr(filings))
                        st.code(json.dumps(filings, indent=2, default=str))
                except Exception as e:
                    st.info(f'Could not fetch SEC filings: {e}')


            except Exception as e:
                st.error(f"Could not fetch financials for {stock_query}: {e}")
