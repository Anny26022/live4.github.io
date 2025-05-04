import streamlit as st
import pandas as pd
import re
import os
from pages.price_bands import fetch_price_bands

st.set_page_config(
    page_title="Symbol Lookup with Price Band",
    page_icon="🔎",
    layout="centered"
)

# --- Modern Compact CSS & Animations ---
st.markdown("""
<style>
body, .stApp { font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif; }
.card {
    background: transparent;
    border: none;
    box-shadow: none;
    border-radius: 1.1rem;
    padding: 1.3rem 1.7rem 1.3rem 1.7rem;
    margin-bottom: 1.5rem;
    animation: fadeInCard 0.7s cubic-bezier(.4,0,.2,1);
    transition: box-shadow 0.3s, border 0.3s;
}
.card:hover { box-shadow: none; border-color: transparent; }
@keyframes fadeInCard { from { opacity: 0; transform: translateY(18px);} to { opacity: 1; transform: none; } }
.section-title {
    font-size: 1.25rem;
    font-weight: 700;
    color: #1976d2;
    margin-bottom: 0.7rem;
    letter-spacing: -0.01em;
    display: flex;
    align-items: center;
    gap: 0.5em;
}
.badge {
    display: inline-block;
    background: #e3eafc;
    color: #1976d2;
    font-weight: 600;
    border-radius: 1em;
    padding: 0.18em 0.85em;
    font-size: 1.01em;
    margin-right: 0.5em;
    margin-bottom: 0.1em;
    box-shadow: 0 1px 4px 0 rgba(31,38,135,0.04);
    vertical-align: middle;
    transition: background 0.2s, color 0.2s;
}
.badge.badge-success { background: #e6f7e9; color: #219150; }
.badge.badge-warn { background: #fff4e5; color: #b26a00; }
.badge.badge-error { background: #ffeaea; color: #d32f2f; }
.stTextInput, .stTextArea, .stMultiSelect, .stNumberInput, .stSelectbox, .stCheckbox { margin-bottom: 0.7rem !important; }
.stTextArea textarea { font-size: 1.08rem; border-radius: 0.7em; border: 1.5px solid #e0e7ef; }
.stButton > button { border-radius: 0.7em !important; font-weight: 600; font-size: 1.01rem; transition: box-shadow 0.2s, background 0.2s; }
.stButton > button:hover { box-shadow: 0 2px 8px 0 #1976d233; background: #e3eafc !important; color: #1976d2 !important; }
.stDataFrame, .stTable { background: transparent !important; border: none; box-shadow: none; border-radius: 1.1rem; font-size: 1.01rem; transition: background 0.3s, border 0.3s; }
.stDataFrame thead tr th { background: #e3eafc !important; color: #1976d2 !important; font-weight: 700 !important; }
.stDataFrame tbody tr:hover { background: #eaf3ff !important; }
.copy-area { background: #f4f8fd; border-radius: 0.7em; border: 1.5px solid #e0e7ef; padding: 0.7em 1em; margin-top: 0.5em; font-size: 1.08em; display: flex; align-items: center; gap: 0.7em; }
.copy-btn { background: #e3eafc; color: #1976d2; border: none; border-radius: 0.7em; padding: 0.3em 1.1em; font-weight: 600; font-size: 1.01em; cursor: pointer; transition: background 0.2s, color 0.2s; }
.copy-btn:hover { background: #1976d2; color: #fff; }
.copy-success { color: #219150; font-weight: 600; margin-left: 0.7em; font-size: 1.01em; display: none; }
@media (max-width: 700px) { .card { padding: 0.7rem 0.5rem; } .section-title { font-size: 1.08rem; } }
.card.section-results {
    margin-top: 0.2rem !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style='display:flex;align-items:center;justify-content:center;margin-bottom:0.5em;'>
  <svg xmlns='http://www.w3.org/2000/svg' width='48' height='48' viewBox='0 0 48 48' fill='none' style='margin-right:16px;'>
    <rect width='48' height='48' rx='12' fill='url(#lookup-bg)'/>
    <g>
      <circle cx='24' cy='24' r='12' fill='#43a047' opacity='0.18'/>
      <rect x='20' y='20' width='8' height='8' rx='2' fill='#29b6f6'/>
    </g>
    <defs>
      <linearGradient id='lookup-bg' x1='0' y1='0' x2='48' y2='48' gradientUnits='userSpaceOnUse'>
        <stop stop-color='#23272F'/>
        <stop offset='1' stop-color='#181A20'/>
      </linearGradient>
    </defs>
  </svg>
  <span style='font-size:2.2rem;font-weight:700;color:#1976d2;'>Symbol Lookup with Price Band</span>
</div>
<p style='text-align:center;margin-top:-0.75em;margin-bottom:2em;color:#555;font-size:1.1rem;'>Enter any symbols to see their price band and key data (from local price band data only)</p>
""", unsafe_allow_html=True)

# --- Ensure price bands are loaded in session state ---
if 'price_bands_df' not in st.session_state or st.session_state.price_bands_df is None or st.session_state.price_bands_df.empty:
    st.session_state.price_bands_df, st.session_state.bands_last_update = fetch_price_bands()
price_bands_df = st.session_state.price_bands_df

# --- EMA Calculation Utility ---
@st.cache_data(show_spinner=True)
def compute_emas_for_all_symbols(eod_folder, ema_periods=[20, 50, 200], symbols=None):
    ema_data = []
    files = os.listdir(eod_folder)
    if symbols is not None:
        symbol_set = set(s.lower() for s in symbols)
        files = [f for f in files if f.lower().endswith('.csv') and f[:-4].lower() in symbol_set]
    for fname in files:
        if not fname.lower().endswith('.csv'):
            continue
        symbol = fname[:-4].upper()
        fpath = os.path.join(eod_folder, fname)
        try:
            df = pd.read_csv(fpath)
            if 'Close' not in df.columns or df.empty:
                continue
            df = df.sort_values('Date')
            latest = df.iloc[-1]
            ema_row = {'Symbol': symbol, 'Close': latest['Close']}
            for period in ema_periods:
                ema_col = f'EMA{period}'
                df[ema_col] = df['Close'].ewm(span=period, adjust=False).mean()
                ema_row[ema_col] = df[ema_col].iloc[-1]
            ema_data.append(ema_row)
        except Exception as e:
            print(f'Error processing {fname}: {e}')
    return pd.DataFrame(ema_data)

# --- FILTERS CARD ---
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.markdown("<div class='section-title'>🔎 Symbol & Filter Options</div>", unsafe_allow_html=True)
st.markdown("<span style='color:#b26a00;font-weight:600;'>Note: You can input up to <b>2000 symbols</b> at once (comma or newline separated).</span>", unsafe_allow_html=True)
symbol_input = st.text_area(
    "Enter symbol(s) (comma-separated or newline, e.g. TAJGVK, PARAS):",
    value="",
    height=120,
    help="Paste up to 2000 symbols, separated by commas or newlines."
)
compute_only_input = st.checkbox(
    "Compute EMA only for input symbols (faster for large lists)",
    value=True,
    help="If checked, only compute EMAs for the symbols you input above. If unchecked, computes for all symbols in the folder."
)
band_options = []
if price_bands_df is not None and not price_bands_df.empty:
    band_options = sorted(price_bands_df['Band'].dropna().unique().tolist())
    band_options = [f"{int(b)}%" for b in band_options]
    band_options.append("No Band")
selected_bands = st.multiselect(
    "Filter by Price Band (optional):",
    options=['All Bands'] + band_options,
    default=['All Bands'],
    help="Filter by price band if desired."
)
ema_options = ['EMA20', 'EMA50', 'EMA200']
selected_ema = st.multiselect(
    "Optional: Filter stocks where Close is above selected EMA(s):",
    options=ema_options,
    help="Only show stocks where the latest close is above the selected EMA(s)."
)
enable_stacked_ema = st.checkbox(
    "Require stacked EMAs (e.g., EMA50 > EMA150 > EMA200)",
    value=False,
    help="Only show stocks where the selected EMAs are strictly stacked.",
    disabled=(len(selected_ema) == 0)
)
st.markdown("</div>", unsafe_allow_html=True)

# --- RESULTS CARD ---
st.markdown("<div class='card section-results'>", unsafe_allow_html=True)
st.markdown("<div class='section-title'>📋 Results & Copy Options</div>", unsafe_allow_html=True)

if symbol_input.strip():
    # Accept both SYMBOL and NSE:SYMBOL formats, split on comma or newline, ignore category headers
    symbols = []
    for s in re.split(r'[,\n]+', symbol_input):
        s = s.strip().upper()
        if s.startswith('###'):
            continue  # skip category headers
        if s.startswith('NSE:'):
            s = s[4:]
        if s:
            symbols.append(s)
    if not symbols:
        st.warning("Please enter at least one valid symbol.")
        st.stop()
    # Filter price_bands_df for these symbols
    df = price_bands_df.copy()
    df['Symbol'] = df['Symbol'].astype(str).str.upper().str.strip()
    all_input_symbols = set(symbols)
    all_valid_symbols = set(df['Symbol'])
    valid_symbols = all_input_symbols & all_valid_symbols
    invalid_symbols = all_input_symbols - all_valid_symbols
    st.markdown(f"""
    <span class='badge'>Symbols entered: {len(all_input_symbols)}</span>
    <span class='badge badge-success'>Valid: {len(valid_symbols)}</span>
    <span class='badge badge-error'>Invalid: {len(invalid_symbols)}</span>
    """, unsafe_allow_html=True)
    if invalid_symbols:
        st.markdown(f"<span class='badge badge-warn'>Invalid symbols (not found): {', '.join(list(invalid_symbols)[:10])}{'...' if len(invalid_symbols) > 10 else ''}</span>", unsafe_allow_html=True)
    filtered_df = df[df['Symbol'].isin(symbols)]
    # Only apply price band filter if a specific band is selected
    if band_options and ('All Bands' not in selected_bands):
        band_map = {f"{int(b)}%": b for b in df['Band'].dropna().unique()}
        allowed_bands = set()
        for band in selected_bands:
            if band == 'No Band':
                allowed_bands.add(None)
            elif band in band_map:
                allowed_bands.add(band_map[band])
        filtered_df = filtered_df[
            (filtered_df['Band'].isna() & ('No Band' in selected_bands)) |
            (filtered_df['Band'].isin([b for b in allowed_bands if b is not None]))
        ]
    # --- EMA Calculation and Merge ---
    eod_folder = r'C:\TradingView-Screener-master\eod2\src\eod2_data\daily'
    emas_df = compute_emas_for_all_symbols(eod_folder, symbols=symbols if compute_only_input else None)
    if not emas_df.empty:
        filtered_df = filtered_df.merge(emas_df, on='Symbol', how='left')
    # --- EMA Filtering ---
    if selected_ema:
        if enable_stacked_ema and len(selected_ema) > 1:
            periods = [int(e.replace('EMA', '')) for e in selected_ema]
            sorted_emas = [f'EMA{p}' for p in sorted(periods)]
            for ema_col in sorted_emas:
                filtered_df = filtered_df[filtered_df['Close'] > filtered_df[ema_col]]
            for i in range(len(sorted_emas) - 1):
                filtered_df = filtered_df[filtered_df[sorted_emas[i]] > filtered_df[sorted_emas[i+1]]]
        else:
            for ema_col in selected_ema:
                if ema_col in filtered_df.columns and 'Close' in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df['Close'] > filtered_df[ema_col]]
    if filtered_df.empty:
        st.warning("No data found for the entered symbols and selected price band(s)/EMA filter.")
        st.stop()
    filtered_df['Price Band'] = filtered_df['Band'].apply(lambda x: f"{int(x)}%" if pd.notnull(x) else "No Band")
    display_cols = [col for col in ['Symbol', 'Security Name', 'Series', 'Price Band', 'Close', 'EMA20', 'EMA50', 'EMA200'] if col in filtered_df.columns]
    st.dataframe(filtered_df[display_cols], use_container_width=True)
    st.markdown(f"<span class='badge badge-success'>Symbols in final results: {filtered_df['Symbol'].nunique()}</span>", unsafe_allow_html=True)
    # Add copyable NSE:SYMBOL list
    if not filtered_df.empty:
        nse_symbols = ','.join([f"NSE:{sym}" for sym in filtered_df['Symbol']])
        st.markdown(f"""
        <div class='copy-area'>
            <span style='flex:1;overflow-x:auto;'>{nse_symbols}</span>
            <button class='copy-btn' id='copy-nse-symbols-btn'>Copy</button>
            <span class='copy-success' id='copy-success-msg'>Copied!</span>
        </div>
        <script>
        const btn = window.parent.document.getElementById('copy-nse-symbols-btn');
        if (btn) {{
            btn.onclick = function() {{
                const txt = `{nse_symbols}`;
                navigator.clipboard.writeText(txt).then(function() {{
                    const msg = window.parent.document.getElementById('copy-success-msg');
                    if (msg) {{
                        msg.style.display = 'inline';
                        setTimeout(() => {{ msg.style.display = 'none'; }}, 1200);
                    }}
                }});
            }}
        }}
        </script>
        """, unsafe_allow_html=True)
else:
    st.info("Enter one or more symbols above to see results.")
st.markdown("</div>", unsafe_allow_html=True) 