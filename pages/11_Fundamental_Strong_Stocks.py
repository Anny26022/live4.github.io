import streamlit as st
import pandas as pd
from tradingview_screener import Query, Column
import yfinance as yf

st.set_page_config(
    page_title="Fundamental Strong Stocks",
    page_icon="",
    layout="centered",
    initial_sidebar_state="auto"
)

st.markdown("""
<div style='display:flex;align-items:center;justify-content:center;margin-bottom:0.5em;'>
  <svg xmlns='http://www.w3.org/2000/svg' width='48' height='48' viewBox='0 0 48 48' fill='none' style='margin-right:16px;'>
    <rect width='48' height='48' rx='12' fill='url(#fund-bg)'/>
    <g>
      <path d='M24 14v10l8 5' stroke='#43a047' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/>
      <circle cx='24' cy='14' r='3' fill='#43a047'/>
      <circle cx='32' cy='29' r='3' fill='#ab47bc'/>
      <circle cx='16' cy='29' r='3' fill='#29b6f6'/>
    </g>
    <defs>
      <linearGradient id='fund-bg' x1='0' y1='0' x2='48' y2='48' gradientUnits='userSpaceOnUse'>
        <stop stop-color='#23272F'/>
        <stop offset='1' stop-color='#181A20'/>
      </linearGradient>
    </defs>
  </svg>
  <span style='font-size:2.5rem;font-weight:700;color:#fff;'>Fundamental Strong Stocks</span>
</div>
<p style='text-align:center;margin-top:-0.75em;margin-bottom:2em;color:#aaa;font-size:1.1rem;'>Discover fundamentally strong stocks in the market</p>
""", unsafe_allow_html=True)

st.markdown('''
    <style>
    body, .main, .block-container {
        background: #fff !important;
        color: #222 !important;
    }
    /* Glassmorphism panel */
    .glass-panel {
        background: rgba(240, 244, 248, 0.85);
        border-radius: 18px;
        box-shadow: 0 8px 32px 0 rgba(31,38,135,0.10);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        border: 1.5px solid #e0e7ef;
        padding: 2.5rem 2rem 1.5rem 2rem;
        margin-bottom: 2.5rem;
        animation: glassFadeIn 1.2s cubic-bezier(.42,0,.58,1);
    }
    @keyframes glassFadeIn {
        from { opacity: 0; transform: translateY(-30px) scale(0.97); }
        to { opacity: 1; transform: translateY(0) scale(1); }
    }
    /* Material UI inspired multiselect */
    div[data-baseweb="select"] {
        min-height: 38px !important;
        font-size: 1rem !important;
        border-radius: 12px !important;
        background: #fff !important;
        border: 2px solid #00e5ff !important;
        box-shadow: 0 2px 12px 0 rgba(0,229,255,0.09);
        transition: border 0.3s, box-shadow 0.3s;
        animation: popIn 0.8s cubic-bezier(.42,0,.58,1);
    }
    @keyframes popIn {
        from { opacity: 0; transform: scale(0.95); }
        to { opacity: 1; transform: scale(1); }
    }
    div[data-baseweb="select"]:hover {
        border: 2px solid #ffeb3b !important;
        box-shadow: 0 4px 18px 0 rgba(255,235,59,0.13);
    }
    /* Strong specificity for tag pill color */
    div[data-baseweb="select"] div[data-baseweb="tag"],
    div[data-baseweb="select"] div[data-baseweb="tag"] span,
    div[data-baseweb="tag"] {
        background: linear-gradient(90deg,#e0f7fa,#b2ebf2) !important;
        background-color: #e0f7fa !important;
        color: #222 !important;
        border-radius: 8px !important;
        font-size: 1rem !important;
        box-shadow: 0 2px 6px 0 rgba(41,121,255,0.08);
        animation: pillPop 0.6s cubic-bezier(.42,0,.58,1);
        border: 1.5px solid #4dd0e1 !important;
    }
    @keyframes pillPop {
        from { opacity: 0; transform: scale(0.7); }
        to { opacity: 1; transform: scale(1); }
    }
    /* Option hover */
    div[data-baseweb="option"]:hover {
        background: #f0f4f8 !important;
        color: #00e5ff !important;
        font-weight: bold;
    }
    /* Label styling */
    label[for^='Choose columns'] {
        color: #00e5ff !important;
        font-weight: 700;
        font-size: 1.12rem;
        letter-spacing: 0.02em;
        text-shadow: 0 1px 8px #2979ff44;
        margin-bottom: 0.2em;
    }
    /* Emoji and icon styling */
    .emoji-label {
        font-size: 1.25rem;
        margin-right: 0.45em;
        vertical-align: middle;
        filter: drop-shadow(0 1px 7px #00e5ff55);
    }
    </style>
''', unsafe_allow_html=True)

# --- Fundamental Columns Selection ---
ALL_FUNDAMENTAL_COLUMNS = [
    'name',
    'close',
    'exchange',
    'sector',
    'industry',
    'earnings_per_share_basic_ttm',
    'basic_eps_net_income',
    'earnings_per_share_diluted_yoy_growth_fy',
    'last_annual_eps',
    'earnings_per_share_fq',
    'earnings_per_share_diluted_qoq_growth_fq',
    'earnings_per_share_diluted_yoy_growth_fq',
    'earnings_per_share_diluted_ttm',
    'earnings_per_share_diluted_yoy_growth_ttm',
    'earnings_per_share_forecast_next_fq',
    'eps_diluted_growth_percent_fq',
    'eps_diluted_growth_percent_fy',
    'eps_surprise_fq',
    'eps_surprise_percent_fq',
    'net_income_yoy_growth_fy',
    'net_income',
    'net_income_qoq_growth_fq',
    'net_income_yoy_growth_fq',
    'net_income_yoy_growth_ttm',
    'total_revenue_yoy_growth_fy',
    'revenue_per_employee',
    'total_revenue_qoq_growth_fq',
    'total_revenue_yoy_growth_fq',
    'total_revenue_yoy_growth_ttm',
    'operating_margin',
    'operating_margin_ttm',
    'return_on_equity',
    'return_on_invested_capital',
    'price_earnings_ttm',
    'debt_to_equity',
    'earnings_release_date',
    'earnings_release_next_date',
]

# --- Short Form to TradingView Field Mapping ---
SHORT_TO_TV_FIELD = {
    "de": "debt_to_equity",
    "peg": "peg_ratio",
    "opm": "operating_margin_ttm",
    "roce": "return_on_invested_capital",
    "roe": "return_on_equity",
    "pe": "price_earnings_ttm",
}

def resolve_field(field):
    """Resolve short form to TradingView field name if present."""
    return SHORT_TO_TV_FIELD.get(field, field)

st.markdown('### Select Fundamental Columns')
def_col_defaults = [
    'name', 'close', 'exchange', 'sector', 'industry',
    'earnings_per_share_basic_ttm', 'net_income', 'total_revenue_yoy_growth_fy',
    'operating_margin', 'return_on_equity', 'price_earnings_ttm', 'debt_to_equity'
]
selected_columns = st.multiselect(
    'Choose columns to include in the scan:',
    options=ALL_FUNDAMENTAL_COLUMNS,
    default=def_col_defaults,
    help='Select the fundamental columns you want to fetch and display.'
)

st.markdown('### Select Exchange')
# --- Exchange Selection ---
EXCHANGES = [
    ("NSE (India)", "NSE", "india"),
    ("BSE (India)", "BSE", "india"),
]
exchange_display_names = [x[0] for x in EXCHANGES]
def_exchange = "NSE (India)"
selected_exchange_display = st.selectbox(
    "Select Exchange:",
    options=exchange_display_names,
    index=0,
    help="Choose the exchange to scan for fundamentally strong stocks."
)
selected_exchange, selected_market = None, None
for display, exch, market in EXCHANGES:
    if display == selected_exchange_display:
        selected_exchange = exch
        selected_market = market
        break

st.markdown('''
<div style="padding: 1em; margin-bottom: 1em; border-radius: 12px; background: rgba(255, 193, 7, 0.13); border: 2px solid #ffc107; text-align: center; color: #ffc107; font-size: 1.1rem; font-weight: 600;">
🚧 Only the first four Growth Filters are currently available. The rest are under development and will be enabled soon!
</div>
''', unsafe_allow_html=True)

st.markdown('### Growth Filters (Optional)')
# --- Growth Filters (QoQ/YoY, EPS/Net Profit/Sales/OPM) ---
growth_filters = [
    ("EPS Diluted Quarterly QoQ Growth", resolve_field('earnings_per_share_diluted_qoq_growth_fq'), 0),
    ("EPS Diluted Quarterly YoY Growth", resolve_field('earnings_per_share_diluted_yoy_growth_fq'), 0),
    ("QoQ% Net Profit Growth", resolve_field('net_income_qoq_growth_fq'), 0),
    ("YoY% Net Profit Growth", resolve_field('net_income_yoy_growth_fq'), 0),
    ("QoQ% Sales Growth", resolve_field('total_revenue_qoq_growth_fq'), 0),
    ("QoQ% OPM Growth", resolve_field('operating_margin'), 0),
    ("YoY% Quartely EPS Growth", resolve_field('earnings_per_share_diluted_yoy_growth_fq'), 0),
    ("YoY% Quartely Sales Growth", resolve_field('total_revenue_yoy_growth_fq'), 0),
    ("YoY% Quartely OPM Growth", resolve_field('operating_margin_ttm'), 0),
]

left, right = st.columns(2)
user_growth_filters = []
for i, (label, col, default) in enumerate(growth_filters):
    target_col = left if i % 2 == 0 else right
    with target_col:
        # Only enable first two left and first two right options (indices 0, 1, 2, 3)
        if i in [0, 1, 2, 3]:
            checked = st.checkbox(label + ' >', key=f'chk_{col}_{i}')
            val = st.number_input(f"", value=None, step=0.1, key=f'inp_{col}_{i}') if checked else None
            user_growth_filters.append((col, val) if checked and val is not None else None)
        else:
            st.checkbox(
                label + ' >',
                value=False,
                key=f'chk_{col}_{i}',
                disabled=True,
                help='This filter is under development. Filters will be available soon.'
            )
            user_growth_filters.append(None)


st.markdown('### Advanced Fundamental Filters (Optional)')
# --- Advanced Fundamental Filters ---
adv_filters = [
    # label, df column(s), input type, default(s), extra
    ("Sales Growth 5 Years(%) >", resolve_field('revenue_growth_5y'), 'number', 0, {}),
    ("ROCE(%) >", resolve_field('roce'), 'number', 0, {}),
    ("P/E Range", resolve_field('pe'), 'range', (0, 500), {}),
    ("0 < PEG < 1", resolve_field('peg'), 'range', (0, 1), {}),
    ("ROE(%) >", resolve_field('roe'), 'number', 0, {}),
    ("OPM TTM(%) >", resolve_field('opm'), 'number', 0, {}),
    ("D/E", resolve_field('de'), 'max', 1, {}),
]
left_adv, right_adv = st.columns(2)
adv_filter_states = {}
for i, (label, col, typ, default, extra) in enumerate(adv_filters):
    target_col = left_adv if i % 2 == 0 else right_adv
    with target_col:
        if label.startswith("Sales Growth 5 Years(%"):
            st.checkbox(
                label + '  🛠️',
                value=False,
                key=f'advchk_{col}',
                disabled=True,
                help='This filter is under development.'
            )
        else:
            checked = st.checkbox(label, key=f'advchk_{col}')
            if checked:
                if typ == 'number':
                    val = st.number_input("", value=None, step=0.1, key=f'advnum_{col}')
                    if val is not None:
                        adv_filter_states[col] = ('gt', val)
                elif typ == 'range':
                    minv, maxv = st.columns(2)
                    with minv:
                        minval = st.number_input("", value=None, step=0.1, key=f'advmin_{col}')
                    with maxv:
                        maxval = st.number_input("", min_value=minval if minval is not None else None, value=None, step=0.1, key=f'advmax_{col}')
                    if minval is not None and maxval is not None:
                        adv_filter_states[col] = ('range', (minval, maxval))
                elif typ == 'max':
                    val = st.number_input("", value=None, step=0.01, key=f'advmax_{col}')
                    if val is not None:
                        adv_filter_states[col] = ('lt', val)
roe_range = st.checkbox("Filter ROE between two values (e.g. -5 and 0)", key="roe_range")
roe_min, roe_max = None, None
if roe_range:
    roe_min, roe_max = st.columns(2)
    with roe_min:
        roe_min_val = st.number_input("ROE min", value=-5.0, step=0.1, key="roe_min_val")
    with roe_max:
        roe_max_val = st.number_input("ROE max", value=0.0, step=0.1, key="roe_max_val")
    adv_filter_states['roe_range'] = ('range', (roe_min_val, roe_max_val))
st.markdown('### Sequential & Special Filters (Optional)')

# --- Sequential & Special Filters section is under development banner ---
st.markdown('''
<div style="padding: 1.5em; margin: 1.5em 0; border-radius: 14px; background: rgba(255, 193, 7, 0.13); border: 2px solid #ffc107; text-align: center; color: #ffc107; font-size: 1.2rem; font-weight: 600;">
🚧 This section is under development.<br>Filters will be available soon!
</div>
''', unsafe_allow_html=True)

# Show all Sequential & Special Filter options as disabled checkboxes
seq_filters = [
    ("Net Profit Last (temporarily disabled)", None),
    ("OPM Increasing For Past (Quarters)", None),
    ("EPS Increasing For Past (Quarters)", None),
    ("Turn Around in Quarterly Net Profits (-ve to +ve)", None),
    ("Is EPS Last Year Greater Than Preceding Year", None),
    ("Net Profit Increasing For Past (Quarters)", None),
    ("Include only stocks with latest(Mar 2025) quarterly results", None),
    ("Sales Increasing For Past (Quarters)", None),
    ("Include only stocks with positive QoQ change", None),
]
left_seq, right_seq = st.columns(2)
for i, (label, _) in enumerate(seq_filters):
    target_col = left_seq if i % 2 == 0 else right_seq
    with target_col:
        st.checkbox(label, value=False, disabled=True)

# Ensure these columns are always included in the TradingView query
REQUIRED_COLUMNS = [
    'earnings_per_share_diluted_qoq_growth_fq',
    'earnings_per_share_diluted_yoy_growth_fq',
    'net_income_qoq_growth_fq',
    'net_income_yoy_growth_fq',
]

with st.spinner("Running fundamental scan..."):
    query = (
        Query()
        .set_markets(selected_market)
        .select(*selected_columns)
        .where(
            Column('exchange') == selected_exchange,
            Column('type') == 'stock'
        )
        .limit(20000)
    )
    # Add required columns to the query columns if not already present
    current_cols = set(query.query.get('columns', []))
    for col in REQUIRED_COLUMNS:
        if col not in current_cols:
            query.query['columns'].append(col)
    count, df = query.get_scanner_data()

# Post-fetch filters for complex conditions
if not df.empty:
    # (Removed debug output for DataFrame columns as per user request)
    # Only use columns that are in the DataFrame
    for filt in user_growth_filters:
        if filt:
            col, val = filt
            if col in df.columns and val is not None:
                df = df[df[col] > val]
    for col, cond in adv_filter_states.items():
        if col in df.columns or col == 'roe_range':
            if col == 'roe_range' and cond[0] == 'range':
                df = df[(df['return_on_equity'] > cond[1][0]) & (df['return_on_equity'] < cond[1][1])]
            elif cond[0] == 'gt' and cond[1] is not None:
                df = df[df[col] > cond[1]]
            elif cond[0] == 'lt' and cond[1] is not None:
                df = df[df[col] < cond[1]]
            elif cond[0] == 'range' and cond[1][0] is not None and cond[1][1] is not None:
                df = df[(df[col] > cond[1][0]) & (df[col] < cond[1][1])]

    # --- Sequential & Special Filters logic temporarily disabled as section is under development ---
    # (All filter logic for this section is omitted)

    #                 colname = f'net_income_fq_{i}'
    #                 if colname in row:
    #                     if (row.get(colname, 0) or 0) <= 0:
    #                         return False
    #                 elif 'net_income' in row:
    #                     if (row.get('net_income', 0) or 0) <= 0:
    #                         return False
    #                 else:
    #                     return False
    #             return True
    #         df = df[df.apply(last_n_quarters_positive, axis=1)]

    st.success(f"Showing {len(df)} fundamentally strong {selected_exchange} stocks.")
    st.dataframe(df, use_container_width=True)
else:
    st.warning("No stocks matched the fundamental criteria. Try adjusting your filters or check back later.")

st.markdown("---")
st.caption("Note: For sequential growth (e.g., EPS increasing for past 2 quarters), additional historical data and logic would be required.")
