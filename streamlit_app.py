import streamlit as st
import inspect
from src.tradingview_screener import Query, col
import pandas as pd
import io
import requests
from bs4 import BeautifulSoup
import subprocess
from functools import lru_cache
import numpy as np
import time
from typing import Dict, List, Any, Optional
from src.animation_utils import apply_staggered_animations, staggered_animation
import os

# --- PAGE CONFIG MUST BE FIRST ---
st.set_page_config(
    page_title="TradingView Screener Pro",
    page_icon="📈",
    layout="centered",
    initial_sidebar_state="collapsed"  # Start with sidebar collapsed
)

# Initialize session state for page navigation if not exists
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'Home'

# Add URL redirect check
current_url = st.query_params.get('page', [''])[0]
if current_url == 'Advanced_Scanner':
    st.experimental_set_query_params(page='Custom_EMA_Scanner')
    st.rerun()

# Define navigation HTML structure
navigation_html = """
<div class="glass-navbar">
    <nav>
        <ul>
            <li><a href="." class="nav-link"><i class="material-icons">home</i> Home</a></li>
            <li><a href="Custom_EMA_Scanner" class="nav-link"><i class="material-icons">show_chart</i> EMA Scanner</a></li>
            <li><a href="Stock_News" class="nav-link"><i class="material-icons">article</i> Stock News</a></li>
            <li><a href="NSE_Past_IPO_Issues" class="nav-link"><i class="material-icons">new_releases</i> IPO Issues</a></li>
            <li><a href="NSE_Volume_Gainers" class="nav-link"><i class="material-icons">trending_up</i> Volume Gainers</a></li>
            <li><a href="Screener_Company_Financials" class="nav-link"><i class="material-icons">assessment</i> Financials</a></li>
            <li><a href="price_bands" class="nav-link"><i class="material-icons">price_change</i> Price Bands</a></li>
            <li><a href="results_calendar" class="nav-link"><i class="material-icons">table_chart</i> Results Calendar</a></li>
        </ul>
    </nav>
</div>

<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/icon?family=Material+Icons');
    
    /* Modern Navigation Bar with Glass Morphism */
    .glass-navbar {
        background: rgba(32, 33, 35, 0.9);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-radius: 8px;
        margin: 0 0 20px 0;
        padding: 4px;
    }
    
    .glass-navbar nav {
        display: flex;
        justify-content: center;
    }
    
    .glass-navbar ul {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
        list-style: none;
        margin: 0;
        padding: 0;
        justify-content: center;
    }
    
    .glass-navbar .nav-link {
        display: flex;
        align-items: center;
        color: rgba(255, 255, 255, 0.9);
        text-decoration: none;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 14px;
        transition: background-color 0.2s;
        white-space: nowrap;
    }
    
    .glass-navbar .nav-link:hover {
        background: rgba(255, 255, 255, 0.1);
    }
    
    .glass-navbar .nav-link .material-icons {
        font-size: 16px;
        margin-right: 8px;
        vertical-align: middle;
    }
    
    .glass-navbar .nav-link.active {
        background: rgba(255, 255, 255, 0.1);
    }
    
    @media (max-width: 768px) {
        .glass-navbar ul {
            flex-direction: column;
        }
        .glass-navbar .nav-link {
            justify-content: flex-start;
            padding: 8px;
        }
    }
</style>
"""

# Display the navigation bar only once
st.markdown(navigation_html, unsafe_allow_html=True)

# Remove any duplicate navigation HTML and keep only the styling
st.markdown("""
<style>
    /* Hide Streamlit Sidebar */
    [data-testid="stSidebar"] {
        display: none !important;
    }
    
    /* Hide Streamlit Sidebar Toggle Button */
    button[kind="header"] {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Apply staggered animations
apply_staggered_animations()

# Feature flag to enable/disable animations
USE_ANIMATIONS = True

LOTTIE_AVAILABLE = False

# Cache for expensive operations with optimized performance
@lru_cache(maxsize=32)
def load_css() -> str:
    """Load and cache CSS content with improved performance"""
    try:
        with open('style.css', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        try:
            with open('app/style.css', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return ""

# Load CSS with caching
css_content = load_css()
if css_content:
    st.markdown(f'<style>{css_content}</style>', unsafe_allow_html=True)
else:
        st.warning("Style file not found. App will run with default styling.")

# Optimized Playwright browser install utility
def playwright_install_ui():
    if not st.session_state.get('playwright_installed', False):
        st.markdown("""
        ### 🛠️ Playwright Browser Installer
        If you see errors about missing browsers (e.g. Chromium), click the button below to install Playwright browser binaries.
        """)
        if st.button("Install Playwright Browsers"):
            with st.spinner("Installing Playwright browsers..."):
                result = subprocess.run(["playwright", "install"], capture_output=True, text=True)
                if result.returncode == 0:
                    st.session_state.playwright_installed = True
                    st.success("Playwright browsers installed successfully!")
                else:
                    st.error(f"Failed to install browsers:\n{result.stderr}")

# Optimized animation loading with caching
@lru_cache(maxsize=4)
def load_lottieurl(url: str) -> Optional[Dict]:
    """Load and cache Lottie animations - placeholder implementation"""
    return None

# Pre-load animations
lottie_loading = None
lottie_chart = None

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

# Optimized app title rendering with animation data attributes
def render_app_title():
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("TradingView Screener Pro")
        st.markdown("<p class='app-subtitle' data-animation='fade-in'>Advanced market screening with modern UI</p>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div style='text-align: center; padding-top: 10px;' data-animation='fade-in'><span style='font-size: 60px;'>📊</span></div>", unsafe_allow_html=True)

# Initialize session state with optimized defaults and animation preferences
if 'query_results' not in st.session_state:
    st.session_state.update({
        'query_results': None,
        'last_query_count': 0,
        'playwright_installed': False,
        'cached_market_data': None,
        'last_market_update': 0,
        'use_animations': True,
        'selected_tab': "build",
        'filter_cache': {},
        'last_filter_update': 0,
        'animation_loaded': False,  # Track if animations have been loaded
        'reduced_motion': False     # Respect user preferences for reduced motion
    })

# --- Reliable tab switching using st.radio ---
tab_options = ["📝 Build Query", "📊 Results"]
if "selected_tab" not in st.session_state or st.session_state.selected_tab not in tab_options:
    st.session_state.selected_tab = tab_options[0]

selected_tab = st.radio(
    "Select Tab", tab_options,
    index=tab_options.index(st.session_state.selected_tab),
    horizontal=True,
    label_visibility="collapsed"
)

st.session_state.selected_tab = selected_tab

if selected_tab == "📝 Build Query":
    # Build Query tab content
    st.markdown('<div class="screener-container" data-animation="fade-in">', unsafe_allow_html=True)
    
    # Create a 2-column layout for the main content
    col1, col2 = st.columns([3, 2])  # Adjusted ratio for better centered layout

    with col1:
        st.markdown('<h2 class="section-header" data-animation="slide-up">🛠️ Query Builder</h2>', unsafe_allow_html=True)

        # 1. Market selection with optimized animations
        @st.cache_data(ttl=3600)  # Cache for 1 hour
        def get_market_options() -> List[tuple]:
            """Get and cache market options"""
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

        # Markets and Instruments selection with animation attributes
        st.markdown('<div class="market-selector" data-animation="fade-in">', unsafe_allow_html=True)
        st.markdown('<h3 class="section-header" data-animation="slide-up">1️⃣ Select Market & Instruments</h3>', unsafe_allow_html=True)

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
        def fetch_fields_for_market(market_code: str, instrument_type: str = 'stock') -> tuple:
            """Fetch and cache fields for a market"""
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
                    content = resp.text

                    fields = []
                    exchanges = set()
                    # If the content is a plain text list (not HTML table)
                    for line in content.splitlines():
                        line = line.strip()
                        if line.startswith("- "):
                            field_name = line[2:]
                            if field_name:
                                fields.append({
                                    "name": field_name,
                                    "display": field_name,
                                    "type": "string",  # Default type
                                })
                    if not fields:
                        # fallback to old HTML parsing in case the format changes
                        soup = BeautifulSoup(content, "html.parser")
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
                    st.markdown(
                        """
                        <div style="height:200px; display:flex; align-items:center; justify-content:center; 
                        background:rgba(72,149,239,0.1); border-radius:8px; margin:10px 0;">
                            <div style="text-align:center;">
                                <div style="font-size:24px; margin-bottom:10px;">🔄</div>
                                <div>Loading data fields, please wait...</div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
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
        st.markdown('<div class="market-selector" data-animation="fade-in">', unsafe_allow_html=True)
        st.markdown('<h3 class="section-header" data-animation="slide-up">2️⃣ Select Exchanges & Data Columns</h3>', unsafe_allow_html=True)
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
        st.markdown('<div class="market-selector" data-animation="fade-in">', unsafe_allow_html=True)
        st.markdown('<h3 class="section-header" data-animation="slide-up">3️⃣ Build Your Filters</h3>', unsafe_allow_html=True)

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
                st.markdown(f'<div class="filter-card" data-animation="fade-in">', unsafe_allow_html=True)
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
        st.markdown('<div class="market-selector" data-animation="fade-in">', unsafe_allow_html=True)
        st.markdown('<h3 class="section-header" data-animation="slide-up">4️⃣ Configure Results</h3>', unsafe_allow_html=True)
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

    # Query preview in the right column with optimized animations
    with col2:
        st.markdown('<h2 class="section-header" data-animation="slide-up">🔍 Query Preview</h2>', unsafe_allow_html=True)
        st.markdown('<div class="query-preview" data-animation="fade-in">', unsafe_allow_html=True)
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
                filter_conds = ", ".join([f"col('{f}') {o} {repr(v)}" for f, o, v in filters if f and o and v])
                if filter_conds:
                    query_code += f".where({filter_conds})"

            if sort_by:
                query_code += f".sort('{sort_by}', '{sort_order}')"

            query_code += f".offset({offset}).limit({row_limit})"

            st.code(query_code, language="python")
        except Exception as e:
            st.error(f"Error generating query preview: {str(e)}")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div style="margin-top: 1rem;">', unsafe_allow_html=True)
        run_query_button = st.button(
            "🚀 Run Query",
            type="primary",
            help="Execute the query and fetch results",
            key="run_query_button"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

    if run_query_button:
        try:
            with st.spinner(""):
                # Show optimized loading animation
                loading_container = st.empty()
                loading_container.markdown("""
                <div class="loading-animation-container" style="text-align: center; padding: 20px;">
                    <div class="shimmer-loader" style="width: 80%; height: 30px; margin: 10px auto;"></div>
                    <div class="shimmer-loader" style="width: 60%; height: 30px; margin: 10px auto;"></div>
                    <div class="shimmer-loader" style="width: 70%; height: 30px; margin: 10px auto;"></div>
                    <p style="margin-top: 15px; opacity: 0.8;">Executing query and fetching results...</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Execute query logic
                if USE_ANIMATIONS and LOTTIE_AVAILABLE and lottie_loading:
                    # Replace st_lottie with a placeholder
                    st.markdown(
                        """
                        <div style="height:200px; display:flex; align-items:center; justify-content:center; 
                        background:rgba(72,149,239,0.1); border-radius:8px; margin:10px 0;">
                            <div style="text-align:center;">
                                <div style="font-size:24px; margin-bottom:10px;">🔄</div>
                                <div>Executing query...</div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                # Store market code in session state for results tab
                st.session_state.market_code = market_code

                q = Query().set_markets(market_code)

                if selected_types:
                    type_conditions = [f"col('type') == '{t}'" for t in selected_types]
                    if len(type_conditions) == 1:
                        q = q.where(eval(type_conditions[0]))
                    else:
                        type_filter = " | ".join(type_conditions)
                        q = q.where(eval(f"({type_filter})"))

                if selected_exchanges:
                    if len(selected_exchanges) == 1:
                        q = q.where(col('exchange') == selected_exchanges[0])
                    else:
                        conditions = []
                        for ex in selected_exchanges:
                            conditions.append(col('exchange') == ex)
                        combined_condition = conditions[0]
                        for condition in conditions[1:]:
                            combined_condition = combined_condition | condition
                        q = q.where(combined_condition)

                columns_to_select = list(set(selected_instruments + ['type', 'exchange']))
                q = q.select(*columns_to_select)

                # Handle filters including price bands
                for f, o, v in filters:
                    if f and o and v:
                        if o == 'in':
                            v = [x.strip() for x in v.split(',')]
                        q = q.where(eval(f"col('{f}') {o} {repr(v)}"))

                if sort_by:
                    q = q.sort(sort_by, sort_order)

                q = q.offset(offset).limit(row_limit)

                count, df = q.get_scanner_data()

                if 'type' in df.columns:
                    df = df[df['type'].isin(selected_types)]

                st.session_state.query_results = df
                st.session_state.last_query_count = count
                st.session_state.selected_tab = "📊 Results"
                st.success(f"✅ Query executed successfully! Found {count} matches. Showing {len(df)} rows.")

                st.session_state.selected_tab = "📊 Results"
                st.rerun()

                # Clear loading animation when complete
                loading_container.empty()

        except Exception as e:
            st.error(f"❌ Error executing query: {str(e)}")

else:
    # Results tab
    if st.session_state.query_results is not None:
        df = st.session_state.query_results

        if not df.empty:
            # Configure columns for display
            column_config = {
                "close": st.column_config.NumberColumn("Price", format="%.2f"),
                "primary": st.column_config.TextColumn("Primary"),
                "sector": st.column_config.TextColumn("Sector"),
                "industry": st.column_config.TextColumn("Industry"),
                "% > EMA50": st.column_config.NumberColumn("% > EMA50", format="%.2f"),
                "% > EMA150": st.column_config.NumberColumn("% > EMA150", format="%.2f"),
                "% > EMA200": st.column_config.NumberColumn("% > EMA200", format="%.2f"),
                "1M %": st.column_config.NumberColumn("1M %", format="%.2f"),
                "3M %": st.column_config.NumberColumn("3M %", format="%.2f"),
                "% from 52W High": st.column_config.NumberColumn("% from 52W High", format="%.2f"),
                "Float %": st.column_config.NumberColumn("Float %", format="%.2f"),
                "MCap (Cr)": st.column_config.NumberColumn("MCap (Cr)", format="%.2f"),
                "Rel Volume": st.column_config.NumberColumn("Rel Volume", format="%.2f"),
            }

            # Exchange filter section - show when multiple exchanges are present
            if 'exchange' in df.columns and len(df['exchange'].unique()) > 1:
                st.subheader("🏢 Exchange Filter")
                available_exchanges = sorted(df['exchange'].unique())
                selected_exchanges = st.multiselect(
                    "Filter by Exchange",
                    options=available_exchanges,
                    default=available_exchanges,
                    format_func=lambda x: f"{x} ({len(df[df['exchange'] == x])} symbols)"
                )
                
                if selected_exchanges:
                    df = df[df['exchange'].isin(selected_exchanges)]
                    st.info(f"Showing {len(df)} symbols from selected exchanges")

            # Price band filter section - only for Indian markets
            market_code = st.session_state.get('market_code', '').lower()
            if market_code == 'india':
                st.subheader("🎯 Price Band Filter")
                
                # Fetch price bands data
                @st.cache_data(ttl=300)
                def fetch_price_bands() -> pd.DataFrame:
                    """Fetch and cache price bands data"""
                    try:
                        url = "https://docs.google.com/spreadsheets/d/1xig6-dQ8PuPdeCxozcYdm15nOFUKMMZFm_p8VvRFDaE/gviz/tq?tqx=out:csv&gid=364491472"
                        bands_df = pd.read_csv(url)
                        bands_df = bands_df[['Symbol', 'Band']]
                        bands_df['Symbol'] = bands_df['Symbol'].str.replace('NSE:', '', regex=False)
                        return bands_df
                    except Exception as e:
                        st.error(f"Error fetching price bands: {str(e)}")
                        return pd.DataFrame(columns=['Symbol', 'Band'])

                price_bands_df = fetch_price_bands()
                
                if not price_bands_df.empty:
                    symbol_to_band = dict(zip(price_bands_df['Symbol'], price_bands_df['Band']))
                    
                    symbol_column = None
                    for col in ['symbol', 'name', 'Stock', 'ticker']:
                        if col in df.columns:
                            symbol_column = col
                            break
                    
                    if symbol_column:
                        df['Price Band'] = df[symbol_column].str.replace('NSE:', '', regex=False).map(symbol_to_band)
                        
                        available_bands = sorted(price_bands_df['Band'].unique())
                        
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            selected_bands = st.multiselect(
                                "Filter by Price Band",
                                options=available_bands,
                                format_func=lambda x: f"Band {x} ({len(price_bands_df[price_bands_df['Band'] == x])} stocks)"
                            )
                        
                        with col2:
                            show_band_info = st.checkbox("Show Price Band Column", value=True)
                        
                        if selected_bands:
                            df = df[df['Price Band'].isin(selected_bands)]
                            st.info(f"Showing {len(df)} stocks in selected price bands")

                            if not show_band_info and 'Price Band' in df.columns:
                                df = df.drop('Price Band', axis=1)

            # Main Results Display
            st.markdown("""
                <div style='
                    background: linear-gradient(135deg, rgba(32, 33, 35, 0.95), rgba(45, 46, 48, 0.95));
                    padding: 1.5rem 2rem;
                    border-radius: 12px;
                    margin: 1rem 0;
                    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    backdrop-filter: blur(10px);
                '>
                    <div style='display: flex; align-items: center; gap: 15px;'>
                        <div style='
                            background: linear-gradient(135deg, #3b82f6, #2563eb);
                            width: 40px;
                            height: 40px;
                            border-radius: 10px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            box-shadow: 0 2px 10px rgba(59, 130, 246, 0.3);
                        '>
                            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                <line x1="18" y1="20" x2="18" y2="10"></line>
                                <line x1="12" y1="20" x2="12" y2="4"></line>
                                <line x1="6" y1="20" x2="6" y2="14"></line>
                            </svg>
                        </div>
                        <div>
                            <h2 style='
                                margin: 0;
                                font-size: 1.5rem;
                                font-weight: 600;
                                color: #fff;
                                letter-spacing: -0.025em;
                            '>Scanner Results</h2>
                            <p style='
                                margin: 4px 0 0 0;
                                font-size: 0.875rem;
                                color: rgba(255, 255, 255, 0.7);
                                font-weight: 400;
                            '>Analyze your screening matches</p>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Add date column configurations if they exist
            date_columns = [col for col in df.columns if any(date_term in col.lower() 
                          for date_term in ['date', 'calendar', 'earnings', 'dividend', 'ex_date', 'release'])]
            
            for date_col in date_columns:
                column_config[date_col] = st.column_config.DateColumn(
                    date_col.replace('_', ' ').title(),
                    format="YYYY-MM-DD"
                )

            # Add Price Band column config if it exists
            if 'Price Band' in df.columns:
                column_config["Price Band"] = st.column_config.NumberColumn("Price Band", format="%.0f")

            # Display results in a single dataframe
            st.dataframe(
                df,
                use_container_width=True,
                height=500,
                column_config=column_config
            )

            # Display statistics
            stats_col1, stats_col2, stats_col3 = st.columns(3)
            with stats_col1:
                st.metric("Total Results", st.session_state.last_query_count)
            with stats_col2:
                unique_exchanges = sorted(df['exchange'].unique()) if 'exchange' in df.columns else []
                st.metric("Exchanges", len(unique_exchanges))
            with stats_col3:
                st.metric("Displayed Rows", len(df))

            # Copy Tickers section
            st.subheader("📋 Copy Tickers")
            ticker_column = None
            for coln in ['name', 'Stock', 'ticker', 'symbol']:
                if coln in df.columns:
                    ticker_column = coln
                    break

            if ticker_column:
                tickers_simple = ','.join(df[ticker_column].astype(str))
                st.text_area("Copy Tickers (comma-separated)",
                            value=tickers_simple,
                            height=100,
                            help=f"Simple comma-separated tickers ({len(df)} symbols)")
                st.markdown(
                    f'<button id="copy-tickers-btn" style="margin-top: 0.5em; padding: 0.5em 1em; background: #222; color: #fff; border: none; border-radius: 4px; cursor: pointer;">Copy</button>'
                    '<script>'
                    'const btn = window.parent.document.getElementById("copy-tickers-btn");'
                    'if (btn) {'
                    'btn.onclick = function() {'
                    'const ta = window.parent.document.querySelector("textarea[aria-label=\'Copy Tickers (comma-separated)\']");'
                    'if (ta) {navigator.clipboard.writeText(ta.value);}'
                    '};'
                    '}'
                    '</script>',
                    unsafe_allow_html=True
                )

            # Download buttons
            dl_col1, dl_col2 = st.columns(2)
            with dl_col1:
                st.download_button(
                    "📥 Download CSV",
                    data=df.to_csv(index=False),
                    file_name="tradingview_results.csv",
                    mime="text/csv"
                )
            with dl_col2:
                buffer = io.BytesIO()
                try:
                    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                        df.to_excel(writer, index=False)
                    buffer.seek(0)
                    st.download_button(
                        "📥 Download Excel",
                        data=buffer,
                        file_name="tradingview_results.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                except Exception as e:
                    st.error(f"Error creating Excel file: {str(e)}")
        else:
            st.info("No results to display. Run a query in the Build Query tab to see results here.")
    else:
        st.info("No results to display. Run a query in the Build Query tab to see results here.")

st.markdown("---")
st.caption("TradingView Screener Pro • Built with Streamlit • Created with ❤️")

# Stock News Page
def render_stock_news():
    st.markdown("""
    <div class='page-header'>
        <h1>📰 Stock News</h1>
        <p class='subtitle'>Latest market insights and company updates</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        <div class='content-card'>
            <h3>📊 Market Overview</h3>
            <div class='news-filters'>
                <span class='filter-tag active'>All Markets</span>
                <span class='filter-tag'>US Stocks</span>
                <span class='filter-tag'>Crypto</span>
                <span class='filter-tag'>Forex</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class='content-card'>
            <h3>🔍 Quick Filters</h3>
            <div class='quick-filters'>
                <div class='filter-item'>
                    <span class='material-icons'>trending_up</span>
                    Top Gainers
                </div>
                <div class='filter-item'>
                    <span class='material-icons'>trending_down</span>
                    Top Losers
                </div>
                <div class='filter-item'>
                    <span class='material-icons'>volume_up</span>
                    High Volume
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# Price Bands Page
def render_price_bands():
    st.markdown("""
    <div class='page-header'>
        <h1>💹 Price Bands</h1>
        <p class='subtitle'>Track and analyze price movements across bands</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        st.markdown("""
        <div class='content-card'>
            <h3>📊 Band Distribution</h3>
            <div class='band-stats'>
                <div class='stat-item'>
                    <span class='stat-label'>Band A</span>
                    <span class='stat-value'>45%</span>
                </div>
                <div class='stat-item'>
                    <span class='stat-label'>Band B</span>
                    <span class='stat-value'>30%</span>
                </div>
                <div class='stat-item'>
                    <span class='stat-label'>Band C</span>
                    <span class='stat-value'>25%</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class='content-card'>
            <h3>📈 Band Analysis</h3>
            <div class='band-filters'>
                <div class='filter-group'>
                    <label>Select Band</label>
                    <select class='modern-select'>
                        <option>All Bands</option>
                        <option>Band A</option>
                        <option>Band B</option>
                        <option>Band C</option>
                    </select>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class='content-card'>
            <h3>🎯 Quick Actions</h3>
            <div class='action-buttons'>
                <button class='action-btn primary'>Export Data</button>
                <button class='action-btn secondary'>Save View</button>
            </div>
        </div>
        """, unsafe_allow_html=True)

# Results Page
def render_results():
    st.markdown("""
    <div class='page-header'>
        <h1>📊 Screening Results</h1>
        <p class='subtitle'>Analyze your screening results with advanced filters</p>
    </div>
    """, unsafe_allow_html=True)

    # Results Toolbar
    st.markdown("""
    <div class='results-toolbar'>
        <div class='toolbar-section'>
            <span class='material-icons'>filter_list</span>
            <select class='modern-select'>
                <option>All Markets</option>
                <option>Stocks</option>
                <option>Crypto</option>
                <option>Forex</option>
            </select>
        </div>
        <div class='toolbar-section'>
            <span class='material-icons'>sort</span>
            <select class='modern-select'>
                <option>Sort by Volume</option>
                <option>Sort by Price</option>
                <option>Sort by Change %</option>
            </select>
        </div>
        <div class='toolbar-actions'>
            <button class='action-btn'><span class='material-icons'>file_download</span> Export</button>
            <button class='action-btn'><span class='material-icons'>refresh</span> Refresh</button>
        </div>
    </div>
""", unsafe_allow_html=True)

# Navigation Logic
if 'page' not in st.session_state:
    st.session_state.page = 'scanner'

# Custom Sidebar Navigation with Emojis and Sleek Design
NAV_ITEMS = [
    ("scanner", "📊", "Advanced Scanner"),
    ("news", "📰", "Stock News"),
    ("ema", "📊", "EMA Scanner"),
    ("ipo", "🔔", "IPO Issues"),
    ("volume", "📈", "Volume Gainers"),
    ("financials", "💹", "Financials"),
    ("bands", "📊", "Price Bands"),
    ("results", "📋", "Results"),
]

sidebar_html = """
<style>
.custom-sidebar-nav {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-top: 1.5em;
}
.custom-sidebar-btn {
    display: flex;
    align-items: center;
    gap: 14px;
    font-size: 1.1em;
    padding: 0.75em 1em;
    border: none;
    border-radius: 8px;
    background: transparent;
    color: #a0aec0;
    font-family: 'Inter', sans-serif;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.15s, color 0.15s, transform 0.15s;
    text-align: left;
}
.custom-sidebar-btn.active, .custom-sidebar-btn:hover {
    background: rgba(59, 130, 246, 0.18);
    color: #fff;
    transform: scale(1.03);
}
.custom-sidebar-emoji {
    font-size: 1.5em;
    margin-right: 6px;
}
</style>
<div class="custom-sidebar-nav">
"""
for key, emoji, label in NAV_ITEMS:
    active = "active" if st.session_state.get("page", "scanner") == key else ""
    sidebar_html += f'''
    <form action="" method="post">
        <button name="nav" value="{key}" class="custom-sidebar-btn {active}" type="submit">
            <span class="custom-sidebar-emoji">{emoji}</span>{label}
        </button>
    </form>
    '''
sidebar_html += "</div>"
st.sidebar.markdown(sidebar_html, unsafe_allow_html=True)

# Handle navigation POST (works on rerun)
if "page" not in st.session_state:
    st.session_state.page = "scanner"
if "nav" in st.session_state:
    st.session_state.page = st.session_state["nav"]

# Render the selected page
if st.session_state.page == 'scanner':
    # Your existing scanner code
    pass
elif st.session_state.page == 'news':
    render_stock_news()
elif st.session_state.page == 'bands':
    render_price_bands()
elif st.session_state.page == 'results':
    render_results()
