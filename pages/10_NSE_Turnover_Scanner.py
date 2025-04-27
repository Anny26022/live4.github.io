import streamlit as st
import pandas as pd
from tradingview_screener import Query, Column

st.set_page_config(
    page_title="NSE Turnover Scanner",
    page_icon="",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.title("NSE Turnover Scanner")
st.caption("Indian stocks by average 10/30 day turnover ()")

# Exchange selector
exchange_options = ['NSE', 'BSE']
selected_exchange = st.radio(
    'Select Exchange:',
    options=exchange_options,
    index=0,
    horizontal=True
)

# Create a query for selected exchange stocks
where_conditions = [
    Column('exchange') == selected_exchange,
    Column('type') == 'stock'
]
# For NSE, only show primary listings
if selected_exchange == 'NSE':
    where_conditions.append(Column('is_primary') == True)

query = (
    Query()
    .set_markets('india')  # Focus on Indian market
    .select(
        'name',  # Stock name/symbol
        'close',  # Current price
        'exchange',  # Exchange (to filter for NSE/BSE)
        'average_volume_10d_calc',  # 10-day average volume
        'average_volume_30d_calc',  # 30-day average volume
        'average_volume_60d_calc',  # 60-day average volume
        'average_volume_90d_calc'   # 90-day average volume
    )
    .where(*where_conditions)
    .limit(20000)  # Set a high limit to get all stocks
)

# Execute the query
count, df = query.get_scanner_data()

# Calculate average turnover in crores for different time periods
if not df.empty:
    # 10-day average turnover
    df['10d_Avg_Turnover_Cr'] = (df['average_volume_10d_calc'] * df['close'] / 10000000).round(2)
    # 30-day average turnover
    df['30d_Avg_Turnover_Cr'] = (df['average_volume_30d_calc'] * df['close'] / 10000000).round(2)
    # 60-day average turnover
    df['60d_Avg_Turnover_Cr'] = (df['average_volume_60d_calc'] * df['close'] / 10000000).round(2)
    # 90-day average turnover
    df['90d_Avg_Turnover_Cr'] = (df['average_volume_90d_calc'] * df['close'] / 10000000).round(2)
    # Rename columns for clarity
    df = df.rename(columns={
        'name': 'Stock Name',
        'close': 'Close Price',
        'average_volume_10d_calc': '10D Avg Vol',
        'average_volume_30d_calc': '30D Avg Vol',
        'average_volume_60d_calc': '60D Avg Vol',
        'average_volume_90d_calc': '90D Avg Vol'
    })
    # Display in Streamlit (without Close Price column)
    st.dataframe(
        df[['Stock Name',
            '10D Avg Vol', '10d_Avg_Turnover_Cr',
            '30D Avg Vol', '30d_Avg_Turnover_Cr',
            '60D Avg Vol', '60d_Avg_Turnover_Cr',
            '90D Avg Vol', '90d_Avg_Turnover_Cr']],
        use_container_width=True
    )
    st.caption(f"Showing {len(df)} {selected_exchange} stocks with 10/30/60/90 day turnover in crores.")
else:
    st.warning("No data found. Please try again later.")
