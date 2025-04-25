import streamlit as st
from src.animation_utils import (
    animation_manager,
    smooth_transition,
    fade_in,
    slide_in,
    pulse,
    optimize_animations
)
from src.performance_monitor import track_performance
import time

# Initialize performance optimizations
optimize_animations()
smooth_transition()

# Preload animations
animation_manager.preload_animations([
    "assets/loading.json",
    "assets/success.json",
    "assets/error.json"
])

# Hide Streamlit default elements
hide_streamlit_style = """
<style>
    /* Hide Streamlit Sidebar */
    section[data-testid="stSidebar"] {display: none;}
    .css-1d391kg {display: none;}
    .e1fqkh3o1 {display: none;}
    div[data-testid="stSidebarNav"] {display: none;}
    div[data-testid="collapsedControl"] {display: none;}
    
    /* Hide other Streamlit elements */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* Ensure sidebar space is removed */
    .main .block-container {
        padding-left: 0rem;
        padding-right: 0rem;
        max-width: 100%;
    }

    /* Force full width */
    .appview-container .main {
        width: 100%;
        margin: 0;
        padding: 0;
    }

    .block-container {
        max-width: 100% !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
        margin: 0 !important;
    }
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

@track_performance
def main():
    st.set_page_config(
        page_title="TradingView Screener",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed",
        menu_items={
            'Get Help': None,
            'Report a bug': None,
            'About': None
        }
    )

    # Custom CSS for top navigation with improved typography
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

            /* Create top navigation */
            .top-nav {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                height: 60px;
                background: linear-gradient(90deg, #1e1e2d, #2d2d44);
                display: flex;
                align-items: center;
                padding: 0 24px;
                z-index: 999;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                font-family: 'Inter', sans-serif;
            }

            .nav-links {
                display: flex;
                gap: 16px;
                align-items: center;
            }

            .nav-link {
                color: #a0aec0;
                text-decoration: none;
                font-size: 14px;
                font-weight: 500;
                padding: 8px 12px;
                border-radius: 6px;
                transition: all 0.2s ease;
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 6px;
                letter-spacing: 0.01em;
                white-space: nowrap;
            }

            .nav-link:hover {
                color: white;
                background: rgba(255,255,255,0.1);
                transform: translateY(-1px);
            }

            .nav-link.active {
                color: white;
                background: rgba(59, 130, 246, 0.5);
            }

            .nav-logo {
                font-size: 16px;
                font-weight: 600;
                color: white;
                margin-right: 24px;
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 8px 12px;
                background: rgba(255,255,255,0.1);
                border-radius: 6px;
                letter-spacing: 0.02em;
            }

            /* Adjust main content to accommodate top nav */
            .main-content {
                margin-top: 60px;
                padding: 24px;
                font-family: 'Inter', sans-serif;
            }

            /* Make the app full width */
            .block-container {
                max-width: 100% !important;
                padding: 0 !important;
            }

            /* Additional styles for better appearance */
            .stApp {
                background: #121212;
            }

            /* Responsive adjustments */
            @media (max-width: 768px) {
                .nav-links {
                    gap: 8px;
                    overflow-x: auto;
                    padding-bottom: 8px;
                    -webkit-overflow-scrolling: touch;
                }

                .nav-link {
                    font-size: 13px;
                    padding: 6px 10px;
                }

                .nav-logo {
                    font-size: 14px;
                    margin-right: 16px;
                }
            }
        </style>
    """, unsafe_allow_html=True)

    # Create navigation HTML
    nav_html = """
        <div class="top-nav">
            <div class="nav-links">
                <span class="nav-logo">📊 TradingView Screener</span>
                <a class="nav-link" onclick="handleNav('Home')">🏠 Home</a>
                <a class="nav-link" onclick="handleNav('Custom EMA Scanner')">📊 EMA Scanner</a>
                <a class="nav-link" onclick="handleNav('Stock News')">📰 Stock News</a>
                <a class="nav-link" onclick="handleNav('Advanced Scanner')">📈 Advanced Scanner</a>
                <a class="nav-link" onclick="handleNav('NSE Past IPO Issues')">🔔 IPO Issues</a>
                <a class="nav-link" onclick="handleNav('NSE Volume Gainers')">📈 Volume Gainers</a>
                <a class="nav-link" onclick="handleNav('Screener Company Financials')">💹 Financials</a>
                <a class="nav-link" onclick="handleNav('Price Bands')">📊 Price Bands</a>
                <a class="nav-link" onclick="handleNav('Results Calendar')">📋 Results Calendar</a>
            </div>
        </div>
        <div class="main-content">
    """
    st.markdown(nav_html, unsafe_allow_html=True)

    # Initialize session state for navigation
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Advanced Scanner"

    # JavaScript for handling navigation
    st.markdown("""
        <script>
            function handleNav(page) {
                // Update session state
                window.parent.postMessage({
                    type: 'streamlit:setComponentValue',
                    value: page
                }, '*');
            }
        </script>
    """, unsafe_allow_html=True)

    # Handle page content based on navigation
    if st.session_state.current_page == "Advanced Scanner":
        fade_in(st.title("Advanced Scanner"))
        slide_in(st.markdown("### Find trading opportunities with precision"), direction="up")
        with st.container():
            fade_in(st.title("Advanced Scanner"))
            slide_in(st.markdown("### Filters"), direction="left")
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.selectbox("Timeframe", ["1D", "4H", "1H", "30min", "15min", "5min"])
            st.multiselect("Indicators", ["RSI", "MACD", "EMA", "SMA", "Bollinger Bands"])
            st.slider("RSI Period", 1, 50, 14)
            st.markdown('</div>', unsafe_allow_html=True)
            
            with st.container():
                fade_in(st.markdown("### Scan Results"))
                st.markdown('<div class="data-table">', unsafe_allow_html=True)
                # Add scan results table here
                st.markdown('</div>', unsafe_allow_html=True)

    elif st.session_state.current_page == "Stock News":
        fade_in(st.title("Stock News"))
        slide_in(st.markdown("### Latest market updates"), direction="up")
        with st.container():
            fade_in(st.title("Stock News"))
            slide_in(st.markdown("### Latest market updates and analysis"), direction="up")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                for i in range(3):
                    st.markdown(f'''
                        <div class="card">
                            <h4>Market Update {i+1}</h4>
                            <p>Latest market news and analysis...</p>
                            <small>2 hours ago</small>
                        </div>
                    ''', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("### Top Movers")
                # Add top movers content
                st.markdown('</div>', unsafe_allow_html=True)

    elif st.session_state.current_page == "Custom EMA Scanner":
        fade_in(st.title("Custom EMA Scanner"))
        slide_in(st.markdown("### Scan stocks based on moving averages"), direction="up")
        with st.container():
            fade_in(st.title("Custom EMA Scanner"))
            slide_in(st.markdown("### Exponential Moving Average Analysis"), direction="up")
            
            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.number_input("Short EMA Period", 1, 50, 9)
                st.number_input("Long EMA Period", 1, 200, 21)
                st.selectbox("Timeframe", ["1D", "4H", "1H", "30min"])
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                # Add EMA chart here
                st.markdown('</div>', unsafe_allow_html=True)

    elif st.session_state.current_page == "NSE Past IPO Issues":
        fade_in(st.title("NSE Past IPO Issues"))
        slide_in(st.markdown("### Track IPO performance"), direction="up")
        with st.container():
            fade_in(st.title("NSE Past IPO Issues"))
            slide_in(st.markdown("### Historical IPO Performance Analysis"), direction="up")
            
            st.markdown('<div class="data-table">', unsafe_allow_html=True)
            # Add IPO data table here
            st.markdown('</div>', unsafe_allow_html=True)

    elif st.session_state.current_page == "NSE Volume Gainers":
        fade_in(st.title("NSE Volume Gainers"))
        slide_in(st.markdown("### High volume stock analysis"), direction="up")
        with st.container():
            fade_in(st.title("NSE Volume Gainers"))
            slide_in(st.markdown("### High Volume Stock Analysis"), direction="up")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown('<div class="data-table">', unsafe_allow_html=True)
                # Add volume gainers table here
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("### Volume Filters")
                st.slider("Min Volume (Millions)", 0, 100, 10)
                st.slider("Price Change %", -10, 10, 0)
                st.markdown('</div>', unsafe_allow_html=True)

    elif st.session_state.current_page == "Screener Company Financials":
        fade_in(st.title("Company Financials"))
        slide_in(st.markdown("### Detailed financial analysis"), direction="up")
        with st.container():
            fade_in(st.title("Company Financials"))
            slide_in(st.markdown("### Detailed Financial Analysis"), direction="up")
            
            tabs = st.tabs(["Balance Sheet", "Income Statement", "Cash Flow", "Ratios"])
            for tab in tabs:
                with tab:
                    st.markdown('<div class="data-table">', unsafe_allow_html=True)
                    # Add financial data tables here
                    st.markdown('</div>', unsafe_allow_html=True)

    elif st.session_state.current_page == "Price Bands":
        fade_in(st.title("Price Bands"))
        slide_in(st.markdown("### Price range analysis"), direction="up")
        with st.container():
            fade_in(st.title("Price Bands"))
            slide_in(st.markdown("### Price Range Analysis"), direction="up")
            
            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.selectbox("Band Type", ["Bollinger Bands", "Keltner Channel", "Donchian Channel"])
                st.number_input("Period", 5, 50, 20)
                st.number_input("Standard Deviation", 1.0, 3.0, 2.0)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                # Add price bands chart here
                st.markdown('</div>', unsafe_allow_html=True)

    elif st.session_state.current_page == "Results Calendar":
        fade_in(st.title("Results Calendar"))
        slide_in(st.markdown("### Company results and announcements"), direction="up")
        with st.container():
            fade_in(st.title("Results Calendar"))
            slide_in(st.markdown("### Company Results and Announcements"), direction="up")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("### Results Schedule")
                # Add results calendar here
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                # Add results visualization here
                st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main() 