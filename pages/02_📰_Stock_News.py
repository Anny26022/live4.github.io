import streamlit as st
import pandas as pd
import io
import time

# Initialize session state for news data
if 'news_df' not in st.session_state:
    st.session_state.news_df = pd.DataFrame()
    st.session_state.news_last_update = None
    st.session_state.news_loading = False

# Page config
st.set_page_config(
    page_title="Stock News",
    page_icon="📰",
    layout="centered"
)

# Load custom CSS
try:
    with open('style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except FileNotFoundError:
    st.warning("Style file not found. Page will run with default styling.")

# Initialize session state for last update time
if 'last_update_time' not in st.session_state:
    st.session_state.last_update_time = time.time()

# --- ALL FUNCTION DEFINITIONS FIRST ---
@st.cache_data(ttl=300)
def fetch_stock_news():
    try:
        # Main news sheet (existing)
        url = "https://docs.google.com/spreadsheets/d/1X6amEBgzjwpbaSST_19z-6zAMbnA4yYpnrYO_faoh_g/gviz/tq?tqx=out:csv&gid=1083642917"
        news_df = pd.read_csv(url)
        news_df.columns = [col.strip() for col in news_df.columns]
        # --- NEW: Load the additional sheet for Analyst/Result News ---
        analyst_url = "https://docs.google.com/spreadsheets/d/1X6amEBgzjwpbaSST_19z-6zAMbnA4yYpnrYO_faoh_g/gviz/tq?tqx=out:csv&gid=909294572"
        analyst_df = pd.read_csv(analyst_url)
        analyst_df.columns = [col.strip() for col in analyst_df.columns]
        # Ensure 'SUBCATNAME' column exists in both DataFrames
        if 'SUBCATNAME' not in news_df.columns:
            news_df['SUBCATNAME'] = ''
        if 'SUBCATNAME' not in analyst_df.columns:
            analyst_df['SUBCATNAME'] = ''
        # Ensure 'PDF' column exists in both DataFrames
        if 'PDF' not in news_df.columns:
            news_df['PDF'] = ''
        if 'PDF' not in analyst_df.columns:
            analyst_df['PDF'] = ''
        # Add a column to distinguish source/type if not present
        if 'SOURCE' not in news_df.columns:
            news_df['SOURCE'] = 'Main'
        if 'SOURCE' not in analyst_df.columns:
            analyst_df['SOURCE'] = 'Analyst/Result'
        # Standardize columns for concatenation
        all_cols = sorted(set(news_df.columns).union(set(analyst_df.columns)))
        news_df = news_df.reindex(columns=all_cols)
        analyst_df = analyst_df.reindex(columns=all_cols)
        
        # --- Convert Google Drive file IDs to sharable PDF links if needed ---
        def ensure_pdf_url(val):
            val = str(val).strip()
            if val.startswith('http'):
                return val
            # If it's a Google Drive file ID, build the URL
            if val and len(val) >= 20 and '/' not in val and '.' not in val:
                return f"https://drive.google.com/file/d/{val}/view"
            return '' if val in ('', 'nan', 'None') else val
        news_df['PDF'] = news_df['PDF'].apply(ensure_pdf_url)
        analyst_df['PDF'] = analyst_df['PDF'].apply(ensure_pdf_url)
        
        # Concatenate both
        combined_df = pd.concat([news_df, analyst_df], ignore_index=True)
        latest_update = ''
        try:
            latest_update = str(pd.to_datetime(combined_df['NEWS_DT'], errors='coerce').max())
        except Exception:
            latest_update = str(time.time())
        return combined_df, latest_update
    except Exception as e:
        st.error(f"Error fetching news data: {str(e)}")
        return pd.DataFrame(), ''

# --- UI LAYOUT BELOW ---
# Title, Refresh Button, and Auto-refresh info in a single row
col1, col2, col3 = st.columns([3, 1, 2])
with col1:
    st.title("📰 Stock News")
with col2:
    if st.button("🔄 Refresh Now", key="refresh_now"):
        fetch_stock_news.clear()
        st.rerun()
with col3:
    st.markdown(
        """
        <div style='display: flex; align-items: center; height: 100%; justify-content: flex-end;'>
            <span style='background-color: #262730; padding: 10px 16px; border-radius: 5px; font-size: 1rem;'>
                🔄 Auto-refreshing every 5m
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

# Fetch news in background after page loads
if not st.session_state.news_loading and st.session_state.news_df.empty:
    st.session_state.news_loading = True
    with st.spinner("Loading news data..."):
        st.session_state.news_df, st.session_state.news_last_update = fetch_stock_news()
        st.session_state.news_loading = False
        st.rerun()

if not st.session_state.news_df.empty:
    # Add filters at the top with adjusted ratios
    st.subheader("🔍 Filter News")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Filter by date
        if 'NEWS_DT' in st.session_state.news_df.columns:
            st.session_state.news_df['NEWS_DT'] = pd.to_datetime(st.session_state.news_df['NEWS_DT'])
            min_date = st.session_state.news_df['NEWS_DT'].min().date()
            max_date = st.session_state.news_df['NEWS_DT'].max().date()
            selected_date = st.date_input(
                "Select Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
            if len(selected_date) == 2:
                start_date, end_date = selected_date
                st.session_state.news_df = st.session_state.news_df[
                    (st.session_state.news_df['NEWS_DT'].dt.date >= start_date) &
                    (st.session_state.news_df['NEWS_DT'].dt.date <= end_date)
                ]
    
    with col2:
        # Filter by category
        if 'CATEGORYNAME' in st.session_state.news_df.columns:
            # Remove NaN, convert to str, filter out empty/None, then sort as string
            categories_raw = st.session_state.news_df['CATEGORYNAME'].dropna().astype(str).unique().tolist()
            categories = ['All'] + sorted([c for c in categories_raw if c.strip() != ''])
            selected_category = st.selectbox("Select Category", categories)
            if selected_category != 'All':
                st.session_state.news_df = st.session_state.news_df[st.session_state.news_df['CATEGORYNAME'] == selected_category]
        # Filter by subcategory
        if 'SUBCATNAME' in st.session_state.news_df.columns:
            subcats_raw = st.session_state.news_df['SUBCATNAME'].dropna().astype(str).unique().tolist()
            subcats = ['All'] + sorted([s for s in subcats_raw if s.strip() != ''])
            selected_subcat = st.selectbox("Select Subcategory", subcats)
            if selected_subcat != 'All':
                st.session_state.news_df = st.session_state.news_df[st.session_state.news_df['SUBCATNAME'] == selected_subcat]

    # Search box for company/news
    search_term = st.text_input("🔍 Search by Company Name or News Content")
    if search_term:
        mask = st.session_state.news_df.apply(lambda x: x.astype(str).str.contains(search_term, case=False)).any(axis=1)
        st.session_state.news_df = st.session_state.news_df[mask]

    # Display news count and last update time
    col1, col2 = st.columns([2, 1])
    with col1:
        st.info(f"📚 Showing {len(st.session_state.news_df)} news items")
    with col2:
        last_update = time.strftime('%I:%M:%S %p', time.localtime(st.session_state.last_update_time))
        st.info(f"Last updated: {last_update}")
    
    # Configure the display
    display_cols = {
        'NEWS_DT': 'Date & Time',
        'NSE_SYM': 'Symbol',
        'SLONGNAME': 'Company',
        'CATEGORYNAME': 'Category',
        'SUBCATNAME': 'Subcategory',
        'HEADLINE': 'Headline',
        'PDF': 'PDF',
        'Sales TTM Cr': 'Sales (TTM) Cr',
        'OPM %': 'OPM %',
        'NPM %': 'NPM %',
        'ROCE %': 'ROCE %',
        'QoQ Sales %': 'QoQ Sales %',
        'QoQ Profits %': 'QoQ Profits %',
        'YoY Sales %': 'YoY Sales %',
        'YoY Profit %': 'YoY Profit %',
        'SOURCE': 'Source'
    }

    # Only show columns that exist in the dataframe
    display_cols = {k: v for k, v in display_cols.items() if k in st.session_state.news_df.columns}
    
    # Configure column display
    column_config = {
        'NEWS_DT': st.column_config.DatetimeColumn('Date & Time', format="DD-MM-YYYY HH:mm"),
        'NSE_SYM': st.column_config.TextColumn('Symbol'),
        'SLONGNAME': st.column_config.TextColumn('Company'),
        'CATEGORYNAME': st.column_config.TextColumn('Category'),
        'SUBCATNAME': st.column_config.TextColumn('Subcategory'),
        'HEADLINE': st.column_config.TextColumn('Headline', width='large'),
        'PDF': st.column_config.LinkColumn('PDF', display_text='PDF'),
        'Sales TTM Cr': st.column_config.NumberColumn('Sales (TTM) Cr', format="%.2f"),
        'OPM %': st.column_config.NumberColumn('OPM %', format="%.2f"),
        'NPM %': st.column_config.NumberColumn('NPM %', format="%.2f"),
        'ROCE %': st.column_config.NumberColumn('ROCE %', format="%.2f"),
        'QoQ Sales %': st.column_config.NumberColumn('QoQ Sales %', format="%.2f"),
        'QoQ Profits %': st.column_config.NumberColumn('QoQ Profits %', format="%.2f"),
        'YoY Sales %': st.column_config.NumberColumn('YoY Sales %', format="%.2f"),
        'YoY Profit %': st.column_config.NumberColumn('YoY Profit %', format="%.2f"),
        'SOURCE': st.column_config.TextColumn('Source')
    }

    # Display the news dataframe
    st.dataframe(
        st.session_state.news_df[display_cols.keys()],
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
            data=st.session_state.news_df.to_csv(index=False),
            file_name="stock_news.csv",
            mime="text/csv"
        )
    
    with col2:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            st.session_state.news_df.to_excel(writer, index=False)
        buffer.seek(0)
        
        st.download_button(
            "Download Excel",
            data=buffer,
            file_name="stock_news.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    if not st.session_state.news_loading:
        st.warning("Unable to fetch news data. Please try again later.")

# Add auto-refresh script
st.markdown("""
<script>
    function reload() {
        window.location.reload();
    }
    setTimeout(reload, 300000);
</script>
""", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.caption("TradingView Screener Pro • Built with Streamlit • Created with ❤️")

# Page Header
st.markdown("""
<div class='page-header'>
    <h1>📰 Stock News</h1>
    <p class='subtitle'>Latest market insights and company updates</p>
</div>
""", unsafe_allow_html=True)

# Main Content
col1, col2 = st.columns([2, 1])

with col1:
    # Market Overview Card
    st.markdown("""
    <div class='content-card'>
        <h3>📊 Market Overview</h3>
        <div class='news-filters'>
            <span class='filter-tag active'>All Markets</span>
            <span class='filter-tag'>US Stocks</span>
            <span class='filter-tag'>Crypto</span>
            <span class='filter-tag'>Forex</span>
        </div>
        <div class='news-list'>
            <div class='news-item'>
                <span class='news-time'>10:30 AM</span>
                <span class='news-category'>Market Update</span>
                <p class='news-headline'>Major indices showing strong momentum in morning trading</p>
            </div>
            <div class='news-item'>
                <span class='news-time'>09:45 AM</span>
                <span class='news-category'>Economic Data</span>
                <p class='news-headline'>Consumer confidence index beats expectations</p>
            </div>
            <div class='news-item'>
                <span class='news-time'>09:15 AM</span>
                <span class='news-category'>Company News</span>
                <p class='news-headline'>Tech sector leads gains with strong earnings reports</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    # Quick Filters Card
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
            <div class='filter-item'>
                <span class='material-icons'>star</span>
                Most Active
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Market Sentiment Card
    st.markdown("""
    <div class='content-card'>
        <h3>📈 Market Sentiment</h3>
        <div class='sentiment-indicators'>
            <div class='sentiment-item'>
                <span class='sentiment-label'>Fear & Greed Index</span>
                <div class='sentiment-value positive'>65</div>
            </div>
            <div class='sentiment-item'>
                <span class='sentiment-label'>Market Volatility</span>
                <div class='sentiment-value neutral'>Medium</div>
            </div>
            <div class='sentiment-item'>
                <span class='sentiment-label'>Trend Strength</span>
                <div class='sentiment-value positive'>Strong</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Additional CSS for news-specific components
st.markdown("""
<style>
/* News Items */
.news-list {
    margin-top: 1.5rem;
}

.news-item {
    padding: 1rem;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    transition: all 0.3s ease;
}

.news-item:hover {
    background: rgba(255,255,255,0.05);
}

.news-time {
    font-size: 0.8rem;
    color: rgba(255,255,255,0.6);
    margin-right: 1rem;
}

.news-category {
    font-size: 0.8rem;
    color: #2962ff;
    background: rgba(41,98,255,0.1);
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
}

.news-headline {
    margin-top: 0.5rem;
    font-size: 1rem;
    color: rgba(255,255,255,0.9);
}

/* Sentiment Indicators */
.sentiment-indicators {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.sentiment-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem;
    background: rgba(255,255,255,0.05);
    border-radius: 8px;
}

.sentiment-label {
    font-size: 0.9rem;
    color: rgba(255,255,255,0.8);
}

.sentiment-value {
    font-weight: 600;
    padding: 0.25rem 0.75rem;
    border-radius: 4px;
}

.sentiment-value.positive {
    background: rgba(46,204,113,0.2);
    color: #2ecc71;
}

.sentiment-value.neutral {
    background: rgba(241,196,15,0.2);
    color: #f1c40f;
}

.sentiment-value.negative {
    background: rgba(231,76,60,0.2);
    color: #e74c3c;
}

/* Adjust container widths for centered layout */
.content-card {
    max-width: 100%;
    margin-bottom: 1rem;
}

/* Adjust column layouts */
.stColumns {
    gap: 1rem;
}

/* Make dataframes and charts responsive */
.stDataFrame {
    width: 100%;
    max-width: 100%;
}

/* Adjust metrics for smaller width */
.stMetric {
    width: 100%;
}

/* Make buttons full width on smaller screens */
@media (max-width: 768px) {
    .stButton > button {
        width: 100%;
    }
    .stSelectbox, .stDateInput {
        width: 100%;
    }
}

/* Adjust card padding for smaller screens */
@media (max-width: 768px) {
    .content-card {
        padding: 1rem;
    }
}

/* Adjust news items for better readability */
.news-item {
    max-width: 100%;
}

/* Make filter tags wrap better */
.news-filters {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
}
</style>
""", unsafe_allow_html=True) 
