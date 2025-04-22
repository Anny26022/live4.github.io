import streamlit as st
import pandas as pd

# Set page config
st.set_page_config(
    page_title="NSE Results",
    page_icon="📊",
    layout="wide"
)

# Add results data fetching
@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_results():
    """Fetch results data from Google Sheets."""
    try:
        url = "https://docs.google.com/spreadsheets/d/1xig6-dQ8PuPdeCxozcYdm15nOFUKMMZFm_p8VvRFDaE/gviz/tq?tqx=out:csv&gid=948182834"
        df = pd.read_csv(url)
        df = df[['Scrip Code', 'Short Name', 'Long Name', 'Meeting Date']]
        df['Last Updated'] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        return df
    except Exception as e:
        st.error(f"Error fetching results: {str(e)}")
        return pd.DataFrame(columns=['Scrip Code', 'Short Name', 'Long Name', 'Meeting Date', 'Last Updated'])

# Add results section
st.header("📊 NSE Results Calendar")

# Fetch and display results data
results_df = fetch_results()

if not results_df.empty:
    # Show last update time
    st.caption(f"Last Updated: {results_df['Last Updated'].iloc[0]}")
    
    # Add search functionality
    search_term = st.text_input("🔍 Search companies", "")
    
    # Filter based on search term
    if search_term:
        filtered_df = results_df[
            results_df['Short Name'].str.contains(search_term, case=False) |
            results_df['Long Name'].str.contains(search_term, case=False)
        ]
    else:
        filtered_df = results_df
    
    # Group by Meeting Date
    grouped = filtered_df.groupby('Meeting Date')
    
    # Show results by date
    for date, group in grouped:
        with st.expander(f"📅 {date} ({len(group)} companies)"):
            st.dataframe(
                group[['Scrip Code', 'Short Name', 'Long Name']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    'Scrip Code': st.column_config.NumberColumn('Scrip Code'),
                    'Short Name': st.column_config.TextColumn('Symbol'),
                    'Long Name': st.column_config.TextColumn('Company Name')
                }
            )
    
    # Add refresh button
    if st.button("🔄 Refresh Results"):
        st.cache_data.clear()
        st.experimental_rerun()
else:
    st.warning("No results data available. Please try refreshing.") 