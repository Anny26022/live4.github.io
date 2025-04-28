import streamlit as st
import pandas as pd
import io
import time
import pytz

# Initialize session state for news data
if 'news_df' not in st.session_state:
    st.session_state.news_df = pd.DataFrame()
    st.session_state.news_last_update = None
    st.session_state.news_loading = False

# Page config
st.set_page_config(
    page_title="Stock News",
    page_icon="",
    layout="centered",
    initial_sidebar_state="auto"
)

# Load custom CSS
try:
    with open('style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except FileNotFoundError:
    st.warning("Style file not found. Page will run with default styling.")

if 'last_update_time' not in st.session_state:
    st.session_state.last_update_time = time.time()

@st.cache_data(ttl=300)
def fetch_stock_news():
    try:
        url = "https://docs.google.com/spreadsheets/d/1X6amEBgzjwpbaSST_19z-6zAMbnA4yYpnrYO_faoh_g/gviz/tq?tqx=out:csv&gid=1083642917"
        news_df = pd.read_csv(url)
        news_df.columns = [col.strip() for col in news_df.columns]
        analyst_url = "https://docs.google.com/spreadsheets/d/1X6amEBgzjwpbaSST_19z-6zAMbnA4yYpnrYO_faoh_g/gviz/tq?tqx=out:csv&gid=909294572"
        analyst_df = pd.read_csv(analyst_url)
        analyst_df.columns = [col.strip() for col in analyst_df.columns]
        if 'SUBCATNAME' not in news_df.columns:
            news_df['SUBCATNAME'] = ''
        if 'SUBCATNAME' not in analyst_df.columns:
            analyst_df['SUBCATNAME'] = ''
        if 'PDF' not in news_df.columns:
            news_df['PDF'] = ''
        if 'PDF' not in analyst_df.columns:
            analyst_df['PDF'] = ''
        if 'SOURCE' not in news_df.columns:
            news_df['SOURCE'] = 'Main'
        if 'SOURCE' not in analyst_df.columns:
            analyst_df['SOURCE'] = 'Analyst/Result'
        all_cols = sorted(set(news_df.columns).union(set(analyst_df.columns)))
        news_df = news_df.reindex(columns=all_cols)
        analyst_df = analyst_df.reindex(columns=all_cols)
        def ensure_pdf_url(val):
            val = str(val).strip()
            if val.startswith('http'):
                return val
            if val and len(val) >= 20 and '/' not in val and '.' not in val:
                return f"https://drive.google.com/file/d/{val}/view"
            return '' if val in ('', 'nan', 'None') else val
        news_df['PDF'] = news_df['PDF'].apply(ensure_pdf_url)
        analyst_df['PDF'] = analyst_df['PDF'].apply(ensure_pdf_url)
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

# --- Redesigned UI Layout ---
# Header Card
st.markdown("""
<div style='max-width:700px;margin:2rem auto 1.5rem auto;padding:2.2rem 2rem 1.3rem 2rem;background:linear-gradient(90deg,#22243A 60%,#181A20 100%);border-radius:18px;box-shadow:0 4px 32px rgba(44,62,80,0.14);text-align:center;'>
  <div style='display:flex;align-items:center;justify-content:center;'>
    <svg xmlns='http://www.w3.org/2000/svg' width='48' height='48' viewBox='0 0 48 48' fill='none' style='margin-right:16px;'>
      <rect width='48' height='48' rx='12' fill='url(#feed-bg)'/>
      <g>
        <rect x='12' y='16' width='24' height='4' rx='2' fill='#6d4cff'/>
        <rect x='12' y='24' width='16' height='4' rx='2' fill='#43a047'/>
        <rect x='12' y='32' width='8' height='4' rx='2' fill='#29b6f6'/>
      </g>
      <defs>
        <linearGradient id='feed-bg' x1='0' y1='0' x2='48' y2='48' gradientUnits='userSpaceOnUse'>
          <stop stop-color='#23272F'/>
          <stop offset='1' stop-color='#181A20'/>
        </linearGradient>
      </defs>
    </svg>
    <span style='font-size:2.5rem;font-weight:700;color:#fff;'>Stock News</span>
  </div>
  <p style='color:#b0b3c4;font-size:1.07rem;margin:0.1em 0 0.7em 0;'>Latest market insights and company updates</p>
  <div style='display:flex;justify-content:center;gap:1.2rem;margin-top:1.1rem;'>
    <form action="#" method="post" style="display:inline;margin:0;">
      <button type="submit" style="background:#2962ff;color:#fff;padding:0.6em 1.5em;border:none;border-radius:7px;font-size:1.08rem;font-weight:500;cursor:pointer;box-shadow:0 2px 8px rgba(41,98,255,0.09);margin-right:0.7em;">🔄 Refresh Now</button>
    </form>
    <span style='background-color:#23243a;padding:0.6em 1.4em;border-radius:7px;font-size:1.08rem;color:#7ecbff;display:flex;align-items:center;gap:0.5em;'>
      <span style='font-size:1.15em;'>🕒</span> Auto-refreshing every 5m
    </span>
  </div>
</div>
""", unsafe_allow_html=True)

# Filter Card
st.markdown("""
<div style='max-width:700px;margin:0 auto 1.5rem auto;padding:1.7rem 2rem 1.3rem 2rem;background:linear-gradient(90deg,#23243A 60%,#181A20 100%);border-radius:14px;box-shadow:0 2px 16px rgba(44,62,80,0.10);'>
  <div style='display:flex;align-items:center;gap:0.8em;margin-bottom:1.2em;'>
    <span style='font-size:1.5rem;'>🔎</span>
    <span style='font-size:1.35rem;font-weight:700;color:#fff;'>Filter News</span>
  </div>
</div>
""", unsafe_allow_html=True)

# Actual filter widgets (centered)
filter_cols = st.columns([1,1,1])

# --- Dynamically populate category and subcategory from dataframe ---
if not st.session_state.news_df.empty:
    df = st.session_state.news_df.copy()
    # Category options
    if 'CATEGORYNAME' in df.columns:
        categories_raw = df['CATEGORYNAME'].dropna().astype(str).unique().tolist()
        categories = ['All'] + sorted([c for c in categories_raw if c.strip() != ''])
    else:
        categories = ['All']
    # Subcategory options
    if 'SUBCATNAME' in df.columns:
        subcats_raw = df['SUBCATNAME'].dropna().astype(str).unique().tolist()
        subcategories = ['All'] + sorted([s for s in subcats_raw if s.strip() != ''])
    else:
        subcategories = ['All']
    # Date range limits from data
    if 'NEWS_DT' in df.columns and not df.empty:
        df['NEWS_DT'] = pd.to_datetime(df['NEWS_DT'])
        min_db_date = df['NEWS_DT'].min().date()
    else:
        min_db_date = None
else:
    categories = ['All']
    subcategories = ['All']
    min_db_date = None

import pytz
from datetime import datetime
india_tz = pytz.timezone('Asia/Kolkata')
today_ist = datetime.now(india_tz).date()

with filter_cols[0]:
    # Default to current IST date, allow single date selection
    date_range = st.date_input(
        "Select Date Range",
        today_ist,
        min_value=min_db_date if min_db_date else None,
        max_value=today_ist
    )
with filter_cols[1]:
    selected_category = st.selectbox("Select Category", categories)
with filter_cols[2]:
    selected_subcategory = st.selectbox("Select Subcategory", subcategories)

st.markdown("""
<style>
.narrow-search-bar input {
    max-width: 340px;
    min-width: 180px;
    height: 2.2em !important;
    font-size: 1.01rem;
    border-radius: 7px !important;
    border: 1.5px solid #2d3a4a !important;
    background: #181A20 !important;
    color: #cbe8ff !important;
    box-shadow: 0 1px 6px rgba(41,98,255,0.03);
    padding: 0.25em 1em;
}
</style>
""", unsafe_allow_html=True)
search_term = st.text_input(
    "",
    key="news_search",
    placeholder="Search by Company Name or News Content...",
)
st.markdown('<div class="narrow-search-bar"></div>', unsafe_allow_html=True)

# --- REFRESH BUTTON ---
if st.button("🔄 Refresh Now", key="refresh_now_connected"):
    fetch_stock_news.clear()
    st.session_state.news_df, st.session_state.news_last_update = fetch_stock_news()
    st.rerun()

# --- FILTER THE NEWS DATAFRAME BASED ON UI ---
filtered_df = st.session_state.news_df.copy() if not st.session_state.news_df.empty else pd.DataFrame()

# Filter by date range
if not filtered_df.empty and date_range and 'NEWS_DT' in filtered_df.columns:
    filtered_df['NEWS_DT'] = pd.to_datetime(filtered_df['NEWS_DT'])
    filtered_df = filtered_df[filtered_df['NEWS_DT'].dt.date == date_range]

# Filter by category
if not filtered_df.empty and selected_category != 'All' and 'CATEGORYNAME' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['CATEGORYNAME'] == selected_category]

# Filter by subcategory
if not filtered_df.empty and selected_subcategory != 'All' and 'SUBCATNAME' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['SUBCATNAME'] == selected_subcategory]

# Filter by search term
if not filtered_df.empty and search_term:
    mask = filtered_df.apply(lambda x: x.astype(str).str.contains(search_term, case=False), axis=1).any(axis=1)
    filtered_df = filtered_df[mask]

# Fetch news in background after page loads
if not st.session_state.news_loading and st.session_state.news_df.empty:
    st.session_state.news_loading = True
    with st.spinner("Loading news data..."):
        st.session_state.news_df, st.session_state.news_last_update = fetch_stock_news()
        st.session_state.news_loading = False
        st.rerun()

if not filtered_df.empty:
    # Display news count
    col1, col2 = st.columns([2, 1])
    with col1:
        st.info(f"📚 Showing {len(filtered_df)} news items")
    
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
    display_cols = {k: v for k, v in display_cols.items() if k in filtered_df.columns}
    
    # Configure column display
    column_config = {
        'NEWS_DT': st.column_config.DatetimeColumn('Date & Time', format="DD-MM-YYYY hh:mm A"),
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
        filtered_df[display_cols.keys()],
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
            data=filtered_df.to_csv(index=False),
            file_name="stock_news.csv",
            mime="text/csv"
        )
    
    with col2:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            filtered_df.to_excel(writer, index=False)
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
