import pandas as pd
import time

# Helper for PDF URL

def ensure_pdf_url(val):
    val = str(val).strip()
    if val.startswith('http'):
        return val
    # If it's a Google Drive file ID, build the URL
    if val and len(val) >= 20 and '/' not in val and '.' not in val:
        return f"https://drive.google.com/file/d/{val}/view"
    return '' if val in ('', 'nan', 'None') else val

# Fetch and combine stock news and analyst/result news

def fetch_stock_news():
    try:
        url = "https://docs.google.com/spreadsheets/d/1X6amEBgzjwpbaSST_19z-6zAMbnA4yYpnrYO_faoh_g/gviz/tq?tqx=out:csv&gid=1083642917"
        news_df = pd.read_csv(url)
        news_df.columns = [col.strip() for col in news_df.columns]
        analyst_url = "https://docs.google.com/spreadsheets/d/1X6amEBgzjwpbaSST_19z-6zAMbnA4yYpnrYO_faoh_g/gviz/tq?tqx=out:csv&gid=909294572"
        analyst_df = pd.read_csv(analyst_url)
        analyst_df.columns = [col.strip() for col in analyst_df.columns]
        if 'SUBCATNAME' not in news_df.columns:
            news_df['SUBCATNAME'] = ''
        if 'SUBCATNAME' not in analyst_df.columns:
            analyst_df['SUBCATNAME'] = ''
        if 'PDF' not in news_df.columns:
            news_df['PDF'] = ''
        if 'PDF' not in analyst_df.columns:
            analyst_df['PDF'] = ''
        if 'SOURCE' not in news_df.columns:
            news_df['SOURCE'] = 'Main'
        if 'SOURCE' not in analyst_df.columns:
            analyst_df['SOURCE'] = 'Analyst/Result'
        all_cols = sorted(set(news_df.columns).union(set(analyst_df.columns)))
        news_df = news_df.reindex(columns=all_cols)
        analyst_df = analyst_df.reindex(columns=all_cols)
        news_df['PDF'] = news_df['PDF'].apply(ensure_pdf_url)
        analyst_df['PDF'] = analyst_df['PDF'].apply(ensure_pdf_url)
        combined_df = pd.concat([news_df, analyst_df], ignore_index=True)
        latest_update = ''
        try:
            latest_update = str(pd.to_datetime(combined_df['NEWS_DT'], errors='coerce').max())
        except Exception:
            latest_update = str(time.time())
        return combined_df, latest_update
    except Exception as e:
        # Do not use st.error here, just raise or return empty
        return pd.DataFrame(), ''
