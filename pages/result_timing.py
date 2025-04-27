import streamlit as st
import pandas as pd
from datetime import datetime, time
import pytz
from streamlit_autorefresh import st_autorefresh

# Page config
st.set_page_config(
    page_title="Result Timing Analysis",
    page_icon="⏰",
    layout="centered"
)

# Load custom CSS
try:
    with open('style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except FileNotFoundError:
    st.warning("Style file not found. Page will run with default styling.")

# Define market hours in IST
MARKET_OPEN = time(9, 7)  # 9:07 AM
MARKET_CLOSE = time(15, 30)  # 3:30 PM

@st.cache_data(ttl=300)
def fetch_stock_news():
    try:
        # Main news sheet
        url = "https://docs.google.com/spreadsheets/d/1X6amEBgzjwpbaSST_19z-6zAMbnA4yYpnrYO_faoh_g/gviz/tq?tqx=out:csv&gid=1083642917"
        news_df = pd.read_csv(url)
        news_df.columns = [col.strip() for col in news_df.columns]
        
        # Convert NEWS_DT to datetime
        news_df['NEWS_DT'] = pd.to_datetime(news_df['NEWS_DT'])
        
        # Filter only result-related news
        result_df = news_df[
            (news_df['CATEGORYNAME'].str.contains('Result', case=False, na=False)) |
            (news_df['SUBCATNAME'].str.contains('Result', case=False, na=False))
        ].copy()
        
        # Add time classification
        def classify_time(dt):
            if pd.isna(dt):
                return "Unknown"
            
            # Get time from datetime (data is already in IST)
            time_ist = dt.time()
            
            if MARKET_OPEN <= time_ist <= MARKET_CLOSE:
                return "During Market Hours (9:07 AM - 3:30 PM)"
            else:
                return "After Market Hours (3:30 PM - 9:07 AM)"
        
        result_df['Announcement Time'] = result_df['NEWS_DT'].apply(classify_time)

        # Add Weekend column
        result_df['Weekend'] = result_df['NEWS_DT'].dt.dayofweek.isin([5, 6])
        
        return result_df
    except Exception as e:
        st.error(f"Error fetching news data: {str(e)}")
        return pd.DataFrame()

# Auto-refresh every 5 minutes (300,000 ms)
st_autorefresh(interval=300000, key="datarefresh5min")

# Page Header
st.title("⏰ Result Timing Analysis")
st.caption("Analyze result announcements during and after market hours")

# Refresh button
refresh = st.button("🔄 Refresh Data", help="Fetch the latest result data from source (bypasses cache)")
if refresh:
    st.cache_data.clear()
    st.rerun()

# Fetch and process data
result_df = fetch_stock_news()

if not result_df.empty:
    # Date filter
    st.subheader("📅 Select Date")
    min_date = result_df['NEWS_DT'].min().date()
    max_date = result_df['NEWS_DT'].max().date()
    
    selected_date = st.date_input(
        "Filter by date (DD-MM-YYYY)",
        value=max_date,
        min_value=min_date,
        max_value=max_date,
        format="DD/MM/YYYY"
    )
    
    # Filter dataframe by single date
    filtered_df = result_df[result_df['NEWS_DT'].dt.date == selected_date]
    
    # Display metrics
    st.subheader("📊 Result Announcement Statistics")
    col1, col2, col3, col4 = st.columns(4)

    total_results = len(filtered_df)
    market_hours = len(filtered_df[(filtered_df['Announcement Time'] == "During Market Hours (9:07 AM - 3:30 PM)") & (~filtered_df['Weekend'])])
    after_hours = len(filtered_df[(filtered_df['Announcement Time'] == "After Market Hours (3:30 PM - 9:07 AM)") & (~filtered_df['Weekend'])])
    weekend_results = len(filtered_df[filtered_df['Weekend']])

    with col1:
        st.metric("Total Results", total_results)
    with col2:
        st.metric("During Market Hours", market_hours)
    with col3:
        st.metric("After Market Hours", after_hours)
    with col4:
        st.metric("Weekend Results", weekend_results)
    
    # Function to format symbols for copying
    def format_symbols_for_copy(df):
        if 'NSE_SYM' in df.columns:
            symbols = df['NSE_SYM'].tolist()
            return ','.join([f"NSE:{sym}" for sym in symbols])
        return ""

    # Display results by timing
    st.subheader("🕒 Results During Market Hours")
    market_hours_df = filtered_df[
        (filtered_df['Announcement Time'] == "During Market Hours (9:07 AM - 3:30 PM)") &
        (~filtered_df['Weekend'])
    ].sort_values('NEWS_DT', ascending=False)
    if not market_hours_df.empty:
        # Add copy button for market hours symbols
        market_symbols = format_symbols_for_copy(market_hours_df)
        if market_symbols:
            st.text_area("Copy Market Hours Symbols", market_symbols, height=100)
        
        st.dataframe(
            market_hours_df[[
                'NEWS_DT', 'NSE_SYM', 'SLONGNAME', 'HEADLINE',
                'Sales TTM Cr', 'OPM %', 'QoQ Sales %', 'QoQ Profits %', 'YoY Sales %', 'YoY Profit %']
            ],
            column_config={
                'NEWS_DT': st.column_config.DatetimeColumn('Date & Time', format="DD-MM-YYYY hh:mm a"),
                'NSE_SYM': st.column_config.TextColumn('Symbol'),
                'SLONGNAME': st.column_config.TextColumn('Company'),
                'HEADLINE': st.column_config.TextColumn('Headline', width='large'),
                'Sales TTM Cr': st.column_config.NumberColumn('Sales TTM Cr', format="%.2f"),
                'OPM %': st.column_config.NumberColumn('OPM %', format="%.2f"),
                'QoQ Sales %': st.column_config.NumberColumn('QoQ Sales %', format="%.2f"),
                'QoQ Profits %': st.column_config.NumberColumn('QoQ Profits %', format="%.2f"),
                'YoY Sales %': st.column_config.NumberColumn('YoY Sales %', format="%.2f"),
                'YoY Profit %': st.column_config.NumberColumn('YoY Profit %', format="%.2f")
            },
            hide_index=True
        )
    else:
        st.info("No results announced during market hours in the selected date range")
    
    st.subheader("🌙 Results After Market Hours")
    after_hours_df = filtered_df[
        (filtered_df['Announcement Time'] == "After Market Hours (3:30 PM - 9:07 AM)") &
        (~filtered_df['Weekend'])
    ].sort_values('NEWS_DT', ascending=False)
    if not after_hours_df.empty:
        # Add copy button for after hours symbols
        after_hours_symbols = format_symbols_for_copy(after_hours_df)
        if after_hours_symbols:
            st.text_area("Copy After Hours Symbols", after_hours_symbols, height=100)
        
        st.dataframe(
            after_hours_df[[
                'NEWS_DT', 'NSE_SYM', 'SLONGNAME', 'HEADLINE',
                'Sales TTM Cr', 'OPM %', 'QoQ Sales %', 'QoQ Profits %', 'YoY Sales %', 'YoY Profit %']
            ],
            column_config={
                'NEWS_DT': st.column_config.DatetimeColumn('Date & Time', format="DD-MM-YYYY hh:mm a"),
                'NSE_SYM': st.column_config.TextColumn('Symbol'),
                'SLONGNAME': st.column_config.TextColumn('Company'),
                'HEADLINE': st.column_config.TextColumn('Headline', width='large'),
                'Sales TTM Cr': st.column_config.NumberColumn('Sales TTM Cr', format="%.2f"),
                'OPM %': st.column_config.NumberColumn('OPM %', format="%.2f"),
                'QoQ Sales %': st.column_config.NumberColumn('QoQ Sales %', format="%.2f"),
                'QoQ Profits %': st.column_config.NumberColumn('QoQ Profits %', format="%.2f"),
                'YoY Sales %': st.column_config.NumberColumn('YoY Sales %', format="%.2f"),
                'YoY Profit %': st.column_config.NumberColumn('YoY Profit %', format="%.2f")
            },
            hide_index=True 
        )
    else:
        st.info("No results announced after market hours in the selected date range")
    
    st.subheader("📅 Results on Weekends (Saturday/Sunday)")
    is_selected_weekend = selected_date.weekday() in [5, 6]
    if is_selected_weekend:
        weekend_df = filtered_df[filtered_df['Weekend']].sort_values('NEWS_DT', ascending=False)
        if not weekend_df.empty:
            weekend_symbols = format_symbols_for_copy(weekend_df)
            if weekend_symbols:
                st.text_area("Copy Weekend Symbols", weekend_symbols, height=100)
            st.dataframe(
                weekend_df[[
                    'NEWS_DT', 'NSE_SYM', 'SLONGNAME', 'HEADLINE',
                    'Sales TTM Cr', 'OPM %', 'QoQ Sales %', 'QoQ Profits %', 'YoY Sales %', 'YoY Profit %']
                ],
                column_config={
                    'NEWS_DT': st.column_config.DatetimeColumn('Date & Time', format="DD-MM-YYYY hh:mm a"),
                    'NSE_SYM': st.column_config.TextColumn('Symbol'),
                    'SLONGNAME': st.column_config.TextColumn('Company'),
                    'HEADLINE': st.column_config.TextColumn('Headline', width='large'),
                    'Sales TTM Cr': st.column_config.NumberColumn('Sales TTM Cr', format="%.2f"),
                    'OPM %': st.column_config.NumberColumn('OPM %', format="%.2f"),
                    'QoQ Sales %': st.column_config.NumberColumn('QoQ Sales %', format="%.2f"),
                    'QoQ Profits %': st.column_config.NumberColumn('QoQ Profits %', format="%.2f"),
                    'YoY Sales %': st.column_config.NumberColumn('YoY Sales %', format="%.2f"),
                    'YoY Profit %': st.column_config.NumberColumn('YoY Profit %', format="%.2f")
                },
                hide_index=True
            )
        else:
            st.info("No results announced on weekends in the selected date range")
    else:
        st.info("Weekend results are only shown when a weekend date is selected.")
else:
    st.error("Unable to fetch result data. Please try refreshing the page.") 