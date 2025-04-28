import streamlit as st
from tradingview_screener import Query, col
import pandas as pd

st.set_page_config(
    page_title="🛠️ Advanced Scanner",
    page_icon="🛠️",
    layout="centered",
    initial_sidebar_state="auto"
)

st.title("🛠️ Advanced Scanner")

st.markdown("""
<style>
.dev-banner {
    background: linear-gradient(90deg, #ff5858 0%, #ffc837 100%);
    color: #222;
    border-radius: 18px;
    padding: 2.5rem 2rem;
    font-size: 2.1rem;
    font-weight: 800;
    margin-bottom: 2.5rem;
    box-shadow: 0 8px 32px 0 rgba(255,88,88,0.18);
    text-align: center;
    letter-spacing: 0.02em;
    animation: fadeInUp 1.1s cubic-bezier(0.4,0,0.2,1);
}
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(32px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes scalePop {
  from { transform: scale(0.95); opacity: 0.7; }
  to { transform: scale(1); opacity: 1; }
}
@keyframes shimmer {
  0% { background-position: -1000px 0; }
  100% { background-position: 1000px 0; }
}

.stButton > button {
    transition: background 0.18s, color 0.18s, transform 0.18s, box-shadow 0.18s;
    animation: scalePop 0.5s cubic-bezier(0.4,0,0.2,1);
    position: relative;
    overflow: hidden;
}
.stButton > button:hover {
    background: linear-gradient(90deg, #ffc837 0%, #ff5858 100%);
    color: #23272f;
    transform: translateY(-2px) scale(1.04);
    box-shadow: 0 4px 16px rgba(255,88,88,0.12);
}
.stButton > button:active {
    transform: scale(0.97);
}

.stProgress > div > div {
    background: linear-gradient(90deg, #3b82f6 0%, #60a5fa 100%);
    animation: shimmer 2.5s linear infinite;
    background-size: 1000px 100%;
}

.stDataFrame, .stTable {
    animation: fadeInUp 0.7s cubic-bezier(0.4,0,0.2,1);
}

.stMetric {
    animation: scalePop 0.6s cubic-bezier(0.4,0,0.2,1);
}

.stSelectbox > div > div > div > input:focus {
    box-shadow: 0 0 0 2px #3b82f6;
    transition: box-shadow 0.2s cubic-bezier(0.4,0,0.2,1);
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="dev-banner">
🚧 This page is under development.<br>We will come back soon!
</div>
""", unsafe_allow_html=True)
st.stop()

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
            # Place all parameter widgets here
            st.subheader("Exchange Filter")
            selected_exchanges = st.multiselect("Select exchanges", ["NSE", "BSE"], default=["NSE"])
            st.subheader("Volume Analysis")
            min_rel_vol = st.slider("Minimum Relative Volume", 1.0, 5.0, 1.2, step=0.05)
        
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
                            # Process and display results
                            st.success(f"Found {count} stocks matching criteria")
                            
                            # Calculate percentage above each EMA
                            df['Above_EMA50%'] = ((df['close'] - df['EMA50']) / df['EMA50'] * 100).round(2)
                            df['Above_EMA150%'] = ((df['close'] - df['EMA150']) / df['EMA150'] * 100).round(2)
                            df['Above_EMA200%'] = ((df['close'] - df['EMA200']) / df['EMA200'] * 100).round(2)
                            
                            # Calculate percentage from 52-week high
                            df['From_52WH%'] = ((df['price_52_week_high'] - df['close']) / df['price_52_week_high'] * 100).round(2)
                            
                            # Format relative volume
                            df['Rel_Volume'] = df['relative_volume_10d_calc'].round(2)
                            
                            # Format market cap to display in Crores
                            df['Market_Cap_Cr'] = (df['market_cap_basic'] / 10000000).round(2)
                            
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
                            
                            # Display results
                            st.dataframe(display_df, use_container_width=True)
                        else:
                            st.warning("No stocks found matching the criteria")
                    except Exception as e:
                        st.error(f"Error running scanner: {str(e)}")
                        st.info("Please try adjusting the parameters or try again later.")
else:
    st.warning("Your screen width is too narrow for optimal viewing. Please use a wider screen or desktop device for the best experience.")

# Add professional CSS styling and animations
st.markdown("""
<style>
/* Modern Color Variables */
:root {
    --primary: rgba(28, 131, 225, 1);
    --primary-light: rgba(28, 131, 225, 0.1);
    --primary-dark: rgba(20, 92, 158, 1);
    --accent: rgba(255, 159, 67, 1);
    --success: rgba(46, 213, 115, 1);
    --error: rgba(255, 71, 87, 1);
    --bg-dark: rgba(30, 30, 30, 0.95);
    --bg-card: rgba(240, 242, 246, 0.05);
    --text-primary: rgba(255, 255, 255, 0.9);
    --text-secondary: rgba(255, 255, 255, 0.7);
}

/* Glass Morphism Effect */
.glass-card {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05));
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.15);
}

/* Enhanced Card Designs */
.scanner-info-card {
    background: var(--bg-card);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 24px;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}

.scanner-info-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--primary), var(--accent));
    transform: scaleX(0);
    transition: transform 0.4s ease;
}

.scanner-info-card:hover::before {
    transform: scaleX(1);
}

.scanner-info-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 24px rgba(0, 0, 0, 0.2);
}

/* Sophisticated Button Styles */
.stButton > button {
    background: linear-gradient(135deg, var(--primary), var(--primary-dark));
    border: none;
    padding: 12px 24px;
    border-radius: 8px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}

.stButton > button::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 0;
    height: 0;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 50%;
    transform: translate(-50%, -50%);
    transition: width 0.6s ease, height 0.6s ease;
}

.stButton > button:hover::before {
    width: 300%;
    height: 300%;
}

/* Advanced Table Styling */
.stDataFrame {
    border-radius: 12px;
    overflow: hidden;
    animation: slideUp 0.5s ease-out;
}

.stDataFrame table {
    border-collapse: separate;
    border-spacing: 0;
    width: 100%;
}

.stDataFrame thead th {
    background: var(--bg-dark);
    padding: 12px 16px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 2px solid var(--primary-light);
}

.stDataFrame tbody tr {
    transition: all 0.3s ease;
}

.stDataFrame tbody tr:hover {
    background: var(--primary-light);
    transform: scale(1.01);
}

/* Animated Metrics */
.stMetric {
    background: var(--bg-card);
    border-radius: 12px;
    padding: 16px;
    transition: all 0.3s ease;
}

.stMetric:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
}

/* Loading Animation */
@keyframes shimmer {
    0% { background-position: -1000px 0; }
    100% { background-position: 1000px 0; }
}

.stSpinner {
    background: linear-gradient(90deg, var(--bg-card) 0%, var(--primary-light) 50%, var(--bg-card) 100%);
    background-size: 1000px 100%;
    animation: shimmer 2s infinite linear;
}

/* Progress Bars */
.stProgress > div > div {
    background: linear-gradient(90deg, var(--primary), var(--accent));
    border-radius: 8px;
    transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Dropdown Enhancements */
.stSelectbox select {
    background: var(--bg-card);
    border: 1px solid var(--primary-light);
    border-radius: 8px;
    padding: 8px 16px;
    transition: all 0.3s ease;
}

.stSelectbox select:hover {
    border-color: var(--primary);
    box-shadow: 0 0 0 2px var(--primary-light);
}

/* Slider Styling */
.stSlider input {
    accent-color: var(--primary);
}

.stSlider input::-webkit-slider-thumb {
    box-shadow: 0 0 10px var(--primary);
}

/* Success/Error Messages */
.stSuccess {
    background: linear-gradient(135deg, var(--success), rgba(46, 213, 115, 0.8));
    border-radius: 8px;
    padding: 16px;
    animation: slideIn 0.5s ease-out;
}

.stError {
    background: linear-gradient(135deg, var(--error), rgba(255, 71, 87, 0.8));
    border-radius: 8px;
    padding: 16px;
    animation: shake 0.5s ease-in-out;
}

/* Advanced Animations */
@keyframes slideUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes slideIn {
    from { opacity: 0; transform: translateX(-20px); }
    to { opacity: 1; transform: translateX(0); }
}

@keyframes shake {
    0%, 100% { transform: translateX(0); }
    20%, 60% { transform: translateX(-5px); }
    40%, 80% { transform: translateX(5px); }
}

@keyframes pulse {
    0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(28, 131, 225, 0.4); }
    70% { transform: scale(1.05); box-shadow: 0 0 0 10px rgba(28, 131, 225, 0); }
    100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(28, 131, 225, 0); }
}

/* Responsive Design */
@media (max-width: 768px) {
    .scanner-info-card {
        padding: 16px;
        margin-bottom: 16px;
    }
    
    .stButton > button {
        padding: 8px 16px;
    }
    
    .stDataFrame thead th {
        padding: 8px 12px;
    }
}

/* Dark Mode Optimizations */
@media (prefers-color-scheme: dark) {
    .scanner-info-card {
        background: var(--bg-card);
    }
    
    .stDataFrame thead th {
        background: var(--bg-dark);
    }
}

/* Custom Scrollbar */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: var(--bg-card);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb {
    background: var(--primary);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--primary-dark);
}

/* Tooltip Animations */
[data-tooltip] {
    position: relative;
}

[data-tooltip]::before {
    content: attr(data-tooltip);
    position: absolute;
    bottom: 100%;
    left: 50%;
    transform: translateX(-50%) scale(0);
    padding: 8px 12px;
    background: var(--bg-dark);
    color: var(--text-primary);
    border-radius: 4px;
    font-size: 12px;
    opacity: 0;
    transition: all 0.3s ease;
    pointer-events: none;
    white-space: nowrap;
}

[data-tooltip]:hover::before {
    transform: translateX(-50%) scale(1);
    opacity: 1;
}

/* Loading Skeleton Animation */
@keyframes skeletonLoading {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}

.skeleton {
    background: linear-gradient(90deg, var(--bg-card) 25%, var(--primary-light) 50%, var(--bg-card) 75%);
    background-size: 200% 100%;
    animation: skeletonLoading 1.5s infinite;
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
st.markdown("""
<div style='display:flex;align-items:center;justify-content:center;margin-bottom:0.5em;'>
  <svg xmlns='http://www.w3.org/2000/svg' width='48' height='48' viewBox='0 0 48 48' fill='none' style='margin-right:16px;'>
    <rect width='48' height='48' rx='12' fill='url(#build-bg)'/>
    <g>
      <circle cx='24' cy='24' r='12' fill='#43a047' fill-opacity='0.85'/>
      <path d='M28 20l-8 8' stroke='#fff' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/>
      <circle cx='28' cy='20' r='2' fill='#fff'/>
      <circle cx='20' cy='28' r='2' fill='#fff'/>
    </g>
    <defs>
      <linearGradient id='build-bg' x1='0' y1='0' x2='48' y2='48' gradientUnits='userSpaceOnUse'>
        <stop stop-color='#23272F'/>
        <stop offset='1' stop-color='#181A20'/>
      </linearGradient>
    </defs>
  </svg>
  <span style='font-size:2.5rem;font-weight:700;color:#fff;'>Advanced Scanner</span>
</div>
<p style='text-align:center;margin-top:-0.75em;margin-bottom:2em;color:#aaa;font-size:1.1rem;'>Scan for high-momentum stocks above key EMAs</p>
""", unsafe_allow_html=True)

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
                
            except Exception as e:
                st.error(f"Error running scanner: {str(e)}")
                st.info("Please try adjusting the parameters or try again later.")

# Add professional CSS styling and animations
st.markdown("""
<style>
/* Modern Color Variables */
:root {
    --primary: rgba(28, 131, 225, 1);
    --primary-light: rgba(28, 131, 225, 0.1);
    --primary-dark: rgba(20, 92, 158, 1);
    --accent: rgba(255, 159, 67, 1);
    --success: rgba(46, 213, 115, 1);
    --error: rgba(255, 71, 87, 1);
    --bg-dark: rgba(30, 30, 30, 0.95);
    --bg-card: rgba(240, 242, 246, 0.05);
    --text-primary: rgba(255, 255, 255, 0.9);
    --text-secondary: rgba(255, 255, 255, 0.7);
}

/* Glass Morphism Effect */
.glass-card {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05));
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.15);
}

/* Enhanced Card Designs */
.scanner-info-card {
    background: var(--bg-card);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 24px;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}

.scanner-info-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--primary), var(--accent));
    transform: scaleX(0);
    transition: transform 0.4s ease;
}

.scanner-info-card:hover::before {
    transform: scaleX(1);
}

.scanner-info-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 24px rgba(0, 0, 0, 0.2);
}

/* Sophisticated Button Styles */
.stButton > button {
    background: linear-gradient(135deg, var(--primary), var(--primary-dark));
    border: none;
    padding: 12px 24px;
    border-radius: 8px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}

.stButton > button::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 0;
    height: 0;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 50%;
    transform: translate(-50%, -50%);
    transition: width 0.6s ease, height 0.6s ease;
}

.stButton > button:hover::before {
    width: 300%;
    height: 300%;
}

/* Advanced Table Styling */
.stDataFrame {
    border-radius: 12px;
    overflow: hidden;
    animation: slideUp 0.5s ease-out;
}

.stDataFrame table {
    border-collapse: separate;
    border-spacing: 0;
    width: 100%;
}

.stDataFrame thead th {
    background: var(--bg-dark);
    padding: 12px 16px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 2px solid var(--primary-light);
}

.stDataFrame tbody tr {
    transition: all 0.3s ease;
}

.stDataFrame tbody tr:hover {
    background: var(--primary-light);
    transform: scale(1.01);
}

/* Animated Metrics */
.stMetric {
    background: var(--bg-card);
    border-radius: 12px;
    padding: 16px;
    transition: all 0.3s ease;
}

.stMetric:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
}

/* Loading Animation */
@keyframes shimmer {
    0% { background-position: -1000px 0; }
    100% { background-position: 1000px 0; }
}

.stSpinner {
    background: linear-gradient(90deg, var(--bg-card) 0%, var(--primary-light) 50%, var(--bg-card) 100%);
    background-size: 1000px 100%;
    animation: shimmer 2s infinite linear;
}

/* Progress Bars */
.stProgress > div > div {
    background: linear-gradient(90deg, var(--primary), var(--accent));
    border-radius: 8px;
    transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Dropdown Enhancements */
.stSelectbox select {
    background: var(--bg-card);
    border: 1px solid var(--primary-light);
    border-radius: 8px;
    padding: 8px 16px;
    transition: all 0.3s ease;
}

.stSelectbox select:hover {
    border-color: var(--primary);
    box-shadow: 0 0 0 2px var(--primary-light);
}

/* Slider Styling */
.stSlider input {
    accent-color: var(--primary);
}

.stSlider input::-webkit-slider-thumb {
    box-shadow: 0 0 10px var(--primary);
}

/* Success/Error Messages */
.stSuccess {
    background: linear-gradient(135deg, var(--success), rgba(46, 213, 115, 0.8));
    border-radius: 8px;
    padding: 16px;
    animation: slideIn 0.5s ease-out;
}

.stError {
    background: linear-gradient(135deg, var(--error), rgba(255, 71, 87, 0.8));
    border-radius: 8px;
    padding: 16px;
    animation: shake 0.5s ease-in-out;
}

/* Advanced Animations */
@keyframes slideUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes slideIn {
    from { opacity: 0; transform: translateX(-20px); }
    to { opacity: 1; transform: translateX(0); }
}

@keyframes shake {
    0%, 100% { transform: translateX(0); }
    20%, 60% { transform: translateX(-5px); }
    40%, 80% { transform: translateX(5px); }
}

@keyframes pulse {
    0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(28, 131, 225, 0.4); }
    70% { transform: scale(1.05); box-shadow: 0 0 0 10px rgba(28, 131, 225, 0); }
    100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(28, 131, 225, 0); }
}

/* Responsive Design */
@media (max-width: 768px) {
    .scanner-info-card {
        padding: 16px;
        margin-bottom: 16px;
    }
    
    .stButton > button {
        padding: 8px 16px;
    }
    
    .stDataFrame thead th {
        padding: 8px 12px;
    }
}

/* Dark Mode Optimizations */
@media (prefers-color-scheme: dark) {
    .scanner-info-card {
        background: var(--bg-card);
    }
    
    .stDataFrame thead th {
        background: var(--bg-dark);
    }
}

/* Custom Scrollbar */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: var(--bg-card);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb {
    background: var(--primary);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--primary-dark);
}

/* Tooltip Animations */
[data-tooltip] {
    position: relative;
}

[data-tooltip]::before {
    content: attr(data-tooltip);
    position: absolute;
    bottom: 100%;
    left: 50%;
    transform: translateX(-50%) scale(0);
    padding: 8px 12px;
    background: var(--bg-dark);
    color: var(--text-primary);
    border-radius: 4px;
    font-size: 12px;
    opacity: 0;
    transition: all 0.3s ease;
    pointer-events: none;
    white-space: nowrap;
}

[data-tooltip]:hover::before {
    transform: translateX(-50%) scale(1);
    opacity: 1;
}

/* Loading Skeleton Animation */
@keyframes skeletonLoading {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}

.skeleton {
    background: linear-gradient(90deg, var(--bg-card) 25%, var(--primary-light) 50%, var(--bg-card) 75%);
    background-size: 200% 100%;
    animation: skeletonLoading 1.5s infinite;
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
