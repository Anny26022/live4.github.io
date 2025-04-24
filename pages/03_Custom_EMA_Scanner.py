import sys
import streamlit as st
import pandas as pd
import os
from tradingview_screener import Query, Column, col
from utils import get_listing_date_map_cached
import plotly.express as px
import plotly.graph_objects as go
from streamlit.components.v1 import html
import time

# Page Configuration
st.set_page_config(
    page_title="Custom EMA Stock Scanner",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Remove top padding and menu
st.markdown("""
    <style>
        .block-container {
            padding-top: 0rem;
            padding-bottom: 0rem;
        }
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- Import price bands from price_bands.py ---
from pages.price_bands import fetch_price_bands
price_bands_df, bands_last_update = fetch_price_bands()

# Custom CSS
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

    /* Animation Keyframes */
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

    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }

    @keyframes scaleIn {
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
        0% { background-position: -1000px 0; }
        100% { background-position: 1000px 0; }
    }

    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }

    /* Global Styles with Animations */
    .stApp {
        background: var(--bg-dark) !important;
        opacity: 0;
        animation: fadeIn 0.5s var(--animation-timing) forwards;
    }

    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 1000px !important;
        animation: slideInUp 0.5s var(--animation-timing) forwards;
    }

    /* Header Section with Animation */
    .header-section {
        text-align: left;
        margin-bottom: 2rem;
        padding: 1.5rem 2rem;
        background: linear-gradient(135deg, var(--primary), var(--primary-dark));
        border-radius: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        opacity: 0;
        animation: scaleIn 0.6s var(--animation-timing) forwards;
        position: relative;
        overflow: hidden;
    }

    .header-section::after {
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        bottom: 0;
        left: 0;
        background: linear-gradient(45deg, transparent, rgba(255,255,255,0.1), transparent);
        transform: translateX(-100%);
        animation: shimmer 3s infinite;
    }

    .header-title {
        font-size: 2rem;
        font-weight: 700;
        color: white;
        margin: 0;
        letter-spacing: -0.025em;
        transform: translateY(20px);
        opacity: 0;
        animation: slideInUp 0.6s var(--animation-timing) 0.2s forwards;
    }

    .header-subtitle {
        font-size: 1rem;
        color: rgba(255, 255, 255, 0.9);
        margin-top: 0.5rem;
        font-weight: 400;
        transform: translateY(20px);
        opacity: 0;
        animation: slideInUp 0.6s var(--animation-timing) 0.3s forwards;
    }

    /* Filter Card Animations */
    .filter-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 0.75rem;
        padding: 1.25rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        transition: all 0.3s var(--animation-timing);
        opacity: 0;
        animation: scaleIn 0.5s var(--animation-timing) forwards;
        position: relative;
    }

    .filter-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
    }

    .filter-card::before {
        content: '';
        position: absolute;
        inset: 0;
        border-radius: 0.75rem;
        padding: 1px;
        background: linear-gradient(45deg, transparent, var(--primary-light), transparent);
        mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
        -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
        -webkit-mask-composite: xor;
        mask-composite: exclude;
        opacity: 0;
        transition: opacity 0.3s var(--animation-timing);
    }

    .filter-card:hover::before {
        opacity: 1;
    }

    /* Input Animations */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > div {
        transition: all 0.2s var(--animation-timing);
    }

    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stSelectbox > div > div > div:focus {
        transform: translateY(-1px);
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
    }

    /* Button Animations */
    .stButton > button {
        background: var(--primary);
        color: white;
        border: none;
        padding: 0.625rem 1.25rem;
        border-radius: 0.5rem;
        font-weight: 600;
        font-size: 0.875rem;
        transition: all 0.3s var(--animation-timing);
        position: relative;
        overflow: hidden;
    }

    .stButton > button::after {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 300%;
        height: 300%;
        background: radial-gradient(circle, rgba(255,255,255,0.2) 0%, transparent 60%);
        transform: translate(-50%, -50%) scale(0);
        opacity: 0;
        transition: transform 0.6s var(--animation-timing), opacity 0.6s var(--animation-timing);
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    }

    .stButton > button:hover::after {
        transform: translate(-50%, -50%) scale(1);
        opacity: 1;
    }

    .stButton > button:active {
        transform: translateY(1px);
    }

    /* MultiSelect Animation */
    .stMultiSelect > div > div > div {
        transition: all 0.2s var(--animation-timing);
    }

    .stMultiSelect > div > div > div[data-focused="true"] {
        transform: translateY(-1px);
    }

    /* Checkbox Animation */
    .stCheckbox > label > div[role="checkbox"] {
        transition: all 0.2s var(--animation-timing);
    }

    .stCheckbox > label > div[role="checkbox"][data-checked="true"] {
        animation: pulse 0.3s var(--animation-timing);
    }

    /* Table Row Animations */
    .stDataFrame tbody tr {
        transition: all 0.2s var(--animation-timing);
        opacity: 0;
        animation: fadeIn 0.3s var(--animation-timing) forwards;
    }

    .stDataFrame tbody tr:hover {
        transform: translateX(4px);
    }

    /* Loading Animation */
    .loading {
        position: relative;
        overflow: hidden;
    }

    .loading::after {
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        bottom: 0;
        left: 0;
        background: linear-gradient(90deg, 
            transparent 0%, 
            rgba(var(--text-primary), 0.1) 50%, 
            transparent 100%);
        animation: shimmer 1.5s infinite;
    }

    /* Responsive Animations */
    @media (prefers-reduced-motion: reduce) {
        *, ::before, ::after {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
            scroll-behavior: auto !important;
        }
    }

    /* Filter Section */
    .filter-section {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1.25rem;
        margin-bottom: 1.5rem;
    }

    .filter-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 0.75rem;
        padding: 1.25rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        transition: all 0.2s;
    }

    .filter-card:hover {
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    .filter-title {
        font-size: 1rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid var(--border-color);
    }

    /* Input Styles - More Compact */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > div {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 0.375rem;
        padding: 0.35rem 0.5rem;
        font-size: 0.8125rem;
        transition: all 0.2s var(--animation-timing);
        min-height: 2rem;
        line-height: 1;
    }

    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stSelectbox > div > div > div:focus {
        border-color: var(--primary);
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }

    /* MultiSelect Styles - More Compact */
    .stMultiSelect > div {
        background: transparent;
        margin-bottom: 0.5rem;
    }

    .stMultiSelect > div > div > div {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 0.375rem;
        min-height: 2rem;
        color: var(--text-primary);
        font-size: 0.8125rem;
        padding: 0.25rem 0.5rem;
    }

    .stMultiSelect [data-baseweb="tag"] {
        height: 1.25rem;
        font-size: 0.75rem;
        margin: 0.125rem;
        padding: 0.125rem 0.375rem;
        background: var(--primary-light);
        border-radius: 0.25rem;
    }

    .stMultiSelect [data-baseweb="tag"]:hover {
        background: var(--primary);
    }

    .stMultiSelect [data-baseweb="tag"] span[role="button"] {
        margin-left: 0.25rem;
    }

    /* Form Field Labels */
    .stSelectbox > label, 
    .stMultiSelect > label,
    .stNumberInput > label,
    .stTextInput > label {
        font-size: 0.75rem;
        font-weight: 500;
        margin-bottom: 0.25rem;
        color: var(--text-primary);
    }

    /* Filter Card - More Compact */
    .filter-card {
        padding: 0.75rem;
        margin-bottom: 0.75rem;
    }

    .filter-title {
        font-size: 0.875rem;
        margin-bottom: 0.5rem;
        padding-bottom: 0.375rem;
    }

    /* MultiSelect Dropdown Menu */
    div[data-baseweb="popover"] {
        max-height: 300px !important;
        overflow-y: auto !important;
        font-size: 0.8125rem !important;
    }

    div[data-baseweb="popover"] [role="listbox"] {
        padding: 0.25rem !important;
    }

    div[data-baseweb="popover"] [role="option"] {
        min-height: 1.75rem !important;
        padding: 0.25rem 0.5rem !important;
    }

    /* Checkbox more compact */
    .stCheckbox > label {
        font-size: 0.8125rem;
        margin-bottom: 0.25rem;
        display: flex;
        align-items: center;
        gap: 0.375rem;
    }

    .stCheckbox > label > div[role="checkbox"] {
        transform: scale(0.85);
    }

    /* Make multiselect tags more compact */
    div[data-baseweb="tag"] {
        height: 1.25rem !important;
        padding: 0 0.25rem !important;
        margin: 0.125rem !important;
        background: var(--primary-light) !important;
        border-radius: 0.25rem !important;
    }
    
    div[data-baseweb="tag"] span {
        font-size: 0.7rem !important;
        line-height: 1.2 !important;
        color: white !important;
    }
    
    div[data-baseweb="tag"]:hover {
        background: var(--primary) !important;
    }

    /* Remove extra padding from container */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        max-width: 1000px !important;
    }

    /* Header more compact */
    .header-section {
        margin-bottom: 1rem;
        padding: 1rem 1.25rem;
    }

    .header-title {
        font-size: 1.5rem;
    }

    .header-subtitle {
        font-size: 0.875rem;
        margin-top: 0.25rem;
    }
    
    /* Row spacing for form elements */
    .stSelectbox, .stNumberInput, .stTextInput, .stMultiSelect {
        margin-bottom: 0.5rem !important;
    }
    
    /* More compact col gap */
    .row-widget.stRow {
        gap: 0.75rem !important;
    }
    
    /* More compact buttons */
    .stButton > button {
        padding: 0.375rem 0.75rem;
        font-size: 0.8125rem;
        min-width: 0;
    }
    
    /* Column spacing */
    div[data-testid="column"] {
        padding: 0 0.375rem !important;
    }
    
    /* Make multiselect dropdown compact */
    [data-baseweb="select"] [role="listbox"] {
        max-height: 200px !important;
    }

    /* Additional Spacing Adjustments */
    .stMarkdown {
        margin-bottom: 0.5rem;
    }
    
    .stMarkdown p {
        margin-bottom: 0.25rem;
        font-size: 0.875rem;
    }
    
    /* Make labels inline with inputs where possible */
    .stNumberInput, .stCheckbox {
        display: flex !important;
        align-items: center !important;
        gap: 0.5rem !important;
        margin-bottom: 0.25rem !important;
    }
    
    .stNumberInput > label, .stCheckbox > label {
        margin-bottom: 0 !important;
        min-width: 4rem !important;
        flex-shrink: 0 !important;
    }
    
    /* Reduce height of number input */
    .stNumberInput > div {
        width: 100% !important;
    }
    
    .stNumberInput input {
        padding: 0.25rem 0.5rem !important;
    }

    /* Remove Streamlit Branding */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* Responsive Design */
    @media (max-width: 768px) {
        .block-container {
            padding: 1rem !important;
        }
        
        .header-section {
            padding: 1rem;
            margin-bottom: 1.5rem;
        }
        
        .header-title {
            font-size: 1.5rem;
        }
        
        .filter-section {
            grid-template-columns: 1fr;
            gap: 1rem;
        }
        
        .filter-card {
            padding: 1rem;
        }
    }

    /* Fix number input styling */
    .stNumberInput > div > div > div {
        display: flex !important;
        align-items: center !important;
        border-radius: 0.375rem !important;
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        overflow: hidden !important;
    }

    .stNumberInput > div > div > div > input {
        border: none !important;
        border-radius: 0 !important;
        background: transparent !important;
        padding: 0.35rem 0.5rem !important;
        flex: 1 !important;
        height: 1.75rem !important;
        min-height: 1.75rem !important;
        font-size: 0.8125rem !important;
        box-shadow: none !important;
    }

    .stNumberInput > div > div > div > button {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 1.75rem !important;
        height: 1.75rem !important;
        min-width: 1.75rem !important;
        color: var(--text-primary) !important;
        background: color-mix(in srgb, var(--bg-card) 50%, var(--text-primary) 5%) !important;
        border: none !important;
        border-radius: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        transition: background 0.2s var(--animation-timing) !important;
    }

    .stNumberInput > div > div > div > button:hover {
        background: color-mix(in srgb, var(--bg-card) 50%, var(--text-primary) 10%) !important;
    }

    .stNumberInput > div > div > div > button:first-of-type {
        border-right: 1px solid var(--border-color) !important;
    }

    .stNumberInput > div > div > div > button:last-of-type {
        border-left: 1px solid var(--border-color) !important;
    }

    .stNumberInput > div > div > div > button svg {
        width: 0.875rem !important;
        height: 0.875rem !important;
    }

    /* Fix number input label alignment */
    .stNumberInput {
        margin-bottom: 0.75rem !important;
    }

    .stNumberInput > label {
        display: block !important;
        font-size: 0.75rem !important;
        font-weight: 500 !important;
        margin-bottom: 0.25rem !important;
        color: var(--text-primary) !important;
    }

    /* Adjust number input widths */
    div[data-testid="column"] .stNumberInput > div {
        max-width: 100% !important;
    }

    /* Row layout for Market Cap range */
    .row-widget.stRow {
        display: flex !important;
        align-items: center !important;
        gap: 0.75rem !important;
        margin-bottom: 0.5rem !important;
    }

    .row-widget.stRow > [data-testid="column"] {
        flex: 1 !important;
        padding: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# Remove top padding and menu (moved to CSS)
st.markdown("")

# Header Section
st.markdown("""
<div class="header-section">
    <h1 class="header-title">Custom EMA Stock Scanner</h1>
    <p class="header-subtitle">Scan stocks based on moving averages and technical indicators</p>
</div>
""", unsafe_allow_html=True)

# Main Container
with st.container():
    # Market Region Section
    st.markdown('<div class="filter-card">', unsafe_allow_html=True)
    st.markdown('<h3 class="filter-title">Market Region</h3>', unsafe_allow_html=True)
    market_regions = [
        "america", "india", "europe", "hongkong", "japan", 
        "australia", "canada", "uk", "crypto", "forex"
    ]
    selected_regions = st.multiselect(
        "Select Market Region(s)",
        options=market_regions,
        default=["india"],
        key="market_region"
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # EMA Filters Section
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="filter-card">', unsafe_allow_html=True)
        st.markdown('<h3 class="filter-title">Price Above Moving Averages</h3>', unsafe_allow_html=True)
        enable_above_ema = st.checkbox("Enable Above EMA Filters", value=True)
        if enable_above_ema:
            ema_options = [
                ("Above 200 Days MA", "EMA200"),
                ("Above 150 Days MA", "EMA150"),
                ("Above 50 Days MA", "EMA50"),
                ("Above 20 Days MA", "EMA20"),
                ("Above 10 Days MA", "EMA10"),
            ]
            selected_above = st.multiselect(
                "Select Moving Averages:",
                [label for label, _ in ema_options],
                default=["Above 200 Days MA", "Above 150 Days MA", "Above 50 Days MA"],
                key="ema_above"
            )
        else:
            selected_above = []
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="filter-card">', unsafe_allow_html=True)
        st.markdown('<h3 class="filter-title">Price Below Moving Averages</h3>', unsafe_allow_html=True)
        enable_below_ema = st.checkbox("Enable Below EMA Filters", value=False)
        if enable_below_ema:
            below_options = [
                ("Below 200 Days MA", "EMA200"),
                ("Below 150 Days MA", "EMA150"),
                ("Below 50 Days MA", "EMA50"),
                ("Below 20 Days MA", "EMA20"),
                ("Below 10 Days MA", "EMA10"),
            ]
            selected_below = st.multiselect(
                "Select Moving Averages:",
                [label for label, _ in below_options],
                key="ema_below"
            )
        else:
            selected_below = []
        st.markdown('</div>', unsafe_allow_html=True)

    # Additional Filters Section
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="filter-card">', unsafe_allow_html=True)
        st.markdown('<h3 class="filter-title">Price Levels</h3>', unsafe_allow_html=True)
        
        # Near Highs
        enable_near_highs = st.checkbox("Near New Highs", value=False)
        if enable_near_highs:
            near_highs = st.multiselect(
                "Select High Points:",
                ["1 Month High", "3 Month High", "52 Week High"],
                key="near_highs"
            )
        else:
            near_highs = []
        
        # Price Range from 52w Low
        enable_52w_low = st.checkbox("% from 52w Low Price Range", value=False)
        if enable_52w_low:
            col_min, col_max = st.columns(2)
            with col_min:
                low_52w_min = st.number_input("Min %", min_value=0, max_value=1000, value=30)
            with col_max:
                low_52w_max = st.number_input("Max %", min_value=0, max_value=1000, value=1000)
            use_52w_low = True
        else:
            low_52w_min = 30
            low_52w_max = 1000
            use_52w_low = False
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="filter-card">', unsafe_allow_html=True)
        st.markdown('<h3 class="filter-title">Market Parameters</h3>', unsafe_allow_html=True)
        
        # Market Cap and Stock Price
        st.markdown("**Market Cap Range (Cr.)**")
        col_min, col_max = st.columns(2)
        with col_min:
            market_cap_min = st.number_input("Min", min_value=0, max_value=5000000, value=0)
        with col_max:
            market_cap_max = st.number_input("Max", min_value=0, max_value=5000000, value=500000)
        
        st.markdown("**Stock Price Range (₹)**")
        col_min, col_max = st.columns(2)
        with col_min:
            stock_price_min = st.number_input("Min Price", min_value=0, max_value=150000, value=0)
        with col_max:
            stock_price_max = st.number_input("Max Price", min_value=0, max_value=150000, value=150000)
        
        # Free Float (%)
        enable_float = st.checkbox("Free Float (%)", value=False)
        if enable_float:
            col_min, col_max = st.columns(2)
            with col_min:
                float_min = st.number_input("Min % Free Float", min_value=0, max_value=100, value=0)
            with col_max:
                float_max = st.number_input("Max % Free Float", min_value=0, max_value=100, value=100)
            use_float = True
        else:
            float_min = 0
            float_max = 100
            use_float = False
        st.markdown('</div>', unsafe_allow_html=True)

    # Exchange Selection
    st.markdown('<div class="filter-card">', unsafe_allow_html=True)
    st.markdown('<h3 class="filter-title">Exchange Selection</h3>', unsafe_allow_html=True)
    exchange_options = ["NSE", "BSE"]
    selected_exchanges = st.multiselect(
        "Select Exchange(s):",
        options=exchange_options,
        default=["NSE"],
        key="exchange_select"
    )
    st.markdown('</div>', unsafe_allow_html=True)

# --- UI: Price Band Filter ---
st.markdown('<div class="filter-card">', unsafe_allow_html=True)
st.markdown('<h3 class="filter-title">Price Band</h3>', unsafe_allow_html=True)
if not price_bands_df.empty:
    band_options = sorted(price_bands_df['Band'].dropna().unique().tolist())
    band_options = [f"{int(b)}%" for b in band_options]
    band_options.append("No Band")  # Add 'No Band' option for 'no band'
    default_selected_bands = [x for x in band_options if x in ["10%", "20%", "5%"]]
    selected_bands = st.multiselect("Select Price Band(s) (optional)", band_options, default=default_selected_bands, key="price_band")
else:
    selected_bands = []
st.markdown('</div>', unsafe_allow_html=True)

# --- Centrally map listing_dates.txt ---
@st.cache_data(ttl=3600)
def get_listing_dates():
    """
    Returns a dictionary {symbol: listing_date} from listing_dates.txt
    """
    try:
        return get_listing_date_map_cached()
    except Exception as e:
        st.warning(f"Could not load listing dates: {e}")
        return {}

listing_dates_map = get_listing_dates()

# --- Query Construction ---
# Prevent contradictory EMA selections
contradictory_emas = set(selected_above) & set([below_label_map.get(lbl, lbl) for lbl in selected_below])
if contradictory_emas:
    st.warning(f"You selected both 'Above' and 'Below' for: {', '.join(contradictory_emas)}. Please fix your selection.")

# Build filters
ema_filters = []
if enable_above_ema:
    for label in selected_above:
        ema_col = dict(ema_options)[label]
        ema_filters.append(Column("close") > Column(ema_col))
if enable_below_ema:
    for label in selected_below:
        orig_label = below_label_map.get(label, label)
        ema_col = dict(ema_options)[orig_label]

        ema_filters.append(Column("close") < Column(ema_col))

other_filters = []
post_filters = []
# Near Highs
high_map = {
    "1 Month High": "High.1M",
    "3 Month High": "High.3M",
    "52 Week High": "price_52_week_high"
}
for high in near_highs:
    other_filters.append(Column("close") >= Column(high_map[high]))
# Market Cap
if market_cap_min > 0 or market_cap_max < 5000000:
    other_filters.append(Column("market_cap_basic").between(market_cap_min * 1e7, market_cap_max * 1e7))  # Cr. to Rs.
# Stock Price
if stock_price_min > 0 or stock_price_max < 150000:
    other_filters.append(Column("close").between(stock_price_min, stock_price_max))
# Exchange filter
if selected_exchanges:
    other_filters.append(Column("exchange").isin(selected_exchanges))
# Price Band filter
if selected_bands and not price_bands_df.empty:
    allowed_symbols = []
    # Add symbols for selected numeric bands
    band_values = [float(b.replace('%','')) for b in selected_bands if b != "No Band"]
    if band_values:
        allowed_symbols += price_bands_df[price_bands_df['Band'].isin(band_values)]['Symbol'].tolist()
    # Add symbols for 'No Band' selection
    if "No Band" in selected_bands:
        allowed_symbols += price_bands_df[price_bands_df['Band'].isna()]['Symbol'].tolist()
    # Remove duplicates, if any
    allowed_symbols = list(set(allowed_symbols))
    if allowed_symbols:
        other_filters.append(Column("name").isin(allowed_symbols))
    else:
        st.warning(f"No stocks found in selected price band(s). No price band filter applied.")
# % from 52w Low Price Range
if use_52w_low:
    post_filters.append(
        lambda df: ((df["close"] - df["price_52_week_low"]) / df["price_52_week_low"] * 100).between(low_52w_min, low_52w_max)
    )
# Free Float (%)
if use_float:
    other_filters.append(Column("float_shares_percent_current").between(float_min, float_max))

# Combine ONLY Column-based filters for Query
query_filters = ema_filters + [f for f in other_filters if not callable(f)]

# --- Run Query Button ---
if st.button("Run Scan"):
    if contradictory_emas:
        st.error("Cannot run scan with contradictory EMA selections. Please fix your selection.")
    else:
        q = Query().select("name", "close", "volume", "market_cap_basic", "sector", "industry", "price_52_week_low", "price_52_week_high")
        # Correct market logic as in Query.set_markets
        if selected_regions:
            if len(selected_regions) == 1:
                q.url = f"https://scanner.tradingview.com/{selected_regions[0]}/scan"
                q.query['markets'] = [selected_regions[0]]
            else:
                q.url = "https://scanner.tradingview.com/global/scan"
                q.query['markets'] = list(selected_regions)
        if query_filters:
            q = q.where(*query_filters)
        # Set row limit to 20000
        q = q.limit(20000)
        try:
            count, df = q.get_scanner_data()
            # --- Update sector/industry options dynamically ---
            if not df.empty:
                st.session_state['sector_options'] = ["All"] + sorted([x for x in df['sector'].dropna().unique() if x])
                st.session_state['industry_options'] = ["All"] + sorted([x for x in df['industry'].dropna().unique() if x])
            # --- Merge price band info ---
            if not df.empty and not price_bands_df.empty:
                # Merge on symbol/name (assumes df['name'] matches price_bands_df['Symbol'])
                df = df.merge(price_bands_df.rename(columns={'Symbol': 'name'}), on='name', how='left')
                # Display 'No Band' for NaN Band values
                df['Band'] = df['Band'].apply(lambda x: f"{int(x)}%" if pd.notnull(x) else "No Band")
                df = df.rename(columns={'Band': 'Price Band'})
            # --- Merge listing date info ---
            if not df.empty and listing_dates_map:
                df['Listing Date'] = df['name'].map(listing_dates_map)
            # --- Convert market cap to Cr ---
            if not df.empty and 'market_cap_basic' in df.columns:
                df['market_cap_basic'] = (df['market_cap_basic'] / 1e7).round(2)
                df = df.rename(columns={'market_cap_basic': 'Market Cap (Cr.)'})
            # Apply post-fetch filters
            for f in post_filters:
                df = df[f(df)]
            st.session_state['scan_df'] = df.copy()
        except Exception as e:
            st.error(f"Error: {e}\nTry selecting a different region or adjusting your filters/columns.")

# --- (NSE Bulk Deals related code removed as per user request) ---

# --- Use cached scan results for summary/chart/table (always outside Run Scan block) ---
if 'scan_df' in st.session_state and not st.session_state['scan_df'].empty:
    df = st.session_state['scan_df']
    st.write(f"Total Results: {len(df)}")
    # --- Add missing 'No Band' symbols to df with placeholder data ONLY if 'No Band' is selected ---
    if "No Band" in selected_bands:
        import numpy as np
        cols = list(df.columns)
        rows_to_add = []
        no_band_symbols = set(price_bands_df[price_bands_df['Band'].isna()]['Symbol'])
        screener_symbols = set(df['name'])  # Replace df with your main screener DataFrame variable if different
        missing_in_screener = no_band_symbols - screener_symbols
        for sym in missing_in_screener:
            row = {col: np.nan for col in cols}
            row['name'] = sym
            rows_to_add.append(row)
        if rows_to_add:
            import pandas as pd
            df = pd.concat([df, pd.DataFrame(rows_to_add)], ignore_index=True)
            st.session_state['scan_df'] = df
    # --- Unified toggle: Sector / Industry / Search Results ---
    summary_choice = st.radio(
        label="",
        options=["Sector", "Industry", "Search Results"],
        horizontal=True,
        index=0,
        key="summary_choice_toggle",
        format_func=lambda x: f" {x}"
    )

    if summary_choice == "Search Results":
        st.dataframe(df)
    else:
        group_col = 'sector' if summary_choice == "Sector" else 'industry'
        label_title = summary_choice
        group_counts = df[group_col].value_counts().reset_index()
        group_counts.columns = [group_col, 'count']
        total_stocks = int(df.shape[0])
        donut_colors = px.colors.qualitative.Plotly[:len(group_counts)]
        fig = go.Figure(data=[go.Pie(
            labels=group_counts[group_col],
            values=group_counts['count'],
            hole=0.6,
            marker=dict(colors=donut_colors, line=dict(color='#222', width=1)),
            textinfo='percent',
            textposition='inside',
            insidetextorientation='radial',
            sort=False,
            showlegend=False
        )])
        fig.update_layout(
            annotations=[dict(
                text=f"<b>Total Stocks:<br>{total_stocks}</b>",
                x=0.5, y=0.5, font_size=20, showarrow=False, font_color="#fff", align="center"
            )],
            showlegend=False,
            margin=dict(l=0, r=0, t=10, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('<div class="scroll-table">', unsafe_allow_html=True)
        st.markdown(f"""
        <style>
        .summary-table {{width:100%;border-collapse:collapse;background:rgba(20,22,30,0.98);font-size:1.13rem;}}
        .summary-table th, .summary-table td {{padding:0.45em 0.9em;text-align:left;}}
        .summary-table th {{color:#7fd7ff;font-weight:700;border-bottom:2px solid #222;}}
        .summary-table tr {{border-bottom:1px solid #222;}}
        .summary-table td {{color:#eee;}}
        .color-dot {{height:0.95em;width:0.95em;display:inline-block;border-radius:50%;margin-right:0.5em;vertical-align:middle;}}
        </style>
        """, unsafe_allow_html=True)
        table_html = f"<table class='summary-table'>"
        table_html += f"<tr><th>{label_title}</th><th>Number of Stocks Passed</th><th>% of Stocks in Scan</th></tr>"
        for idx, row in group_counts.iterrows():
            color = donut_colors[idx % len(donut_colors)]
            pct = (row['count'] / total_stocks) * 100
            table_html += f"<tr><td><span class='color-dot' style='background:{color}'></span>{row[group_col]}</td>"
            table_html += f"<td>{row['count']}</td>"
            table_html += f"<td>{pct:.1f}%</td></tr>"
        table_html += "</table>"
        st.markdown(table_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("Run a scan to see results.")
