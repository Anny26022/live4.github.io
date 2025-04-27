import pandas as pd
import time
from datetime import datetime

def fetch_results():
    """Fetch results data from Google Sheets."""
    try:
        url = "https://docs.google.com/spreadsheets/d/1xig6-dQ8PuPdeCxozcYdm15nOFUKMMZFm_p8VvRFDaE/gviz/tq?tqx=out:csv&gid=948182834"
        df = pd.read_csv(url)
        df = df[['Scrip Code', 'Short Name', 'Long Name', 'Meeting Date']]
        # Ensure Scrip Code is numeric
        df['Scrip Code'] = pd.to_numeric(df['Scrip Code'])
        df['Last Updated'] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        latest_update = df['Last Updated'].iloc[0] if not df.empty else str(time.time())
        return df, latest_update
    except Exception as e:
        return pd.DataFrame(columns=['Scrip Code', 'Short Name', 'Long Name', 'Meeting Date', 'Last Updated']), str(time.time())
