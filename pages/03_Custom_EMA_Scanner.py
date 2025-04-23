import streamlit as st
from tradingview_screener import Query, Column, col
import pandas as pd
import os
from utils import get_listing_date_map_cached
import sys

st.set_page_config(
    page_title="Custom EMA Stock Scanner",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.title("Custom EMA Stock Scanner")

# --- UI: Market Region Selection ---
st.subheader("Market Region")
# Example region list (should match your supported TradingView regions)
market_regions = [
    "america", "india", "europe", "hongkong", "japan", "australia", "canada", "uk", "crypto", "forex"
]
selected_regions = st.multiselect(
    "Choose Market Region(s):",
    options=market_regions,
    default=["india"],
    key="market_region"
)

# --- UI: EMA Selection ---
st.subheader("Price Above/Below Moving Averages")
ema_options = [
    ("Above 200 Days MA", "EMA200"),
    ("Above 150 Days MA", "EMA150"),
    ("Above 50 Days MA", "EMA50"),
    ("Above 20 Days MA", "EMA20"),
    ("Above 10 Days MA", "EMA10"),
]

# --- Minimalistic EMA Condition Toggles ---
enable_above_ema = st.checkbox("'Above' EMA", value=True)
enable_below_ema = st.checkbox("'Below' EMA", value=False)

def get_default_above_ema():
    return ["Above 200 Days MA", "Above 150 Days MA", "Above 50 Days MA"]

selected_above = []
selected_below = []
if enable_above_ema:
    selected_above = st.multiselect(
        "",
        [label for label, _ in ema_options],
        default=get_default_above_ema(),
        key="ema_above",
        disabled=not enable_above_ema
    )
else:
    st.multiselect(
        "",
        [label for label, _ in ema_options],
        default=get_default_above_ema(),
        key="ema_above",
        disabled=True
    )
if enable_below_ema:
    selected_below = st.multiselect(
        "",
        [label.replace("Above", "Below") for label, _ in ema_options],
        key="ema_below",
        disabled=not enable_below_ema
    )
else:
    st.multiselect(
        "",
        [label.replace("Above", "Below") for label, _ in ema_options],
        key="ema_below",
        disabled=True
    )

# --- Minimalistic Near Highs Toggle ---
enable_near_highs = st.checkbox("Near New Highs", value=False)
near_highs = []
if enable_near_highs:
    near_highs = st.multiselect(
        "",
        ["1 Month High", "3 Month High", "52 Week High"],
        key="near_highs",
        disabled=not enable_near_highs
    )
else:
    st.multiselect(
        "",
        ["1 Month High", "3 Month High", "52 Week High"],
        key="near_highs",
        disabled=True
    )

# --- % from 52w Low Price Range Toggle ---
enable_52w_low = st.checkbox("% from 52w Low Price Range:")
col_52w_low, col_52w_low_min, col_52w_low_max = st.columns([0.15, 0.2, 0.2])
with col_52w_low:
    use_52w_low = enable_52w_low
with col_52w_low_min:
    low_52w_min = st.number_input("", min_value=0, max_value=1000, value=30, key="low_52w_min", disabled=not enable_52w_low)
with col_52w_low_max:
    low_52w_max = st.number_input(" ", min_value=0, max_value=1000, value=1000, key="low_52w_max", disabled=not enable_52w_low)

# --- Free Float (%) Toggle ---
enable_float = st.checkbox("Free Float(%):")
col_float, col_float_min, col_float_max = st.columns([0.15, 0.2, 0.2])
with col_float:
    use_float = enable_float
with col_float_min:
    float_min = st.number_input("", min_value=0, max_value=100, value=0, key="float_min", disabled=not enable_float)
with col_float_max:
    float_max = st.number_input("  ", min_value=0, max_value=100, value=100, key="float_max", disabled=not enable_float)

# --- Fetch Price Band Data ---
@st.cache_data(ttl=300)
def fetch_price_bands():
    try:
        url = "https://docs.google.com/spreadsheets/d/1xig6-dQ8PuPdeCxozcYdm15nOFUKMMZFm_p8VvRFDaE/gviz/tq?tqx=out:csv&gid=364491472"
        df = pd.read_csv(url)
        df = df[['Symbol', 'Band']]
        df['Band'] = pd.to_numeric(df['Band'], errors='coerce')
        return df
    except Exception as e:
        st.error(f"Error fetching price bands: {str(e)}")
        return pd.DataFrame(columns=['Symbol', 'Band'])

price_bands_df = fetch_price_bands()

# --- UI: Price Band Filter ---
st.subheader("Price Band")
if not price_bands_df.empty:
    band_options = sorted(price_bands_df['Band'].dropna().unique().tolist())
    band_options = [f"{int(b)}%" for b in band_options]
    band_options.append("None")  # Add 'None' option for 'no band'
    default_selected_bands = [x for x in band_options if x in ["10%", "20%", "5%"]]
    selected_bands = st.multiselect("Select Price Band(s) (optional)", band_options, default=default_selected_bands, key="price_band")
else:
    selected_bands = []

# --- UI: Other Filters (add more as needed) ---
st.subheader("Other Filters")
# Manual inputs for Market Cap and Stock Price
market_cap_min = st.number_input(
    "Market Cap Min (Cr.)", min_value=0, max_value=5000000, value=0, step=1, key="mcap_min")
market_cap_max = st.number_input(
    "Market Cap Max (Cr.)", min_value=0, max_value=5000000, value=500000, step=1, key="mcap_max")
stock_price_min = st.number_input(
    "Stock Price Min (₹)", min_value=0, max_value=150000, value=0, step=1, key="stock_min")
stock_price_max = st.number_input(
    "Stock Price Max (₹)", min_value=0, max_value=150000, value=150000, step=1, key="stock_max")

# --- UI: Exchange Selection ---
st.subheader("Exchange")
exchange_options = ["NSE", "BSE"]  # Default to Indian exchanges
selected_exchanges = st.multiselect(
    "Select Exchange(s):",
    options=exchange_options,
    default=["NSE"],
    key="exchange_select"
)

# --- Centrally map listing_dates.txt ---
@st.cache_data(ttl=3600)
def get_listing_dates():
    """
    Returns a dictionary {symbol: listing_date} from listing_dates.txt
    """
    try:
        return get_listing_date_map_cached()
    except Exception as e:
        st.warning(f"Could not load listing dates: {e}")
        return {}

listing_dates_map = get_listing_dates()

# --- Query Construction ---
# Prevent contradictory EMA selections
contradictory_emas = set(selected_above) & set([below_label_map.get(lbl, lbl) for lbl in selected_below])
if contradictory_emas:
    st.warning(f"You selected both 'Above' and 'Below' for: {', '.join(contradictory_emas)}. Please fix your selection.")

# Build filters
ema_filters = []
if enable_above_ema:
    for label in selected_above:
        ema_col = dict(ema_options)[label]
        ema_filters.append(Column("close") > Column(ema_col))
if enable_below_ema:
    for label in selected_below:
        orig_label = below_label_map.get(label, label)
        ema_col = dict(ema_options)[orig_label]

        ema_filters.append(Column("close") < Column(ema_col))

other_filters = []
post_filters = []
# Near Highs
high_map = {
    "1 Month High": "High.1M",
    "3 Month High": "High.3M",
    "52 Week High": "price_52_week_high"
}
for high in near_highs:
    other_filters.append(Column("close") >= Column(high_map[high]))
# Market Cap
if market_cap_min > 0 or market_cap_max < 5000000:
    other_filters.append(Column("market_cap_basic").between(market_cap_min * 1e7, market_cap_max * 1e7))  # Cr. to Rs.
# Stock Price
if stock_price_min > 0 or stock_price_max < 150000:
    other_filters.append(Column("close").between(stock_price_min, stock_price_max))
# Exchange filter
if selected_exchanges:
    other_filters.append(Column("exchange").isin(selected_exchanges))
# Price Band filter
if selected_bands and not price_bands_df.empty:
    band_values = [float(b.replace('%','')) for b in selected_bands if b != "None"]
    allowed_symbols = []
    if band_values:
        allowed_symbols += price_bands_df[price_bands_df['Band'].isin(band_values)]['Symbol'].tolist()
    if "None" in selected_bands:
        allowed_symbols += price_bands_df[price_bands_df['Band'].isna()]['Symbol'].tolist()
    if allowed_symbols:
        other_filters.append(Column("name").isin(allowed_symbols))
    else:
        st.warning(f"No stocks found in selected price band(s). No price band filter applied.")
# % from 52w Low Price Range
if use_52w_low:
    post_filters.append(
        lambda df: ((df["close"] - df["price_52_week_low"]) / df["price_52_week_low"] * 100).between(low_52w_min, low_52w_max)
    )
# Free Float (%)
if use_float:
    other_filters.append(Column("float_shares_percent_current").between(float_min, float_max))

# Combine ONLY Column-based filters for Query
query_filters = ema_filters + [f for f in other_filters if not callable(f)]

# --- Run Query Button ---
if st.button("Run Scan"):
    if contradictory_emas:
        st.error("Cannot run scan with contradictory EMA selections. Please fix your selection.")
    else:
        q = Query().select("name", "close", "volume", "market_cap_basic", "sector", "industry", "price_52_week_low", "price_52_week_high")
        # Correct market logic as in Query.set_markets
        if selected_regions:
            if len(selected_regions) == 1:
                q.url = f"https://scanner.tradingview.com/{selected_regions[0]}/scan"
                q.query['markets'] = [selected_regions[0]]
            else:
                q.url = "https://scanner.tradingview.com/global/scan"
                q.query['markets'] = list(selected_regions)
        if query_filters:
            q = q.where(*query_filters)
        # Set row limit to 20000
        q = q.limit(20000)
        try:
            count, df = q.get_scanner_data()
            # --- Update sector/industry options dynamically ---
            if not df.empty:
                st.session_state['sector_options'] = ["All"] + sorted([x for x in df['sector'].dropna().unique() if x])
                st.session_state['industry_options'] = ["All"] + sorted([x for x in df['industry'].dropna().unique() if x])
            # --- Merge price band info ---
            if not df.empty and not price_bands_df.empty:
                # Merge on symbol/name (assumes df['name'] matches price_bands_df['Symbol'])
                df = df.merge(price_bands_df.rename(columns={'Symbol': 'name'}), on='name', how='left')
                # Display 'No Band' for NaN Band values
                df['Band'] = df['Band'].apply(lambda x: f"{int(x)}%" if pd.notnull(x) else "No Band")
                df = df.rename(columns={'Band': 'Price Band'})
            # --- Merge listing date info ---
            if not df.empty and listing_dates_map:
                df['Listing Date'] = df['name'].map(listing_dates_map)
            # --- Convert market cap to Cr ---
            if not df.empty and 'market_cap_basic' in df.columns:
                df['market_cap_basic'] = (df['market_cap_basic'] / 1e7).round(2)
                df = df.rename(columns={'market_cap_basic': 'Market Cap (Cr.)'})
            # Apply post-fetch filters
            for f in post_filters:
                df = df[f(df)]
            st.write(f"Total Results: {len(df)}")
            st.dataframe(df)
            # --- Inline copy-to-clipboard helper ---
            def st_copy_to_clipboard(text, label="Copy", key=None, height=32, font_size="1.3rem"):
                btn_id = f"copy_btn_{key or label}".replace(" ", "_")
                textarea_id = f"copy_area_{key or label}".replace(" ", "_")
                st.markdown(f'''<div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:-1.5rem;">
                    <label style="font-weight:600;">{label}</label>
                    <button id="{btn_id}" style="font-size:{font_size};background:none;border:none;cursor:pointer;" title="Copy to clipboard">📋</button>
                    <span id="{btn_id}_msg" style="color:green;font-size:0.95rem;display:none;">Copied!</span>
                </div>''', unsafe_allow_html=True)
                st.text_area(" ", text, height=height, key=textarea_id, label_visibility="collapsed")
                st.components.v1.html(f"""
                <script>
                const btn = window.parent.document.getElementById('{btn_id}');
                const ta = window.parent.document.getElementById('{textarea_id}');
                const msg = window.parent.document.getElementById('{btn_id}_msg');
                if (btn && ta && msg) {{
                    btn.onclick = function() {{
                        navigator.clipboard.writeText(ta.value);
                        msg.style.display = 'inline';
                        setTimeout(() => {{ msg.style.display = 'none'; }}, 1200);
                    }}
                }}
                </script>
                """, height=0)

            # --- Add: Copy NSE:TICKER list as comma-separated ---
            if not df.empty and 'name' in df.columns:
                ticker_list = ','.join([f"NSE:{x}" for x in df['name'].astype(str)])
                st_copy_to_clipboard(ticker_list, label="Copy NSE:TICKER List (comma separated)", key="tickerlist_text", height=100)
            # --- Add: Industry-wise grouped NSE:TICKERs ---
            if not df.empty and 'industry' in df.columns and 'name' in df.columns:
                industry_groups = df.groupby('industry')
                sorted_industries = sorted(industry_groups.groups.keys(), key=lambda s: (-len(industry_groups.get_group(s)), s))
                industry_lines = []
                for industry in sorted_industries:
                    tickers = industry_groups.get_group(industry)['name'].astype(str).tolist()
                    line = f"###{industry.upper()}({len(tickers)})," + ','.join([f"NSE:{t}" for t in tickers])
                    industry_lines.append(line)
                industrywise_str = ','.join(industry_lines)
                st_copy_to_clipboard(industrywise_str, label="Copy Industry-wise NSE:TICKERs (most symbols first)", key="industrywise_text", height=200)
            # --- Add: Sector-wise grouped NSE:TICKERs ---
            if not df.empty and 'sector' in df.columns and 'name' in df.columns:
                sector_groups = df.groupby('sector')
                sorted_sectors = sorted(sector_groups.groups.keys(), key=lambda s: (-len(sector_groups.get_group(s)), s))
                sector_lines = []
                for sector in sorted_sectors:
                    tickers = sector_groups.get_group(sector)['name'].astype(str).tolist()
                    line = f"###{sector.upper()}({len(tickers)})," + ','.join([f"NSE:{t}" for t in tickers])
                    sector_lines.append(line)
                sectorwise_str = ','.join(sector_lines)
                st_copy_to_clipboard(sectorwise_str, label="Copy Sector-wise NSE:TICKERs (most symbols first)", key="sectorwise_text", height=200)
        except Exception as e:
            st.error(f"Error: {e}\nTry selecting a different region or adjusting your filters/columns.")
else:
    st.info("Select your filters and click 'Run Scan' to see results.")
