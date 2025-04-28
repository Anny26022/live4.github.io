import streamlit as st
from tradingview_screener import Query, Column
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="NSE Stocks Analytical Treemap",
    page_icon="🌈",
    layout="centered",
    initial_sidebar_state="auto"
)

# Modern UI Styling
st.markdown("""
<style>
    /* Modern Color Variables */
    :root {
        --primary: #3b82f6;
        --primary-light: #60a5fa;
        --primary-dark: #2563eb;
        --accent: #f59e0b;
        --success: #10b981;
        --error: #ef4444;
        --animation-timing: cubic-bezier(0.4, 0, 0.2, 1);
        --animation-duration: 400ms;
    }

    /* Theme-aware colors */
    [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
        --bg-dark: var(--background-color);
        --bg-card: color-mix(in srgb, var(--background-color) 97%, white);
        --text-primary: var(--text-color);
        --text-secondary: color-mix(in srgb, var(--text-color) 80%, transparent);
        --border-color: color-mix(in srgb, var(--text-color) 20%, transparent);
        background-color: var(--bg-dark);
    }

    /* Remove Streamlit Branding */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* Modern Card Styling */
    .filter-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 0.75rem;
        padding: 1.25rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
    }

    .filter-title {
        font-size: 1rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid var(--border-color);
    }

    /* Header Section */
    .header-section {
        text-align: left;
        margin-bottom: 2rem;
        padding: 1.5rem 2rem;
        background: linear-gradient(135deg, var(--primary), var(--primary-dark));
        border-radius: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    .header-title {
        font-size: 2rem;
        font-weight: 700;
        color: white;
        margin: 0;
    }

    .header-subtitle {
        font-size: 1rem;
        color: rgba(255, 255, 255, 0.9);
        margin-top: 0.5rem;
    }

    /* Responsive Design */
    @media (max-width: 768px) {
        .header-section {
            padding: 1rem;
        }
        
        .header-title {
            font-size: 1.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Modern Header with SVG
st.markdown("""
<div class="header-section">
    <div class="header-title">NSE Stocks Analytical Treemap</div>
    <div class="header-subtitle">A compact, modern, and visually stunning treemap of all Indian NSE stocks. Quickly spot trends, outliers, and sector performance at a glance.</div>
</div>
""", unsafe_allow_html=True)

# --- User Controls in Cards ---
st.markdown('<div class="filter-card">', unsafe_allow_html=True)
st.markdown('<h3 class="filter-title">Performance Metrics</h3>', unsafe_allow_html=True)

# Expanded performance options based on TradingView Screener documentation
perf_options = {
    "Daily % Change": "change",
    "% Change (1W)": "change|1W",
    "% Change (1M)": "change|1M",
    "% Change (3M)": "Perf.3M",
    "% Change (6M)": "Perf.6M",
    "% Change (YTD)": "Perf.YTD",
    "% Change (1Y)": "Perf.Y",
    "% Change (5Y)": "Perf.5Y",
    "% Change (10Y)": "Perf.10Y",
    "% Change (All Time)": "Perf.All",
    "Volume": "volume",
    "Value Traded": "Value.Traded",
}

selected_perf = st.selectbox(
    "Select Performance Metric (color):",
    list(perf_options.keys()),
    index=0
)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="filter-card">', unsafe_allow_html=True)
st.markdown('<h3 class="filter-title">Market Cap Filter</h3>', unsafe_allow_html=True)
# Market cap filter
col1, col2 = st.columns(2)
with col1:
    min_mcap = st.number_input("Minimum Market Cap (Cr):", min_value=0.0, max_value=5000000.0, value=0.0, step=100.0, format="%.0f")
with col2:
    max_mcap = st.number_input("Maximum Market Cap (Cr):", min_value=0.0, max_value=5000000.0, value=5000000.0, step=100.0, format="%.0f")
st.markdown('</div>', unsafe_allow_html=True)

# --- User filter: Stock Price Range ---
st.markdown('<div class="filter-card">', unsafe_allow_html=True)
st.markdown('<h3 class="filter-title">Stock Price Range (₹)</h3>', unsafe_allow_html=True)
col_min, col_max = st.columns(2)
with col_min:
    min_price = st.number_input("Min Price", min_value=0, max_value=1000000, value=0)
with col_max:
    max_price = st.number_input("Max Price", min_value=0, max_value=1000000, value=1000000)
st.markdown('</div>', unsafe_allow_html=True)

# Add toggle for Top Gainers / Top Losers
show_gainers = st.radio(
    "Show:",
    ["Top Gainers", "Top Losers"],
    index=0,
    horizontal=True,
    key="gainer_loser_toggle"
)

# --- Feature 2: Group by Sector/Industry ---
group_by = st.selectbox(
    "Group Treemap By:",
    options=["None", "Sector", "Industry"],
    index=0,
    help="Choose how to group stocks in the treemap."
)

# --- Query NSE Stocks ---
# Use the expanded field list based on documentation
query_fields = [
    'name', 'close', 'change', 'volume', 'Value.Traded', 'market_cap_basic',
    'sector', 'industry',
    'Perf.W', 'Perf.1M', 'Perf.3M', 'Perf.6M', 'Perf.YTD', 'Perf.Y', 'Perf.5Y', 'Perf.10Y', 'Perf.All',
    'change|1W', 'change|1M',
]

query = (
    Query()
    .set_markets("india")
    .select(*query_fields)
    .where(Column("exchange") == "NSE", Column("is_primary") == True)
    .limit(20000)
)

# Get data from TradingView
with st.spinner("Loading NSE stock data..."):
    count, df = query.get_scanner_data()

# Rename columns for easier access
# Use correct mapping for market cap and other columns
# 'market_cap_basic' -> 'Market Cap', 'name' -> 'Stock Name', 'close' -> 'Close Price'
df = df.rename(columns={
    'name': 'Stock Name',
    'close': 'Close Price',
    'market_cap_basic': 'Market Cap',
    'sector': 'sector',
    'industry': 'industry',
})

# Check if required columns are present
# Map perf_options to actual column names in df
# e.g. 'Daily % Change' -> 'change', '% Change (1W)' -> 'change|1W', etc.
field = perf_options[selected_perf]
if field not in df.columns:
    st.error(f"Selected performance metric '{selected_perf}' (field '{field}') not found in data. Available columns: {list(df.columns)}")
    st.stop()

# Ensure required columns exist for treemap
required_cols = ['Stock Name', field, 'Market Cap']
missing_cols = [col for col in required_cols if col not in df.columns]
if missing_cols:
    st.error(f"Data missing required columns. Available columns: {list(df.columns)}. Required: {required_cols}")
    st.stop()

# Market cap filter (convert to crore if needed)
if 'Market Cap' in df.columns and df['Market Cap'].max() > 1e7:
    df['Market Cap'] = df['Market Cap'] / 1e7  # Convert to crore if in paise

# Filter by market cap
filtered_df = df[(df['Market Cap'] >= min_mcap) & (df['Market Cap'] <= max_mcap)]

# Filter by stock price (Close Price)
if 'Close Price' in df.columns:
    filtered_df = filtered_df[(filtered_df['Close Price'] >= min_price) & (filtered_df['Close Price'] <= max_price)]
else:
    st.warning("'Close Price' column not found in data. Stock price filter not applied.")

# Prepare path for treemap based on grouping
if group_by == "Sector" and 'sector' in filtered_df.columns:
    treemap_path = ['sector', 'Stock Name']
elif group_by == "Industry" and 'industry' in filtered_df.columns:
    treemap_path = ['industry', 'Stock Name']
else:
    treemap_path = ['Stock Name']

# Drop NA and ensure numeric for perf field
filtered_df = filtered_df.dropna(subset=[field, 'Market Cap', 'Stock Name'])
filtered_df = filtered_df[pd.to_numeric(filtered_df[field], errors='coerce').notnull()]

# Gainers/Losers logic
if show_gainers == "Top Gainers":
    filtered_df = filtered_df[filtered_df[field] > 0]
    box_sizes = filtered_df[field]
    color_scale = 'RdYlGn'
    color_args = {'color_continuous_scale': color_scale}
else:
    filtered_df = filtered_df[filtered_df[field] < 0]
    box_sizes = filtered_df[field].abs()
    color_scale = px.colors.sequential.Reds[::-1]  # Reverse Reds for deep red = max loss
    min_val = filtered_df[field].min() if not filtered_df.empty else -1
    max_val = filtered_df[field].max() if not filtered_df.empty else 0
    color_args = {
        'color_continuous_scale': color_scale,
        'range_color': (min_val, 0)
    }

# Create treemap with improved styling
fig = px.treemap(
    filtered_df,
    path=treemap_path,
    values=box_sizes,  # Use abs value for losers
    color=field,
    hover_data={
        'Stock Name': True,
        'Close Price': True,
        field: True,
        'Market Cap': True,
        'sector': True,
        'industry': True
    },
    title=f'NSE Stocks Treemap: {selected_perf}',
    height=900,
    **color_args
)
    
# Enhanced treemap styling
fig.update_layout(
    margin=dict(l=0, r=0, t=40, b=0),
    paper_bgcolor='#181A20',
    plot_bgcolor='#181A20',
    font=dict(color='#fff', family='Inter, sans-serif'),
    treemapcolorway=["#d62728", "#2ca02c", "#ff7f0e", "#1f77b4", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"],
    hoverlabel=dict(
        bgcolor="#181A20",
        font_size=14,
        font_family="Inter, sans-serif"
    )
)
    
# Custom hover template
fig.data[0].texttemplate = "%{label}<br>%{customdata[2]:+.2f}%"
fig.data[0].hovertemplate = (
    "<b>%{label}</b><br>" +
    "Close Price: ₹%{customdata[1]:,.2f}<br>" +
    f"{selected_perf}: %{{customdata[2]:+.2f}}%<br>" +
    "Market Cap: ₹%{customdata[3]:,.0f} Cr<br>" +
    "Sector: %{customdata[4]}<br>" +
    "Industry: %{customdata[5]}<extra></extra>"
)
    
st.plotly_chart(fig, use_container_width=True)
    
# Add summary statistics
st.markdown('<div class="filter-card">', unsafe_allow_html=True)
st.markdown('<h3 class="filter-title">Summary Statistics</h3>', unsafe_allow_html=True)
    
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Stocks", len(filtered_df))
with col2:
    avg_perf = filtered_df[field].mean()
    st.metric(f"Average {selected_perf}", f"{avg_perf:+.2f}%")
with col3:
    total_mcap = filtered_df['Market Cap'].sum()
    st.metric("Total Market Cap", f"₹{total_mcap:,.0f} Cr")
    
st.markdown('</div>', unsafe_allow_html=True)

# --- Feature 4: Export Data ---
st.markdown('---')
st.markdown('### Export Filtered Data')
st.download_button(
    label="Download CSV",
    data=filtered_df.to_csv(index=False),
    file_name="nse_filtered_data.csv",
    mime="text/csv"
)
