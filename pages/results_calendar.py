import streamlit as st
import pandas as pd
from datetime import datetime
import time
import threading

# Date parsing helper for export
def parse_date(date_str):
    """Parse DD MMM format and add current year for proper sorting (used in export)."""
    try:
        current_year = datetime.now().year
        return datetime.strptime(f"{date_str} {current_year}", '%d %b %Y')
    except ValueError as e:
        st.error(f"Error parsing date: {date_str}, {str(e)}")
        return datetime.now()

# Page config
st.set_page_config(
    page_title="NSE Results Calendar",
    page_icon="📅",
    layout="centered"
)

# Load custom CSS
try:
    with open('style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except FileNotFoundError:
    pass

def sort_dates(dates):
    """Helper function to sort dates properly"""
    def parse_date_inner(date_str):
        # Parse DD MMM format and add current year for proper sorting
        try:
            current_year = datetime.now().year
            return datetime.strptime(f"{date_str} {current_year}", '%d %b %Y')
        except ValueError as e:
            st.error(f"Error parsing date: {date_str}, {str(e)}")
            return datetime.now()  # Fallback to current date if parsing fails

    return sorted(dates, key=parse_date_inner)

# Add results data fetching
@st.cache_data(ttl=21600)  # Cache for 6 hours
def fetch_results():
    """Fetch results data from Google Sheets. If unavailable, return cached data if possible."""
    try:
        url = "https://docs.google.com/spreadsheets/d/1xig6-dQ8PuPdeCxozcYdm15nOFUKMMZFm_p8VvRFDaE/gviz/tq?tqx=out:csv&gid=948182834"
        df = pd.read_csv(url)
        df = df[['Scrip Code', 'Short Name', 'Long Name', 'Meeting Date']]
        # Ensure Scrip Code is numeric
        df['Scrip Code'] = pd.to_numeric(df['Scrip Code'])
        df['Last Updated'] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        # Use the latest timestamp as version
        latest_update = df['Last Updated'].iloc[0] if not df.empty else str(time.time())
        return df, latest_update
    except Exception as e:
        st.error(f"Error fetching results: {str(e)}")
        # Try to load from cache if available
        cache = st.session_state.get('results_cache')
        if cache is not None:
            st.warning("Showing cached results data. Data may be outdated.")
            return cache['df'], cache['last_update']
        # Fallback to empty
        return pd.DataFrame(columns=['Scrip Code', 'Short Name', 'Long Name', 'Meeting Date', 'Last Updated']), str(time.time())

# --- INTELLIGENT CACHING: ensure user always sees data instantly if possible ---
# On first load, try to show cached data from session state immediately, and update in background.
if 'results_cache' in st.session_state and st.session_state['results_cache']['df'] is not None and not st.session_state['results_cache']['df'].empty:
    results_df = st.session_state['results_cache']['df']
    results_last_update = st.session_state['results_cache']['last_update']
else:
    # Try to fetch from cache_data (Streamlit's persistent cache) if session cache is empty
    try:
        results_df, results_last_update = fetch_results()
        # Save to session state for instant access on next load
        if results_df is not None and not results_df.empty:
            st.session_state['results_cache'] = {'df': results_df, 'last_update': results_last_update}
    except Exception:
        results_df, results_last_update = pd.DataFrame(), None

# Start background fetch for fresh data (will update session cache for next reload)
def _load_results_bg():
    global results_df, results_last_update
    new_df, new_last_update = fetch_results()
    if new_df is not None and not new_df.empty:
        st.session_state['results_cache'] = {'df': new_df, 'last_update': new_last_update}
        # Optionally, trigger a rerun if new data is fresher
        if results_last_update != new_last_update:
            st.experimental_rerun()
threading.Thread(target=_load_results_bg).start()

# Show skeleton/placeholder while loading only if no cached data
if results_df is None or results_df.empty:
    # Try to show last cache if available
    cache = st.session_state.get('results_cache')
    if cache and cache['df'] is not None and not cache['df'].empty:
        results_df = cache['df']
        results_last_update = cache['last_update']
        st.warning("Showing last cached results data. Data may be outdated.")
    else:
        st.info("⌛ Loading results calendar...")

# Page Header
st.markdown("<div class='page-header'>", unsafe_allow_html=True)
st.header("📊 NSE Results Calendar")
st.caption("Track upcoming company results and board meetings")
st.markdown("</div>", unsafe_allow_html=True)

# Main Content
if not results_df.empty:
    # Show last update time
    st.caption(f"Last Updated: {results_df['Last Updated'].iloc[0]}")
    
    # Create three columns for controls
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        # Add search functionality
        search_term = st.text_input("🔍 Search companies")
    
    with col2:
        # Get unique dates and sort them chronologically
        unique_dates = list(results_df['Meeting Date'].unique())
        sorted_dates = sort_dates(unique_dates)
        selected_date = st.selectbox(
            "📅 Select Date",
            ["All Dates"] + sorted_dates,
            help="Choose a specific date to filter results"
        )
    
    with col3:
        # Add export and refresh buttons at the top
        if st.button("📥 Export Results", use_container_width=True):
            export_df = results_df.copy()
            export_df['Scrip Code'] = export_df['Scrip Code'].astype(int)
            export_df['Sort_Date'] = export_df['Meeting Date'].apply(lambda x: parse_date(x))
            export_df = export_df.sort_values(['Sort_Date', 'Short Name'])
            export_df = export_df.drop('Sort_Date', axis=1)
            st.download_button(
                "Download CSV",
                export_df.to_csv(index=False),
                f"nse_results_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv",
                key='download-csv-top'
            )
        if st.button("🔄 Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    # Filter results
    filtered_df = results_df.copy()
    
    if search_term:
        filtered_df = filtered_df[
            filtered_df['Short Name'].str.contains(search_term, case=False) |
            filtered_df['Long Name'].str.contains(search_term, case=False)
        ]
    
    if selected_date != "All Dates":
        filtered_df = filtered_df[filtered_df['Meeting Date'] == selected_date]
    
    # Show summary metrics
    total_companies = len(filtered_df)
    total_dates = len(filtered_df['Meeting Date'].unique())
    
    st.markdown("---")
    
    m1, m2 = st.columns(2)
    with m1:
        st.metric("Total Companies", total_companies)
    with m2:
        st.metric("Meeting Dates", total_dates)

    # Display results in a clean table format
    st.markdown("### 📅 Results Calendar")
    
    # Get sorted unique dates from filtered data
    display_dates = sort_dates(filtered_df['Meeting Date'].unique())
    
    # Display results by date
    for date in display_dates:
        date_group = filtered_df[filtered_df['Meeting Date'] == date]
        # Sort the group by Symbol (Short Name)
        date_group = date_group.sort_values('Short Name')
        
        with st.expander(f"📅 {date} ({len(date_group)} companies)", expanded=True):
            # Create a styled dataframe
            styled_df = pd.DataFrame({
                'Scrip Code': date_group['Scrip Code'].astype(int),
                'Symbol': date_group['Short Name'],
                'Company Name': date_group['Long Name']
            })
            
            st.dataframe(
                styled_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    'Scrip Code': st.column_config.NumberColumn(
                        'Scrip Code',
                        help='NSE Scrip Code',
                        format='%d'
                    ),
                    'Symbol': st.column_config.TextColumn(
                        'Symbol',
                        help='Company Symbol',
                        width='medium'
                    ),
                    'Company Name': st.column_config.TextColumn(
                        'Company Name',
                        help='Full Company Name',
                        width='large'
                    )
                }
            )
    
else:
    st.warning("No results data available. Please try refreshing.")
