import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

# Page config
st.set_page_config(
    page_title="Price Bands Analysis",
    page_icon="📈",
    layout="centered"
)

# Load custom CSS
try:
    with open('style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except FileNotFoundError:
    st.warning("Style file not found. Page will run with default styling.")

# Page Header
st.markdown("""
<div class='page-header'>
    <div class='header-content'>
        <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0iIzAwZmY5NSI+PHBhdGggZD0iTTMgM3YxOGgxOFYzSDN6bTYgMTRINXYtMmg0djJ6bTQtNEg1di0yaDh2MnptNi00SDV2LTJoMTR2MnoiLz48L3N2Zz4=" class="header-icon" />
        <div class='header-text'>
            <h1>Price Bands</h1>
            <p class='subtitle'>Track and analyze price movements across bands</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Add custom CSS for better centered layout
st.markdown("""
<style>
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

.plotly-chart {
    width: 100%;
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
    .stSelectbox {
        width: 100%;
    }
}

/* Adjust card padding for smaller screens */
@media (max-width: 768px) {
    .content-card {
        padding: 1rem;
    }
}

/* Page Header */
.page-header {
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.header-content {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.header-icon {
    width: 40px;
    height: 40px;
}

.header-text h1 {
    margin: 0;
    font-size: 2rem;
    font-weight: 600;
}

.header-text .subtitle {
    margin: 0.5rem 0 0 0;
    color: rgba(255, 255, 255, 0.7);
    font-size: 1rem;
}

/* Content Cards */
.content-card {
    background: rgba(17, 17, 17, 0.8);
    border-radius: 10px;
    padding: 1.2rem;
    margin-bottom: 1.2rem;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

/* Progress bars */
.stProgress > div > div {
    background-color: #36A2EB !important;
}

/* Metrics */
.stMetric {
    background: rgba(17, 17, 17, 0.6);
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 0.8rem;
}

.stMetric label {
    color: rgba(255, 255, 255, 0.6) !important;
}

.stMetric .css-1wivap2 {
    color: #36A2EB !important;
}

/* Buttons */
.stButton > button {
    width: 100%;
    margin-bottom: 0.5rem;
    background-color: #36A2EB;
    border: none;
}

.stButton > button:hover {
    background-color: #2186D1;
}

/* Select box */
.stSelectbox > div > div {
    background-color: rgba(17, 17, 17, 0.8);
    border: 1px solid rgba(255, 255, 255, 0.1);
}

/* Make sure content is properly spaced */
.stColumns {
    gap: 1rem;
}

/* Adjust for centered layout */
@media (max-width: 768px) {
    .content-card {
        margin-bottom: 1rem;
    }
    
    .stMetric {
        margin-bottom: 0.5rem;
    }
}
</style>
""", unsafe_allow_html=True)

# --- Price Bands Data Fetch with Smart Cache and User Prompt ---
@st.cache_data(ttl=300)
def fetch_price_bands():
    try:
        url = "https://docs.google.com/spreadsheets/d/1xig6-dQ8PuPdeCxozcYdm15nOFUKMMZFm_p8VvRFDaE/gviz/tq?tqx=out:csv&gid=364491472"
        df = pd.read_csv(url)
        df = df[['Symbol', 'Series', 'Security Name', 'Band']]
        df['Band'] = pd.to_numeric(df['Band'], errors='coerce')
        df['Last Updated'] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        # Use the latest timestamp as version
        latest_update = df['Last Updated'].iloc[0] if not df.empty else str(time.time())
        return df, latest_update
    except Exception as e:
        st.error(f"Error fetching price bands: {str(e)}")
        return pd.DataFrame(columns=['Symbol', 'Series', 'Security Name', 'Band', 'Last Updated']), str(time.time())

# --- UI Logic for Smart Reload ---
price_bands_df, bands_last_update = fetch_price_bands()
if 'bands_last_seen_update' not in st.session_state:
    st.session_state['bands_last_seen_update'] = bands_last_update
if bands_last_update != st.session_state['bands_last_seen_update']:
    st.info('New price bands data is available!')
    if st.button('Reload Price Bands Data'):
        fetch_price_bands.clear()
        st.session_state['bands_last_seen_update'] = bands_last_update
        st.rerun()

# Fetch the data
price_bands_df = price_bands_df

# Calculate band distribution
if not price_bands_df.empty:
    total_stocks = len(price_bands_df)
    # Count stocks with no band (NaN values)
    no_band_count = price_bands_df['Band'].isna().sum()
    # Get distribution of numeric bands
    band_distribution = price_bands_df['Band'].value_counts()
    
    # Create ordered distribution with specific sequence
    ordered_bands = [20.0, 10.0, 5.0, 2.0, 'No Band']
    ordered_distribution = pd.Series(index=ordered_bands, dtype='float64')
    
    # Fill in the values, using 0 for any missing bands
    for band in ordered_bands:
        if band == 'No Band':
            ordered_distribution[band] = no_band_count
        else:
            ordered_distribution[band] = band_distribution.get(band, 0)
    
    band_distribution = ordered_distribution
    band_percentages = (band_distribution / total_stocks * 100).round(1)

# Main Content - Improved Column Ratios and Containers
col1, col2, col3 = st.columns([1.3, 2, 1.3])

with col1:
    with st.container():
        st.subheader("📊 Band Distribution")
        if not price_bands_df.empty:
            for band in ordered_bands:
                if band == 'No Band':
                    label = 'No Band'
                else:
                    label = f"{int(band)}%"
                percentage = band_percentages[band]
                count = band_distribution[band]
                st.markdown(f"**{label}**")
                st.progress(percentage / 100)
                st.caption(f"{percentage:.1f}% ({count:.1f} stocks)")
        st.markdown("<br>", unsafe_allow_html=True)

with col2:
    with st.container():
        st.subheader("📈 Band Analysis")
        if not price_bands_df.empty:
            ordered_bands = [20.0, 10.0, 5.0, 2.0, 'No Band']
            band_options = ['All Bands'] + [f"{int(band)}%" if isinstance(band, (int, float)) else str(band) for band in ordered_bands]
            selected_band = st.selectbox("Select Band", band_options)
            st.markdown("<br>", unsafe_allow_html=True)
            if selected_band == 'All Bands':
                st.markdown("### Band Distribution Overview")
                # Create donut chart with specific sequence
                ordered_bands = [20.0, 10.0, 5.0, 2.0, 'No Band']
                labels = [f"{int(band)}%" if isinstance(band, (int, float)) else str(band) for band in ordered_bands]
                values = [band_distribution[band] for band in ordered_bands]

                # Define a consistent color scheme - using blues and grays
                colors = ['#36A2EB', '#4BC0C0', '#9AD0F5', '#B8E0F3', '#808080']

                fig = go.Figure(data=[go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.4,
                    marker_colors=colors,
                    sort=False,
                    direction='clockwise',
                    textinfo='percent',  
                    textposition='outside',
                    showlegend=True,  
                    insidetextorientation='radial'  
                )])

                fig.update_layout(
                    legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                    showlegend=True,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    height=420,
                    margin=dict(t=30, b=30, l=0, r=0)
                )

                st.plotly_chart(fig, use_container_width=True)
                
            elif selected_band == 'No Band':
                no_band_data = price_bands_df[price_bands_df['Band'].isna()].copy()
                
                st.markdown("### No Band Summary")
                st.info(f"Total stocks with no band: {len(no_band_data)}")
                
                st.markdown("### Stocks with No Band")
                search = st.text_input("🔍 Search stocks by name or symbol")
                
                if search:
                    no_band_data = no_band_data[
                        no_band_data['Symbol'].str.contains(search, case=False) |
                        no_band_data['Security Name'].str.contains(search, case=False)
                    ]
                
                st.dataframe(
                    no_band_data[['Symbol', 'Security Name', 'Series']],
                    use_container_width=True,
                    height=300,
                    column_config={
                        'Symbol': st.column_config.TextColumn('Symbol', width='medium'),
                        'Security Name': st.column_config.TextColumn('Company Name', width='large'),
                        'Series': st.column_config.TextColumn('Series', width='small')
                    }
                )
            else:
                selected_value = float(selected_band.replace('%', ''))
                band_data = price_bands_df[price_bands_df['Band'] == selected_value].copy()
                
                if not band_data.empty:
                    st.markdown(f"### {selected_band} Summary")
                    st.info(f"Total stocks in {selected_band} band: {len(band_data)}")
                    
                    st.markdown(f"### Stocks in {selected_band}")
                    search = st.text_input("🔍 Search stocks by name or symbol")
                    
                    if search:
                        band_data = band_data[
                            band_data['Symbol'].str.contains(search, case=False) |
                            band_data['Security Name'].str.contains(search, case=False)
                        ]
                    
                    st.dataframe(
                        band_data[['Symbol', 'Security Name', 'Series']],
                        use_container_width=True,
                        height=300,
                        column_config={
                            'Symbol': st.column_config.TextColumn('Symbol', width='medium'),
                            'Security Name': st.column_config.TextColumn('Company Name', width='large'),
                            'Series': st.column_config.TextColumn('Series', width='small')
                        }
                    )
                else:
                    st.warning(f"No stocks found in {selected_band} band")
        st.markdown("<br>", unsafe_allow_html=True)

with col3:
    with st.container():
        st.subheader("🎯 Quick Actions")
        # Export Data Button
        if st.button("Export Data", type="primary", use_container_width=True):
            if not price_bands_df.empty:
                st.download_button(
                    label="Download CSV",
                    data=price_bands_df.to_csv(index=False),
                    file_name=f"price_bands_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    key="download-csv"
                )
        # Refresh Data Button
        if st.button("Refresh Data", type="primary", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        st.markdown("---")
        st.subheader("📊 Band Metrics")
        if not price_bands_df.empty:
            total_stocks = len(price_bands_df)
            total_bands = len(band_distribution.index)
            st.metric("Total Stocks", f"{total_stocks:,}")
            st.metric("Bands (incl. No Band)", total_bands)
            st.markdown(f"<div style='margin-top: 0.8rem; font-size: 1rem; color: #36A2EB;'><b>Last Updated:</b> {price_bands_df['Last Updated'].iloc[0]}</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

# Add extra CSS for more spacing
st.markdown("""
<style>
.stColumns {
    gap: 2.5rem !important;
}
.stContainer, .content-card {
    margin-bottom: 2rem !important;
    padding: 1.5rem !important;
}
</style>
""", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.caption(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}") 
