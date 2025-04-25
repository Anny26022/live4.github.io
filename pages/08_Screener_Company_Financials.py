import sys
import io
if sys.platform.startswith("win"):
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import traceback
import numpy as np

# Try to import Playwright
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# Page config - must be the first Streamlit command
st.set_page_config(
    page_title="Screener Company Financials",
    page_icon="💹",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Update CSS to enforce centered layout and proper width
st.markdown("""
<style>
    /* Container width control */
    .block-container {
        max-width: 960px !important;  /* Reduced from default */
        padding-top: 1rem !important;
        padding-right: 1rem !important;
        padding-left: 1rem !important;
        padding-bottom: 1rem !important;
    }

    /* Enforce centered content */
    .stApp {
        max-width: 100%;
        margin: 0 auto;
    }

    /* Adjust main content area */
    .main .block-container {
        padding-left: max(1rem, calc((100% - 960px) / 2)) !important;
        padding-right: max(1rem, calc((100% - 960px) / 2)) !important;
    }

    /* Ensure DataFrames don't overflow */
    .stDataFrame {
        width: 100% !important;
        max-width: 100% !important;
    }

    .stDataFrame > div {
        width: 100% !important;
        max-width: 100% !important;
        overflow-x: auto !important;
    }

    /* Adjust metric containers for centered layout */
    [data-testid="stMetricValue"] {
        width: 100%;
        text-align: center;
    }

    /* Center align headers */
    .page-header {
        width: 100%;
        max-width: 960px;
        margin: 0 auto;
    }

    /* Ensure buttons don't stretch too wide */
    .stButton > button {
        max-width: 200px;
        margin: 0 auto;
        display: block;
    }

    /* Search Field Size Control */
    .stTextInput > div {
        max-width: 400px !important;
        margin: 0 auto !important;
    }

    .stTextInput > div > div > input {
        height: 40px !important;
        min-height: 40px !important;
        padding: 0.5rem 1rem !important;
        font-size: 0.875rem !important;
    }

    /* Search Container Size */
    .search-container {
        max-width: 600px !important;
        margin: 0 auto 1rem auto !important;
        padding: 1rem !important;
    }

    /* Select Box Size */
    .stSelectbox {
        max-width: 400px !important;
        margin: 0 auto !important;
    }

    .stSelectbox > div > div {
        min-height: 40px !important;
    }

    /* Radio Button Container */
    .stRadio > div {
        max-width: 400px !important;
        margin: 0 auto !important;
    }

    /* Column Layout */
    [data-testid="column"] {
        padding: 0 0.5rem !important;
    }

    /* Material Design 3 Variables */
    :root {
        --md-sys-color-primary: rgb(103, 80, 164);
        --md-sys-color-on-primary: rgb(255, 255, 255);
        --md-sys-color-primary-container: rgb(234, 221, 255);
        --md-sys-color-secondary: rgb(98, 91, 113);
        --md-sys-color-surface: rgba(28, 27, 31, 0.95);
        --md-sys-color-surface-container: rgba(73, 69, 79, 0.95);
        --md-elevation-1: 0px 1px 3px 1px rgba(0, 0, 0, 0.15), 0px 1px 2px 0px rgba(0, 0, 0, 0.30);
        --md-elevation-2: 0px 2px 6px 2px rgba(0, 0, 0, 0.15), 0px 1px 2px 0px rgba(0, 0, 0, 0.30);
        --md-elevation-3: 0px 4px 8px 3px rgba(0, 0, 0, 0.15), 0px 1px 3px 0px rgba(0, 0, 0, 0.30);
    }

    /* Advanced Animations */
    @keyframes slideInUp {
        from {
            transform: translateY(20px);
            opacity: 0;
        }
        to {
            transform: translateY(0);
            opacity: 1;
        }
    }

    @keyframes fadeScale {
        from {
            transform: scale(0.95);
            opacity: 0;
        }
        to {
            transform: scale(1);
            opacity: 1;
        }
    }

    @keyframes shimmer {
        0% {
            background-position: -1000px 0;
        }
        100% {
            background-position: 1000px 0;
        }
    }

    @keyframes pulse {
        0% {
            box-shadow: 0 0 0 0 rgba(103, 80, 164, 0.4);
        }
        70% {
            box-shadow: 0 0 0 10px rgba(103, 80, 164, 0);
        }
        100% {
            box-shadow: 0 0 0 0 rgba(103, 80, 164, 0);
        }
    }

    /* Material Container Styles */
    .block-container {
        padding: 1rem !important;
        max-width: 1200px !important;
        animation: fadeScale 0.5s ease-out;
    }

    /* Material Header */
    .page-header {
        background: var(--md-sys-color-surface);
        border-radius: 16px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: var(--md-elevation-2);
        animation: slideInUp 0.5s ease-out;
        border: 1px solid rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(10px);
    }

    .header-content {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .header-icon {
        width: 28px;
        height: 28px;
        animation: pulse 2s infinite;
    }

    .header-text h1 {
        font-size: 1.5rem;
        font-weight: 600;
        margin: 0;
        background: linear-gradient(45deg, #fff, rgba(255,255,255,0.7));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* Material Search Container */
    .search-container {
        background: var(--md-sys-color-surface-container);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: var(--md-elevation-1);
        animation: slideInUp 0.6s ease-out;
        border: 1px solid rgba(255, 255, 255, 0.06);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .search-container:hover {
        transform: translateY(-2px);
        box-shadow: var(--md-elevation-2);
    }

    /* Material Inputs */
    .stTextInput > div > div > input:focus {
        border-color: var(--md-sys-color-primary) !important;
        box-shadow: 0 0 0 2px rgba(103, 80, 164, 0.2) !important;
        transform: translateY(-1px);
    }

    /* Material Buttons */
    .stButton > button {
        background: var(--md-sys-color-primary) !important;
        color: var(--md-sys-color-on-primary) !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        letter-spacing: 0.025em !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        position: relative !important;
        overflow: hidden !important;
    }

    .stButton > button::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 300%;
        height: 300%;
        background: radial-gradient(circle, rgba(255,255,255,0.2) 0%, transparent 50%);
        transform: translate(-50%, -50%) scale(0);
        transition: transform 0.5s ease-out;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: var(--md-elevation-2);
    }

    .stButton > button:hover::before {
        transform: translate(-50%, -50%) scale(1);
    }

    .stButton > button:active {
        transform: translateY(0);
    }

    /* Material Select */
    .stSelectbox > div > div:hover {
        border-color: var(--md-sys-color-primary) !important;
        background: rgba(255, 255, 255, 0.08) !important;
    }

    /* Material DataFrames */
    .stDataFrame {
        animation: fadeScale 0.5s ease-out;
    }

    .stDataFrame td {
        transition: all 0.2s ease;
    }

    .stDataFrame tr:hover td {
        background: rgba(103, 80, 164, 0.1) !important;
    }

    /* Material Metrics */
    .stMetric {
        background: var(--md-sys-color-surface-container) !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        transition: all 0.3s ease !important;
        animation: slideInUp 0.7s ease-out;
    }

    .stMetric:hover {
        transform: translateY(-2px);
        box-shadow: var(--md-elevation-2);
    }

    /* Material Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--md-sys-color-surface-container) !important;
        border-radius: 12px !important;
        padding: 0.25rem !important;
        gap: 0.25rem !important;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
        position: relative !important;
        overflow: hidden !important;
    }

    .stTabs [data-baseweb="tab"]::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(45deg, var(--md-sys-color-primary), rgba(103, 80, 164, 0.5));
        opacity: 0;
        transition: opacity 0.2s ease;
    }

    .stTabs [data-baseweb="tab"]:hover::before {
        opacity: 0.1;
    }

    .stTabs [aria-selected="true"]::before {
        opacity: 0.2;
    }

    /* Loading States */
    .stSpinner {
        animation: fadeScale 0.3s ease-out;
    }

    /* Alerts and Messages */
    .stAlert {
        background: var(--md-sys-color-surface-container) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        animation: slideInUp 0.5s ease-out;
    }

    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
        background: transparent;
    }

    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.2);
        border-radius: 4px;
        transition: background 0.2s ease;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.3);
    }

    /* Loading Shimmer Effect */
    .shimmer {
        background: linear-gradient(90deg, 
            rgba(255,255,255,0) 0%, 
            rgba(255,255,255,0.1) 50%, 
            rgba(255,255,255,0) 100%);
        background-size: 1000px 100%;
        animation: shimmer 2s infinite linear;
    }

    /* Interactive States */
    *:focus-visible {
        outline: 2px solid var(--md-sys-color-primary) !important;
        outline-offset: 2px !important;
    }

    /* Tooltip */
    [data-tooltip] {
        position: relative;
    }

    [data-tooltip]:before {
        content: attr(data-tooltip);
        position: absolute;
        bottom: 100%;
        left: 50%;
        transform: translateX(-50%) scale(0.8);
        padding: 0.5rem;
        background: var(--md-sys-color-surface-container);
        border-radius: 4px;
        font-size: 0.75rem;
        opacity: 0;
        pointer-events: none;
        transition: all 0.2s ease;
    }

    [data-tooltip]:hover:before {
        transform: translateX(-50%) scale(1);
        opacity: 1;
    }

    /* Center the search container */
    .search-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        max-width: 800px !important;
        margin: 0 auto !important;
        padding: 2rem !important;
    }

    /* Style for the search input */
    .stTextInput {
        width: 100%;
        max-width: 500px !important;
        margin: 0 auto !important;
    }

    .stTextInput > div {
        width: 100% !important;
        max-width: 500px !important;
        margin: 0 auto !important;
    }

    /* Style for the radio buttons */
    .stRadio {
        width: 100%;
        max-width: 500px !important;
        margin: 1rem auto !important;
        display: flex;
        justify-content: center;
    }

    .stRadio > div {
        display: flex;
        justify-content: center;
    }

    /* Search Container Styles */
    .search-container {
        background: rgba(28, 27, 31, 0.95) !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        margin: 1rem auto !important;
        max-width: 600px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }

    /* Search Input Styles */
    .stTextInput > div {
        width: 100% !important;
        max-width: 100% !important;
    }

    .stTextInput > div > div > input {
        background: rgba(73, 69, 79, 0.95) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        height: 45px !important;
        font-size: 1rem !important;
        border-radius: 8px !important;
        padding: 0 1rem !important;
    }

    .stTextInput > div > div > input:focus {
        border-color: rgb(103, 80, 164) !important;
        box-shadow: 0 0 0 1px rgb(103, 80, 164) !important;
    }

    .stTextInput > div > div > input::placeholder {
        color: rgba(255, 255, 255, 0.6) !important;
    }

    /* Radio Button Styles */
    .stRadio > div {
        display: flex;
        justify-content: center;
        gap: 1rem;
        margin-top: 1rem !important;
    }

    .stRadio > div > div {
        background: rgba(73, 69, 79, 0.95) !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
    }

    .stRadio > div > div > label {
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# Page Header
st.markdown("""
<div class='page-header'>
    <div class='header-content'>
        <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0iIzAwZmY5NSI+PHBhdGggZD0iTTMgM3YxOGgxOFYzSDN6bTYgMTRINXYtMmg0djJ6bTQtNEg1di0yaDh2MnptNi00SDV2LTJoMTR2MnoiLz48L3N2Zz4=" class="header-icon" />
        <div class='header-text'>
            <h1>Company Financials</h1>
            <p class='subtitle'>Analyze detailed financial statements and ratios</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Define helper functions first
@st.cache_data(ttl=300)  # Cache for 5 minutes
def search_symbols(query):
    try:
        url = f"https://www.screener.in/api/company/search/?q={query}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json(), None
    except requests.RequestException as e:
        return None, f"Network error: {str(e)}"
    except Exception as e:
        return None, f"Error: {str(e)}"

def get_symbol_from_item(item):
    if 'symbol' in item:
        return item['symbol']
    if 'url' in item:
        parts = item['url'].split('/')
        if len(parts) > 2:
            return parts[2]
    return ""

def extract_symbol(selected_option):
    if not selected_option:
        return None
    if '(' in selected_option and selected_option.endswith(')'):
        return selected_option.split('(')[-1][:-1]
    return selected_option

def parse_table_with_bs4(table):
    # Get headers
    headers = []
    thead = table.find("thead")
    if thead:
        for th in thead.find_all("th"):
            headers.append(th.get_text(strip=True))
    else:
        # Try first row as header
        first_row = table.find("tr")
        if first_row:
            for th in first_row.find_all(["th", "td"]):
                headers.append(th.get_text(strip=True))
    # Get rows
    rows = []
    tbody = table.find("tbody") or table
    for tr in tbody.find_all("tr"):
        cells = []
        for td in tr.find_all(["td", "th"]):
            # Get text, fallback to child span/div if present
            text = td.get_text(strip=True)
            if not text:
                # Try to get text from span/div
                span = td.find(["span", "div"])
                if span:
                    text = span.get_text(strip=True)
            cells.append(text)
        if cells:
            rows.append(cells)
    # Pad rows to match headers
    for i in range(len(rows)):
        if len(rows[i]) < len(headers):
            rows[i] += [np.nan] * (len(headers) - len(rows[i]))
    # Build DataFrame
    if headers and rows:
        df = pd.DataFrame(rows, columns=headers)
    else:
        df = pd.DataFrame(rows)
    return df

@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_table_with_requests(url, table_caption_keywords):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        tables = soup.find_all("table")
        for table in tables:
            caption = table.find("caption")
            if caption and any(kw.lower() in caption.text.lower() for kw in table_caption_keywords):
                return pd.read_html(io.StringIO(str(table)))[0], None
            thead = table.find("thead")
            if thead and any(kw.lower() in thead.text.lower() for kw in table_caption_keywords):
                return pd.read_html(io.StringIO(str(table)))[0], None
        for table in tables:
            df = pd.read_html(io.StringIO(str(table)))[0]
            if df.shape[1] > 3 and df.shape[0] > 2:
                return df, None
        return None, "No suitable table found"
    except Exception as e:
        return None, str(e)

@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_table_with_playwright(url, table_caption_keywords, tab):
    if not PLAYWRIGHT_AVAILABLE:
        return None, "Playwright is not installed. Please run 'pip install playwright' and 'playwright install'."
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            try:
                page.goto(url, timeout=40000)
                page.wait_for_timeout(4000)
                
                # Simulate click on the correct tab
                tab_selector = {
                    "Profit & Loss": "a[href$='#profit-loss']",
                    "Balance Sheet": "a[href$='#balance-sheet']",
                    "Cash Flow": "a[href$='#cash-flow']",
                    "Ratios": "a[href$='#ratios']",
                    "Analysis": "a[href$='#analysis']",
                    "Peers": "a[href$='#peers']",
                    "Shareholding": "a[href$='#shareholding']",
                    "Documents": "a[href$='#documents']"
                }.get(tab)
                
                if tab_selector:
                    try:
                        page.click(tab_selector, timeout=3000)
                        page.wait_for_timeout(2500)
                    except Exception:
                        pass
                
                # Wait for content to load
                page.wait_for_timeout(2000)
                
                # Get the page content
                html = page.content()
                
            except Exception as e:
                browser.close()
                return None, f"Navigation failed: {str(e)}"
            finally:
                browser.close()
                
        # Parse the HTML
        soup = BeautifulSoup(html, "html.parser")
        
        # Find all tables
        tables = soup.find_all("table")
        if not tables:
            return None, "No tables found"
            
        # Try to find the correct table
        for table in tables:
            try:
                df = pd.read_html(io.StringIO(str(table)))[0]
                if not df.empty and df.shape[1] > 1:  # Ensure table has content
                    return df, None
            except Exception:
                continue
                
        return None, "No suitable table found"
        
    except Exception as e:
        return None, f"Error: {str(e)}"

# Define keywords for table search
tab_keywords = {
    "Quarters": ["quarters", "quarterly"],
    "Profit & Loss": ["profit", "p&l", "income"],
    "Balance Sheet": ["balance"],
    "Cash Flow": ["cash"],
    "Ratios": ["ratios"],
    "Analysis": ["analysis", "scorecard", "growth", "valuation"],
    "Peers": ["peers", "peer comparison", "comparison"],
    "Shareholding": ["shareholding", "share holding", "pattern"],
    "Documents": ["documents", "annual report", "report"]
}

# Search and Company Selection
st.markdown("<div class='search-container'>", unsafe_allow_html=True)

# Search field
search = st.text_input(
    "🔍 Search company by name or symbol",
    value="",
    placeholder="Enter company name or symbol (e.g., SBIN, TCS)",
    key="company_search",
    help="Enter company name or NSE symbol (e.g., SBIN, TCS, INFY)"
)

# Statement type selection
consolidated = st.radio(
    "Statement Type:",
    ["Standalone", "Consolidated"],
    index=0,
    horizontal=True,
    help="Choose between standalone or consolidated financial statements"
)

if search:
    with st.spinner("Searching for companies..."):
        symbols_result, error = search_symbols(search)
        if error:
            st.error(f"Search failed: {error}")
            symbols = []
        else:
            symbols = symbols_result

    if not symbols:
        st.warning("No companies found. Try a different search term.")
    else:
        options = [f"{item['name']} ({get_symbol_from_item(item)})" for item in symbols if 'name' in item and get_symbol_from_item(item)]
        selected = st.selectbox(
            "Select company",
            options,
            key="company_select",
            help="Choose a company from the search results"
        ) if options else None

        if selected:
            ticker = extract_symbol(selected)
            
            # Financial Components Tabs
            tab = st.selectbox(
                "Select Financial Component:",
                ["Quarters", "Profit & Loss", "Balance Sheet", "Cash Flow", "Ratios", "Analysis", "Peers", "Shareholding", "Documents"],
                key="financial_tab",
                help="Choose which financial information to view"
            )

            consolidated_path = "/consolidated" if consolidated == "Consolidated" else ""
            tab_anchor = {
                "Quarters": "#quarters",
                "Profit & Loss": "#profit-loss",
                "Balance Sheet": "#balance-sheet",
                "Cash Flow": "#cash-flow",
                "Ratios": "#ratios",
                "Analysis": "#analysis",
                "Peers": "#peers",
                "Shareholding": "#shareholding",
                "Documents": "#documents"
            }[tab]
            url = f"https://www.screener.in/company/{ticker.upper()}{consolidated_path}/{tab_anchor}"

            # st.caption(f"URL: {url}")  # Hide the URL from the UI

            # Financial Data Display
            st.markdown("<div class='financial-card'>", unsafe_allow_html=True)
            
            with st.spinner(f"Fetching {tab.lower()} data..."):
                try:
                    if tab == "Quarters":
                        df, error = fetch_table_with_requests(url, tab_keywords[tab])
                    else:
                        df, error = fetch_table_with_playwright(url, tab_keywords[tab], tab)
                    
                    if error:
                        st.error(f"Failed to fetch data: {error}")
                    elif df is not None:
                        # Add metrics before the table
                        if 'Market Cap' in df.columns:
                            st.metric("Market Cap", df['Market Cap'].iloc[-1])
                        if 'Book Value' in df.columns:
                            st.metric("Book Value", df['Book Value'].iloc[-1])
                        
                        # Display the table with improved styling
                        st.dataframe(
                            df,
                            height=600,
                            use_container_width=True,
                            column_config={
                                col: st.column_config.NumberColumn(
                                    col,
                                    help=f"Values for {col}",
                                    format="%.2f"
                                ) for col in df.select_dtypes(include=['float64', 'int64']).columns
                            }
                        )
                        
                        # Download options
                        col1, col2 = st.columns(2)
                        with col1:
                            csv = df.to_csv(index=False)
                            st.download_button(
                                "📥 Download CSV",
                                csv,
                                f"{ticker.upper()}_{tab.replace(' ', '_')}.csv",
                                "text/csv",
                                help="Download the data as a CSV file"
                            )
                        
                        with col2:
                            # Excel download
                            buffer = io.BytesIO()
                            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                                df.to_excel(writer, index=False)
                            buffer.seek(0)
                            
                            st.download_button(
                                "📊 Download Excel",
                                buffer,
                                f"{ticker.upper()}_{tab.replace(' ', '_')}.xlsx",
                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                help="Download the data as an Excel file"
                            )
                    else:
                        st.warning("No data found for this section. The data may be unavailable.")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                    with st.expander("Show error details"):
                        st.code(traceback.format_exc())

            st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# Footer with refresh button
st.markdown("---")
col1, col2 = st.columns([3, 1])
with col1:
    now = datetime.now().strftime('%d-%b-%Y %H:%M:%S IST')
    st.caption(f"Last Updated: {now}")
with col2:
    if st.button("🔄 Refresh Data", help="Clear cache and fetch fresh data"):
        st.cache_data.clear()
        st.rerun()
