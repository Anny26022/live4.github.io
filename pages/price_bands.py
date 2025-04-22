import streamlit as st
import pandas as pd

# Set page config
st.set_page_config(
    page_title="NSE Price Bands",
    page_icon="📊",
    layout="wide"
)

# Add price band data fetching
@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_price_bands():
    """Fetch price band data from Google Sheets."""
    try:
        url = "https://docs.google.com/spreadsheets/d/1xig6-dQ8PuPdeCxozcYdm15nOFUKMMZFm_p8VvRFDaE/gviz/tq?tqx=out:csv&gid=364491472"
        df = pd.read_csv(url)
        df = df[['Symbol', 'Series', 'Security Name', 'Band']]
        df['Band'] = pd.to_numeric(df['Band'], errors='coerce')
        df['Last Updated'] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        return df
    except Exception as e:
        st.error(f"Error fetching price bands: {str(e)}")
        return pd.DataFrame(columns=['Symbol', 'Series', 'Security Name', 'Band', 'Last Updated'])

# Add price band section
st.header("📊 NSE Price Bands")

# Fetch and display price band data
price_bands_df = fetch_price_bands()

if not price_bands_df.empty:
    # Show last update time
    st.caption(f"Last Updated: {price_bands_df['Last Updated'].iloc[0]}")
    
    # Show price band distribution
    band_counts = price_bands_df['Band'].value_counts().sort_index()
    # Add count for No Band (NaN values)
    no_band_count = price_bands_df['Band'].isna().sum()
    if no_band_count > 0:
        band_counts = pd.concat([pd.Series({'No Band': no_band_count}), band_counts])
    st.bar_chart(band_counts)
    
    # Allow filtering by price band
    band_options = sorted(price_bands_df['Band'].dropna().unique())
    # Add "No Band" option if there are stocks without bands
    if no_band_count > 0:
        band_options = [None] + band_options
        
    selected_band = st.selectbox(
        "Select Price Band",
        options=band_options,
        format_func=lambda x: "No Band" if x is None else f"Band {x}"
    )
    
    # Show stocks in selected band
    if selected_band is None:
        # Show stocks with no band
        filtered_stocks = price_bands_df[price_bands_df['Band'].isna()]
    else:
        # Show stocks with selected band
        filtered_stocks = price_bands_df[price_bands_df['Band'] == selected_band]
        
    st.dataframe(
        filtered_stocks[['Symbol', 'Security Name']],
        use_container_width=True,
        height=200
    )
    
    # Add refresh button
    if st.button("🔄 Refresh Price Bands"):
        st.cache_data.clear()
        st.experimental_rerun() 