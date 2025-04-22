import streamlit as st
import pandas as pd
import io
import time

# Set the page configuration
st.set_page_config(
    page_title="Stock News - TradingView Screener Pro",
    page_icon="📰",
    layout="wide"
)

# Title and auto-refresh info
col1, col2 = st.columns([3, 1])
with col1:
    st.title("📰 Stock News")
with col2:
    st.markdown("""
    <div style='text-align: right; margin-top: 20px;'>
        <span style='background-color: #262730; padding: 10px; border-radius: 5px;'>
            🔄 Auto-refreshing every 20s
        </span>
    </div>
    """, unsafe_allow_html=True)

# Initialize session state for last update time
if 'last_update_time' not in st.session_state:
    st.session_state.last_update_time = time.time()

# Fetch news data with auto-refresh
@st.cache_data(ttl=20)  # Cache expires after 20 seconds
def fetch_stock_news():
    try:
        url = "https://docs.google.com/spreadsheets/d/1X6amEBgzjwpbaSST_19z-6zAMbnA4yYpnrYO_faoh_g/gviz/tq?tqx=out:csv&gid=1083642917"
        news_df = pd.read_csv(url)
        # Clean up column names
        news_df.columns = [col.strip() for col in news_df.columns]
        st.session_state.last_update_time = time.time()
        return news_df
    except Exception as e:
        st.error(f"Error fetching news data: {str(e)}")
        return pd.DataFrame()

# Auto-refresh mechanism
def get_current_news():
    # Check if 20 seconds have passed since last update
    if time.time() - st.session_state.last_update_time >= 20:
        # Clear the cache to force a refresh
        fetch_stock_news.clear()
    return fetch_stock_news()

# Get the news data
news_df = get_current_news()

# Add a refresh button for manual refresh
if st.button("🔄 Refresh Now"):
    fetch_stock_news.clear()
    news_df = fetch_stock_news()
    st.success("Data refreshed!")

if not news_df.empty:
    # Add filters at the top
    st.subheader("🔍 Filter News")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Filter by date
        if 'NEWS_DT' in news_df.columns:
            news_df['NEWS_DT'] = pd.to_datetime(news_df['NEWS_DT'])
            min_date = news_df['NEWS_DT'].min().date()
            max_date = news_df['NEWS_DT'].max().date()
            selected_date = st.date_input(
                "Select Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
            if len(selected_date) == 2:
                start_date, end_date = selected_date
                news_df = news_df[
                    (news_df['NEWS_DT'].dt.date >= start_date) &
                    (news_df['NEWS_DT'].dt.date <= end_date)
                ]
    
    with col2:
        # Filter by category
        if 'CATEGORYNAME' in news_df.columns:
            categories = ['All'] + sorted(news_df['CATEGORYNAME'].unique().tolist())
            selected_category = st.selectbox("Select Category", categories)
            if selected_category != 'All':
                news_df = news_df[news_df['CATEGORYNAME'] == selected_category]

    # Search box for company/news
    search_term = st.text_input("🔍 Search by Company Name or News Content")
    if search_term:
        mask = news_df.apply(lambda x: x.astype(str).str.contains(search_term, case=False)).any(axis=1)
        news_df = news_df[mask]

    # Display news count and last update time
    col1, col2 = st.columns([2, 1])
    with col1:
        st.info(f"📚 Showing {len(news_df)} news items")
    with col2:
        last_update = time.strftime('%I:%M:%S %p', time.localtime(st.session_state.last_update_time))
        st.info(f"Last updated: {last_update}")
    
    # Configure the display
    display_cols = {
        'NEWS_DT': 'Date & Time',
        'NSE_SYM': 'Symbol',
        'SLONGNAME': 'Company',
        'CATEGORYNAME': 'Category',
        'HEADLINE': 'Headline',
        'Sales TTM Cr': 'Sales (TTM) Cr',
        'OPM %': 'OPM %',
        'QoQ Sales %': 'QoQ Sales %',
        'QoQ Profits %': 'QoQ Profits %',
        'YoY Sales %': 'YoY Sales %',
        'YoY Profit %': 'YoY Profit %'
    }

    # Only show columns that exist in the dataframe
    display_cols = {k: v for k, v in display_cols.items() if k in news_df.columns}
    
    # Configure column display
    column_config = {
        'NEWS_DT': st.column_config.DatetimeColumn('Date & Time', format="DD-MM-YYYY HH:mm"),
        'NSE_SYM': st.column_config.TextColumn('Symbol'),
        'SLONGNAME': st.column_config.TextColumn('Company'),
        'CATEGORYNAME': st.column_config.TextColumn('Category'),
        'HEADLINE': st.column_config.TextColumn('Headline', width='large'),
        'Sales TTM Cr': st.column_config.NumberColumn('Sales (TTM) Cr', format="%.2f"),
        'OPM %': st.column_config.NumberColumn('OPM %', format="%.2f"),
        'QoQ Sales %': st.column_config.NumberColumn('QoQ Sales %', format="%.2f"),
        'QoQ Profits %': st.column_config.NumberColumn('QoQ Profits %', format="%.2f"),
        'YoY Sales %': st.column_config.NumberColumn('YoY Sales %', format="%.2f"),
        'YoY Profit %': st.column_config.NumberColumn('YoY Profit %', format="%.2f")
    }

    # Display the news dataframe
    st.dataframe(
        news_df[display_cols.keys()],
        use_container_width=True,
        height=600,
        column_config=column_config,
        hide_index=True
    )

    # Download options
    st.subheader("📥 Download Data")
    col1, col2 = st.columns(2)
    
    with col1:
        st.download_button(
            "Download CSV",
            data=news_df.to_csv(index=False),
            file_name="stock_news.csv",
            mime="text/csv"
        )
    
    with col2:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            news_df.to_excel(writer, index=False)
        buffer.seek(0)
        
        st.download_button(
            "Download Excel",
            data=buffer,
            file_name="stock_news.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.warning("Unable to fetch news data. Please try again later.")

# Add auto-refresh script
st.markdown("""
<script>
    function reload() {
        window.location.reload();
    }
    setTimeout(reload, 20000);
</script>
""", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.caption("TradingView Screener Pro • Built with Streamlit • Created with ❤️") 