import streamlit as st
import pandas as pd
from datetime import datetime
import time

# Initialize session state for results data
if 'results_df' not in st.session_state:
    st.session_state.results_df = pd.DataFrame()
    st.session_state.results_last_update = None
    st.session_state.results_loading = False

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
@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_results():
    """Fetch results data from Google Sheets."""
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
        return pd.DataFrame(columns=['Scrip Code', 'Short Name', 'Long Name', 'Meeting Date', 'Last Updated']), str(time.time())

# Page Header
st.markdown("<div class='page-header'>", unsafe_allow_html=True)
st.header("📊 NSE Results Calendar")
st.caption("Track upcoming company results and board meetings")
st.markdown("</div>", unsafe_allow_html=True)

# Fetch results in background after page loads
if not st.session_state.results_loading and st.session_state.results_df.empty:
    st.session_state.results_loading = True
    with st.spinner("Loading results data..."):
        st.session_state.results_df, st.session_state.results_last_update = fetch_results()
        st.session_state.results_loading = False
        st.rerun()

# Main Content
if not st.session_state.results_df.empty:
    # Show last update time
    st.caption(f"Last Updated: {st.session_state.results_df['Last Updated'].iloc[0]}")
    
    # Create three columns for controls
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        # Add search functionality
        search_term = st.text_input("🔍 Search companies")
    
    with col2:
        # Get unique dates and sort them chronologically
        unique_dates = list(st.session_state.results_df['Meeting Date'].unique())
        sorted_dates = sort_dates(unique_dates)
        selected_date = st.selectbox(
            "📅 Select Date",
            ["All Dates"] + sorted_dates,
            help="Choose a specific date to filter results"
        )
    
    with col3:
        # Add export and refresh buttons at the top
        if st.button("📥 Export Results", use_container_width=True):
            export_df = st.session_state.results_df.copy()
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
    filtered_df = st.session_state.results_df.copy()
    
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
    if not st.session_state.results_loading:
        st.warning("No results data available. Please try refreshing.") 
