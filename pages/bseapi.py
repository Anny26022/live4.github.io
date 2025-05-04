import streamlit as st
import datetime
import pandas as pd
import io
from utils.bse_announcements_utils import BSEAnnouncements
import traceback
from datetime import time
import pytz
import os
import concurrent.futures
from fpdf import FPDF
import calendar

# Page config
st.set_page_config(
    page_title="BSE Announcements",
    page_icon="📢",
    layout="centered"
)

# Define market hours in IST (24-hour format)
MARKET_OPEN = time(9, 7)  # 9:07 AM
MARKET_CLOSE = time(15, 30)  # 15:30 PM

# Load equity.csv and create Security Code to Security Id mapping
try:
    equity_df = pd.read_csv('equity.csv')
    scrip_to_securityid = dict(zip(equity_df['Security Code'], equity_df['Security Id']))
except Exception as e:
    st.warning(f"Could not load equity.csv: {e}")
    scrip_to_securityid = {}

# Add this near the top, after scrip_to_securityid is defined
symbol_aliases = {
    "MINDTREE": "LTIM",
    # Add more symbol changes here as needed
}

# Title and description
st.title("📢 BSE Corporate Announcements")

# Initialize the BSEAnnouncements class
try:
    bse = BSEAnnouncements()
except Exception as e:
    st.error(f"Error initializing BSE Announcements utility: {str(e)}")
    st.error(traceback.format_exc())
    st.stop()

# Set default date range: from_date is 1 year back, to_date is None
from datetime import timedelta

today = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
default_from = today.date() - timedelta(days=365)
default_to = None

# Create filters in a container
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        from_date = st.date_input(
            "From Date",
            value=default_from,
            help="Select start date for announcements"
        )
        st.caption("Format: DD-MM-YYYY (use calendar picker)")
        category = st.selectbox(
            "Category",
            options=['Board Meeting', 'Result', 'Company Update', 'Corp. Action', 'AGM/EGM', 'Insider Trading / SAST', 'New Listing', 'Integrated Filing', 'Others'],
            index=1,  # Default to 'Result'
            help="Filter by announcement category"
        )
    with col2:
        # Set the default To Date to the last day of the same month as From Date (or today, if that's earlier)
        to_date_default = default_to
        if from_date:
            last_day = calendar.monthrange(from_date.year, from_date.month)[1]
            last_of_month = from_date.replace(day=last_day)
            to_date_default = min(last_of_month, today.date())
        to_date = st.date_input(
            "To Date",
            value=to_date_default,
            max_value=today.date(),
            help="Select end date for announcements (cannot be in the future)"
        )
        st.caption("Format: DD-MM-YYYY (use calendar picker)")
        security_name = st.text_input(
            "Company Name/Security Code",
            help="Enter company name or security code to filter"
        )

# Only enable fetch if both dates are selected
fetch_enabled = from_date is not None and to_date is not None

# Show warning if To Date is not selected
if to_date is None:
    st.warning("Please select a 'To Date' to fetch announcements. This field is mandatory.")

# Convert dates to required format if selected
from_date_str = from_date.strftime("%d/%m/%Y") if from_date else ""
to_date_str = to_date.strftime("%d/%m/%Y") if to_date else ""

# Add global volume filter state
if 'volume_min' not in st.session_state:
    st.session_state['volume_min'] = 0
if 'volume_max' not in st.session_state:
    st.session_state['volume_max'] = None

global_move_results = []  # Collect all move_results from all sections

def fetch_all_bse_announcements(bse, from_date, to_date, category, scrip, subcategory):
    """Fetch all announcements from BSE"""
    try:
        df = bse.fetch_all_announcements_api(
            from_date=from_date,
            to_date=to_date,
            category=category,
            scrip=scrip,
            subcategory=subcategory
        )
        
        if not df.empty:
            # Robustly parse all possible BSE datetime formats for DT_TM
            dt_col = 'DT_TM'
            if dt_col in df.columns:
                # Try ISO/mixed first
                df[dt_col] = pd.to_datetime(df[dt_col], format='mixed', errors='coerce')
                # Try '%d-%m-%Y %H:%M:%S' for any NaT
                mask_nat = df[dt_col].isna() & df[dt_col].notnull()
                if mask_nat.any():
                    df.loc[mask_nat, dt_col] = pd.to_datetime(df.loc[mask_nat, dt_col], format='%d-%m-%Y %H:%M:%S', errors='coerce')
                # Try '%d/%m/%Y %H:%M:%S' for any remaining NaT
                mask_nat = df[dt_col].isna() & df[dt_col].notnull()
                if mask_nat.any():
                    df.loc[mask_nat, dt_col] = pd.to_datetime(df.loc[mask_nat, dt_col], format='%d/%m/%Y %H:%M:%S', errors='coerce')
            # Add time classification (using IST time directly)
            df['Time_Classification'] = df['DT_TM'].apply(classify_time)
            # Sort by date and time
            df = df.sort_values('DT_TM', ascending=False)
        return df
    except Exception as e:
        st.error(f"Error fetching announcements: {str(e)}")
        return pd.DataFrame()

def classify_time(dt):
    """Classify announcement time as during market hours or after hours (IST)"""
    try:
        if pd.isna(dt) or dt is None:
            return "Unknown"
            
        if dt.weekday() >= 5:  # Weekend
            return "Weekend"
            
        # Ensure we have a valid datetime before getting time
        if not isinstance(dt, (datetime.datetime, pd.Timestamp)):
            return "Unknown"
            
        t = dt.time()
        if MARKET_OPEN <= t <= MARKET_CLOSE:
            return "During Market Hours"
        else:
            return "After Hours"
    except (AttributeError, TypeError, ValueError):
        return "Unknown"

def get_pdf_link(row):
    if row.get('ATTACHMENTNAME'):
        if row.get('PDFFLAG') == 0:
            return f"https://www.bseindia.com/xml-data/corpfiling/AttachLive/{row['ATTACHMENTNAME']}"
        elif row.get('PDFFLAG') == 1:
            return f"https://www.bseindia.com/xml-data/corpfiling/AttachHis/{row['ATTACHMENTNAME']}"
        elif row.get('PDFFLAG') == 2:
            return None  # Optionally handle this case
    return None

def calc_post_earnings_move(security_id, ann_date, data_dir="eod2/src/eod2_data/daily", csv_path=None):
    import os
    try:
        if not security_id or pd.isna(security_id):
            return None, None, None, None, None, None, None
        # Use provided csv_path if available
        if csv_path is None:
            sec_id_clean = str(security_id).strip().lower()
            csv_path = os.path.join(data_dir, f"{sec_id_clean}.csv")
            if not os.path.exists(csv_path):
                alt_csv_path = os.path.join(data_dir, f"{sec_id_clean.replace(' ', '')}.csv")
                if os.path.exists(alt_csv_path):
                    csv_path = alt_csv_path
                else:
                    return None, None, None, None, None, None, None
        try:
            df = pd.read_csv(csv_path, parse_dates=['Date'])
        except Exception:
            return None, None, None, None, None, None, None
        # Clean Date column
        df['Date'] = pd.to_datetime(df['Date'].astype(str).str.strip(), format='%Y-%m-%d', errors='coerce')
        df = df.sort_values('Date').reset_index(drop=True)
        # Validate announcement date
        ann_date_parsed = pd.to_datetime(str(ann_date).strip(), format='%Y-%m-%d', errors='coerce')
        if pd.isna(ann_date_parsed):
            return None, None, None, None, None, None, None
        # Find all trading days on or after the announcement date
        future_days = df[df['Date'] >= ann_date_parsed].reset_index(drop=True)
        if len(future_days) == 0:
            return None, None, None, None, None, None, None
        # Get announcement day close (or next trading day if announcement was on holiday)
        close_0 = None
        if not future_days.empty and pd.notna(future_days.loc[0, 'Close']):
            close_0 = future_days.loc[0, 'Close']
        # Get 30-day and 60-day closes (use max available if not enough days)
        close_30 = None
        close_60 = None
        days_30 = None
        days_60 = None
        if len(future_days) > 1:
            idx_30 = min(30, len(future_days) - 1)
            idx_60 = min(60, len(future_days) - 1)
            if pd.notna(future_days.loc[idx_30, 'Close']):
                close_30 = future_days.loc[idx_30, 'Close']
                days_30 = idx_30
            if pd.notna(future_days.loc[idx_60, 'Close']):
                close_60 = future_days.loc[idx_60, 'Close']
                days_60 = idx_60
        # Calculate pre-announcement moves
        pre_10 = None
        pre_20 = None
        idx = df[df['Date'] >= ann_date_parsed].index
        if len(idx) > 0:
            idx = idx[0]
        idx_10 = idx - 10 if idx - 10 >= 0 else None
        idx_20 = idx - 20 if idx - 20 >= 0 else None
        if idx_10 is not None and pd.notna(df.loc[idx_10, 'Close']) and close_0 is not None:
            pre_10 = (close_0 - df.loc[idx_10, 'Close']) / df.loc[idx_10, 'Close'] * 100
        if idx_20 is not None and pd.notna(df.loc[idx_20, 'Close']) and close_0 is not None:
            pre_20 = (close_0 - df.loc[idx_20, 'Close']) / df.loc[idx_20, 'Close'] * 100
        # Calculate post-announcement moves
        move_30 = None
        move_60 = None
        peak_move = None
        if close_0 is not None and close_0 != 0:
            if close_30 is not None:
                move_30 = (close_30 - close_0) / close_0 * 100
            if close_60 is not None:
                move_60 = (close_60 - close_0) / close_0 * 100
            # Peak move: max % move from close_0 to any close in future_days
            closes = future_days['Close'].dropna()
            if not closes.empty:
                peak_move = ((closes - close_0) / close_0 * 100).max()
        return pre_10, pre_20, move_30, move_60, days_30, days_60, peak_move
    except Exception:
        return None, None, None, None, None, None, None

def find_ohlcv_csv(code, security_id, data_dir="eod2/src/eod2_data/daily"):
    import os
    # Use current working directory as base
    data_dir_abs = os.path.abspath(data_dir)
    candidates = set()
    for val in [code, security_id]:
        if not val or pd.isna(val):
            continue
        val = str(val).strip()
        candidates.add(val.lower())
        candidates.add(val.upper())
        candidates.add(val.replace(' ', '').lower())
        candidates.add(val.replace(' ', '').upper())
    for candidate in candidates:
        csv_path = os.path.join(data_dir_abs, f"{candidate}.csv")
        if os.path.exists(csv_path):
            return csv_path
    return None

def process_announcement_row(args):
    row, section_key = args
    import os
    code = row.get('SCRIP_CD')
    security_id = scrip_to_securityid.get(code, code)
    security_id = symbol_aliases.get(str(security_id).upper(), security_id)
    data_dir = "eod2/src/eod2_data/daily"
    csv_path = find_ohlcv_csv(code, security_id, data_dir)
    ann_date_raw = row.get('DT_TM')
    ann_date = pd.to_datetime(ann_date_raw).date() if ann_date_raw else None
    
    if not csv_path or not os.path.exists(csv_path):
        return None
        
    try:
        df_ohlc = pd.read_csv(csv_path, parse_dates=['Date'])
        df_ohlc['Date'] = pd.to_datetime(df_ohlc['Date'].astype(str).str.strip(), errors='coerce')
        df_ohlc = df_ohlc.sort_values('Date').reset_index(drop=True)
        # For weekend announcements, we need to find the next trading day
        if section_key == "weekend":
            # Find the next trading day after the announcement
            next_trading_days = df_ohlc[df_ohlc['Date'].dt.date > ann_date]
            if next_trading_days.empty:
                return None
            # Use the next trading day's date for calculations
            next_trading_date = next_trading_days.iloc[0]['Date'].date()
            pre_10, pre_20, move_30, move_60, days_30, days_60, peak_move = calc_post_earnings_move(security_id, next_trading_date, data_dir=data_dir, csv_path=csv_path)
        else:
            # For non-weekend announcements, check if announcement date exists in data
            dates_in_file = df_ohlc['Date'].dt.date.tolist()
            if ann_date not in dates_in_file:
                return None
            pre_10, pre_20, move_30, move_60, days_30, days_60, peak_move = calc_post_earnings_move(security_id, ann_date, data_dir=data_dir, csv_path=csv_path)
    except Exception as e:
        return None

    # Get volume and check if it's a trading day
    volume = None
    close_ann = None
    open_next = None
    is_trading_day = False
    
    try:
        df_ohlc = pd.read_csv(csv_path, parse_dates=['Date'])
        df_ohlc['Date'] = pd.to_datetime(df_ohlc['Date'].astype(str).str.strip(), errors='coerce')
        df_ohlc = df_ohlc.sort_values('Date').reset_index(drop=True)
        
        # Check if announcement date is a trading day
        ann_date_data = df_ohlc[df_ohlc['Date'].dt.date == ann_date]
        is_trading_day = not ann_date_data.empty
        
        if is_trading_day:
            # Validate volume data
            raw_volume = ann_date_data.iloc[0]['Volume']
            if pd.notna(raw_volume) and raw_volume >= 0:
                try:
                    volume = int(raw_volume)
                except (ValueError, OverflowError):
                    volume = None
            else:
                volume = None
            
            close_ann = ann_date_data.iloc[0]['Close'] if pd.notna(ann_date_data.iloc[0]['Close']) else None
            
            # For trading days (including special Saturday sessions), use next trading day for gap
            next_trading_day = df_ohlc[df_ohlc['Date'].dt.date > ann_date].iloc[0] if len(df_ohlc[df_ohlc['Date'].dt.date > ann_date]) > 0 else None
            if next_trading_day is not None:
                open_next = next_trading_day['Open'] if pd.notna(next_trading_day['Open']) else None
        else:
            # For non-trading days (regular weekends/holidays), find last trading day and next trading day
            last_trading_day = df_ohlc[df_ohlc['Date'].dt.date < ann_date].iloc[-1] if len(df_ohlc[df_ohlc['Date'].dt.date < ann_date]) > 0 else None
            next_trading_day = df_ohlc[df_ohlc['Date'].dt.date > ann_date].iloc[0] if len(df_ohlc[df_ohlc['Date'].dt.date > ann_date]) > 0 else None
            
            if last_trading_day is not None:
                # Validate volume data
                raw_volume = last_trading_day['Volume']
                if pd.notna(raw_volume) and raw_volume >= 0:
                    try:
                        volume = int(raw_volume)
                    except (ValueError, OverflowError):
                        volume = None
                else:
                    volume = None
                
                close_ann = last_trading_day['Close'] if pd.notna(last_trading_day['Close']) else None
            
            if next_trading_day is not None:
                open_next = next_trading_day['Open'] if pd.notna(next_trading_day['Open']) else None
    except Exception:
        volume = None
        close_ann = None
        open_next = None
    
    # Gap calculation for After Market Hours and Weekend
    gap_check = ''
    gap_pct = ''
    
    if section_key in ["after", "weekend"]:
        try:
            if close_ann is not None and open_next is not None and close_ann != 0:
                # Calculate absolute gap percentage
                gap_pct = round((open_next - close_ann) / close_ann * 100, 2)
                # Consider a significant gap if > 0.5%
                gap_check = '✔️' if abs(gap_pct) > 0.5 else '❌'
            else:
                gap_check = '❌'
                gap_pct = 'N/A'
        except Exception:
            gap_check = '❌'
            gap_pct = 'N/A'
    
    return {
        'Security Id': security_id,
        'Announcement Date': ann_date,
        'Volume': volume,
        'Pre 10d %': round(pre_10, 2) if pre_10 is not None else 'N/A',
        'Pre 20d %': round(pre_20, 2) if pre_20 is not None else 'N/A',
        'Move 30d %': f"{round(move_30, 2)} ({days_30}d)" if move_30 is not None and days_30 is not None and days_30 != 30 else (round(move_30, 2) if move_30 is not None else 'N/A'),
        'Move 60d %': f"{round(move_60, 2)} ({days_60}d)" if move_60 is not None and days_60 is not None and days_60 != 60 else (round(move_60, 2) if move_60 is not None else 'N/A'),
        'Peak Move %': round(peak_move, 2) if peak_move is not None else 'N/A',
        **({'Gap?': gap_check, 'Gap %': gap_pct} if section_key in ["after", "weekend"] else {})
    }

def show_post_earnings_moves(df, section_key):
    # Always show the toggle at the top and enable by default for all sections
    show_moves = st.toggle("Show Pre/Post-Earnings Move % (10d/20d/30d/60d)", value=True, key=f"move_toggle_{section_key}")
    if show_moves:
        move_results = []
        copyable_symbols = set()
        seen = set()
        missing_ohlcv = []  # Track missing OHLCV data
        tasks = []
        data_dir = "eod2/src/eod2_data/daily"
        for _, row in df.iterrows():
            code = row.get('SCRIP_CD')
            security_id = scrip_to_securityid.get(code, code)
            security_id = symbol_aliases.get(str(security_id).upper(), security_id)
            ann_date = pd.to_datetime(row.get('DT_TM')).date() if row.get('DT_TM') else None
            key = (security_id, ann_date)
            if key in seen:
                continue
            seen.add(key)
            csv_path = find_ohlcv_csv(code, security_id, data_dir)
            if not csv_path:
                # Convert security_id to string before adding to missing_ohlcv
                missing_ohlcv.append(str(security_id))
                continue
            # Pass the original section_key but treat weekend same as after for processing
            tasks.append((row, section_key))
        # Parallel processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(process_announcement_row, tasks))
        # Always include calculation columns, even if values are 'N/A'
        calculation_cols = ['Security Id', 'Announcement Date', 'Volume', 'Pre 10d %', 'Pre 20d %', 'Move 30d %', 'Move 60d %', 'Peak Move %', 'Gap?', 'Gap %']
        move_results_full = []
        for r in results:
            if r is not None:
                # Ensure all calculation columns are present
                for col in calculation_cols:
                    if col not in r:
                        r[col] = 'N/A'
                move_results_full.append(r)
        move_results = move_results_full
        for r in move_results:
            if (r['Move 30d %'] != 'N/A') or (r['Move 60d %'] != 'N/A'):
                copyable_symbols.add(f"NSE:{r['Security Id']}")
        global_move_results.extend(move_results)
        min_vol = st.session_state.get('volume_min', 0)
        max_vol = st.session_state.get('volume_max', None)
        filtered_results = [r for r in move_results if (r['Volume'] is not None and r['Volume'] >= min_vol and (max_vol is None or r['Volume'] <= max_vol))]
        if filtered_results:
            df_moves = pd.DataFrame(filtered_results)
            # Remove Volume and Announcement Date columns if present
            for col in ['Volume', 'Announcement Date']:
                if col in df_moves.columns:
                    df_moves.drop(columns=[col], inplace=True)
            # Sort Gap % for after market hours and weekend
            if section_key in ["after", "weekend"] and 'Gap %' in df_moves.columns:
                def gap_sort_key(val):
                    try:
                        v = float(val)
                        return (v > 0, v)  # (False, negative) comes before (True, positive)
                    except:
                        return (True, float('inf'))  # N/A or invalid at the end
                df_moves = df_moves.assign(_gap_sort=df_moves['Gap %'].apply(gap_sort_key))
                df_moves = df_moves.sort_values('_gap_sort').drop(columns=['_gap_sort'])
            # Show the post-earnings move table always expanded (not in an expander)
            just_symbols = ','.join(sorted(copyable_symbols))
            st.code(just_symbols, language=None)
            st.dataframe(df_moves, use_container_width=True)
        else:
            st.info("No symbols with available OHLCV data.")
            if missing_ohlcv:
                # Ensure all items in missing_ohlcv are strings before joining
                missing_str = ', '.join(str(x) for x in missing_ohlcv)
                st.warning(f"Missing OHLCV data for: {missing_str}")
    return show_moves

# Ensure fetch_announcements is only True when the button is clicked, and reset to False on filter change
if 'fetch_announcements' not in st.session_state:
    st.session_state['fetch_announcements'] = False

# Track previous filter values to detect changes
if 'prev_filters' not in st.session_state:
    st.session_state['prev_filters'] = {
        'from_date': from_date,
        'to_date': to_date,
        'category': category,
        'security_name': security_name
    }

filters_changed = (
    st.session_state['prev_filters']['from_date'] != from_date or
    st.session_state['prev_filters']['to_date'] != to_date or
    st.session_state['prev_filters']['category'] != category or
    st.session_state['prev_filters']['security_name'] != security_name
)

if filters_changed:
    st.session_state['fetch_announcements'] = False
    st.session_state['prev_filters'] = {
        'from_date': from_date,
        'to_date': to_date,
        'category': category,
        'security_name': security_name
    }

# Fetch announcements button
if st.button("Fetch Announcements", type="primary", disabled=not fetch_enabled):
    st.session_state['fetch_announcements'] = True

if st.session_state['fetch_announcements']:
    try:
        with st.spinner("Fetching all announcements from BSE API (all pages)..."):
            df = fetch_all_bse_announcements(
                bse,
                from_date=from_date_str,
                to_date=to_date_str,
                category=category,
                scrip=security_name,
                subcategory="-1"
            )
            
            if not df.empty:
                # --- Aggregate all symbols with calculated move % from all sections ---
                data_dir = "eod2/src/eod2_data/daily"
                all_move_symbols = dict()  # symbol -> (move_30, move_60)
                seen = set()
                for section in ["During Market Hours", "After Hours", "Weekend"]:
                    section_df = df[df['Time_Classification'] == section]
                    for _, row in section_df.iterrows():
                        code = row.get('SCRIP_CD')
                        security_id = scrip_to_securityid.get(code, code)
                        security_id = symbol_aliases.get(str(security_id).upper(), security_id)
                        sec_id_clean = str(security_id).strip().lower()
                        csv_path = os.path.join(data_dir, f"{sec_id_clean}.csv")
                        alt_csv_path = os.path.join(data_dir, f"{sec_id_clean.replace(' ', '')}.csv")
                        if not os.path.exists(csv_path) and not os.path.exists(alt_csv_path):
                            continue
                        ann_date = pd.to_datetime(row.get('DT_TM')).date() if row.get('DT_TM') else None
                        key = (security_id, ann_date)
                        if key in seen:
                            continue
                        seen.add(key)
                        pre_10, pre_20, move_30, move_60, days_30, days_60, peak_move = calc_post_earnings_move(security_id, ann_date)
                        if (move_30 is not None) or (move_60 is not None):
                            all_move_symbols[security_id] = (move_30, move_60)
                if all_move_symbols:
                    # Reference expander for detailed move %
                    with st.expander("Symbols with calculated move % (reference)", expanded=False):
                        lines = [f"NSE:{sym} (30d: {round(m30,2) if m30 is not None else 'N/A'}%, 60d: {round(m60,2) if m60 is not None else 'N/A'}%)" for sym, (m30, m60) in sorted(all_move_symbols.items())]
                        st.text('\n'.join(lines))
                    # Copy expander for plain symbols only
                    with st.expander("Copy only the symbols (for clipboard)", expanded=False):
                        just_symbols = ','.join([f"NSE:{sym}" for sym in sorted(all_move_symbols.keys())])
                        st.code(just_symbols, language=None)

                # Display metrics for result announcements
                if category in ["-1", "Result"]:
                    result_df = df[df['CATEGORYNAME'].str.contains('Result', case=False, na=False)]
                    if not result_df.empty:
                        st.subheader("Result Announcement Statistics")
                        total_results = len(result_df)
                        market_hours = len(result_df[result_df['Time_Classification'] == 'During Market Hours'])
                        after_hours = len(result_df[result_df['Time_Classification'] == 'After Hours'])
                        weekend = len(result_df[result_df['Time_Classification'] == 'Weekend'])
                        unknown = len(result_df[result_df['Time_Classification'] == 'Unknown'])
                        
                        col1, col2, col3, col4, col5 = st.columns(5)
                        with col1:
                            st.metric("Total Results", total_results)
                        with col2:
                            st.metric("During Market Hours", market_hours)
                        with col3:
                            st.metric("After Hours", after_hours)
                        with col4:
                            st.metric("Weekend", weekend)
                        with col5:
                            st.metric("Unknown Time", unknown)
                        
                        st.write("Timing Distribution:")
                        timing_dist = result_df['Time_Classification'].value_counts()
                        st.bar_chart(timing_dist)

                        # --- Grouping and Display ---
                        # Add Unknown section
                        if unknown > 0:
                            st.markdown("## ❓ Results with Unknown Timing")
                            unknown_df = result_df[result_df['Time_Classification'] == 'Unknown']
                            if not unknown_df.empty:
                                temp_df = unknown_df.copy()
                                temp_df['Security Id'] = temp_df['SCRIP_CD'].apply(lambda x: scrip_to_securityid.get(x, x))
                                temp_df['PDF Link'] = temp_df.apply(get_pdf_link, axis=1)
                                temp_df['DT_TM'] = temp_df['DT_TM'].apply(lambda x: x.strftime('%d-%m-%Y %I:%M:%S %p') if pd.notna(x) else 'Unknown')
                                with st.expander("Show results with unknown timing", expanded=True):
                                    st.dataframe(
                                        temp_df[['DT_TM', 'Security Id', 'SLONGNAME', 'HEADLINE', 'PDF Link']],
                                        use_container_width=True,
                                        column_config={
                                            'PDF Link': st.column_config.LinkColumn(
                                                'PDF Link',
                                                help='Download PDF attachment',
                                                display_text='\U0001F4C4 PDF'
                                            )
                                        }
                                    )

                        # 1. During Market Hours
                        during_df = result_df[result_df['Time_Classification'] == 'During Market Hours']
                        if not during_df.empty:
                            # Removed group by date checkbox and grouped logic
                            during_df['DT_TM'] = pd.to_datetime(during_df['DT_TM'], errors='coerce')
                            st.markdown("## 🕒 Results During Market Hours")
                            temp_df = during_df.copy()
                            temp_df['Security Id'] = temp_df['SCRIP_CD'].apply(lambda x: scrip_to_securityid.get(x, x))
                            show_moves = show_post_earnings_moves(temp_df, "market")
                            temp_df['PDF Link'] = temp_df.apply(get_pdf_link, axis=1)
                            temp_df['DT_TM'] = temp_df['DT_TM'].dt.strftime('%d-%m-%Y %I:%M:%S %p')
                            with st.expander("Show all results table", expanded=not show_moves):
                                st.dataframe(
                                    temp_df[['DT_TM', 'Security Id', 'SLONGNAME', 'HEADLINE', 'PDF Link']],
                                    use_container_width=True,
                                    column_config={
                                        'PDF Link': st.column_config.LinkColumn(
                                            'PDF Link',
                                            help='Download PDF attachment',
                                            display_text='\U0001F4C4 PDF'
                                        )
                                    }
                                )
                        # 2. After Market Hours
                        after_df = result_df[result_df['Time_Classification'] == 'After Hours']
                        if not after_df.empty:
                            # Removed group by date checkbox and grouped logic
                            after_df['DT_TM'] = pd.to_datetime(after_df['DT_TM'], errors='coerce')
                            st.markdown("## 🌙 Results After Market Hours")
                            temp_df = after_df.copy()
                            temp_df['Security Id'] = temp_df['SCRIP_CD'].apply(lambda x: scrip_to_securityid.get(x, x))
                            show_moves = show_post_earnings_moves(temp_df, "after")
                            temp_df['PDF Link'] = temp_df.apply(get_pdf_link, axis=1)
                            temp_df['DT_TM'] = temp_df['DT_TM'].dt.strftime('%d-%m-%Y %I:%M:%S %p')
                            with st.expander("Show all results table", expanded=not show_moves):
                                st.dataframe(
                                    temp_df[['DT_TM', 'Security Id', 'SLONGNAME', 'HEADLINE', 'PDF Link']],
                                    use_container_width=True,
                                    column_config={
                                        'PDF Link': st.column_config.LinkColumn(
                                            'PDF Link',
                                            help='Download PDF attachment',
                                            display_text='\U0001F4C4 PDF'
                                        )
                                    }
                                )
                        # 3. Weekend
                        weekend_df = result_df[result_df['Time_Classification'] == 'Weekend']
                        if not weekend_df.empty:
                            # Removed group by date checkbox and grouped logic
                            weekend_df['DT_TM'] = pd.to_datetime(weekend_df['DT_TM'], errors='coerce')
                            st.markdown("## 📅 Results on Weekends (Saturday/Sunday)")
                            temp_df = weekend_df.copy()
                            temp_df['Security Id'] = temp_df['SCRIP_CD'].apply(lambda x: scrip_to_securityid.get(x, x))
                            show_moves = show_post_earnings_moves(temp_df, "weekend")  # Keep weekend key but use after logic in process_announcement_row
                            temp_df['PDF Link'] = temp_df.apply(get_pdf_link, axis=1)
                            temp_df['DT_TM'] = temp_df['DT_TM'].dt.strftime('%d-%m-%Y %I:%M:%S %p')
                            with st.expander("Show all results table", expanded=False):
                                st.dataframe(
                                    temp_df[['DT_TM', 'Security Id', 'SLONGNAME', 'HEADLINE', 'PDF Link']],
                                    use_container_width=True,
                                    column_config={
                                        'PDF Link': st.column_config.LinkColumn(
                                            'PDF Link',
                                            help='Download PDF attachment',
                                            display_text='\U0001F4C4 PDF'
                                        )
                                    }
                                )
                        elif during_df.empty and after_df.empty:
                            st.info("No result announcements found for the selected date range.")
                
                # Download options
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.download_button(
                        "Download as CSV",
                        df.to_csv(index=False).encode('utf-8'),
                        "bse_announcements.csv",
                        "text/csv",
                        key='download-csv'
                    )
                with col2:
                    excel_buffer = io.BytesIO()
                    df.to_excel(excel_buffer, index=False)
                    excel_buffer.seek(0)
                    st.download_button(
                        "Download as Excel",
                        excel_buffer,
                        "bse_announcements.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key='download-excel'
                    )
                with col3:
                    # Generate PDF in memory
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", size=10)
                    # Table header
                    col_width = pdf.w / (len(df.columns) + 1)
                    row_height = pdf.font_size * 1.5
                    for col in df.columns:
                        pdf.cell(col_width, row_height, str(col), border=1)
                    pdf.ln(row_height)
                    # Table rows
                    for i, row in df.iterrows():
                        for col in df.columns:
                            val = str(row[col])
                            if len(val) > 30:
                                val = val[:27] + '...'
                            pdf.cell(col_width, row_height, val, border=1)
                        pdf.ln(row_height)
                    pdf_bytes = pdf.output(dest='S').encode('latin1')
                    pdf_buffer = io.BytesIO(pdf_bytes)
                    st.download_button(
                        "Download as PDF",
                        pdf_buffer,
                        "bse_announcements.pdf",
                        "application/pdf",
                        key='download-pdf'
                    )
            else:
                st.warning("No announcements found for the selected criteria.")
    except Exception as e:
        st.error(f"Error fetching announcements: {str(e)}")
        st.error(traceback.format_exc())

# After fetching announcements and before showing tables, add global volume filter UI
if st.session_state.get('fetch_announcements', False):
    all_volumes = [r['Volume'] for r in global_move_results if r['Volume'] is not None]
    if all_volumes:
        min_volume = min(all_volumes)
        max_volume = max(all_volumes)
        st.sidebar.markdown('### Global Volume Filter')
        st.session_state['volume_min'], st.session_state['volume_max'] = st.sidebar.slider(
            'Select volume range (on announcement date):',
            min_value=min_volume,
            max_value=max_volume,
            value=(min_volume, max_volume),
            step=1
        )
    else:
        st.sidebar.markdown('### Global Volume Filter')
        st.info('No volume data available for the selected announcements.')

# Add some custom CSS for better styling
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #232526 0%, #181A20 100%);
        color: #fff;
        border: none;
        padding: 0.6rem 1.2rem;
        border-radius: 0.6rem;
        font-weight: 700;
        font-size: 1.08rem;
        letter-spacing: 0.01em;
        box-shadow: 0 2px 8px rgba(44,44,44,0.13);
        transition: background 0.3s, box-shadow 0.3s, transform 0.2s;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #181A20 0%, #232526 100%);
        box-shadow: 0 4px 18px rgba(44,44,44,0.16);
        transform: translateY(-2px) scale(1.04);
    }
    .stButton>button:disabled, .stButton>button[disabled] {
        color: #fff !important;
        opacity: 0.55 !important;
        background: linear-gradient(90deg, #232526 0%, #181A20 100%) !important;
    }
    .stDataFrame {
        border-radius: 0.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    input[type="text"][data-baseweb="input"] {
        border: 1.5px solid #e5e7eb !important;
        border-radius: 0.5rem !important;
        font-size: 1.08rem !important;
    }
    </style>
""", unsafe_allow_html=True) 