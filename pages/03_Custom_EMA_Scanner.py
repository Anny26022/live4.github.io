import streamlit as st
st.set_page_config(
    page_title="Custom EMA Scanner",
    page_icon="📈",
    layout="centered",
    initial_sidebar_state="collapsed"
)
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.news_modal import show_news_for_symbol
import pandas as pd
from tradingview_screener import Query, Column, col
from utils.listing_dates import get_listing_date_map_cached
import plotly.express as px
import plotly.graph_objects as go
from streamlit.components.v1 import html
import time
import logging

# --- Ensure session state variables are initialized ---
if 'price_bands_loading' not in st.session_state:
    st.session_state.price_bands_loading = False
if 'price_bands_df' not in st.session_state:
    st.session_state.price_bands_df = pd.DataFrame()
if 'bands_last_update' not in st.session_state:
    st.session_state.bands_last_update = None

# Page Configuration

# Initialize price bands in session state if not present
if 'price_bands_df' not in st.session_state:
    st.session_state.price_bands_df = pd.DataFrame()
    st.session_state.bands_last_update = None
    st.session_state.price_bands_loading = False

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
        --animation-duration: 400ms;
        --stagger-delay: 50ms;
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
            transform: translate3d(0, 20px, 0);
            opacity: 0;
        }
        to {
            transform: translate3d(0, 0, 0);
            opacity: 1;
        }
    }

    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }

    @keyframes scaleIn {
        from {
            transform: translate3d(0, 0, 0) scale(0.98);
            opacity: 0;
        }
        to {
            transform: translate3d(0, 0, 0) scale(1);
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
        animation: fadeIn var(--animation-duration) var(--animation-timing) forwards;
        will-change: opacity;
    }

    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 1000px !important;
        opacity: 0;
        animation: slideInUp var(--animation-duration) var(--animation-timing) 100ms forwards;
        will-change: transform, opacity;
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
        animation: scaleIn var(--animation-duration) var(--animation-timing) 200ms forwards;
        position: relative;
        overflow: hidden;
        transform: translate3d(0, 0, 0);
        backface-visibility: hidden;
        perspective: 1000px;
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
        transform: translate3d(0, 0, 0);
        opacity: 0;
        animation: slideInUp var(--animation-duration) var(--animation-timing) 300ms forwards;
        will-change: transform, opacity;
    }

    .header-subtitle {
        font-size: 1rem;
        color: rgba(255, 255, 255, 0.9);
        margin-top: 0.5rem;
        font-weight: 400;
        transform: translate3d(0, 0, 0);
        opacity: 0;
        animation: slideInUp var(--animation-duration) var(--animation-timing) 400ms forwards;
        will-change: transform, opacity;
    }

    /* Filter Card Animations */
    .filter-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 0.75rem;
        padding: 1.25rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        transition: transform 200ms var(--animation-timing);
        opacity: 0;
        animation: scaleIn var(--animation-duration) var(--animation-timing) forwards;
        position: relative;
        transform: translate3d(0, 0, 0);
        backface-visibility: hidden;
    }

    .filter-card:hover {
        transform: translate3d(0, -2px, 0);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
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
        transition: transform 200ms var(--animation-timing),
                    box-shadow 200ms var(--animation-timing);
        will-change: transform, box-shadow;
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
        transition: transform 200ms var(--animation-timing),
                    box-shadow 200ms var(--animation-timing);
        position: relative;
        overflow: hidden;
        transform: translate3d(0, 0, 0);
        backface-visibility: hidden;
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
        transform: translate3d(0, -2px, 0);
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
        transition: none !important;
        animation: none !important;
    }

    .stMultiSelect > div > div > div[data-focused="true"] {
        transform: translateY(-1px);
    }

    /* Checkbox Animation */
    .stCheckbox > label > div[role="checkbox"] {
        transition: none !important;
        animation: none !important;
    }

    .stCheckbox > label > div[role="checkbox"][data-checked="true"] {
        animation: pulse 0.3s var(--animation-timing);
    }

    /* Table Row Animations */
    .stDataFrame tbody tr {
        opacity: 0;
        animation: fadeIn 300ms var(--animation-timing) forwards;
        animation-delay: calc(var(--stagger-delay) * var(--row-index, 0));
        will-change: opacity, transform;
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
        content: none !important;
    }

    .shimmer-loader {
        display: none !important;
    }

    /* Responsive Animations */
    @media (prefers-reduced-motion: reduce) {
        *,
        ::before,
        ::after {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
            scroll-behavior: auto !important;
        }
        
        .stApp,
        .block-container,
        .header-section,
        .header-title,
        .header-subtitle,
        .filter-card {
            animation: none !important;
            opacity: 1 !important;
        }
    }

    /* Filter Section */
    .filter-section {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1rem;
        margin-bottom: 1rem;
        opacity: 0;
        animation: fadeIn var(--animation-duration) var(--animation-timing) 500ms forwards;
        will-change: opacity;
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

    /* Optimize Chart Animations */
    [data-testid="stChart"] {
        opacity: 0;
        animation: fadeIn var(--animation-duration) var(--animation-timing) 600ms forwards;
        will-change: opacity;
    }

    /* Remove Unnecessary Transitions */
    .stMultiSelect [data-baseweb="tag"],
    .stCheckbox > label > div[role="checkbox"][data-checked="true"],
    div[data-baseweb="popover"],
    .stDataFrame thead th {
        transition: none !important;
        animation: none !important;
    }

    /* Fix Streamlit sidebar background and responsiveness */
    @media (max-width: 800px) {
        section[data-testid="stSidebar"] {
            background: #232526 !important;
            opacity: 1 !important;
            box-shadow: 0 2px 10px 0 rgba(31, 38, 135, 0.10);
            color: #fff !important;
        }
    }
    section[data-testid="stSidebar"] {
        background: #232526 !important;
        opacity: 1 !important;
        color: #fff !important;
        box-shadow: 0 2px 10px 0 rgba(31, 38, 135, 0.10);
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
        "india"
    ]
    selected_regions = st.multiselect(
        "Select Market Region(s)",
        options=market_regions,
        default=["india"],
        key="market_region"
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # --- EMA Options (always defined for later use) ---
    ema_options = [
        ("Above 200 Days MA", "EMA200"),
        ("Above 150 Days MA", "EMA150"),
        ("Above 50 Days MA", "EMA50"),
        ("Above 20 Days MA", "EMA20"),
        ("Above 10 Days MA", "EMA10"),
    ]

    # Instrument Type Filter UI
    INSTRUMENT_TYPES = {
        "stock": "Stocks"
    }
    selected_instrument_types = st.multiselect(
        "Instrument Types",
        options=list(INSTRUMENT_TYPES.keys()),
        default=["stock"],
        format_func=lambda x: INSTRUMENT_TYPES[x],
        help="Select one or more instrument types to include in the scan."
    )
    if not selected_instrument_types:
        st.warning("⚠️ Please select at least one instrument type to continue.")
        st.stop()

    # --- Disable all filters if only Funds/ETFs selected ---
    disable_all_filters = (
        len(selected_instrument_types) == 1 and selected_instrument_types[0] == "fund"
    )
    allow_exchange_select_only = disable_all_filters

    # EMA Filters Section
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="filter-card">', unsafe_allow_html=True)
        st.markdown('<h3 class="filter-title">Price Above Moving Averages</h3>', unsafe_allow_html=True)
        enable_above_ema = st.checkbox("Enable Above EMA Filters", value=not disable_all_filters, disabled=disable_all_filters)
        if enable_above_ema:
            selected_above = st.multiselect(
                "Select Moving Averages:",
                [label for label, _ in ema_options],
                default=["Above 200 Days MA", "Above 150 Days MA", "Above 50 Days MA"],
                key="ema_above",
                disabled=disable_all_filters
            )
        else:
            selected_above = []
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="filter-card">', unsafe_allow_html=True)
        st.markdown('<h3 class="filter-title">Price Below Moving Averages</h3>', unsafe_allow_html=True)
        enable_below_ema = st.checkbox("Enable Below EMA Filters", value=False, disabled=disable_all_filters)
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
                key="ema_below",
                disabled=disable_all_filters
            )
        else:
            selected_below = []
        st.markdown('</div>', unsafe_allow_html=True)

    # Additional Filters Section
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="filter-card">', unsafe_allow_html=True)
        st.markdown('<h3 class="filter-title">Price Levels</h3>', unsafe_allow_html=True)
        enable_near_highs = st.checkbox("Near New Highs", value=False, disabled=disable_all_filters)
        if enable_near_highs:
            near_highs = st.multiselect(
                "Select High Points:",
                ["1 Month High", "3 Month High", "52 Week High"],
                key="near_highs",
                disabled=disable_all_filters
            )
        else:
            near_highs = []
        enable_52w_low = st.checkbox("% from 52w Low Price Range", value=False, disabled=disable_all_filters)
        if enable_52w_low:
            col_min, col_max = st.columns(2)
            with col_min:
                low_52w_min = st.number_input("Min %", min_value=0, max_value=1000, value=30, disabled=disable_all_filters)
            with col_max:
                low_52w_max = st.number_input("Max %", min_value=0, max_value=1000, value=1000, disabled=disable_all_filters)
            use_52w_low = True
        else:
            low_52w_min = 30
            low_52w_max = 1000
            use_52w_low = False
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="filter-card">', unsafe_allow_html=True)
        st.markdown('<h3 class="filter-title">Market Parameters</h3>', unsafe_allow_html=True)
        st.markdown("**Market Cap Range (Cr.)**")
        col_min, col_max = st.columns(2)
        with col_min:
            market_cap_min = st.number_input("Min", min_value=0, max_value=5000000, value=0, disabled=disable_all_filters)
        with col_max:
            market_cap_max = st.number_input("Max", min_value=0, max_value=5000000, value=500000, disabled=disable_all_filters)
        st.markdown("**Stock Price Range (₹)**")
        col_min, col_max = st.columns(2)
        with col_min:
            stock_price_min = st.number_input("Min Price", min_value=0, max_value=150000, value=0, disabled=disable_all_filters)
        with col_max:
            stock_price_max = st.number_input("Max Price", min_value=0, max_value=150000, value=150000, disabled=disable_all_filters)
        st.markdown('</div>', unsafe_allow_html=True)

    # Advanced Fundamental Filters
    st.markdown("""
    <style>
    .adv-filters-title {
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)
    st.markdown('<div class="adv-filters-title">Advanced Fundamental Filters (Optional)</div>', unsafe_allow_html=True)
    st.warning('🚧 This section is under development. Filters will be available soon!', icon="⚠️")

    # Show all advanced fundamental filters as disabled (visible but not selectable)
    col1, col2 = st.columns(2)
    with col1:
        sales_growth_5y = st.checkbox("Sales Growth 5 Years(%) >", disabled=True)
        pe_range = st.checkbox("P/E Range", disabled=True)
        roe = st.checkbox("ROE(%) >", disabled=True)
        de = st.checkbox("D/E", disabled=True)
        roe_between = st.checkbox("Filter ROE between two values (e.g. -5 and 0)", disabled=True)
    with col2:
        roce = st.checkbox("ROCE(%) >", disabled=True)
        peg = st.checkbox("0 < PEG < 1", disabled=True)
        opm_ttm = st.checkbox("OPM TTM(%) >", disabled=True)

    # Turnover in Crores Filter (compact, checkbox inline)
    st.markdown('<div class="filter-card" style="padding-bottom:0.5rem;">', unsafe_allow_html=True)
    turnover_cols = st.columns([1, 4, 2, 2, 2])
    with turnover_cols[0]:
        turnover_filter_enabled = st.checkbox("", value=False, key="turnover_enabled", disabled=disable_all_filters)
    with turnover_cols[1]:
        st.markdown('<span style="font-weight:600; font-size:1rem; line-height:2.4;">Turnover (in Cr.)</span>', unsafe_allow_html=True)
    with turnover_cols[2]:
        turnover_period = st.selectbox(
            "Period",
            options=["10-day", "30-day", "60-day", "90-day"],
            index=0,
            key="turnover_period",
            disabled=not turnover_filter_enabled or disable_all_filters
        )
    with turnover_cols[3]:
        turnover_min = st.number_input(
            "Min",
            min_value=0.0, max_value=100000.0, value=0.0, step=0.1,
            key="turnover_min",
            disabled=not turnover_filter_enabled or disable_all_filters
        )
    with turnover_cols[4]:
        turnover_max = st.number_input(
            "Max",
            min_value=0.0, max_value=100000.0, value=100000.0, step=0.1,
            key="turnover_max",
            disabled=not turnover_filter_enabled or disable_all_filters
        )
    st.markdown('</div>', unsafe_allow_html=True)

    # Exchange Selection
    st.markdown('<div class="filter-card">', unsafe_allow_html=True)
    st.markdown('<h3 class="filter-title">Exchange Selection</h3>', unsafe_allow_html=True)
    exchange_options = ["NSE", "BSE"]
    selected_exchanges = st.multiselect(
        "Select Exchange(s):",
        options=exchange_options,
        default=["NSE"],
        key="exchange_select",
        disabled=not allow_exchange_select_only and disable_all_filters
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Optional 200 MA Uptrend Filter (from 07_NSE_200EMA_Uptrend.py) ---
    with st.expander("Optional: 200 MA Uptrend Filter", expanded=False):
        apply_200ma_uptrend = st.checkbox("Enable 200 EMA/SMA Uptrend Filter (NSE/BSE)", value=False, disabled=disable_all_filters)
        if apply_200ma_uptrend:
            # Market selection (India only)
            from src.tradingview_screener.markets_list import MARKETS
            market_names = [name for name, code in MARKETS if code == 'india']
            market_codes = {name: code for name, code in MARKETS if code == 'india'}
            selected_market_name = market_names[0]
            selected_market = market_codes[selected_market_name]
            # Exchange selection
            exchange_options = ["NSE", "BSE"]
            exchange_input = st.selectbox("Select Exchange (Uptrend Filter)", exchange_options, index=0, key="customema_uptrend_exchange", disabled=disable_all_filters)
            # MA type
            ma_type = st.radio("Select Moving Average Type (Uptrend Filter)", ["EMA", "SMA"], index=0, horizontal=True, key="customema_uptrend_ma_type", disabled=disable_all_filters)
            ma_prefix = "EMA200" if ma_type == "EMA" else "SMA200"
            # Periods
            period_options = [("1 Month", "1M"), ("3 Months", "3M"), ("6 Months", "6M")]
            default_period_labels = ["1 Month"]
            selected_period_labels = st.multiselect(
                "Select MA history periods to compare (Uptrend Filter)",
                [label for label, code in period_options],
                default=default_period_labels,
                key="customema_uptrend_periods",
                disabled=disable_all_filters
            )
            selected_periods = [code for label, code in period_options if label in selected_period_labels]
            # Build uptrend filter
            ma_filters = []
            ma_columns = [ma_prefix] + [f"{ma_prefix}|{p}" for p in selected_periods]
            for i in range(len(ma_columns) - 1):
                ma_filters.append(col(ma_columns[i]) > col(ma_columns[i + 1]))
            # Optionally: store these filters in session state or inject into your main query logic below
            st.info("200 EMA/SMA Uptrend filter will be applied to your custom scan query below.")
            st.session_state['customema_uptrend_filter'] = {
                'enabled': True,
                'market': selected_market,
                'exchange': exchange_input,
                'ma_type': ma_type,
                'ma_prefix': ma_prefix,
                'periods': selected_periods,
                'ma_filters': ma_filters,
                'ma_columns': ma_columns
            }
        else:
            st.session_state['customema_uptrend_filter'] = {'enabled': False}

    # --- UI: Price Band Filter ---
    st.markdown('<div class="filter-card">', unsafe_allow_html=True)
    st.markdown('<h3 class="filter-title">Price Band</h3>', unsafe_allow_html=True)

    # Fetch price bands in background after page loads
    if not st.session_state.price_bands_loading and st.session_state.price_bands_df.empty:
        st.session_state.price_bands_loading = True
        with st.spinner("Loading price bands..."):
            from pages.price_bands import fetch_price_bands
            st.session_state.price_bands_df, st.session_state.bands_last_update = fetch_price_bands()
            st.session_state.price_bands_loading = False
            st.rerun()

    if not st.session_state.price_bands_df.empty:
        band_options = sorted(st.session_state.price_bands_df['Band'].dropna().unique().tolist())
        band_options = [f"{int(b)}%" for b in band_options]
        band_options.append("No Band")  # Add 'No Band' option for 'no band'
        # Default should include 5%, 10%, 20%, and No Band
        default_selected_bands = [x for x in band_options if x in ["10%", "20%", "5%", "No Band"]]
        selected_bands = st.multiselect("Select Price Band(s) (optional)", band_options, default=default_selected_bands, key="price_band", disabled=disable_all_filters)
    else:
        selected_bands = []
        if not st.session_state.price_bands_loading:
            st.info("Price bands will be loaded when you start scanning.")
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
    # Build below_label_map dynamically to match label style
    below_options = [
        ("Below 200 Days MA", "EMA200"),
        ("Below 150 Days MA", "EMA150"),
        ("Below 50 Days MA", "EMA50"),
        ("Below 20 Days MA", "EMA20"),
        ("Below 10 Days MA", "EMA10"),
    ]
    below_label_map = {below: above for (below, _), (above, _) in zip(below_options, ema_options)}

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
    if selected_bands and not st.session_state.price_bands_df.empty:
        allowed_symbols = []
        # Add symbols for selected numeric bands
        band_values = [float(b.replace('%','')) for b in selected_bands if b != "No Band"]
        if band_values:
            allowed_symbols += st.session_state.price_bands_df[st.session_state.price_bands_df['Band'].isin(band_values)]['Symbol'].tolist()
        # Add symbols for 'No Band' selection
        if "No Band" in selected_bands:
            allowed_symbols += st.session_state.price_bands_df[st.session_state.price_bands_df['Band'].isna()]['Symbol'].tolist()
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
    if 'use_float' not in locals():
        use_float = False
    if use_float:
        other_filters.append(Column("float_shares_percent_current").between(float_min, float_max))
    # --- REMOVE turnover filter from query construction ---
    # (Was: if turnover_filter_enabled: ... other_filters.append(...))

    # Add F&O support filter to the list before combining
    other_filters.append(Column('type').isin(selected_instrument_types))

    # Combine all filters
    query_filters = ema_filters + [f for f in other_filters if not callable(f)]

    # Inject 200 EMA/SMA Uptrend Filter if enabled
    uptrend_filter = st.session_state.get('customema_uptrend_filter', {'enabled': False})
    if uptrend_filter.get('enabled'):
        # Only add if not already present (avoid double-injection)
        query_filters += uptrend_filter['ma_filters']
        # Optionally, enforce exchange and market
        if 'exchange' in uptrend_filter and uptrend_filter['exchange']:
            query_filters.append(col('exchange') == uptrend_filter['exchange'])

    # --- DEBUG: Log EMA and Turnover Filters ---
    logging.basicConfig(level=logging.INFO)
    if enable_above_ema or enable_below_ema or turnover_filter_enabled:
        logging.info('--- Filter Debug Info ---')
        if enable_above_ema:
            logging.info(f'Above EMA filters: {selected_above}')
        if enable_below_ema:
            logging.info(f'Below EMA filters: {selected_below}')
        if turnover_filter_enabled:
            logging.info(f'Turnover filter: period={turnover_period}, min={turnover_min}, max={turnover_max}')
        logging.info(f'Query filters: {query_filters}')

    # --- Run Query Button ---
    st.markdown('<div style="margin-top: 1rem;">', unsafe_allow_html=True)

    # Check if price bands are still loading
    if st.session_state.price_bands_loading:
        st.warning("⌛ Please wait while price bands are loading...")
        st.button("🚀 Run Query", type="primary", disabled=True, help="Button is disabled while price bands are loading")
    else:
        run_query_button = st.button(
            "🚀 Run Query",
            type="primary",
            help="Execute the query and fetch results",
            key="run_query_button",
            disabled=disable_all_filters and not allow_exchange_select_only
        )

    st.markdown('</div>', unsafe_allow_html=True)

    if run_query_button and not st.session_state.price_bands_loading:
        if contradictory_emas:
            st.error("Cannot run scan with contradictory EMA selections. Please fix your selection.")
        else:
            try:
                with st.spinner(""):
                    # Show optimized loading animation
                    loading_container = st.empty()
                    loading_container.markdown("""
                    <div class="loading-animation-container" style="text-align: center; padding: 20px;">
                        <div style="font-size: 1.2rem; color: #4CAF50; margin-bottom: 15px;">🔄 Fetching Results...</div>
                        <div class="shimmer-loader" style="width: 80%; height: 30px; margin: 10px auto;"></div>
                        <div class="shimmer-loader" style="width: 60%; height: 30px; margin: 10px auto;"></div>
                        <div class="shimmer-loader" style="width: 70%; height: 30px; margin: 10px auto;"></div>
                    </div>
                    """, unsafe_allow_html=True)

                # Special case for Funds/ETFs only
                if (
                    len(selected_instrument_types) == 1 and selected_instrument_types[0] == "fund"
                    and len(selected_regions) == 1 and selected_regions[0] == "india"
                ):
                    # Only fetch required columns (use 'name' instead of 'ticker' for TradingView India)
                    exchange_choices = ["NSE", "BSE"]
                    dfs = []
                    for exch in exchange_choices:
                        q = Query().set_markets('india').where(col('type') == 'fund').where(col('exchange') == exch).select('name', 'exchange', 'type').offset(0).limit(20000)
                        count, df_exch = q.get_scanner_data()
                        dfs.append(df_exch)
                    df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

                    # Rename 'name' to 'ticker' for display
                    if 'name' in df.columns:
                        # Remove any existing 'ticker' column to avoid duplicates
                        if 'ticker' in df.columns:
                            df.drop(columns=['ticker'], inplace=True)
                        df.rename(columns={'name': 'ticker'}, inplace=True)

                    # Merge Price Band if available
                    if not df.empty and not st.session_state.price_bands_df.empty:
                        df = df.merge(
                            st.session_state.price_bands_df.rename(columns={'Symbol': 'ticker'}),
                            on='ticker', how='left'
                        )
                        df['Price Band'] = df['Band'].apply(lambda x: f"{int(x)}%" if pd.notnull(x) else "No Band")
                        df.drop(columns=['Band'], inplace=True, errors='ignore')
                    else:
                        df['Price Band'] = ""

                    # Ensure only required columns and correct order
                    display_cols = ['ticker', 'exchange', 'type', 'Price Band']
                    for col in display_cols:
                        if col not in df.columns:
                            df[col] = ""
                    df = df[display_cols]

                    # Optionally configure pretty column names
                    column_config = {
                        "ticker": "Ticker",
                        "exchange": "Exchange",
                        "type": "Type",
                        "Price Band": "Price Band"
                    }

                    st.dataframe(df, use_container_width=True, column_config=column_config)
                else:
                    # --- Ensure turnover columns are always present if turnover filter is enabled ---
                    turnover_required_cols = ["average_volume_10d_calc", "average_volume_30d_calc", "average_volume_60d_calc", "average_volume_90d_calc", "close"]
                    select_cols = ["name", "close", "volume", "market_cap_basic", "sector", "industry", "price_52_week_low", "price_52_week_high", "average_volume_10d_calc", "average_volume_30d_calc", "average_volume_60d_calc", "average_volume_90d_calc", "type"]
                    # If user has custom selection, ensure required cols are present
                    if 'user_selected_columns' in locals() and isinstance(user_selected_columns, list):
                        select_cols = user_selected_columns.copy()
                        for col in turnover_required_cols:
                            if col not in select_cols:
                                select_cols.append(col)
                    q = Query().select(*select_cols)
                    # Correct market logic as in Query.set_markets
                    if selected_regions:
                        if len(selected_regions) == 1:
                            q.url = f"https://scanner.tradingview.com/{selected_regions[0]}/scan"
                            q.query['markets'] = [selected_regions[0]]
                        else:
                            q.url = "https://scanner.tradingview.com/global/scan"
                            q.query['markets'] = list(selected_regions)
                    q = q.where(*query_filters)
                    # Set row limit to 20000
                    q = q.limit(20000)
                    count, df = q.get_scanner_data()
                
                # Update loading indicator with success message
                loading_container.markdown(f"""
                <div style="text-align: center; padding: 20px;">
                    <div style="font-size: 1.2rem; color: #4CAF50;">✅ Successfully fetched {len(df)} results!</div>
                </div>
                """, unsafe_allow_html=True)
                time.sleep(1)  # Brief pause to show success message
                loading_container.empty()  # Clear the loading message

                # --- ADVANCED FUNDAMENTAL FILTERS (POST-FETCH) ---
                # Apply advanced filters to df based on user inputs
                if not df.empty:
                    # P/E Range
                    if 'pe_range' in locals() and pe_range:
                        if 'pe_min' in locals() and 'pe_max' in locals():
                            if 'price_earnings_ttm' in df.columns:
                                df = df[(df['price_earnings_ttm'] >= pe_min) & (df['price_earnings_ttm'] <= pe_max)]
                    # ROE (%) >
                    if 'roe' in locals() and roe:
                        if 'roe_val' in locals():
                            if 'return_on_equity' in df.columns:
                                df = df[df['return_on_equity'] >= roe_val]
                    # D/E
                    if 'de' in locals() and de:
                        if 'de_max' in locals():
                            if 'debt_to_equity' in df.columns:
                                df = df[df['debt_to_equity'] <= de_max]
                    # ROE between
                    if 'roe_between' in locals() and roe_between:
                        if 'roe_between_min' in locals() and 'roe_between_max' in locals():
                            if 'return_on_equity' in df.columns:
                                df = df[(df['return_on_equity'] >= roe_between_min) & (df['return_on_equity'] <= roe_between_max)]
                    # ROCE (%) >
                    if 'roce' in locals() and roce:
                        if 'roce_val' in locals():
                            if 'return_on_invested_capital' in df.columns:
                                df = df[df['return_on_invested_capital'] >= roce_val]
                    # PEG (0 < PEG < 1)
                    if 'peg' in locals() and peg:
                        if 'peg_min' in locals() and 'peg_max' in locals():
                            if 'peg_ratio' in df.columns:
                                df = df[(df['peg_ratio'] > peg_min) & (df['peg_ratio'] < peg_max)]
                    # OPM TTM(%) >
                    if 'opm_ttm' in locals() and opm_ttm:
                        if 'opm_ttm_val' in locals():
                            if 'operating_margin_ttm' in df.columns:
                                df = df[df['operating_margin_ttm'] >= opm_ttm_val]
                st.session_state['scan_df'] = df.copy()
            except Exception as e:
                st.error(f"Error: {e}\nTry selecting a different region or adjusting your filters/columns.")

    # --- Apply turnover filter post-fetch ---
    if (
        turnover_filter_enabled and
        'scan_df' in st.session_state and
        not st.session_state['scan_df'].empty
    ):
        df = st.session_state['scan_df']
        period_map = {
            "10-day": "average_volume_10d_calc",
            "30-day": "average_volume_30d_calc",
            "60-day": "average_volume_60d_calc",
            "90-day": "average_volume_90d_calc",
        }
        selected_vol_col = period_map[turnover_period]
        df['Turnover_Cr'] = (df[selected_vol_col] * df['close'] / 10000000).round(2)
        df = df[df['Turnover_Cr'].between(turnover_min, turnover_max)]
        st.session_state['scan_df'] = df.copy()

# --- Use cached scan results for summary/chart/table (always outside Run Scan block) ---
if 'scan_df' in st.session_state and not st.session_state['scan_df'].empty:
    df = st.session_state['scan_df'].reset_index(drop=True)
    st.write(f"Total Results: {len(df)}")
    # --- Unified toggle: Sector / Industry / Search Results / Live News ---
    # Only set the radio index for redirect, otherwise let Streamlit manage the selection
    if run_query_button and not st.session_state.price_bands_loading:
        st.session_state['scan_redirect'] = True
    summary_options = ["Sector", "Industry", "Search Results", "Live News"]
    if st.session_state.get('scan_redirect', False):
        summary_choice_index = 2  # 'Search Results'
        st.session_state['scan_redirect'] = False
    else:
        summary_choice_index = None
    summary_choice = st.radio(
        label="",
        options=summary_options,
        horizontal=True,
        index=summary_choice_index if summary_choice_index is not None else 0,
        key="summary_choice_toggle",
        format_func=lambda x: f" {x}"
    )
    # Always use st.session_state['summary_choice_toggle'] for content display
    if st.session_state['summary_choice_toggle'] == "Search Results":
        st.dataframe(df)
        
        # Add Copy Tickers Section
        st.markdown("### 📋 Copy Tickers")
        
        # Create tabs for different copy formats
        copy_format_tab1, copy_format_tab2, copy_format_tab3 = st.tabs(["Simple Format", "Industry-wise", "Sector-wise"])
        
        with copy_format_tab1:
            # Simple NSE:SYMBOL format
            if not df.empty:
                simple_tickers = ','.join([f"NSE:{symbol}" for symbol in df['name']])
                st.text_area(
                    "Copy Tickers (NSE:SYMBOL format)",
                    value=simple_tickers,
                    height=100,
                    help=f"Simple comma-separated tickers ({len(df)} symbols)"
                )
        
        with copy_format_tab2:
            # Industry-wise categorized format
            if not df.empty and 'industry' in df.columns:
                # Group by industry and sort by count descending
                industry_groups = df.groupby('industry')['name'].agg(list).reset_index()
                industry_groups['count'] = industry_groups['name'].apply(len)
                industry_groups = industry_groups.sort_values('count', ascending=False)
                
                # Format the text
                industry_text = []
                for _, row in industry_groups.iterrows():
                    if pd.notna(row['industry']) and row['industry']:  # Check for valid industry name
                        symbols = [f"NSE:{symbol}" for symbol in row['name']]
                        industry_text.append(f"###{row['industry']}({row['count']})")
                        industry_text.append(','.join(symbols))
                
                industry_formatted = '\n'.join(industry_text)
                st.text_area(
                    "Copy Tickers (Industry-wise)",
                    value=industry_formatted,
                    height=300,
                    help="Tickers categorized by industry"
                )
            elif not df.empty:
                st.info("Industry information not available for selected instrument type.")
        
        with copy_format_tab3:
            # Sector-wise categorized format
            if not df.empty and 'sector' in df.columns:
                # Group by sector and sort by count descending
                sector_groups = df.groupby('sector')['name'].agg(list).reset_index()
                sector_groups['count'] = sector_groups['name'].apply(len)
                sector_groups = sector_groups.sort_values('count', ascending=False)
                
                # Format the text
                sector_text = []
                for _, row in sector_groups.iterrows():
                    if pd.notna(row['sector']) and row['sector']:  # Check for valid sector name
                        symbols = [f"NSE:{symbol}" for symbol in row['name']]
                        sector_text.append(f"###{row['sector']}({row['count']})")
                        sector_text.append(','.join(symbols))
                
                sector_formatted = '\n'.join(sector_text)
                st.text_area(
                    "Copy Tickers (Sector-wise)",
                    value=sector_formatted,
                    height=300,
                    help="Tickers categorized by sector"
                )
            elif not df.empty:
                st.info("Sector information not available for selected instrument type.")
        
    elif st.session_state['summary_choice_toggle'] == "Live News":
        st.markdown("### 📰 Live News for All Results")
        st.markdown("""
            <style>
            .compact-search-bar input {
                max-width: 200px !important;
                min-width: 120px !important;
                font-size: 0.95rem !important;
                padding: 0.22rem 0.7rem !important;
                border-radius: 6px !important;
                border: 1.2px solid #5fa8d3 !important;
                background: rgba(255,255,255,0.10) !important;
                color: #eaeaea !important;
                margin-bottom: 0.18rem !important;
                margin-top: 0.0rem !important;
                box-shadow: 0 1.5px 6px 0 rgba(95,168,211,0.06);
            }
            .compact-search-bar input:focus {
                border: 2px solid #f1c40f !important;
                background: rgba(255,255,255,0.14) !important;
            }
            .compact-search-bar label {
                font-size: 0.89rem !important;
                color: #5fa8d3 !important;
                font-weight: 600 !important;
                margin-bottom: 0.07rem !important;
            }
            </style>
        """, unsafe_allow_html=True)
        search_col, _ = st.columns([1, 8])
        with search_col:
            symbol_search = st.text_input(
                "Search Symbol(s) in Results",
                "",
                key="news_symbol_search",
                help="Type to filter result symbols (comma-separated for multiple)",
                label_visibility="collapsed",
                placeholder="🔍 Symbol(s)..."
            )
            st.markdown('<div class="compact-search-bar"></div>', unsafe_allow_html=True)
        if symbol_search.strip():
            search_terms = [s.strip().upper() for s in symbol_search.split(",") if s.strip()]
            filtered_symbols = [symbol for symbol in df['name'] if any(term in symbol.upper() for term in search_terms)]
        else:
            filtered_symbols = list(df['name'])
        if len(filtered_symbols) == 0:
            st.info("No symbols match your search.")
        for symbol in filtered_symbols:
            # --- Inline, interactive calendar icon and direct date selection for each symbol ---
            col1, col2 = st.columns([7, 3])
            with col1:
                with st.expander(f"News for {symbol}", expanded=False):
                    show_news_for_symbol(symbol, date_filter=st.session_state.get(f"news_date_{symbol}", None))
            with col2:
                selected_date = st.date_input(
                    label="",
                    key=f"news_date_{symbol}",
                    value=None,
                    help=f"Pick a date to filter news for {symbol}",
                    format="YYYY-MM-DD"
                )
                st.markdown(
                    f'<span style="font-size:1.1rem;color:#5fa8d3;font-weight:700;">📅</span>',
                    unsafe_allow_html=True
                )
    else:
        if st.session_state['summary_choice_toggle'] == "Sector" and 'sector' in df.columns:
            group_col = 'sector'
        elif st.session_state['summary_choice_toggle'] == "Industry" and 'industry' in df.columns:
            group_col = 'industry'
        else:
            group_col = None
        label_title = st.session_state['summary_choice_toggle']
        if group_col:
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
            st.info(f"{label_title} information not available for selected instrument type.")
else:
    st.info("Run a scan to see results.")