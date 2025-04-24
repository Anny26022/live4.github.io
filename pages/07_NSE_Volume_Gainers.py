import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(
    page_title="NSE Volume Gainers",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.title("NSE Volume Gainers")
refresh_interval = 15
st.caption(f"Auto-refresh every {refresh_interval} seconds")

def js_autorefresh(interval_sec=15, key="autorefresh"):
    st.markdown(f"""
        <script>
        function refreshPage() {{
            window.location.reload();
        }}
        setTimeout(refreshPage, {{interval}});
        </script>
    """.replace("{{interval}}", str(interval_sec * 1000)), unsafe_allow_html=True)

js_autorefresh(refresh_interval, key="volume_gainers_autorefresh")

now = datetime.now().strftime('%d-%b-%Y %H:%M:%S IST')
st.write(f"As on {now}")

url = "https://www.nseindia.com/api/live-analysis-volume-gainers"
referer = "https://www.nseindia.com/market-data/live-equity-market"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": referer,
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://www.nseindia.com"
}

try:
    session = requests.Session()
    session.get("https://www.nseindia.com", headers=headers, timeout=10)
    response = session.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    data = response.json()
    gainers = None
    for key in ['data', 'volumeGainers', 'volumeGainer', 'rows']:
        if key in data:
            gainers = data[key]
            break
    if gainers is None:
        gainers = data if isinstance(data, list) else []
    if gainers and isinstance(gainers, list) and len(gainers) > 0:
        df = pd.DataFrame(gainers)
        if 'pChange' in df.columns:
            df = df.rename(columns={'pChange': '% CHG'})
        col_list = df.columns.tolist()
        security_col = None
        for c in ['SECURITY', 'companyName', 'security']:
            if c in col_list:
                security_col = c
                break
        pchange_col = None
        for c in ['% CHG', 'perChange']:
            if c in col_list:
                pchange_col = c
                break
        ltp_col = None
        for c in ['LTP', 'ltp']:
            if c in col_list:
                ltp_col = c
                break
        if security_col and pchange_col and ltp_col:
            cols = col_list.copy()
            cols.remove(pchange_col)
            cols.remove(ltp_col)
            sec_idx = cols.index(security_col)
            cols.insert(sec_idx + 1, pchange_col)
            pch_idx = cols.index(pchange_col)
            cols.insert(pch_idx + 1, ltp_col)
            df = df[cols]
        if '% CHG' in df.columns:
            df = df.sort_values('% CHG', ascending=False)
        st.dataframe(df, height=600)
        csv = df.to_csv(index=False)
        st.download_button("Download (.csv)", csv, "nse_volume_gainers.csv", "text/csv")
    else:
        st.warning("No volume gainers data available.")
except Exception as e:
    st.error(f"Failed to fetch volume gainers: {e}")
