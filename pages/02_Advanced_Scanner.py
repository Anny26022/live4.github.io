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
    layout="wide"
)

# Title and description
st.title("📊 Advanced Technical Scanner")
st.markdown("""
This advanced scanner helps you find stocks that meet specific technical and fundamental criteria:

### 📈 Technical Criteria
- Above key moving averages (20, 50, 200 EMA)
- RSI between 40 and 70 (not overbought/oversold)
- MACD showing bullish momentum
- Within 25% of 52-week high

### 📊 Volume & Market Criteria
- High relative volume (>1.2x average)
- Market cap above $1B
- Stocks and ETFs only

### 🔍 Additional Features
- Exchange filtering
- Download results as CSV
- Summary statistics
""")

# Helper function for exchange filter (copied from main app)
def apply_exchange_filter(df, key_suffix=""):
    """
    Apply exchange filter to any dataframe that has an 'exchange' column.
    Returns the filtered dataframe and success message.
    """
    if df is None or df.empty or 'exchange' not in df.columns:
        return df, ""
        
    # Get unique exchanges (using set to ensure truly unique values)
    unique_exchanges = sorted(list(set(df['exchange'].unique())))
    display_df = df.copy()
    
    # Only show exchange filter if there are multiple unique exchanges
    if len(unique_exchanges) > 1:
        exchange_counts = df['exchange'].value_counts()
        exchange_options = [f"{ex} ({exchange_counts[ex]})" for ex in unique_exchanges]
        
        st.subheader("🏢 Filter by Exchange")
        
        # Create dropdown multiselect for exchanges with unique key
        selected_exchange_filters = st.multiselect(
            "Select exchanges to filter",
            options=exchange_options,
            default=[],
            help="Select one or more exchanges to filter the results",
            key=f"exchange_multiselect_results_{key_suffix}"
        )
        
        # Apply exchange filter without re-running query
        if selected_exchange_filters:
            # Extract exchange names without the counts
            selected_exchanges = [ex.split(" (")[0].strip() for ex in selected_exchange_filters]
            # Create a boolean mask for all selected exchanges
            exchange_mask = display_df['exchange'].isin(selected_exchanges)
            # Apply the filter
            display_df = display_df[exchange_mask]
            
            # Show counts for each selected exchange
            exchange_breakdown = []
            for ex in selected_exchanges:
                count = len(display_df[display_df['exchange'] == ex])
                exchange_breakdown.append(f"{ex}: {count}")
            
            success_msg = f"""
            Filtered results:
            - Total rows: {len(display_df)}
            - By exchange: {', '.join(exchange_breakdown)}
            """
            return display_df, success_msg
            
    return display_df, ""

# Add parameter controls
st.sidebar.header("📊 Scanner Parameters")

# Market selection
market = st.sidebar.selectbox(
    "Select Market",
    ["america", "india"],
    index=0,
    help="Choose the market to scan"
)

# Volume threshold
vol_threshold = st.sidebar.slider(
    "Minimum Relative Volume",
    min_value=1.0,
    max_value=5.0,
    value=1.2,
    step=0.1,
    help="Minimum relative volume compared to 10-day average"
)

# RSI range
rsi_min, rsi_max = st.sidebar.slider(
    "RSI Range",
    min_value=0,
    max_value=100,
    value=(40, 70),
    help="RSI range to filter stocks"
)

# Price from high
price_from_high = st.sidebar.slider(
    "Maximum % Below 52-Week High",
    min_value=5,
    max_value=50,
    value=25,
    step=5,
    help="Maximum percentage below 52-week high"
)

# Market cap
market_cap_options = {
    "All": 0,
    ">$1B": 1_000_000_000,
    ">$5B": 5_000_000_000,
    ">$10B": 10_000_000_000,
    ">$50B": 50_000_000_000,
}
market_cap = st.sidebar.selectbox(
    "Minimum Market Cap",
    options=list(market_cap_options.keys()),
    index=1,
    help="Minimum market capitalization"
)

# Run scanner button
if st.button("🔍 Run Technical Scanner", type="primary"):
    with st.spinner("Running comprehensive technical analysis query..."):
        try:
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
                    
                    # Market cap filter (if selected)
                    col('market_cap_basic') > market_cap_options[market_cap] if market_cap_options[market_cap] > 0 else None,
                    
                    # Only stocks and ETFs
                    col('type').isin(['stock', 'fund'])
                )
                .order_by('relative_volume_10d_calc', ascending=False)
                .limit(100)
            )
            
            count, df = q.get_scanner_data()
            
            if not df.empty:
                # Apply exchange filter
                display_df, filter_msg = apply_exchange_filter(df, "advanced_tech")
                
                # Calculate and add percentage from 52-week high
                display_df['pct_from_high'] = ((display_df['price_52_week_high'] - display_df['close']) / 
                                             display_df['price_52_week_high'] * 100).round(2)
                
                # Format relative volume
                display_df['relative_volume_10d_calc'] = display_df['relative_volume_10d_calc'].round(2)
                
                # Format RSI and MACD
                display_df['RSI'] = display_df['RSI'].round(2)
                display_df['MACD_Diff'] = (display_df['MACD.macd'] - display_df['MACD.signal']).round(3)
                
                # Reorder and rename columns for better display
                cols_to_display = [
                    'name', 'exchange', 'close',
                    'relative_volume_10d_calc', 'RSI', 'MACD_Diff',
                    'pct_from_high'
                ]
                
                display_df = display_df[cols_to_display].rename(columns={
                    'relative_volume_10d_calc': 'Rel Volume',
                    'pct_from_high': '% From High',
                    'MACD_Diff': 'MACD Diff'
                })
                
                if filter_msg:
                    st.success(filter_msg)
                else:
                    st.success(f"Found {count} stocks meeting the criteria. Showing top {len(display_df)} results.")
                
                # Show results in tabs
                tab1, tab2 = st.tabs(["📊 Results Table", "📈 Summary Statistics"])
                
                with tab1:
                    st.dataframe(display_df, use_container_width=True, height=600)
                    
                    # Add download button for current view
                    st.download_button(
                        "📥 Download Results",
                        data=display_df.to_csv(index=False),
                        file_name="technical_analysis_results.csv",
                        mime="text/csv"
                    )
                
                with tab2:
                    # Show summary statistics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Avg Relative Volume", 
                                 f"{display_df['Rel Volume'].mean():.2f}x")
                    
                    with col2:
                        st.metric("Avg RSI",
                                 f"{display_df['RSI'].mean():.1f}")
                    
                    with col3:
                        st.metric("Avg % From High",
                                 f"{display_df['% From High'].mean():.1f}%")
                    
                    with col4:
                        st.metric("Total Results",
                                 f"{len(display_df):,}")
                    
                    # Add distribution plots
                    try:
                        import plotly.express as px
                        
                        # RSI Distribution
                        fig_rsi = px.histogram(display_df, x='RSI', 
                                             title='RSI Distribution',
                                             nbins=20)
                        st.plotly_chart(fig_rsi, use_container_width=True)
                        
                        # % From High Distribution
                        fig_high = px.histogram(display_df, x='% From High',
                                              title='Distribution of % Below 52-Week High',
                                              nbins=20)
                        st.plotly_chart(fig_high, use_container_width=True)
                        
                    except ImportError:
                        st.info("Install plotly to see distribution charts")
                
            else:
                st.warning("No stocks found matching all criteria. Try adjusting the parameters.")
                
        except Exception as e:
            st.error(f"Error executing query: {str(e)}")
            st.code(str(e), language="python")

# Add a separator
st.markdown("---")

# NSE Multi-EMA Scanner
st.header("📈 NSE Multi-EMA Scanner")
st.markdown("""
This scanner finds NSE stocks that are trading above multiple EMAs:
- Above 50-day EMA
- Above 150-day EMA
- Above 200-day EMA

These stocks show strong upward momentum and are trading above key technical levels.
""")

if st.button("🔍 Run NSE Multi-EMA Scan", type="primary"):
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
                    'total_shares_outstanding'  # Total shares
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
                
                # Show results in tabs
                tab1, tab2 = st.tabs(["📊 Results", "📈 Analysis"])
                
                with tab1:
                    st.success(f"Found {count} NSE stocks trading above all EMAs (50, 150, 200)")
                    st.dataframe(display_df, use_container_width=True)
                    
                    # Add copy buttons for tickers
                    st.subheader("📋 Copy Tickers")
                    
                    # Create two columns for industry and sector groupings
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**By Industry**")
                        
                        # Group tickers by industry and get counts
                        industry_counts = display_df.groupby('Industry').size().sort_values(ascending=False)
                        
                        # Create formatted string with industry grouping in descending order of count
                        formatted_industry_tickers = []
                        for industry, count in industry_counts.items():
                            group = display_df[display_df['Industry'] == industry]
                            tickers = group['Stock'].tolist()
                            formatted_industry_tickers.append(f"###{industry}({count}),{','.join(tickers)}")
                        
                        # Join all groups with commas
                        industry_tickers_text = ','.join(formatted_industry_tickers)
                        
                        # Create copy button for industry
                        st.markdown(f"""
                        <div style="display: flex; align-items: center; margin-bottom: 10px;">
                            <button 
                                onclick="navigator.clipboard.writeText(`{industry_tickers_text}`);this.innerHTML='Copied!';setTimeout(() => this.innerHTML='📋 Copy Industry List', 2000)"
                                style="background-color: #FF4B4B; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;"
                            >
                                📋 Copy Industry List
                            </button>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Show text area with formatted tickers by industry
                        st.text_area("Industry-wise Grouping",
                                    value=industry_tickers_text,
                                    height=300,
                                    help=f"Industry-wise grouped tickers ({len(display_df)} stocks total) - Sorted by number of stocks")
                    
                    with col2:
                        st.markdown("**By Sector**")
                        
                        # Group tickers by sector and get counts
                        sector_counts = display_df.groupby('Sector').size().sort_values(ascending=False)
                        
                        # Create formatted string with sector grouping in descending order of count
                        formatted_sector_tickers = []
                        for sector, count in sector_counts.items():
                            group = display_df[display_df['Sector'] == sector]
                            tickers = group['Stock'].tolist()
                            formatted_sector_tickers.append(f"###{sector}({count}),{','.join(tickers)}")
                        
                        # Join all groups with commas
                        sector_tickers_text = ','.join(formatted_sector_tickers)
                        
                        # Create copy button for sector
                        st.markdown(f"""
                        <div style="display: flex; align-items: center; margin-bottom: 10px;">
                            <button 
                                onclick="navigator.clipboard.writeText(`{sector_tickers_text}`);this.innerHTML='Copied!';setTimeout(() => this.innerHTML='📋 Copy Sector List', 2000)"
                                style="background-color: #FF4B4B; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;"
                            >
                                📋 Copy Sector List
                            </button>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Show text area with formatted tickers by sector
                        st.text_area("Sector-wise Grouping",
                                    value=sector_tickers_text,
                                    height=300,
                                    help=f"Sector-wise grouped tickers ({len(display_df)} stocks total) - Sorted by number of stocks")
                    
                    # Download button
                    st.download_button(
                        "📥 Download Results",
                        data=display_df.to_csv(index=False),
                        file_name="nse_multi_ema_scan.csv",
                        mime="text/csv"
                    )
                
                with tab2:
                    # Summary statistics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Avg % > EMA50", 
                                 f"{display_df['% > EMA50'].mean():.1f}%")
                    
                    with col2:
                        st.metric("Avg % > EMA150",
                                 f"{display_df['% > EMA150'].mean():.1f}%")
                    
                    with col3:
                        st.metric("Avg % > EMA200",
                                 f"{display_df['% > EMA200'].mean():.1f}%")
                    
                    with col4:
                        st.metric("Avg RSI",
                                 f"{display_df['RSI'].mean():.1f}")
                    
                    # Distribution plots
                    try:
                        import plotly.express as px
                        
                        # EMA Distance Distribution
                        fig_ema = px.box(display_df, 
                                       y=['% > EMA50', '% > EMA150', '% > EMA200'],
                                       title='Distribution of Distance from EMAs')
                        st.plotly_chart(fig_ema, use_container_width=True)
                        
                        # RSI Distribution
                        fig_rsi = px.histogram(display_df, x='RSI',
                                             title='RSI Distribution',
                                             nbins=20)
                        st.plotly_chart(fig_rsi, use_container_width=True)
                        
                    except ImportError:
                        st.info("Install plotly to see distribution charts")
                
            else:
                st.warning("No NSE stocks found trading above all EMAs. Try during market hours.")
                
        except Exception as e:
            st.error(f"Error executing scan: {str(e)}")
            st.code(str(e), language="python") 