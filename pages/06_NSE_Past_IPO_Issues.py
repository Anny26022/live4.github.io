import streamlit as st
import pandas as pd
import requests
from io import StringIO
from datetime import datetime, date

def get_nse_session():
    session = requests.Session()
    homepage = "https://www.nseindia.com"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    session.get(homepage, headers=headers, timeout=10)
    return session

def fetch_nse_api_data(api_url, referer):
    session = get_nse_session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": referer,
    }
    response = session.get(api_url, headers=headers, timeout=15)
    response.raise_for_status()
    return response.json()

st.set_page_config(
    page_title="NSE Past IPO Issues",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.title("NSE Past IPO Issues (Equity/SME)")
st.markdown("---")

refresh_interval = 15  # seconds
st.caption(f"⏳ Auto-refresh every {refresh_interval} seconds")

# Fallback JS-based auto-refresh for all Streamlit versions
def js_autorefresh(interval_sec=15, key="autorefresh"):
    st.markdown(f"""
        <script>
        function refreshPage() {{
            window.location.reload();
        }}
        setTimeout(refreshPage, {interval_sec * 1000});
        </script>
    """, unsafe_allow_html=True)
js_autorefresh(refresh_interval, key="past_ipo_issues_autorefresh")

# Only allow Equity or SME
market_type = st.radio(
    "Select IPO Segment:",
    options=["Equity", "SME"],
    index=0,
    horizontal=True
)

base_url = "https://www.nseindia.com/api/public-past-issues?&from_date=01-01-2008&to_date=24-04-2025"
if market_type == "Equity":
    url = f"{base_url}&security_type=Equity"
    referer = "https://www.nseindia.com/market-data/new-public-issues-ipo"
else:  # SME
    url = f"{base_url}&security_type=SME"
    referer = "https://www.nseindia.com/market-data/new-public-issues-ipo"

def parse_date(date_str):
    for fmt in ("%d-%b-%Y", "%d-%b-%y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except Exception:
            continue
    return pd.NaT

try:
    data = fetch_nse_api_data(url, referer)
    ipo_list = None
    if isinstance(data, dict) and "data" in data:
        ipo_list = data["data"]
    elif isinstance(data, list):
        ipo_list = data
    if ipo_list is not None and isinstance(ipo_list, list) and len(ipo_list) > 0:
        df = pd.DataFrame(ipo_list)
        # Remove unwanted columns if present
        for col in ['htmSym', 'link', 'removal_date', 'linkRemovalDate']:
            if col in df.columns:
                df = df.drop(columns=[col])
        # Calendar filter
        date_col = None
        for col in ["issue_open_date", "ipoStartDate", "IPO START DATE", "ISSUE START DATE"]:
            if col in df.columns:
                date_col = col
                break
        if date_col:
            df['issue_open_date_parsed'] = df[date_col].apply(lambda x: parse_date(str(x)) if pd.notnull(x) else pd.NaT)
            min_date = df['issue_open_date_parsed'].min()
            max_date = df['issue_open_date_parsed'].max()
            today = pd.to_datetime(date.today())
            default_end = today if min_date <= today <= max_date else max_date
            start_date, end_date = st.date_input(
                "Filter IPOs by Issue Open Date Range:",
                value=(min_date, default_end),
                min_value=min_date,
                max_value=max_date
            )
            df = df[(df['issue_open_date_parsed'] >= pd.to_datetime(start_date)) & (df['issue_open_date_parsed'] <= pd.to_datetime(end_date))]
            df['Year'] = df['issue_open_date_parsed'].dt.year
        if 'issue_open_date_parsed' in df.columns:
            df = df.drop(columns=['issue_open_date_parsed'])
        st.success(f"Fetched {len(df)} IPO issues (filtered from {len(ipo_list)} total).")
        # --- Always show summary tables at the top (if columns exist) ---
        col1, col2, col3 = st.columns(3)
        with col1:
            status_col = None
            for c in ["status", "Status", "STATUS"]:
                if c in df.columns:
                    status_col = c
                    break
            if status_col:
                st.subheader("By Status")
                st.dataframe(df.groupby(status_col).size().reset_index(name='Count'))
            else:
                st.info("No status column found.")
        with col2:
            if 'Year' in df.columns:
                st.subheader("By Year")
                st.dataframe(df.groupby('Year').size().reset_index(name='Count'))
            else:
                st.info("No year info available.")
        with col3:
            issue_type_col = None
            for c in ["issue_type", "Issue Type", "ISSUE TYPE", "SECURITY TYPE"]:
                if c in df.columns:
                    issue_type_col = c
                    break
            if issue_type_col:
                st.subheader("By Issue Type")
                st.dataframe(df.groupby(issue_type_col).size().reset_index(name='Count'))
            else:
                st.info("No issue type column found.")
        st.markdown("---")
        st.subheader("All Past IPO Issues (Full Table)")
        st.dataframe(df, height=700)
        csv = df.to_csv(index=False)
        st.download_button("Download All IPO Issues as CSV", csv, "nse_past_ipo_issues.csv", "text/csv")
    else:
        st.error("No IPO issues found for the selected period.")
except Exception as e:
    st.error(f"Failed to fetch IPO issues: {e}")
