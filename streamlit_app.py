import streamlit as st
from src.tradingview_screener import Query, col
import pandas as pd
import inspect
import requests
from bs4 import BeautifulSoup
import logging
import time
import json
import io

# Feature flag to enable/disable animations
USE_ANIMATIONS = True

# Try to import streamlit-lottie, fall back gracefully if not available
try:
    from streamlit_lottie import st_lottie
    LOTTIE_AVAILABLE = True
except ImportError:
    LOTTIE_AVAILABLE = False
    USE_ANIMATIONS = False

# Set the page configuration with the new modern title and wide layout
st.set_page_config(
    page_title="TradingView Screener Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load our custom CSS
try:
    with open('style.css', encoding='utf-8') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except FileNotFoundError:
    # Check if CSS file is in the app directory
    try:
        with open('app/style.css', encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Style file not found. App will run with default styling.")

# Load animations
def load_lottieurl(url):
    if not USE_ANIMATIONS:
        return None
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception:
        return None

# Loading animation for data fetch
lottie_loading = load_lottieurl('https://assets2.lottiefiles.com/packages/lf20_x62chJ.json')
lottie_chart = load_lottieurl('https://assets4.lottiefiles.com/packages/lf20_49rdyysj.json')

# Helper function to create card containers
def card(title, content, icon="", is_sidebar=False):
    card_class = "custom-card"
    if icon:
        title = f"{icon} {title}"
    if is_sidebar:
        with st.sidebar:
            st.markdown(f"<div class='{card_class}'><h4>{title}</h4>{content}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='{card_class}'><h4>{title}</h4>{content}</div>", unsafe_allow_html=True)

# App title with animation or fallback image
col1, col2 = st.columns([3, 1])
with col1:
    st.title("TradingView Screener Pro")
    st.markdown("<p class='app-subtitle'>Advanced market screening with modern UI</p>", unsafe_allow_html=True)
with col2:
    if USE_ANIMATIONS and LOTTIE_AVAILABLE and lottie_chart:
        st_lottie(lottie_chart, height=120, key="chart_animation")
    else:
        # Fallback image if animation is not available
        st.markdown("<div style='text-align: center; padding-top: 20px;'><span style='font-size: 80px;'>📊</span></div>", unsafe_allow_html=True)

# Session state initialization
if 'query_results' not in st.session_state:
    st.session_state.query_results = None
    st.session_state.last_query_count = 0
    st.session_state.selected_tab = "build"

# Create tabs for better organization
tabs = st.tabs(["📝 Build Query", "📊 Results", "ℹ️ About"])

# About section in the About tab
with tabs[2]:
    # Title and Description
    st.title("TradingView Screener Pro")
    st.markdown("""
    TradingView Screener is a Python package for creating custom stock, crypto, forex, and asset screeners using TradingView's official API.
    It retrieves data directly from TradingView—no web scraping or HTML parsing required.
    """)

    # Key Features Section
    st.header("Key Features")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### 🔍 Over 3000 Fields")
        st.markdown("Access OHLC, indicators, fundamental metrics, and much more. Comprehensive data at your fingertips.")

        st.markdown("##### 🌍 Multiple Markets")
        st.markdown("Trade across stocks, crypto, forex, CFD, futures, bonds, and more. Global market coverage in one tool.")

        st.markdown("##### ⏰ Customizable Timeframes")
        st.markdown("Choose timeframes like 1 minute, 5 minutes, 1 hour, or 1 day for each field. Flexible time-based analysis.")

    with col2:
        st.markdown("##### 🎯 Advanced Filtering")
        st.markdown("Use SQL-like syntax with AND/OR operators for powerful, flexible queries. Find exactly what you're looking for.")

        st.markdown("##### 🔌 Direct API Access")
        st.markdown("Communicate with TradingView's /screener endpoint for robust, up-to-date data. Real-time market insights.")

    # Quickstart Section
    st.header("Quickstart Example")

    code = '''
from tradingview_screener import Query, col

# Create a simple stock screener
screener = (Query()
    .select('name', 'close', 'volume', 'market_cap_basic')
    .where(col('type') == 'stock')
    .where(col('exchange') == 'NASDAQ')
    .where(col('volume') > 1000000)
    .sort('market_cap_basic', 'desc')
    .limit(50))

# Get the results
count, data = screener.get_scanner_data()
    '''

    st.code(code, language='python')

    # Additional Resources
    st.header("Additional Resources")

    resources_col1, resources_col2 = st.columns(2)

    with resources_col1:
        st.markdown("#### 📚 Documentation")
        st.markdown("Comprehensive guides and API reference")
        if st.button("View Docs"):
            st.markdown("[Documentation](https://github.com/your-repo/docs)")

    with resources_col2:
        st.markdown("#### 💻 GitHub")
        st.markdown("Source code and contribution guidelines")
        if st.button("View Source"):
            st.markdown("[GitHub Repository](https://github.com/your-repo)")

    # Footer
    st.markdown("---")
    st.markdown("Built with ❤️ using Python and Streamlit")

# --- Sidebar: Help/Docs ---
st.sidebar.header("📖 Documentation")
doc_expander = st.sidebar.expander("Query methods", expanded=False)
with doc_expander:
    st.markdown(f"```python\n{inspect.getdoc(Query)}\n```")

doc_expander2 = st.sidebar.expander("Column operations", expanded=False)
with doc_expander2:
    st.markdown(f"```python\n{inspect.getdoc(col)}\n```")

# --- DYNAMIC QUERY BUILDER (REDESIGNED UI) ---
with tabs[0]:
    st.markdown('<div class="screener-container">', unsafe_allow_html=True)

    # Create a 2-column layout for the main content
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown('<h2 class="section-header">🛠️ Query Builder</h2>', unsafe_allow_html=True)

        # 1. Market selection
        def get_market_options():
            from src.tradingview_screener.markets_list import MARKETS
            return [(m[0], m[1]) for m in MARKETS]

        # Define instrument types
        INSTRUMENT_TYPES = {
            "stock": "Stocks",
            "dr": "ADRs/GDRs",
            "fund": "Funds/ETFs",
            "crypto": "Cryptocurrencies",
            "forex": "Forex",
            "futures": "Futures",
            "bond": "Bonds",
            "index": "Indices",
            "economic": "Economic Indicators",
            "cfd": "CFDs"
        }

        # Markets and Instruments selection
        st.markdown('<div class="market-selector">', unsafe_allow_html=True)
        st.markdown('<h3 class="section-header">1️⃣ Select Market & Instruments</h3>', unsafe_allow_html=True)

        # Two-column layout for market and instrument selection
        market_col, instrument_col = st.columns(2)

        with market_col:
            market_options = get_market_options()
            market_display_names = [m[0] for m in market_options]
            market_code_map = {m[0]: m[1] for m in market_options}
            selected_market = st.selectbox(
                "Market/Region",
                market_display_names,
                index=0,
                key="market_selector",
                help="Select the market or country region to search"
            )
            market_code = market_code_map[selected_market]

        with instrument_col:
            selected_types = st.multiselect(
                "Instrument Types",
                options=list(INSTRUMENT_TYPES.keys()),
                default=[],
                format_func=lambda x: INSTRUMENT_TYPES[x],
                help="Select one or more instrument types to include"
            )
        st.markdown('</div>', unsafe_allow_html=True)

        if not selected_types:
            st.warning("⚠️ Please select at least one instrument type to continue")
            st.stop()

        # 2. Fetch fields & exchanges dynamically
        @st.cache_data(show_spinner=False, ttl=60*60)
        def fetch_fields_for_market(market_code, instrument_type='stock'):
            """Fetch fields based on instrument type."""
            INSTRUMENT_FIELD_URLS = {
                'stock': 'stocks',
                'dr': 'stocks',
                'fund': 'stocks',
                'crypto': 'crypto',
                'forex': 'forex',
                'futures': 'futures',
                'bond': 'bonds',
                'index': 'stocks',
                'economic': 'economics2',
                'cfd': 'cfd',
                'coin': 'crypto',
                'option': 'options'
            }

            url_suffix = INSTRUMENT_FIELD_URLS.get(instrument_type, 'stocks')
            url = f"https://shner-elmo.github.io/TradingView-Screener/fields/{url_suffix}.html"

            try:
                with st.spinner(f"🔄 Fetching fields for {INSTRUMENT_TYPES[instrument_type]}..."):
                    resp = requests.get(url, timeout=5)
                    resp.raise_for_status()
                    soup = BeautifulSoup(resp.text, "html.parser")
                    fields = []
                    exchanges = set()

                    for row in soup.select("tr"):
                        cols = row.find_all("td")
                        if len(cols) >= 3:
                            field_name = cols[0].text.strip()
                            display_name = cols[1].text.strip()
                            field_type = cols[2].text.strip()
                            if not all([field_name, display_name, field_type]):
                                continue
                            fields.append({
                                "name": field_name,
                                "display": display_name,
                                "type": field_type,
                            })
                            if len(cols) > 3:
                                exchanges.update([e.strip() for e in cols[3].text.split(",") if e.strip()])

                    if not fields:
                        basic_fields = [
                            {"name": "name", "display": "Name", "type": "string"},
                            {"name": "description", "display": "Description", "type": "string"},
                            {"name": "type", "display": "Type", "type": "string"},
                            {"name": "exchange", "display": "Exchange", "type": "string"},
                            {"name": "close", "display": "Close", "type": "float"},
                            {"name": "volume", "display": "Volume", "type": "float"},
                        ]
                        st.warning(f"⚠️ No fields found for {INSTRUMENT_TYPES[instrument_type]}, using basic fields")
                        return basic_fields, []

                    st.success(f"✅ Successfully loaded {len(fields)} fields for {INSTRUMENT_TYPES[instrument_type]}")
                    return fields, sorted(list(exchanges))

            except Exception as e:
                st.error(f"❌ Error fetching fields: {str(e)}")
                return [
                    {"name": "name", "display": "Name", "type": "string"},
                    {"name": "description", "display": "Description", "type": "string"},
                    {"name": "type", "display": "Type", "type": "string"},
                    {"name": "exchange", "display": "Exchange", "type": "string"},
                    {"name": "close", "display": "Close", "type": "float"},
                    {"name": "volume", "display": "Volume", "type": "float"},
                ], []

        # Loading animation for field fetching
        with st.container():
            if USE_ANIMATIONS and LOTTIE_AVAILABLE and lottie_loading:
                loading_placeholder = st.empty()
                with loading_placeholder.container():
                    st_lottie(lottie_loading, height=200, key="loading_animation")
                    st.info("Loading data fields, please wait...")
            else:
                loading_placeholder = st.empty()

            try:
                all_fields = []
                all_exchanges = set()
                for instrument_type in selected_types:
                    type_fields, type_exchanges = fetch_fields_for_market(market_code, instrument_type)
                    for field in type_fields:
                        if field not in all_fields:
                            field["display"] = f"[{INSTRUMENT_TYPES[instrument_type]}] {field['display']}"
                            all_fields.append(field)
                    all_exchanges.update(type_exchanges)

                seen = set()
                fields = []
                for field in all_fields:
                    if field["name"] not in seen:
                        seen.add(field["name"])
                        fields.append(field)

                loading_placeholder.empty()
            except Exception as e:
                st.error(f"❌ Error fetching fields: {str(e)}")
                fields = [
                    {"name": "name", "display": "Name", "type": "string"},
                    {"name": "description", "display": "Description", "type": "string"},
                    {"name": "type", "display": "Type", "type": "string"},
                    {"name": "exchange", "display": "Exchange", "type": "string"},
                    {"name": "close", "display": "Close", "type": "float"},
                    {"name": "volume", "display": "Volume", "type": "float"},
                ]
                loading_placeholder.empty()

        # 3. Exchange selection
        HARDCODED_EXCHANGES = {
            'india': ['NSE', 'BSE'],
            'america': ['All'] + ['AMEX', 'CBOE', 'NASDAQ', 'NYSE', 'OTC'],
        }

        # Exchange and Column Selection
        st.markdown('<div class="market-selector">', unsafe_allow_html=True)
        st.markdown('<h3 class="section-header">2️⃣ Select Exchanges & Data Columns</h3>', unsafe_allow_html=True)
        exchange_col, column_col = st.columns(2)

        with exchange_col:
            if market_code.lower() == "india":
                selected_exchanges = st.multiselect(
                    "🏢 Select Exchanges",
                    options=HARDCODED_EXCHANGES['india'],
                    default=[],
                    key="exchange_multiselect_india",
                    help="Select one or more exchanges to filter by"
                )
            else:
                exchange_options = HARDCODED_EXCHANGES.get(market_code.lower(), [])
                selected_exchanges = st.multiselect(
                    "🏢 Select Exchanges",
                    options=exchange_options,
                    default=[],
                    key="exchange_multiselect_other",
                    help="Select one or more exchanges to filter by"
                )
                if "All" in selected_exchanges:
                    selected_exchanges = [ex for ex in exchange_options if ex != "All"]

        with column_col:
            name_to_field = {f["name"]: f for f in fields}
            def_field_names = ['name', 'description', 'type', 'exchange', 'close', 'volume']
            selected_instruments = st.multiselect(
                "📊 Select Data Columns",
                options=[f["name"] for f in fields],
                default=[name for name in def_field_names if name in name_to_field],
                format_func=lambda n: f"{name_to_field[n]['display']} [{name_to_field[n]['type']}]",
                help="Choose which columns to display in the results"
            )
        st.markdown('</div>', unsafe_allow_html=True)

        # 4. Filter Builder
        st.markdown('<div class="market-selector">', unsafe_allow_html=True)
        st.markdown('<h3 class="section-header">3️⃣ Build Your Filters</h3>', unsafe_allow_html=True)

        filter_ops = {
            "==": (lambda f, v: (f, "==", v), "Equal to"),
            ">": (lambda f, v: (f, ">", v), "Greater than"),
            "<": (lambda f, v: (f, "<", v), "Less than"),
            ">=": (lambda f, v: (f, ">=", v), "Greater than or equal"),
            "<=": (lambda f, v: (f, "<=", v), "Less than or equal"),
            "in": (lambda f, v: (f, "in", v), "In list (comma separated)")
        }

        num_filters = st.slider("Number of filters", min_value=0, max_value=5, value=0, step=1)

        filters = []
        if num_filters > 0:
            for i in range(num_filters):
                st.markdown(f'<div class="filter-card">', unsafe_allow_html=True)
                st.markdown(f"#### Filter {i+1}")

                field = st.selectbox(
                    f"Field",
                    [f["name"] for f in fields],
                    format_func=lambda n: f"{name_to_field[n]['display']} [{name_to_field[n]['type']}]",
                    key=f"filter_field_selectbox_{i}"
                )
                op = st.selectbox(
                    f"Operator",
                    list(filter_ops.keys()),
                    format_func=lambda x: filter_ops[x][1],
                    key=f"filter_op_selectbox_{i}"
                )

                val = st.text_input(f"Value", key=f"filter_val_{i}")

                filters.append((field, op, val))
                st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # 5. Results Configuration
        st.markdown('<div class="market-selector">', unsafe_allow_html=True)
        st.markdown('<h3 class="section-header">4️⃣ Configure Results</h3>', unsafe_allow_html=True)
        sort_col, limit_col, offset_col = st.columns(3)

        with sort_col:
            sort_by = st.selectbox(
                "Sort by",
                options=[None] + selected_instruments,
                format_func=lambda n: "(None)" if n is None else f"{name_to_field[n]['display']}",
                key="sort_by_selector"
            )
            sort_order = st.radio("Sort order", options=["desc", "asc"], horizontal=True)

        with limit_col:
            row_limit = st.number_input("Row limit", min_value=1, max_value=20000, value=20000)

        with offset_col:
            offset = st.number_input("Start at row", min_value=0, value=0, step=10)
        st.markdown('</div>', unsafe_allow_html=True)

    # Query preview in the right column
    with col2:
        st.markdown('<h2 class="section-header">🔍 Query Preview</h2>', unsafe_allow_html=True)
        st.markdown('<div class="query-preview">', unsafe_allow_html=True)
        try:
            query_code = f"Query().set_markets('{market_code}')"

            if selected_types:
                type_conditions = [f"col('type') == '{t}'" for t in selected_types]
                if len(type_conditions) == 1:
                    query_code += f".where({type_conditions[0]})"
                else:
                    type_filter = " | ".join(type_conditions)
                    query_code += f".where(({type_filter}))"

            if selected_exchanges:
                if len(selected_exchanges) == 1:
                    query_code += f".where(col('exchange') == '{selected_exchanges[0]}')"
                else:
                    exch_conds = " | ".join([f"col('exchange') == '{ex}'" for ex in selected_exchanges])
                    query_code += f".where(({exch_conds}))"

            if selected_instruments:
                query_code += f".select({', '.join([repr(c) for c in selected_instruments])})"

            if filters:
                filter_conds = ", ".join([f"col('{f}') {o} {repr(v)}" for f, o, v i
