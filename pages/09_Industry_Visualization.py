import streamlit as st
import pandas as pd
from tradingview_screener import Query, col, Column
import plotly.express as px
from pages.price_bands import fetch_price_bands
from scipy.stats import zscore

st.set_page_config(
    page_title="Industry Visualization",
    page_icon="",
    layout="centered",
    initial_sidebar_state="auto"
)

# Page Header with modern SVG (Material: Pie Chart)
st.markdown("""
<div style='display:flex;align-items:center;justify-content:center;margin-bottom:0.5em;'>
  <svg xmlns='http://www.w3.org/2000/svg' width='48' height='48' viewBox='0 0 48 48' fill='none' style='margin-right:16px;'>
    <rect width='48' height='48' rx='12' fill='url(#pie-bg)'/>
    <g>
      <path d='M24 8a16 16 0 1 1-16 16h16z' fill='#ab47bc'/>
      <path d='M24 8v16h16A16 16 0 0 0 24 8z' fill='#43a047'/>
      <path d='M24 8v16H8A16 16 0 0 1 24 8z' fill='#29b6f6'/>
    </g>
    <defs>
      <linearGradient id='pie-bg' x1='0' y1='0' x2='48' y2='48' gradientUnits='userSpaceOnUse'>
        <stop stop-color='#23272F'/>
        <stop offset='1' stop-color='#181A20'/>
      </linearGradient>
    </defs>
  </svg>
  <span style='font-size:2.5rem;font-weight:700;color:#fff;'>Industry Visualization</span>
</div>
<p style='text-align:center;margin-top:-0.75em;margin-bottom:2em;color:#aaa;font-size:1.1rem;'>Visualize industry trends and sector performance</p>
""", unsafe_allow_html=True)

# --- Glassmorphism UI/UX Redesign (Compact Version) ---
st.markdown("""
<style>
body, .stApp {
    background: #181c24 !important;
}
.glass-card {
    background: rgba(30, 33, 43, 0.74);
    border-radius: 14px;
    box-shadow: 0 4px 18px 0 rgba(31, 38, 135, 0.27);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    border: 1px solid rgba(255, 255, 255, 0.13);
    padding: 1.2rem 1.1rem 1.1rem 1.1rem;
    margin-bottom: 1.1rem;
    margin-top: 0.5rem;
    max-width: 100%;
}
.glass-title {
    color: #fff;
    font-size: 1.45rem;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-shadow: 0 1px 10px #0007;
    margin-bottom: 0.32em;
    font-family: 'Segoe UI', 'Roboto', sans-serif;
}
.glass-subtitle {
    color: #b0b8c5;
    font-size: 0.97rem;
    font-weight: 400;
    margin-bottom: 1.1em;
    font-family: 'Segoe UI', 'Roboto', sans-serif;
}
.stNumberInput>div>input, .stSelectbox>div>div>div>input, .stSelectbox>div>div>div>div {
    background: rgba(255,255,255,0.10) !important;
    border-radius: 6px !important;
    color: #fff !important;
    border: 1px solid #23293b !important;
    font-size: 0.98rem !important;
    padding: 0.25rem 0.7rem !important;
    height: 2.1rem !important;
}
.stNumberInput>div>input:focus, .stSelectbox>div>div>div>input:focus {
    border: 1.2px solid #80cbc4 !important;
}
.stNumberInput label, .stSelectbox label {
    color: #b0b8c5 !important;
    font-weight: 500 !important;
    font-size: 0.92rem !important;
    margin-bottom: 0.25rem !important;
}
.stPlotlyChart>div>div>svg {
    font-family: 'Segoe UI', 'Roboto', sans-serif !important;
}
</style>
<div class='glass-card'>
    <div class='glass-title'>NSE Industry-wise Visualization</div>
    <div class='glass-subtitle'>Explore the distribution of NSE stocks by industry using TradingView Screener API. Use the filters below to customize your view.</div>
</div>
""", unsafe_allow_html=True)

with st.container():
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns([1.1, 1.1, 1.1, 1])
    with col1:
        returns_type = st.selectbox(
            "Returns Type:",
            ["1 Day Return", "1 Week Return", "1 Month Return"],
            index=0,
            key="returns_type"
        )
    with col2:
        market_cap_min = st.number_input("Market Cap (Cr.) >", min_value=0, value=999, step=1, key="market_cap_min")
    with col3:
        stock_return_min = st.number_input("Stock Return(%) >", min_value=0.0, value=5.0, step=0.1, key="stock_return_min")
    with col4:
        min_industry_count = st.number_input("No. of stock in Industry >=", min_value=1, value=2, step=1, key="min_industry_count")
    st.markdown("</div>", unsafe_allow_html=True)

# --- Fetch all NSE stocks via TradingView API (reference: 03_Custom_EMA_Scanner) ---
with st.spinner("Fetching all NSE stocks via TradingView API..."):
    try:
        # Map returns_type to TradingView column
        returns_col_map = {
            "1 Day Return": "change",
            "1 Week Return": "Perf.W",
            "1 Month Return": "Perf.1M"
        }
        returns_col = returns_col_map[returns_type]
        q = (
            Query()
            .set_markets('india')
            .select('name', 'industry', 'sector', 'exchange', 'type', 'market_cap_basic', returns_col)
            .where(
                col('exchange') == 'NSE',
                col('type') == 'stock',
                Column('market_cap_basic') > (market_cap_min * 1e7),
                Column(returns_col) > stock_return_min
            )
            .limit(20000)
        )
        count, df = q.get_scanner_data()

        # --- Apply price band filter (only 10%, 20%, 5%, No Band) ---
        price_bands_df, _ = fetch_price_bands()
        allowed_bands = [10.0, 20.0, 5.0]
        allowed_symbols = price_bands_df[price_bands_df['Band'].isin(allowed_bands)]['Symbol'].tolist()
        no_band_symbols = price_bands_df[price_bands_df['Band'].isna()]['Symbol'].tolist()
        allowed_symbols += no_band_symbols
        df = df[df['name'].isin(allowed_symbols)]
        df = df.merge(price_bands_df.rename(columns={'Symbol': 'name'}), on='name', how='left')
        df['Band'] = df['Band'].apply(lambda x: f"{int(x)}%" if pd.notnull(x) else "No Band")
    except Exception as e:
        st.error(f"Failed to fetch data: {e}")
        df = pd.DataFrame()

if not df.empty:
    df = df[df['industry'].notna() & (df['industry'] != '')]
    # Filter by minimum number of stocks in industry
    industry_counts = df['industry'].value_counts()
    valid_industries = industry_counts[industry_counts >= min_industry_count].index
    df = df[df['industry'].isin(valid_industries)]

    # --- Custom-styled Toggle for Industry/Sector visualization (Streamlit-native) ---
    st.markdown("""
    <style>
    .custom-radio-row {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        margin-bottom: 0.5rem;
        margin-top: -0.4rem;
    }
    .custom-radio .stRadio > div {
        display: flex !important;
        gap: 0.7rem !important;
        background: rgba(30,30,30,0.68);
        border-radius: 2rem;
        padding: 0.18rem 0.5rem;
        box-shadow: 0 2px 8px rgba(41,98,255,0.08);
        border: 1px solid #222;
        font-size: 1.07rem;
        min-width: 180px;
        max-width: 260px;
        margin-left: auto;
    }
    .custom-radio .stRadio label {
        display: flex;
        align-items: center;
        font-weight: 500;
        color: #fff;
        cursor: pointer;
        padding: 0.15rem 0.7rem;
        border-radius: 1.2rem;
        transition: background 0.18s, color 0.18s;
        font-size: 1.06rem;
    }
    .custom-radio .stRadio input[type=\"radio\"] {
        accent-color: #1de9b6;
        margin-right: 0.38em;
        width: 1.1em;
        height: 1.1em;
        border-radius: 50%;
        border: 2px solid #3949ab;
        background: #23272f;
    }
    .custom-radio .stRadio label[data-baseweb=\"radio\"]:has(input[type=\"radio\"]:checked) {
        background: #1de9b6;
        color: #23272f;
    }
    @media (max-width: 700px) {
        .custom-radio .stRadio > div {
            font-size: 0.97rem;
            padding: 0.09rem 0.18rem;
            min-width: 120px;
        }
        .custom-radio-row { margin-bottom: 0.2rem; }
    }
    </style>
    """, unsafe_allow_html=True)
    st.markdown('<div class="custom-radio-row custom-radio">', unsafe_allow_html=True)
    # Only use ONE source of truth for the toggle state
    default_toggle = st.session_state.get('industry_sector_toggle', 'Industry')
    viz_type = st.radio(
        '',
        options=['Industry', 'Sector'],
        index=0 if default_toggle == 'Industry' else 1,
        key='industry_sector_toggle_radio',
        horizontal=True,
        help='Switch between Industry and Sector view',
        label_visibility='collapsed',
    )
    st.session_state['industry_sector_toggle'] = viz_type
    st.markdown('</div>', unsafe_allow_html=True)
    # --- Select grouping column based on toggle ---
    group_col = 'industry' if viz_type == 'Industry' else 'sector'
    group_label = 'Industry' if viz_type == 'Industry' else 'Sector'

    icon_svg = '''<svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="vertical-align:middle;margin-right:8px;"><rect x="2.5" y="13.5" width="4" height="8" rx="1.5" fill="#1de9b6"/><rect x="9.5" y="9.5" width="4" height="12" rx="1.5" fill="#2962ff"/><rect x="16.5" y="4.5" width="4" height="17" rx="1.5" fill="#ff4081"/></svg>'''
    st.markdown(f"""
    <div style='display:flex;align-items:center;margin-bottom:0.5rem;'>
        {icon_svg}
        <span style='font-size:1.6rem;font-weight:700;color:white;'>Max Stock Return by {group_label} (Histogram)</span>
    </div>
    """, unsafe_allow_html=True)

    hist_df = df[[group_col, 'name', returns_col]].copy()
    hist_df = hist_df.rename(columns={group_col: group_label, 'name': 'Stock', returns_col: 'Return'})
    # Find max return per group
    max_per_group = hist_df.groupby(group_label).apply(lambda x: x.loc[x['Return'].idxmax()]).reset_index(drop=True)
    # X-axis: group (with % of total stocks in group)
    group_sizes = df[group_col].value_counts(normalize=True) * 100
    max_per_group[f'{group_label}Label'] = max_per_group[group_label] + ' (' + max_per_group[group_label].map(lambda x: f"{group_sizes[x]:.1f}".rstrip('0').rstrip('.') if group_sizes[x] % 1 else str(int(group_sizes[x]))) + '%)'

    # --- Custom hovertemplate (compact, with percent formatting) ---
    def build_hovertemplate(row):
        stocks = hist_df[hist_df[group_label] == row[group_label]].sort_values('Return', ascending=False)
        percent = group_sizes[row[group_label]]
        percent_str = f"{percent:.1f}".rstrip('0').rstrip('.') if percent % 1 else str(int(percent))
        lines = [
            f"<span style='font-size:13px'><b>{row[group_label]}</b> <span style='color:#aaa'>({percent_str}%)</span></span>",
            f"<span style='font-size:12px;color:#1de9b6'><b>Max: {row['Return']:.1f}%</b></span>"
        ]
        for _, srow in stocks.head(6).iterrows():
            lines.append(f"<span style='color:#3949ab;font-size:12px'>{srow['Stock']}</span> <span style='font-size:12px'><b>{srow['Return']:.1f}%</b></span>")
        if len(stocks) > 6:
            lines.append(f"<span style='font-size:11px;color:#bbb'>+{len(stocks)-6} more...</span>")
        return '<br>'.join(lines)
    hovertext = max_per_group.apply(build_hovertemplate, axis=1)
    max_per_group = max_per_group.reset_index(drop=True)
    if len(hovertext.shape) == 1 and len(hovertext) == len(max_per_group):
        max_per_group['hovertext'] = hovertext
    else:
        max_per_group['hovertext'] = [''] * len(max_per_group)

    fig_hist = px.bar(
        max_per_group,
        x=f'{group_label}Label',
        y='Return',
        text='Stock',
        labels={f'{group_label}Label': f'% of Total Stocks in the {group_label}', 'Return': f'{returns_type} (%)'},
        color_discrete_sequence=['#1de9b6'],
        height=560
    )
    fig_hist.update_traces(
        width=0.22,
        textposition='outside',
        marker_line_width=1.1,
        marker_line_color='#23242a',
        hovertemplate='%{customdata[0]}'
    )
    fig_hist.update_traces(customdata=max_per_group[['hovertext']].values.tolist())
    fig_hist.update_layout(
        xaxis_title=f"{group_label} (% of Total Stocks in the {group_label})",
        yaxis_title=f"Return (%)",
        showlegend=False,
        margin=dict(t=44, b=68, l=24, r=24),
        xaxis_tickangle=-28,
        xaxis_tickfont=dict(size=12, family='Inter, sans-serif', color='#cbe8ff'),
        yaxis_tickfont=dict(size=12, family='Inter, sans-serif', color='#cbe8ff'),
        xaxis_title_font=dict(size=13, family='Inter, sans-serif', color='#fff'),
        yaxis_title_font=dict(size=13, family='Inter, sans-serif', color='#fff'),
        plot_bgcolor='#181A20',
        paper_bgcolor='#181A20',
        bargap=0.32,
        bargroupgap=0.18,
    )
    st.markdown('<div class="glass-card" style="padding:1.2rem 0.6rem 0.7rem 0.6rem;">', unsafe_allow_html=True)
    st.plotly_chart(fig_hist, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.warning("No industry data available to display.")
