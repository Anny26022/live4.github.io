import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

# --- Price Bands Data Fetch with Smart Cache ---
@st.cache_data(ttl=21600)
def fetch_price_bands():
    try:
        url = "https://docs.google.com/spreadsheets/d/1xig6-dQ8PuPdeCxozcYdm15nOFUKMMZFm_p8VvRFDaE/gviz/tq?tqx=out:csv&gid=364491472"
        df = pd.read_csv(url)
        df = df[['Symbol', 'Series', 'Security Name', 'Band']]
        df['Band'] = pd.to_numeric(df['Band'], errors='coerce')
        current_time = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        df['Last Updated'] = current_time
        # Use the latest timestamp as version
        latest_update = df['Last Updated'].iloc[0] if not df.empty else str(time.time())
        return df, latest_update
    except Exception as e:
        st.error(f"Error fetching price bands: {str(e)}")
        return pd.DataFrame(columns=['Symbol', 'Series', 'Security Name', 'Band', 'Last Updated']), str(time.time())

# Initialize session state for price bands data
if 'price_bands_df' not in st.session_state:
    # Always load from cache for instant page load
    st.session_state.price_bands_df, st.session_state.bands_last_update = fetch_price_bands()

if __name__ == "__main__":
    # Load custom CSS
    try:
        with open('style.css') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Style file not found. Page will run with default styling.")

    # Page Header with modern SVG (Material: Signal Cell Tower)
    st.markdown("""
    <div style='display:flex;align-items:center;justify-content:center;margin-bottom:0.5em;'>
      <svg xmlns='http://www.w3.org/2000/svg' width='48' height='48' viewBox='0 0 48 48' fill='none' style='margin-right:16px;'>
        <rect width='48' height='48' rx='12' fill='url(#bands-bg)'/>
        <g>
          <rect x='16' y='28' width='4' height='8' rx='2' fill='#43a047'/>
          <rect x='24' y='20' width='4' height='16' rx='2' fill='#29b6f6'/>
          <rect x='32' y='12' width='4' height='24' rx='2' fill='#ab47bc'/>
        </g>
        <defs>
          <linearGradient id='bands-bg' x1='0' y1='0' x2='48' y2='48' gradientUnits='userSpaceOnUse'>
            <stop stop-color='#23272F'/>
            <stop offset='1' stop-color='#181A20'/>
          </linearGradient>
        </defs>
      </svg>
      <span style='font-size:2.5rem;font-weight:700;color:#fff;'>Price Bands</span>
    </div>
    <p style='text-align:center;margin-top:-0.75em;margin-bottom:2em;color:#aaa;font-size:1.1rem;'>Monitor stocks with price band movements</p>
    """, unsafe_allow_html=True)

    # Add a refresh button to clear cache and reload
    refresh = st.button("🔄 Refresh Price Bands", help="Clear cache and fetch fresh data")
    if refresh:
        st.cache_data.clear()
        st.session_state.price_bands_df, st.session_state.bands_last_update = fetch_price_bands()
        st.rerun()

    if not st.session_state.price_bands_df.empty:
        # Calculate band distribution
        total_stocks = len(st.session_state.price_bands_df)
        no_band_count = st.session_state.price_bands_df['Band'].isna().sum()
        band_distribution = st.session_state.price_bands_df['Band'].value_counts()
        
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
                if not st.session_state.price_bands_df.empty:
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
                if not st.session_state.price_bands_df.empty:
                    ordered_bands = [20.0, 10.0, 5.0, 2.0, 'No Band']
                    band_options = ['All Bands'] + [f"{int(band)}%" if isinstance(band, (int, float)) else str(band) for band in ordered_bands]
                    selected_band = st.selectbox(
                        "Select Price Band",
                        options=band_options,
                        key="band_selector"
                    )
                    st.markdown("<br>", unsafe_allow_html=True)
                    search = st.text_input("🔍 Search stocks by name or symbol")
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
                        no_band_data = st.session_state.price_bands_df[st.session_state.price_bands_df['Band'].isna()].copy()
                        
                        st.markdown("### No Band Summary")
                        st.info(f"Total stocks with no band: {len(no_band_data)}")
                        
                        st.markdown("### Stocks with No Band")
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
                        band_data = st.session_state.price_bands_df[st.session_state.price_bands_df['Band'] == selected_value].copy()
                        
                        if not band_data.empty:
                            st.markdown(f"### {selected_band} Summary")
                            st.info(f"Total stocks in {selected_band} band: {len(band_data)}")
                            
                            st.markdown(f"### Stocks in {selected_band}")
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
                # --- Compact, Colorful, Modern Glassmorphism CSS for Buttons ---
                st.markdown("""
                <style>
                .glass-btn {
                    background: linear-gradient(90deg, #00ff95 0%, #36a2eb 100%);
                    border: 1.5px solid rgba(255,255,255,0.32);
                    box-shadow: 0 2px 12px 0 rgba(31,38,135,0.10);
                    backdrop-filter: blur(5px);
                    -webkit-backdrop-filter: blur(5px);
                    border-radius: 7px;
                    color: #fff;
                    font-weight: 600;
                    font-size: 0.92rem;
                    padding: 0.28rem 0;
                    margin-bottom: 0.35rem;
                    width: 90%;
                    outline: none;
                    transition: all 0.16s cubic-bezier(.4,0,.2,1);
                    position: relative;
                    overflow: hidden;
                    letter-spacing: 0.01em;
                    min-height: 31px;
                }
                .glass-btn:hover {
                    background: linear-gradient(90deg, #36a2eb 0%, #00ff95 100%);
                    color: #fff;
                    transform: translateY(-1px) scale(1.025);
                    box-shadow: 0 4px 16px 0 rgba(54,162,235,0.13);
                }
                .glass-btn:active {
                    background: linear-gradient(90deg, #00bfff 0%, #00ff95 100%);
                    color: #fff;
                    transform: scale(0.97);
                }
                @keyframes glassPulse {
                  0% { box-shadow: 0 0 0 0 rgba(54,162,235,0.09); }
                  70% { box-shadow: 0 0 0 6px rgba(0,255,149,0); }
                  100% { box-shadow: 0 0 0 0 rgba(0,255,149,0); }
                }
                .glass-btn.glass-animate {
                  animation: glassPulse 1.2s infinite;
                }
                </style>
                """, unsafe_allow_html=True)
                # --- End Compact Colorful Glassmorphism CSS ---
                # Streamlit native buttons for correct functionality
                export_btn = st.button("Export Data", key="export_data_btn", use_container_width=True)
                if export_btn and not st.session_state.price_bands_df.empty:
                    st.download_button(
                        label="Download CSV",
                        data=st.session_state.price_bands_df.to_csv(index=False),
                        file_name=f"price_bands_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        key="download-csv",
                        help="Download the complete price bands data"
                    )
                st.markdown("---")
                st.subheader("📊 Band Metrics")
                if not st.session_state.price_bands_df.empty:
                    total_stocks = len(st.session_state.price_bands_df)
                    total_bands = len(band_distribution.index)
                    st.metric(
                        label="Total Stocks",
                        value=f"{total_stocks:,}",
                        help="Total number of stocks in the dataset"
                    )
                    st.metric(
                        label="Number of Price Bands",
                        value=total_bands,
                        help="Total number of different price bands (including No Band)"
                    )
                    st.markdown(f"<div style='margin-top: 0.8rem; font-size: 1rem; color: #36A2EB;'><b>Last Updated:</b> {st.session_state.price_bands_df['Last Updated'].iloc[0]}</div>", unsafe_allow_html=True)
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
    