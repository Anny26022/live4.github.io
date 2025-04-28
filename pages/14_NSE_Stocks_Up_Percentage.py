import streamlit as st
import pandas as pd
from tradingview_screener import Query, Column
import plotly.express as px

st.set_page_config(
    page_title="Stocks Up by %",
    page_icon="📈",
    layout="centered"
)

st.markdown("""
<div style='display:flex;align-items:center;justify-content:center;margin-bottom:0.5em;'>
  <svg xmlns='http://www.w3.org/2000/svg' width='48' height='48' viewBox='0 0 48 48' fill='none' style='margin-right:16px;'>
    <rect width='48' height='48' rx='12' fill='url(#up-bg)'/>
    <g>
      <rect x='14' y='24' width='4' height='8' rx='2' fill='#43a047'/>
      <rect x='22' y='18' width='4' height='14' rx='2' fill='#29b6f6'/>
      <rect x='30' y='12' width='4' height='20' rx='2' fill='#ab47bc'/>
    </g>
    <defs>
      <linearGradient id='up-bg' x1='0' y1='0' x2='48' y2='48' gradientUnits='userSpaceOnUse'>
        <stop stop-color='#23272F'/>
        <stop offset='1' stop-color='#181A20'/>
      </linearGradient>
    </defs>
  </svg>
  <span style='font-size:2.5rem;font-weight:700;color:#fff;'>Stocks Up by %</span>
</div>
<p style='text-align:center;margin-top:-0.75em;margin-bottom:2em;color:#aaa;font-size:1.1rem;'>See which stocks are up by a chosen % today</p>
""", unsafe_allow_html=True)

# --- UI Controls ---
selected_market_code = "india"
exchange_options = ["NSE", "BSE", "Both"]
selected_exchange = st.selectbox("Select Exchange:", exchange_options, index=0)
instrument_options = ["stock", "fund", "etf", "reit", "all"]
selected_instrument = st.selectbox("Select Instrument Type:", instrument_options, index=0)
official_period_field_map = {
    "1 Week": "Perf.W",
    "1 Month": "Perf.1M",
    "3 Months": "Perf.3M",
    "6 Months": "Perf.6M",
    "YTD": "Perf.YTD",
    "1 Year": "Perf.Y",
    "5 Years": "Perf.5Y",
    "10 Years": "Perf.10Y",
    "All Time": "Perf.All"
}
period = st.selectbox("Select period for % change:", list(official_period_field_map.keys()), index=0)
field = official_period_field_map[period]
show_movers = st.radio(
    "Show:",
    options=["Top Movers (gainers)", "Top Losers (decliners)"],
    index=0,
    horizontal=True
) == "Top Movers (gainers)"
percent_threshold = st.number_input(
    f"Show stocks {'up' if show_movers else 'down'} by at least (%) over selected period:",
    min_value=0.0,
    max_value=100.0,
    value=2.0,
    step=0.1,
    format="%.2f"
)

# --- Query Construction ---
where_conditions = []
if selected_exchange == "Both":
    where_conditions.append(Column("exchange").isin(["NSE", "BSE"]))
else:
    where_conditions.append(Column("exchange") == selected_exchange)
if selected_instrument != "all":
    where_conditions.append(Column("type") == selected_instrument)
where_conditions.append(Column("is_primary") == True)

# Add performance condition based on the selected field
if show_movers:
    where_conditions.append(Column(field) >= percent_threshold)
else:
    where_conditions.append(Column(field) <= -percent_threshold)

# Always include all official performance fields in select for fallback
perf_fields = list(official_period_field_map.values())
select_fields = ['name', 'close', 'volume', 'market_cap_basic', 'sector', 'industry', 'type'] + perf_fields

query = (
    Query()
    .set_markets(selected_market_code)
    .select(*select_fields)
    .where(*where_conditions)
    .limit(20000)
)

@st.cache_data(show_spinner=False)
def fetch_stock_data(_query):
    return _query.get_scanner_data()

with st.spinner("Loading stock data..."):
    count, df = fetch_stock_data(query)

# --- Robust column renaming and fallback logic ---
if not df.empty:
    # Try to use the requested period, otherwise fallback to next available official perf field
    period_priority = [field] + perf_fields
    found_field = next((f for f in period_priority if f in df.columns), None)
    if found_field is None:
        st.error(f"None of the required columns for % change were found. Available columns: {list(df.columns)}. Please check your data source or period selection.")
        st.stop()
    actual_period = period
    if found_field != field:
        fallback_period = {v: k for k, v in official_period_field_map.items()}.get(found_field, found_field)
        st.warning(f"Data for '{period}' not available. Showing results for '{fallback_period}' instead.")
        actual_period = fallback_period
    
    # Convert market cap to crore if needed
    if 'market_cap_basic' in df.columns and df['market_cap_basic'].max() > 1e7:
        df['market_cap_basic'] = df['market_cap_basic'] / 1e7
    
    rename_dict = {
        'name': 'Stock Name',
        'close': 'Close Price',
        found_field: f'% Change ({actual_period})',
        'volume': 'Volume',
        'market_cap_basic': 'Market Cap',
        'type': 'Instrument Type'
    }
    rename_dict = {k: v for k, v in rename_dict.items() if k in df.columns}
    df = df.rename(columns=rename_dict)
    sort_col = f'% Change ({actual_period})'
    if sort_col in df.columns:
        df = df.sort_values(by=sort_col, ascending=not show_movers)
    else:
        st.error(f"Data missing required column '{sort_col}'. Available columns: {list(df.columns)}. Please check your data source or period selection.")
        st.stop()

    # Debug: Show available instrument types
    # if 'Instrument Type' in df.columns:
    #     st.write("Instrument types present in data:", df['Instrument Type'].unique())
    # else:
    #     st.write("No instrument type column present in data.")

    min_price, max_price = st.slider(
        "Filter by Close Price:",
        min_value=float(df["Close Price"].min() if not df.empty else 0),
        max_value=float(df["Close Price"].max() if not df.empty else 10000),
        value=(float(df["Close Price"].min() if not df.empty else 0), float(df["Close Price"].max() if not df.empty else 10000)),
        step=1.0,
        format="%.2f"
    )
    min_cap, max_cap = st.slider(
        "Filter by Market Cap (Cr):",
        min_value=float(df["Market Cap"].min() if not df.empty else 0),
        max_value=float(df["Market Cap"].max() if not df.empty else 1e13),
        value=(float(df["Market Cap"].min() if not df.empty else 0), float(df["Market Cap"].max() if not df.empty else 1e13)),
        step=1e7,
        format="%.0f"
    )
    filtered_df = df[
        (df["Close Price"] >= min_price) &
        (df["Close Price"] <= max_price) &
        (df["Market Cap"] >= min_cap) &
        (df["Market Cap"] <= max_cap)
    ]
    # Enforce percent threshold filter again here for robustness
    if show_movers:
        filtered_df = filtered_df[filtered_df[sort_col] >= percent_threshold]
    else:
        filtered_df = filtered_df[filtered_df[sort_col] <= -percent_threshold]

    st.markdown("""
        <style>
            .stSlider > div[data-baseweb="slider"] {background: rgba(36, 40, 47, 0.55);border-radius: 16px;padding: 1.2rem 2rem 1.7rem 2rem;box-shadow: 0 8px 32px 0 rgba(31,38,135,0.15);backdrop-filter: blur(6px);-webkit-backdrop-filter: blur(6px);border: 1.5px solid rgba(255,255,255,0.12);max-width: 520px;margin-bottom: 1.5rem;margin-top: 1.2rem;transition: box-shadow 0.35s, background 0.35s, border 0.35s;}
            .stSlider .rc-slider {margin: 0 0 0.8rem 0;height: 22px;}
            .stSlider .rc-slider-rail {background: rgba(200, 200, 255, 0.18);height: 7px;transition: background 0.3s;}
            .stSlider .rc-slider-track {background: linear-gradient(90deg, #43e97b 0%, #38f9d7 100%);height: 7px;border-radius: 7px;transition: background 0.3s;}
            .stSlider .rc-slider-handle {border: none;background: #fff;box-shadow: 0 2px 12px 0 #38f9d755;width: 20px;height: 20px;margin-top: -7px;transition: box-shadow 0.2s, background 0.2s;}
            .stSlider .rc-slider-handle:active {box-shadow: 0 0 0 8px #43e97b33;}
            .stSlider .rc-slider-mark {width: 100%;display: flex;justify-content: space-between;position: absolute;top: -1.4em;left: 0;right: 0;pointer-events: none;}
            .stSlider .rc-slider-mark-text {color: #b3c7f7;font-size: 0.93rem;letter-spacing: 0.04em;background: rgba(36,40,47,0.7);padding: 0.18em 0.7em;border-radius: 7px;min-width: 2.7em;text-align: center;white-space: nowrap;overflow: hidden;text-overflow: ellipsis;box-shadow: 0 2px 8px 0 rgba(0,0,0,0.10);margin-left: 0;margin-right: 0;transition: background 0.3s, color 0.3s;}
            .stSlider .rc-slider-dot {display: none;}
            .stTextInput > div > input {background: rgba(36, 40, 47, 0.45);color: #fff;border-radius: 10px;border: 1.5px solid rgba(255,255,255,0.13);font-size: 1.08rem;padding: 0.45rem 1.1rem;height: 2.3rem;box-shadow: 0 2px 12px 0 rgba(0,0,0,0.10);transition: background 0.3s, border 0.3s;}
            .stRadio > div {background: rgba(36, 40, 47, 0.45);border-radius: 10px;padding: 0.35rem 0.8rem;max-width: 520px;margin-bottom: 1.1rem;border: 1.5px solid rgba(255,255,255,0.10);transition: background 0.3s, border 0.3s;}
            .stMetric { color: #1976d2 !important; font-size: 1.13rem; }
            .stDataFrame, .stTable {background: rgba(36, 40, 47, 0.45) !important;border-radius: 13px;font-size: 1.01rem;border: 1.5px solid rgba(255,255,255,0.09);box-shadow: 0 4px 24px 0 rgba(31,38,135,0.09);transition: background 0.3s, border 0.3s;}
            .stSlider label[data-testid="stMarkdownContainer"] > div {display: none !important;}
        </style>
    """, unsafe_allow_html=True)
    if not filtered_df.empty:
        st.metric(
            f"Number of stocks {'up' if show_movers else 'down'} by at least {percent_threshold:.2f}% in {actual_period}",
            len(filtered_df)
        )
        # Only show columns that exist in the DataFrame to avoid KeyError
        display_cols = [col for col in ['Stock Name', 'Instrument Type', 'Close Price', f'% Change ({actual_period})', 'Volume', 'Market Cap'] if col in filtered_df.columns]
        st.dataframe(
            filtered_df[display_cols],
            use_container_width=True
        )
        plot_df = filtered_df.head(30).copy()
        plot_df = plot_df[plot_df['Market Cap'].notna() & (plot_df['Market Cap'] > 0)]
        if not plot_df.empty:
            fig = px.scatter(
                plot_df,
                x='Stock Name',
                y=f'% Change ({actual_period})',
                size='Market Cap',
                color='Close Price',
                hover_data=['Volume', 'Close Price', 'Market Cap'],
                title=f"{'Top' if show_movers else 'Bottom'} 30 Stocks by % Change ({actual_period})",
                labels={
                    'Stock Name': 'Stock',
                    f'% Change ({actual_period})': '% Change',
                    'Close Price': 'Close Price',
                    'Market Cap': 'Market Cap',
                },
                color_continuous_scale=px.colors.sequential.Viridis,
                template='plotly_dark',
                opacity=0.87,
            )
            fig.update_traces(
                marker=dict(
                    line=dict(width=0.7, color='#222'),
                    sizemode='area',
                    opacity=0.87,
                ),
                selector=dict(mode='markers')
            )
            fig.update_layout(
                xaxis_tickangle=-38,
                plot_bgcolor='rgba(24,26,32,0.96)',
                paper_bgcolor='rgba(24,26,32,0.99)',
                font=dict(family='Segoe UI, Roboto, Arial', size=15, color='#e6e6e6'),
                title_font=dict(size=23, family='Segoe UI, Roboto, Arial', color='#fff'),
                margin=dict(l=10, r=10, t=54, b=70),
                height=450,
                xaxis=dict(showgrid=False, zeroline=False),
                yaxis=dict(showgrid=True, gridcolor='rgba(120,120,120,0.16)', zeroline=False),
                coloraxis_colorbar=dict(
                    title=dict(text='Close Price', font=dict(color='#b3c7f7', size=15)),
                    thickness=12,
                    len=0.56,
                    yanchor='middle',
                    y=0.54,
                    outlinewidth=0,
                    tickfont=dict(color='#b3c7f7', size=13),
                    bgcolor='rgba(24,26,32,0.99)'
                ),
            )
            fig.update_xaxes(showline=False, linewidth=0.8, linecolor='#333', mirror=False, showgrid=False)
            fig.update_yaxes(showline=False, linewidth=0.8, linecolor='#333', mirror=False, gridwidth=0.7)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No suitable data for plotting. (Market Cap missing or zero for all top stocks)")
        st.caption(
            f"Showing {len(filtered_df)} {selected_market_code.upper()} stocks {'up' if show_movers else 'down'} by at least {percent_threshold:.2f}% in {actual_period}."
        )
    else:
        st.warning("No stocks found matching the criteria. Try lowering the threshold or check back later.")
else:
    st.warning("No stocks found matching the criteria. Try lowering the threshold or check back later.")
