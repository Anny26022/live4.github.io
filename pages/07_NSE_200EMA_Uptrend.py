import streamlit as st
st.set_page_config(page_title="200 MA Uptrend Scanner", page_icon="📈", layout="centered")

st.title("📈 200 MA Uptrend Scanner")

from src.tradingview_screener import Query, Column as col, And, Or
from src.tradingview_screener.markets_list import MARKETS

# Only allow Indian market
market_names = [name for name, code in MARKETS if code == 'india']
market_codes = {name: code for name, code in MARKETS if code == 'india'}
selected_market_name = market_names[0]
selected_market = market_codes[selected_market_name]

# Restrict exchanges to NSE/BSE only
exchange_options = ["NSE", "BSE"]
exchange_input = st.selectbox("Select Exchange", exchange_options, index=0)

# Allow user to select SMA or EMA
ma_type = st.radio("Select Moving Average Type", ["EMA", "SMA"], index=0, horizontal=True)
ma_prefix = "EMA200" if ma_type == "EMA" else "SMA200"

# Allow user to select which MA history periods to use (1M, 3M, 6M)
period_options = [
    ("1 Month", "1M"),
    ("3 Months", "3M"),
    ("6 Months", "6M")
]
default_period_labels = ["1 Month"]
selected_period_labels = st.multiselect(
    "Select MA history periods to compare",
    [label for label, code in period_options],
    default=default_period_labels
)
selected_periods = [code for label, code in period_options if label in selected_period_labels]

# Build uptrend filter dynamically using selected MA type
ma_filters = []
ma_columns = [ma_prefix] + [f"{ma_prefix}|{p}" for p in selected_periods]
for i in range(len(ma_columns) - 1):
    ma_filters.append(col(ma_columns[i]) > col(ma_columns[i + 1]))

st.caption(f"Find {exchange_input} stocks with a consistent 200 {ma_type} uptrend over the last {', '.join(selected_period_labels)}, sorted by relative volume.")

# If NSE is selected, add 'is_primary' to columns and display
show_primary = exchange_input == "NSE"
if show_primary:
    extra_select = ['is_primary']
else:
    extra_select = []

with st.spinner("Running TradingView scan..."):
    query = (
        Query()
        .set_markets(selected_market)
        .where(
            col('type') == 'stock',
            col('exchange') == exchange_input,
            *ma_filters,
            col('volume') > 50000
        )
        .select(
            'name',
            'close',
            *ma_columns,
            'volume',
            'relative_volume_10d_calc',
            'sector',
            'industry',
            'exchange',
            *extra_select
        )
        .order_by('relative_volume_10d_calc', ascending=False)
        .limit(100)
    )
    count, df = query.get_scanner_data()

if df is not None and not df.empty:
    st.success(f"Found {count} {exchange_input} stocks with 200 {ma_type} uptrend!")
    display_cols = [
        'name', 'close', *ma_columns, 'volume', 'relative_volume_10d_calc', 'sector', 'industry', 'exchange',
        *extra_select
    ]
    st.dataframe(
        df[display_cols],
        use_container_width=True
    )
else:
    st.info(f"No {exchange_input} stocks found with a consistent 200 {ma_type} uptrend for {', '.join(selected_period_labels)}.")
