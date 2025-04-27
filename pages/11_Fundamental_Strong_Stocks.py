import streamlit as st
import pandas as pd
from tradingview_screener import Query, Column
import yfinance as yf

st.set_page_config(
    page_title="Fundamentally Strong Stocks",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.title("📊 Fundamentally Strong Stocks (NSE)")
st.caption("Stocks filtered by robust fundamentals: positive growth, low debt, and strong profitability.")

st.markdown('''
    <style>
    body, .main, .block-container {
        background: #181c22 !important;
        color: #fff !important;
    }
    /* Glassmorphism panel */
    .glass-panel {
        background: rgba(24,28,34,0.7);
        border-radius: 18px;
        box-shadow: 0 8px 32px 0 rgba(31,38,135,0.37);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        border: 1.5px solid rgba(255,255,255,0.18);
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
        background: rgba(40,44,52,0.85) !important;
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
        background: #21242b !important;
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
        checked = st.checkbox(label + ' >', key=f'chk_{col}_{i}')
        val = st.number_input(f"", value=None, step=0.1, key=f'inp_{col}_{i}') if checked else None
        user_growth_filters.append((col, val) if checked and val is not None else None)

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

# Add ROE range filter for negative only selection
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
# --- Sequential & Special Filters ---
seq_filters = [
    ("Net Profit Last", resolve_field('net_income'), 'last_positive', 1, "Quarters is +ve"),
    ("Net Profit Increasing For Past (Quarters)", resolve_field('net_income'), 'increasing', 2, "Quarters"),
    ("OPM Increasing For Past (Quarters)", resolve_field('operating_margin'), 'increasing', 2, "Quarters"),
    ("Include only stocks with latest(Mar 2025) quarterly results", None, 'latest_quarter', None, None),
    ("EPS Increasing For Past (Quarters)", resolve_field('earnings_per_share_diluted_ttm'), 'increasing', 2, "Quarters"),
    ("Sales Increasing For Past (Quarters)", resolve_field('total_revenue_yoy_growth_ttm'), 'increasing', 2, "Quarters"),
    ("Turn Around in Quarterly Net Profits (-ve to +ve)", resolve_field('net_income'), 'turnaround', None, None),
    ("Include only stocks with positive QoQ change", resolve_field('qoq_positive'), 'qoq_positive', None, None),
    ("Is EPS Last Year Greater Than Preceding Year", resolve_field('last_annual_eps'), 'eps_annual_gt_prev', None, None)
]
left_seq, right_seq = st.columns(2)

# --- Net Profit Last (Quarters is +ve) Sequential Filter ---
# (Temporarily disabled: checkbox and logic removed as per user request)
# (To re-enable, uncomment logic below and restore checkbox in UI)

seq_filter_states = {}
for i, (label, col, typ, default, suffix) in enumerate(seq_filters):
    target_col = left_seq if i % 2 == 0 else right_seq
    with target_col:
        # Disable checkbox for 'Net Profit Last' temporarily
        if label == 'Net Profit Last':
            st.markdown(f'<span style="color:grey">{label} (temporarily disabled)</span>', unsafe_allow_html=True)
            continue
        checked = st.checkbox(label, key=f'seqchk_{label}')
        if checked:
            val = None
            if typ in ["last_positive", "increasing"]:
                val = st.selectbox("", options=list(range(1, 9)), index=(default-1 if default else 0), key=f'seqnum_{label}')
                if suffix:
                    st.markdown(f"<span style='margin-left: 8px;'>{suffix}</span>", unsafe_allow_html=True)
            elif typ == "qoq_positive":
                val = st.selectbox("", options=["FII", "DII", "Promoter", "All"], index=0, key=f'seqqoq_{label}')
            seq_filter_states[label] = (typ, col, val)

# Note: Actual implementation of these filters on the DataFrame will require historical data or additional logic, which is not included here.
# You can scaffold the logic for these filters as needed based on available data.

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

    # --- Apply Sequential & Special Filters ---
    # (Net Profit Last (Quarters is +ve) filter DISABLED as per user request)
    # if 'Net Profit Last' in seq_filter_states:
    #     typ, col, val = seq_filter_states['Net Profit Last']
    #     if typ == 'last_positive' and val:
    #         if 'net_income' not in query.query['columns']:
    #             query.query['columns'].append('net_income')
    #         def last_n_quarters_positive(row):
    #             for i in range(val):
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
