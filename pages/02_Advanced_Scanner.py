import streamlit as st
from tradingview_screener import Query, col
import pandas as pd

# Add clipboard component
def create_copy_button(text, button_text):
    st.markdown("""
        <script>
        function copyToClipboard(text) {
            navigator.clipboard.writeText(text);
        }
        </script>
        <button onclick="copyToClipboard('{}');">{}</button>
    """.format(text, button_text), unsafe_allow_html=True)

# Page config
st.set_page_config(
    page_title="Advanced Scanner - TradingView Screener",
    page_icon="📊",
    layout="centered"
)

# Load custom CSS
try:
    with open('style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except FileNotFoundError:
    pass

# NSE Multi-EMA Scanner Section
st.markdown("<div class='page-header'>", unsafe_allow_html=True)
st.title("📈 NSE Multi-EMA Scanner")
st.caption("Find high-momentum NSE stocks trading above key EMAs (50, 150, 200)")
st.markdown("</div>", unsafe_allow_html=True)

# Criteria Card
st.markdown("""
<div class='scanner-info-card'>
    <h3>🎯 Scanner Criteria</h3>
    <ul>
        <li><strong>Price Action:</strong> Trading above 50, 150, and 200-day EMAs</li>
        <li><strong>Momentum:</strong> Shows strong upward trend and momentum</li>
        <li><strong>Market Data:</strong> Includes volume, performance, and market cap</li>
        <li><strong>Analysis:</strong> Industry and sector-wise grouping</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# Add vertical space for clarity
st.markdown("<br>", unsafe_allow_html=True)

# Main layout: parameters and results side by side for desktop, stacked for mobile
is_wide = True
try:
    # Use Streamlit's internal state if available
    is_wide = st.columns is not None
except Exception:
    is_wide = True

if is_wide:
    with st.container():
        param_col, results_col = st.columns([1.1, 2], gap="large")
        with param_col:
            st.markdown("<div class='parameter-card'><h4>Scanner Parameters</h4></div>", unsafe_allow_html=True)
            # Place all parameter widgets here (e.g., exchange filter, sliders, checkboxes)
            # Example:
            st.subheader("Exchange Filter")
            selected_exchanges = st.multiselect("Select exchanges", ["NSE", "BSE"], default=["NSE"])
            st.subheader("Volume Analysis")
            min_rel_vol = st.slider("Minimum Relative Volume", 1.0, 5.0, 1.2, step=0.05)
            # Add more parameter widgets as needed
        with results_col:
            # Remove card for results on wide screens for max width
            st.markdown("<div style='padding:0;margin:0;'>", unsafe_allow_html=True)
            # Only show results if scan has been run
            if st.button("🔍 Run NSE Multi-EMA Scan", type="primary", use_container_width=True, key="run_scan"):
                with st.spinner("Scanning NSE stocks above multiple EMAs..."):
                    try:
                        q = (
                            Query()
                            .set_markets('india')
                            .select(
                                'name', 'close', 
                                'EMA50', 'EMA150', 'EMA200',
                                'exchange', 'type',
                                'relative_volume_10d_calc',
                                'is_primary',
                                'sector', 'industry',
                                'Perf.1M',  # 1-month performance
                                'Perf.3M',  # 3-month performance
                                'market_cap_basic',  # Market Cap
                                'price_52_week_high',  # 52-week high
                                'float_shares_outstanding',  # Float shares
                                'total_shares_outstanding',  # Total shares
                                'RSI'  # Adding RSI for analysis
                            )
                            .where(
                                # Exchange and type filters
                                col('exchange') == 'NSE',
                                col('type') == 'stock',
                                col('is_primary') == True,
                                
                                # Price filter
                                col('close') > 20,
                                
                                # EMA conditions
                                col('close') > col('EMA50'),
                                col('close') > col('EMA150'),
                                col('close') > col('EMA200')
                            )
                            .order_by('relative_volume_10d_calc', ascending=False)
                        )
                        
                        # Batch fetching to get all results
                        batch_size = 1000
                        max_rows = 5000  # Set a high limit
                        dfs = []
                        total_count = None
                        
                        for offset in range(0, max_rows, batch_size):
                            q_batch = q.offset(offset).limit(batch_size)
                            count, df_batch = q_batch.get_scanner_data()
                            
                            if total_count is None:
                                total_count = count
                            
                            if df_batch is not None and not df_batch.empty:
                                dfs.append(df_batch)
                                if len(df_batch) < batch_size:  # Got all results
                                    break
                            else:
                                break
                        
                        # Combine all batches
                        if dfs:
                            df = pd.concat(dfs, ignore_index=True)
                            count = total_count  # Use the total count from first batch
                        else:
                            df = pd.DataFrame()
                            count = 0
                        
                        if not df.empty:
                            # Calculate percentage above each EMA
                            df['Above_EMA50%'] = ((df['close'] - df['EMA50']) / df['EMA50'] * 100).round(2)
                            df['Above_EMA150%'] = ((df['close'] - df['EMA150']) / df['EMA150'] * 100).round(2)
                            df['Above_EMA200%'] = ((df['close'] - df['EMA200']) / df['EMA200'] * 100).round(2)
                            
                            # Calculate percentage from 52-week high
                            df['From_52WH%'] = ((df['price_52_week_high'] - df['close']) / df['price_52_week_high'] * 100).round(2)
                            
                            # Format relative volume
                            df['Rel_Volume'] = df['relative_volume_10d_calc'].round(2)
                            
                            # Format market cap to display in Crores
                            df['Market_Cap_Cr'] = (df['market_cap_basic'] / 10000000).round(2)  # Convert to Crores
                            
                            # Format performance columns
                            df['1M_Perf'] = df['Perf.1M'].round(2)
                            df['3M_Perf'] = df['Perf.3M'].round(2)
                            
                            # Calculate float shares as percentage of total shares
                            df['Float_Shares%'] = (df['float_shares_outstanding'] / df['total_shares_outstanding'] * 100).round(2)
                            
                            # Select and rename columns for display
                            display_cols = [
                                'name', 'close', 'is_primary',
                                'sector', 'industry',
                                'Above_EMA50%', 'Above_EMA150%', 'Above_EMA200%',
                                '1M_Perf', '3M_Perf',
                                'From_52WH%',
                                'Float_Shares%',
                                'Market_Cap_Cr',
                                'Rel_Volume'
                            ]
                            
                            # Add NSE: prefix to stock names
                            df['name'] = 'NSE:' + df['name']
                            
                            display_df = df[display_cols].rename(columns={
                                'name': 'Stock',
                                'close': 'Price',
                                'is_primary': 'Primary',
                                'sector': 'Sector',
                                'industry': 'Industry',
                                'Above_EMA50%': '% > EMA50',
                                'Above_EMA150%': '% > EMA150',
                                'Above_EMA200%': '% > EMA200',
                                '1M_Perf': '1M %',
                                '3M_Perf': '3M %',
                                'From_52WH%': '% from 52W High',
                                'Float_Shares%': 'Float %',
                                'Market_Cap_Cr': 'MCap (Cr)',
                                'Rel_Volume': 'Rel Volume'
                            })
                            
                            # Use extra spacing and padding for the results table
                            st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)
                            st.dataframe(
                                display_df,
                                use_container_width=True,
                                hide_index=True,
                                column_config={
                                    'Rel Volume': st.column_config.NumberColumn('Rel Volume', width='large'),
                                    'MCap (Cr)': st.column_config.NumberColumn('MCap (Cr)', width='large'),
                                    'Float %': st.column_config.NumberColumn('Float %', width='medium'),
                                    '1M %': st.column_config.NumberColumn('1M %', width='medium'),
                                    '3M %': st.column_config.NumberColumn('3M %', width='medium'),
                                    '% from 52W High': st.column_config.NumberColumn('% from 52W High', width='medium')
                                }
                            )
                            st.download_button(
                                "📥 Export Results",
                                display_df.to_csv(index=False),
                                "scanner_results.csv",
                                "text/csv",
                                use_container_width=True
                            )
                            # Add more vertical space after table
                            st.markdown("<div style='margin-bottom: 1.2rem;'></div>", unsafe_allow_html=True)
                            # Place other results/metrics/plots here as needed
                        else:
                            st.warning("No NSE stocks found trading above all EMAs. Try during market hours.")
                            
                    except Exception as e:
                        st.error(f"Error executing scan: {str(e)}")
                        st.code(str(e), language="python") 
            st.markdown("</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='parameter-card'><h4>Scanner Parameters</h4></div>", unsafe_allow_html=True)
    # Place all parameter widgets here (e.g., exchange filter, sliders, checkboxes)
    # Example:
    st.subheader("Exchange Filter")
    selected_exchanges = st.multiselect("Select exchanges", ["NSE", "BSE"], default=["NSE"])
    st.subheader("Volume Analysis")
    min_rel_vol = st.slider("Minimum Relative Volume", 1.0, 5.0, 1.2, step=0.05)
    # Add more parameter widgets as needed
    st.markdown("<div class='results-card'><h4>📊 Scanner Results</h4></div>", unsafe_allow_html=True)
    # Only show results if scan has been run
    if st.button("🔍 Run NSE Multi-EMA Scan", type="primary", use_container_width=True, key="run_scan"):
        with st.spinner("Scanning NSE stocks above multiple EMAs..."):
            try:
                q = (
                    Query()
                    .set_markets('india')
                    .select(
                        'name', 'close', 
                        'EMA50', 'EMA150', 'EMA200',
                        'exchange', 'type',
                        'relative_volume_10d_calc',
                        'is_primary',
                        'sector', 'industry',
                        'Perf.1M',  # 1-month performance
                        'Perf.3M',  # 3-month performance
                        'market_cap_basic',  # Market Cap
                        'price_52_week_high',  # 52-week high
                        'float_shares_outstanding',  # Float shares
                        'total_shares_outstanding',  # Total shares
                        'RSI'  # Adding RSI for analysis
                    )
                    .where(
                        # Exchange and type filters
                        col('exchange') == 'NSE',
                        col('type') == 'stock',
                        col('is_primary') == True,
                        
                        # Price filter
                        col('close') > 20,
                        
                        # EMA conditions
                        col('close') > col('EMA50'),
                        col('close') > col('EMA150'),
                        col('close') > col('EMA200')
                    )
                    .order_by('relative_volume_10d_calc', ascending=False)
                )
                
                # Batch fetching to get all results
                batch_size = 1000
                max_rows = 5000  # Set a high limit
                dfs = []
                total_count = None
                
                for offset in range(0, max_rows, batch_size):
                    q_batch = q.offset(offset).limit(batch_size)
                    count, df_batch = q_batch.get_scanner_data()
                    
                    if total_count is None:
                        total_count = count
                    
                    if df_batch is not None and not df_batch.empty:
                        dfs.append(df_batch)
                        if len(df_batch) < batch_size:  # Got all results
                            break
                    else:
                        break
                
                # Combine all batches
                if dfs:
                    df = pd.concat(dfs, ignore_index=True)
                    count = total_count  # Use the total count from first batch
                else:
                    df = pd.DataFrame()
                    count = 0
                
                if not df.empty:
                    # Calculate percentage above each EMA
                    df['Above_EMA50%'] = ((df['close'] - df['EMA50']) / df['EMA50'] * 100).round(2)
                    df['Above_EMA150%'] = ((df['close'] - df['EMA150']) / df['EMA150'] * 100).round(2)
                    df['Above_EMA200%'] = ((df['close'] - df['EMA200']) / df['EMA200'] * 100).round(2)
                    
                    # Calculate percentage from 52-week high
                    df['From_52WH%'] = ((df['price_52_week_high'] - df['close']) / df['price_52_week_high'] * 100).round(2)
                    
                    # Format relative volume
                    df['Rel_Volume'] = df['relative_volume_10d_calc'].round(2)
                    
                    # Format market cap to display in Crores
                    df['Market_Cap_Cr'] = (df['market_cap_basic'] / 10000000).round(2)  # Convert to Crores
                    
                    # Format performance columns
                    df['1M_Perf'] = df['Perf.1M'].round(2)
                    df['3M_Perf'] = df['Perf.3M'].round(2)
                    
                    # Calculate float shares as percentage of total shares
                    df['Float_Shares%'] = (df['float_shares_outstanding'] / df['total_shares_outstanding'] * 100).round(2)
                    
                    # Select and rename columns for display
                    display_cols = [
                        'name', 'close', 'is_primary',
                        'sector', 'industry',
                        'Above_EMA50%', 'Above_EMA150%', 'Above_EMA200%',
                        '1M_Perf', '3M_Perf',
                        'From_52WH%',
                        'Float_Shares%',
                        'Market_Cap_Cr',
                        'Rel_Volume'
                    ]
                    
                    # Add NSE: prefix to stock names
                    df['name'] = 'NSE:' + df['name']
                    
                    display_df = df[display_cols].rename(columns={
                        'name': 'Stock',
                        'close': 'Price',
                        'is_primary': 'Primary',
                        'sector': 'Sector',
                        'industry': 'Industry',
                        'Above_EMA50%': '% > EMA50',
                        'Above_EMA150%': '% > EMA150',
                        'Above_EMA200%': '% > EMA200',
                        '1M_Perf': '1M %',
                        '3M_Perf': '3M %',
                        'From_52WH%': '% from 52W High',
                        'Float_Shares%': 'Float %',
                        'Market_Cap_Cr': 'MCap (Cr)',
                        'Rel_Volume': 'Rel Volume'
                    })
                    
                    # Use extra spacing and padding for the results table
                    st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                    st.download_button(
                        "📥 Export Results",
                        display_df.to_csv(index=False),
                        "scanner_results.csv",
                        "text/csv",
                        use_container_width=True
                    )
                    # Add more vertical space after table
                    st.markdown("<div style='margin-bottom: 1.2rem;'></div>", unsafe_allow_html=True)
                    # Place other results/metrics/plots here as needed
                else:
                    st.warning("No NSE stocks found trading above all EMAs. Try during market hours.")
                    
            except Exception as e:
                st.error(f"Error executing scan: {str(e)}")
                st.code(str(e), language="python") 

# Add or update CSS for padding, card separation, and responsive layout
st.markdown("""
<style>
.scanner-info-card {
    background-color: rgba(28, 131, 225, 0.1);
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 24px;
}

.parameter-card, .results-card {
    background: rgba(30, 30, 30, 0.75);
    border-radius: 10px;
    padding: 1.5rem 1.2rem 1.2rem 1.2rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 2px 8px 0 rgba(20, 20, 20, 0.07);
}

@media (max-width: 900px) {
    .stColumns {
        flex-direction: column !important;
    }
    .parameter-card, .results-card {
        margin-bottom: 1.2rem;
        width: 100% !important;
        min-width: 0 !important;
    }
    .stDataFrame {
        min-width: 0 !important;
        width: 100% !important;
        overflow-x: auto !important;
    }
    .stDownloadButton, .stButton {
        width: 100% !important;
        min-width: 0 !important;
    }
}
.results-card, .parameter-card {
    min-width: 0 !important;
    width: 100% !important;
}
.stDataFrame {
    min-width: 0 !important;
    width: 100% !important;
    overflow-x: auto !important;
}
</style>
""", unsafe_allow_html=True)

# --- FIX: DataFrame should only expand to container, not full viewport ---
# Remove 100vw width, use 100% of parent only
st.markdown("""
<style>
.stDataFrame {
    width: 100% !important;
    min-width: 0 !important;
    max-width: 100% !important;
    background: rgba(240, 242, 246, 0.07);
    border-radius: 8px;
    padding: 10px;
    overflow-x: auto !important;
}
@media (max-width: 900px) {
    .stDataFrame {
        width: 100% !important;
        min-width: 0 !important;
        max-width: 100% !important;
    }
}
</style>
""", unsafe_allow_html=True)

# Separator before Advanced Scanner
st.markdown("---")

# Advanced Scanner Section
st.markdown("<div class='page-header'>", unsafe_allow_html=True)
st.header("📊 Advanced Technical Scanner")
st.caption("Custom technical and fundamental screening for US and Indian markets")
st.markdown("</div>", unsafe_allow_html=True)

# Create main layout for Advanced Scanner
main_col1, main_col2 = st.columns([2.5, 1.5])

with main_col2:
    st.markdown("""
    <div class='scanner-info-card'>
        <h3>📈 Scanner Features</h3>
        <ul>
            <li><strong>Technical Analysis:</strong> Moving averages, RSI, MACD</li>
            <li><strong>Volume Analysis:</strong> Relative volume, trading activity</li>
            <li><strong>Market Data:</strong> Market cap, price performance</li>
            <li><strong>Smart Filtering:</strong> Exchange, stock type, custom criteria</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Scanner Parameters Card
    st.markdown("<div class='parameter-card'>", unsafe_allow_html=True)
    st.subheader("🎯 Scanner Parameters")
    
    # Market selection with icons
    market = st.selectbox(
        "🌎 Select Market",
        {
            "america": "US Markets 🇺🇸",
            "india": "Indian Markets 🇮🇳"
        },
        format_func=lambda x: {
            "america": "US Markets 🇺🇸",
            "india": "Indian Markets 🇮🇳"
        }[x],
        index=0,
        help="Choose the market to scan"
    )
    
    # Volume Analysis
    st.markdown("#### 📊 Volume Analysis")
    vol_threshold = st.slider(
        "Minimum Relative Volume",
        min_value=1.0,
        max_value=5.0,
        value=1.2,
        step=0.1,
        help="Filter stocks with volume above X times their 10-day average"
    )
    
    # Technical Indicators
    st.markdown("#### 📈 Technical Indicators")
    rsi_min, rsi_max = st.slider(
        "RSI Range",
        min_value=0,
        max_value=100,
        value=(40, 70),
        help="Filter stocks within specific RSI range"
    )
    
    price_from_high = st.slider(
        "Maximum % Below 52-Week High",
        min_value=5,
        max_value=50,
        value=25,
        step=5,
        help="Find stocks within a certain percentage of their 52-week high"
    )
    
    # Market Cap Filter
    st.markdown("#### 💰 Market Cap Filter")
    market_cap_options = {
        "All": "All Market Caps",
        ">$1B": "Large Cap (>$1B)",
        ">$5B": "Mega Cap (>$5B)",
        ">$10B": "Super Cap (>$10B)",
        ">$50B": "Ultra Cap (>$50B)",
    }
    market_cap = st.selectbox(
        "Minimum Market Cap",
        options=list(market_cap_options.keys()),
        format_func=lambda x: market_cap_options[x],
        index=1,
        help="Filter stocks by minimum market capitalization"
    )
    
    st.markdown("</div>", unsafe_allow_html=True)

with main_col1:
    # Action buttons
    col1, col2 = st.columns([1, 1])
    with col1:
        scan_button = st.button("🔍 Run Scanner", type="primary", use_container_width=True)
    with col2:
        clear_button = st.button("🔄 Reset Filters", type="secondary", use_container_width=True)
    
    if scan_button:
        with st.spinner("Running comprehensive technical analysis..."):
            try:
                # Convert market cap options to values
                market_cap_values = {
                    "All": 0,
                    ">$1B": 1_000_000_000,
                    ">$5B": 5_000_000_000,
                    ">$10B": 10_000_000_000,
                    ">$50B": 50_000_000_000,
                }
                
                q = (
                    Query()
                    .set_markets(market)
                    .select(
                        'name', 'close', 'volume', 
                        'EMA20', 'EMA50', 'EMA200',
                        'relative_volume_10d_calc',
                        'RSI', 'MACD.macd', 'MACD.signal',
                        'price_52_week_high',
                        'market_cap_basic',
                        'exchange', 'type'
                    )
                    .where(
                        # Price above moving averages
                        col('close') > col('EMA20'),
                        col('close') > col('EMA50'),
                        col('close') > col('EMA200'),
                        
                        # High relative volume
                        col('relative_volume_10d_calc') > vol_threshold,
                        
                        # RSI between user-defined range
                        col('RSI').between(rsi_min, rsi_max),
                        
                        # MACD bullish (MACD line above signal line)
                        col('MACD.macd') > col('MACD.signal'),
                        
                        # Within user-defined % of 52-week high
                        col('close').above_pct('price_52_week_high', (100 - price_from_high) / 100),
                        
                        # Market cap filter
                        col('market_cap_basic') > market_cap_values[market_cap] if market_cap_values[market_cap] > 0 else None,
                        
                        # Only stocks and ETFs
                        col('type').isin(['stock', 'fund'])
                    )
                    .order_by('relative_volume_10d_calc', ascending=False)
                    .limit(100)
                )
                
                count, df = q.get_scanner_data()
                
                if not df.empty:
                    # Results Overview
                    st.markdown("<div class='results-overview'>", unsafe_allow_html=True)
                    overview_cols = st.columns(4)
                    
                    with overview_cols[0]:
                        st.metric("Total Stocks", len(df))
                    with overview_cols[1]:
                        st.metric("Avg RSI", f"{df['RSI'].mean():.1f}")
                    with overview_cols[2]:
                        st.metric("Avg Rel Volume", f"{df['relative_volume_10d_calc'].mean():.1f}x")
                    with overview_cols[3]:
                        st.metric("Exchanges", df['exchange'].nunique())
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Exchange Filter
                    if 'exchange' in df.columns and len(df['exchange'].unique()) > 1:
                        st.markdown("#### 🏢 Exchange Filter")
                        exchanges = sorted(df['exchange'].unique())
                        exchange_counts = df['exchange'].value_counts()
                        selected_exchanges = st.multiselect(
                            "Select exchanges",
                            options=exchanges,
                            format_func=lambda x: f"{x} ({exchange_counts[x]} stocks)",
                            help="Filter results by specific exchanges"
                        )
                        
                        if selected_exchanges:
                            df = df[df['exchange'].isin(selected_exchanges)]
                    
                    # Results Table
                    st.markdown("#### 📊 Scanner Results")
                    
                    # Format the dataframe for display
                    display_df = pd.DataFrame({
                        'Symbol': df['name'],
                        'Exchange': df['exchange'],
                        'Close': df['close'].round(2),
                        'Rel Volume': df['relative_volume_10d_calc'].round(1),
                        'RSI': df['RSI'].round(1),
                        '% From High': ((1 - df['close'] / df['price_52_week_high']) * 100).round(1),
                        'Market Cap': df['market_cap_basic'].apply(lambda x: f"${x/1e9:.1f}B")
                    })
                    
                    st.dataframe(
                        display_df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            'Symbol': st.column_config.TextColumn('Symbol', width='medium'),
                            'Exchange': st.column_config.TextColumn('Exchange', width='small'),
                            'Close': st.column_config.NumberColumn('Price', format="$%.2f"),
                            'Rel Volume': st.column_config.NumberColumn('Rel Vol', format="%.1fx"),
                            'RSI': st.column_config.NumberColumn('RSI', format="%.1f"),
                            '% From High': st.column_config.NumberColumn('% From High', format="%.1f%%"),
                            'Market Cap': st.column_config.TextColumn('Market Cap', width='medium')
                        }
                    )
                    
                    # Export button
                    st.download_button(
                        "📥 Export Results",
                        display_df.to_csv(index=False),
                        "scanner_results.csv",
                        "text/csv",
                        use_container_width=True
                    )
                    
                else:
                    st.warning("No stocks found matching the criteria. Try adjusting the filters.")
                    
            except Exception as e:
                st.error(f"Error running scanner: {str(e)}")
                st.info("Please try adjusting the parameters or try again later.")

# Add custom CSS for modern styling
st.markdown("""
<style>
.scanner-info-card {
    background-color: rgba(28, 131, 225, 0.1);
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 20px;
}

.scanner-info-card h3 {
    color: #1C83E1;
    margin-bottom: 15px;
}

.scanner-info-card ul {
    list-style-type: none;
    padding-left: 0;
}

.scanner-info-card li {
    margin-bottom: 10px;
    padding-left: 25px;
    position: relative;
}

.scanner-info-card li:before {
    content: "•";
    color: #1C83E1;
    font-weight: bold;
    position: absolute;
    left: 10px;
}

.parameter-card {
    background-color: rgba(240, 242, 246, 0.1);
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 20px;
}

.results-overview {
    background-color: rgba(28, 131, 225, 0.1);
    border-radius: 10px;
    padding: 20px;
    margin: 20px 0;
}

/* Improve spacing and readability */
.stSlider, .stSelectbox {
    margin-bottom: 25px;
}

/* Make metrics more prominent */
.stMetric {
    background-color: rgba(28, 131, 225, 0.05);
    padding: 10px;
    border-radius: 8px;
}

/* Style the dataframe */
.stDataFrame {
    background-color: rgba(240, 242, 246, 0.1);
    border-radius: 10px;
    padding: 10px;
}

/* Add emphasis to the Multi-EMA Scanner section */
.page-header:first-of-type {
    border-bottom: 2px solid rgba(28, 131, 225, 0.2);
    margin-bottom: 2rem;
    padding-bottom: 1rem;
}

/* Style the separator */
hr {
    margin: 3rem 0;
    border: none;
    border-top: 2px solid rgba(28, 131, 225, 0.1);
}
</style>
""", unsafe_allow_html=True)

# CSS: Make results section and dataframe use the full width
st.markdown("""
<style>
@media (min-width: 900px) {
    .results-card, .stDataFrame {
        width: 100% !important;
        min-width: 100% !important;
        max-width: 100% !important;
    }
}
.stDataFrame {
    background: rgba(240, 242, 246, 0.07);
    border-radius: 8px;
    padding: 10px;
    overflow-x: auto !important;
}
</style>
""", unsafe_allow_html=True)