import streamlit as st
import io
st.set_page_config(page_title="Financials Viewer", layout="wide")

# --- Responsive Mobile CSS ---
st.markdown('''
<style>
/* Viewport for mobile scaling */
@media (max-width: 600px) {
  html, body, .main .block-container {
    padding: 0 !important;
    margin: 0 !important;
    max-width: 100vw !important;
    min-width: 0 !important;
    overflow-x: hidden !important;
  }
  .block-container {
    padding: 0.5rem 0.2rem !important;
  }
  .stSelectbox, .stTextInput, .stNumberInput, .stToggle, .stExpander, .stButton {
    font-size: 1.08rem !important;
    min-width: 0 !important;
    width: 100% !important;
    margin-bottom: 0.7rem !important;
  }
  .stExpander > summary {
    font-size: 1.07rem !important;
    padding: 0.7rem 0.5rem !important;
  }
  .stDataFrame, .stTable, .dataframe, table {
    display: block !important;
    width: 100vw !important;
    max-width: 100vw !important;
    overflow-x: auto !important;
    font-size: 0.97rem !important;
  }
  .stMarkdown, .stCaption, .stHeader, .stSubheader {
    word-break: break-word !important;
    padding-left: 0.2rem !important;
    padding-right: 0.2rem !important;
  }
  .stButton > button {
    width: 100% !important;
    min-width: 0 !important;
  }
  .stAlert, .stInfo, .stWarning, .stError {
    font-size: 0.98rem !important;
    padding: 0.7rem 0.4rem !important;
  }
}

/* Always make tables scrollable horizontally */
.stDataFrame, .stTable, .dataframe, table {
  overflow-x: auto !important;
  display: block !important;
  max-width: 100vw !important;
  width: 100% !important;
}

/* Responsive SVG and logo containers */
svg, img {
  max-width: 100%;
  height: auto;
}
</style>
''', unsafe_allow_html=True)

from bs4 import BeautifulSoup
import pandas as pd
import os

# Path to local HTML files (for demo, only RELIANCE is available)
DATA_DIR = os.path.dirname(os.path.dirname(__file__))
HTML_FILES = {
    'RELIANCE': os.path.join(DATA_DIR, 'screener.txt'),
    # Add more mappings here for other companies if you download their HTML
}

import requests

def load_html(symbol, consolidated=False):
    symbol = symbol.upper()
    url = f"https://www.screener.in/company/{symbol}/"
    if consolidated:
        url += "consolidated/"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.text
        else:
            return None
    except Exception:
        return None

def extract_tables(soup):
    """
    Extract all tables and return as list of (title, DataFrame)
    """
    tables = []
    for section in soup.find_all('section'):
        # Use section id or h2 as table title if available
        title = section.get('id', None)
        h2 = section.find('h2')
        if h2:
            title = h2.text.strip()
        for table in section.find_all('table'):
            try:
                df = pd.read_html(io.StringIO(str(table)))[0]
                tables.append((title, df))
            except Exception:
                continue
    # Also get tables outside <section>
    for table in soup.find_all('table'):
        if not any(table.find_parent('section') for _ in [table]):
            try:
                df = pd.read_html(io.StringIO(str(table)))[0]
                tables.append(("Other Table", df))
            except Exception:
                continue
    return tables

import re
def extract_links(soup):
    """
    Categorize document/report links into Announcements, Annual Reports, Credit Ratings, and Concalls.
    Returns a dict of lists.
    """
    categories = {
        'Announcements': [],
        'Annual Reports': [],
        'Credit Ratings': [],
        'Concalls': {}, # {date: {'Transcript': url, 'Notes': url, 'PPT': url}}
    }
    # Announcements: extract from <ul class='list-links'>
    ann_section = soup.find('ul', class_='list-links')
    if ann_section:
        for li in ann_section.find_all('li', class_='overflow-wrap-anywhere', recursive=False):
            a = li.find('a', href=True)
            if not a:
                continue
            title = a.contents[0].strip() if a.contents else a.text.strip()
            href = a['href']
            # Find summary/date in <div> or <span> inside <a>
            summary = ""
            for tag in a.find_all(['div', 'span']):
                if tag.text.strip():
                    summary = tag.text.strip()
                    break
            categories['Announcements'].append((title, href, summary))
    # Annual Reports (robust extraction for Financial Year XXXX and 'from bse' etc)
    for a in soup.find_all('a', href=True):
        anchor_text = a.get_text(separator=" ", strip=True)
        year_match = re.match(r'Financial Year \d{4}', anchor_text)
        is_annual = 'annual report' in anchor_text.lower()
        if year_match or is_annual:
            # Extract 'from bse' or similar from <span class="sub">
            src = ''
            sub_span = a.find('span', class_='sub')
            if sub_span:
                src = sub_span.get_text(strip=True)
            # Remove the sub span text from the anchor text
            main_title = anchor_text.replace(src, '').strip()
            display_text = main_title
            if src:
                display_text += f' from {src}'
            categories['Annual Reports'].append((display_text, a['href']))
    # Credit Ratings (robust for all agencies and formats)
    CREDIT_AGENCIES = ['crisil', 'care', 'icra', 'india ratings', 'fitch', 'moody', 's&p', 'rating', 'update']
    for a in soup.find_all('a', href=True):
        text_lower = a.text.lower()
        href_lower = a['href'].lower()
        if any(agency in text_lower or agency in href_lower for agency in CREDIT_AGENCIES):
            categories['Credit Ratings'].append((a.text.strip(), a['href']))
    # Concalls: robust extraction as a list of dicts (handles duplicates and all HTML cases)
    concall_regex = re.compile(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}', re.IGNORECASE)
    categories['Concalls'] = []  # List of concall dicts
    for li in soup.find_all('li'):
        # 1. Get the date from the first <div> in <li>
        date_div = li.find('div')
        date = date_div.get_text(strip=True) if date_div else None
        if not date or not concall_regex.match(date):
            continue
        entry = {'date': date, 'Transcript': None, 'Notes': None, 'PPT': None}
        # 2. Extract links/buttons/divs for Transcript, Notes, PPT
        for el in li.find_all(['a', 'button', 'div']):
            label = el.get_text(strip=True)
            if label in entry:
                if el.name == 'a' and el.has_attr('href'):
                    entry[label] = el['href']
                else:
                    entry[label] = None
        categories['Concalls'].append(entry)
    return categories

def extract_text_blocks(soup):
    """
    Extract major text blocks (overview, key insights, business description, commentary)
    """
    blocks = {}
    # Company name and meta description
    try:
        name = soup.find('h1').text.strip()
        description = soup.find('meta', {'name': 'description'})['content']
        blocks['Overview'] = f"**{name}**\n\n{description}"
    except Exception:
        pass
    # All <section> blocks with text
    for section in soup.find_all('section'):
        sec_id = section.get('id', None)
        h2 = section.find('h2')
        title = h2.text.strip() if h2 else (sec_id if sec_id else "Section")
        text = section.get_text(separator='\n', strip=True)
        if text:
            blocks[title] = text
    return blocks

st.markdown("""
<div style='display: flex; align-items: center; justify-content: center; gap: 12px; margin-top: 56px; margin-bottom: 16px;'>
  <svg width='40' height='40' viewBox='0 0 48 48' fill='none' xmlns='http://www.w3.org/2000/svg'>
    <rect width='48' height='48' rx='12' fill='url(#fin-bg)'/>
    <g>
      <rect x='14' y='26' width='4' height='10' rx='2' fill='#6366f1'/>
      <rect x='22' y='18' width='4' height='18' rx='2' fill='#38bdf8'/>
      <rect x='30' y='12' width='4' height='24' rx='2' fill='#34d399'/>
      <circle cx='16' cy='26' r='2' fill='#6366f1'/>
      <circle cx='24' cy='18' r='2' fill='#38bdf8'/>
      <circle cx='32' cy='12' r='2' fill='#34d399'/>
    </g>
    <defs>
      <linearGradient id='fin-bg' x1='0' y1='0' x2='48' y2='48' gradientUnits='userSpaceOnUse'>
        <stop stop-color='#23272F'/>
        <stop offset='1' stop-color='#181A20'/>
      </linearGradient>
    </defs>
  </svg>
  <span style='font-size:2.2rem;font-weight:700;color:#fff;'> Company Financials</span>
</div>
""", unsafe_allow_html=True)
st.markdown("""
<style>
    .block-container {padding-top: 1rem;}
    .stExpander > summary {font-size: 1.1rem; font-weight: 600;}
</style>
""", unsafe_allow_html=True)

import pandas as pd
# Load merged symbols from master CSV using a relative path
import os
csv_path = os.path.join(os.path.dirname(__file__), '..', 'EQUITY_MASTER.csv')
if os.path.exists(csv_path):
    symbols_df = pd.read_csv(csv_path, dtype=str)
    symbols_df['SYMBOL'] = symbols_df['SYMBOL'].astype(str).str.strip().str.upper()
    symbols_df['NAME OF COMPANY'] = symbols_df['NAME OF COMPANY'].astype(str).fillna("")
else:
    st.error("EQUITY_MASTER.csv not found. Please upload or add the CSV file to the project directory.")
    st.stop()

# Show only symbols in the dropdown
symbol_list = symbols_df['SYMBOL'].dropna().unique().tolist()
selected = st.selectbox("🔎 Select company symbol:", options=symbol_list)
symbol = selected

# Add toggle for Standalone/Consolidated
consolidated = st.toggle("Show Consolidated Data", value=False)
if symbol:
    html = load_html(symbol, consolidated=consolidated)
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        text_blocks = extract_text_blocks(soup)
        tables = extract_tables(soup)
        links = extract_links(soup)

        # --- RAW PDF Extraction for Quarterly Results ---
        raw_pdf_links = []
        # Find the table row with 'Raw PDF' (case-insensitive)
        pdf_row = soup.find(lambda tag: tag.name == 'tr' and tag.find('td', string=lambda s: s and 'raw pdf' in s.lower()))
        if pdf_row:
            tds = pdf_row.find_all('td')
            for td in tds[1:]:  # Skip the label cell
                a = td.find('a', href=True)
                if a and a['href'].endswith('/'):
                    raw_pdf_links.append(a['href'])
                else:
                    raw_pdf_links.append(None)
        # Memorize the extracted PDF links for later use
        memorized_pdf_links = raw_pdf_links.copy()
        # Set up for Raw PDF row injection (but do not display the table here)
        raw_pdf_row_info = None
        qr_idx = None
        if tables:
            for idx, (title, df) in enumerate(tables):
                if title and ("quarter" in title.lower()):
                    qr_idx = idx
                    break
            if qr_idx is not None:
                title, df = tables[qr_idx]
                # Remove any previous Raw PDF row
                df = df[df.iloc[:,0] != "Raw PDF"]
                pdf_row_data = ["Raw PDF"]
                base_url = "https://www.screener.in"
                # Try to load company_id for URL generation
                company_id = None
                csv_path = os.path.join(os.path.dirname(__file__), '..', 'screener_all_listed_company_ids.csv')
                symbol_upper = symbol.strip().upper()
                if os.path.exists(csv_path):
                    try:
                        df_ids = pd.read_csv(csv_path, dtype=str)
                        df_ids.columns = df_ids.columns.str.strip()  # Remove whitespace from headers
                        df_ids['Symbol'] = df_ids['Symbol'].str.strip().str.upper()
                        match = df_ids[df_ids['Symbol'] == symbol_upper]
                        if not match.empty and 'CompanyID' in match.columns:
                            company_id = match.iloc[0]['CompanyID']
                    except Exception as e:
                        company_id = None
                # For each quarter column, fill with extracted link or generated link if missing (robust version)
                for col_idx, col in enumerate(df.columns[1:]):  # skip first column (row label)
                    href = raw_pdf_links[col_idx] if col_idx < len(raw_pdf_links) else None
                    debug_msg = f"DEBUG: symbol={symbol_upper}, company_id={company_id}, col={col}, href={href}"
                    if href:
                        full_url = base_url + href if href.startswith("/") else href
                        cell = f'[Raw PDF]({full_url})'
                        debug_msg += f", using extracted: {full_url}"
                    else:
                        # Try to extract month and year from col header (e.g., 'Dec 2022')
                        import re
                        m = re.match(r'([A-Za-z]+)[^\d]*(\d{4})', str(col))
                        cell = None
                        if company_id and m:
                            month_str, year_str = m.groups()
                            month_map = {'Mar':'03','Jun':'06','Sep':'09','Dec':'12'}
                            month_num = month_map.get(month_str[:3].title())
                            if month_num:
                                url = f'https://www.screener.in/company/source/quarter/{company_id}/{month_num}/{year_str}'
                                cell = f'[Raw PDF]({url})'
                                debug_msg += f", generated: {url}"
                    print(debug_msg)
                    pdf_row_data.append(cell)
                while len(pdf_row_data) < len(df.columns):
                    pdf_row_data.append(None)
                df.loc[len(df)] = pdf_row_data
                while len(pdf_row_data) < len(df.columns):
                    pdf_row_data.append(None)
                df.loc[len(df)] = pdf_row_data



        # --- TradingView logo integration ---
        import re
        import requests
        @st.cache_data(show_spinner=False)
        def tradingview_logo_url(company_name):
            # Group mapping for conglomerates
            GROUP_LOGO_MAP = {
                "TATA": "tata",
                "RELIANCE": "reliance",
                "ADANI": "adani",
                "KALYAN": "kalyan",
                "BIRLA": "birla",
                "GODREJ": "godrej",
                "MAHINDRA": "mahindra",
                "HINDUJA": "hinduja",
                "BAJAJ": "bajaj",
                # Add more group names as needed
            }
            # 1. Try full company slug
            slug_full = re.sub(r'[^a-zA-Z0-9 ]', '', company_name).lower().strip().replace(' ', '-')
            url_full = f"https://s3-symbol-logo.tradingview.com/{slug_full}--big.svg"
            if logo_exists(url_full):
                return url_full
            # 2. Try group fallback
            upper_name = company_name.upper()
            for group, slug in GROUP_LOGO_MAP.items():
                if group in upper_name:
                    url_group = f"https://s3-symbol-logo.tradingview.com/{slug}--big.svg"
                    if logo_exists(url_group):
                        return url_group
            # 3. Fallback: always use India flag logo as last fallback
            return "https://s3-symbol-logo.tradingview.com/country/IN--big.svg"

        def logo_exists(url):
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                }
                resp = requests.get(url, timeout=2, stream=True, headers=headers)
                ok = resp.status_code == 200
                if not ok:
                    print(f"Logo fetch failed: {url} (status {resp.status_code})")
                resp.close()
                return ok
            except Exception as e:
                print(f"Logo fetch exception: {url} ({e})")
                return False

        # Overview section
        if 'Overview' in text_blocks:
            st.markdown("---")
            # Try to get company name from overview block or fallback to selected symbol's name
            company_name = None
            try:
                if symbol in symbols_df['SYMBOL'].values:
                    company_name = symbols_df.loc[symbols_df['SYMBOL'] == symbol, 'NAME OF COMPANY'].values[0]
                else:
                    # fallback: try to extract from text_blocks['Overview']
                    company_name = text_blocks['Overview'].split('\n')[0].replace('**','').strip()
            except Exception:
                company_name = symbol
            logo_url = tradingview_logo_url(company_name)
            # Display TradingView logo and Company Overview header inline
            logo_html = f"<img src='{logo_url}' width='48' style='vertical-align:middle;margin-right:16px;'/>" if logo_exists(logo_url) else "<span style='font-size:2.2rem;margin-right:16px;'>🏢</span>"
            st.markdown(f"<div style='display:flex;align-items:center;gap:12px'>{logo_html}<span style='font-size:2.2rem;font-weight:700;color:#fff;'>Company Overview</span></div>", unsafe_allow_html=True)
            st.markdown(text_blocks['Overview'])

        # Main text commentary
        commentary_keys = [k for k in text_blocks if k != 'Overview']
        # REMOVE the expander for Insights, Business & Commentary at the top as requested by the user
        # if commentary_keys:
        #     with st.expander("📝 Insights, Business & Commentary", expanded=True):
        #         for title in commentary_keys:
        #             st.subheader(title)
        #             st.write(text_blocks[title])

        # Financial tables grouped by type
        if tables:
            st.markdown("---")
            st.header("💹 Financial & Data Tables")
            shown_titles = set()
            peer_table = None
            peer_title = None
            # First, filter out Peer Comparison
            filtered_tables = []
            for title, df in tables:
                if df.shape[0] < 2 or df.shape[1] < 2:
                    continue
                if title and ("peer" in title.lower() or "comparison" in title.lower()):
                    if peer_table is None:
                        peer_table = df
                        peer_title = title
                    continue
                if title in shown_titles:
                    continue
                shown_titles.add(title)
                filtered_tables.append((title, df))
            # Show all regular tables, but skip the first 'Shareholding Pattern' before Peer Comparison
            shareholding_pattern_skipped = False
            for title, df in filtered_tables:
                if (not shareholding_pattern_skipped and title and "shareholding pattern" in title.lower() and "quarterly" not in title.lower() and "yearly" not in title.lower()):
                    shareholding_pattern_skipped = True
                    continue  # Skip the first generic Shareholding Pattern
                with st.expander(f"📄 {title}", expanded=True):
                    st.dataframe(df)
            # --- Peer Comparison: Try API, fallback to HTML ---
            import pandas as pd
            import os
            peer_df = None
            company_id = None
            print(f"[DEBUG] Symbol entered: {symbol}")
            # Try to fetch company ID from CSV if available
            csv_path = os.path.join(os.path.dirname(__file__), '..', 'screener_all_listed_company_ids.csv')
            symbol_upper = symbol.upper()
            if os.path.exists(csv_path):
                try:
                    df_ids = pd.read_csv(csv_path, dtype=str)
                    # Ensure all symbols in the DataFrame are uppercase and stripped
                    df_ids["Symbol"] = df_ids["Symbol"].astype(str).str.strip().str.upper()
                    symbol_upper = symbol.strip().upper()
                    match = df_ids[df_ids["Symbol"] == symbol_upper]
                    if not match.empty:
                        company_id = match.iloc[0]["CompanyID"]
                        print(f"[DEBUG] Found company_id in CSV: {company_id}")
                    else:
                        print(f"[DEBUG] Symbol not found in CSV: {symbol_upper}")
                except Exception as e:
                    print(f"[DEBUG] Error reading CSV: {e}")
            # Fallback: try to extract from HTML if not found in CSV
            if not company_id:
                company_id = extract_company_id_for_api(soup)
                print(f"[DEBUG] Extracted company_id from HTML: {company_id}")
            # Try API if company_id found
            if company_id:
                peer_api_url = f"https://www.screener.in/api/company/{company_id}/peers/"
                print(f"[DEBUG] Calling peer API: {peer_api_url}")
                try:
                    response = requests.get(peer_api_url, timeout=10)
                    print(f"[DEBUG] API response status: {response.status_code}")
                    if response.status_code == 200:
                        from bs4 import BeautifulSoup
                        soup_api = BeautifulSoup(response.text, "html.parser")
                        tables = soup_api.find_all("table")
                        if tables:
                            try:
                                df = pd.read_html(str(tables[0]))[0]
                                if 'Name' in df.columns:
                                    df = df[~df['Name'].astype(str).str.contains('Median', na=False)]
                                print(f"[DEBUG] Peer data found in API HTML: {len(df)} rows")
                                peer_df = df
                            except Exception as e:
                                print(f"[DEBUG] Exception parsing API HTML table: {e}")
                        else:
                            print(f"[DEBUG] No table found in API HTML.")
                    else:
                        print(f"[DEBUG] API call failed with status: {response.status_code}")
                except Exception as e:
                    print(f"[DEBUG] Exception during API call: {e}")
# Fallback: Try to extract from loaded HTML if API fails
if peer_df is None:
    peer_df = extract_peer_table_from_html(soup)

with st.expander("🧑‍🤝‍🧑 Peer Comparison", expanded=False):
    st.warning("🚧 Peer Comparison is under development. Data is highly likely to be incorrect. We are working on it.")
    if peer_df is not None and not peer_df.empty:
        st.dataframe(peer_df)
    else:
        st.info("Peer Comparison data not available for this company.")

try:
    # Find all tables in the main company page soup (not /share-holding/)
    tables = soup.find_all("table", class_="data-table")
    shareholding_tables = []
    for table in tables:
        # Heuristic: look for tables with Promoters, FIIs, DIIs, Public, Others, No. of Shareholders as rows
        try:
            df = pd.read_html(io.StringIO(str(table)))[0]
            # Check if table looks like a shareholding pattern table
            if any(x in df.iloc[:,0].astype(str).str.lower().tolist() for x in ["promoters", "fiis", "diis", "public", "others", "no. of shareholders"]):
                shareholding_tables.append(df)
        except Exception:
            pass
    if len(shareholding_tables) >= 2:
        quarterly_df = shareholding_tables[0]
        yearly_df = shareholding_tables[1]
        # SVG Chart Icon
        st.markdown("""
<svg width='32' height='32' viewBox='0 0 24 24' fill='none' xmlns='http://www.w3.org/2000/svg'>
  <rect width='24' height='24' rx='12' fill='#e3eafe'/>
  <path d='M12 4v8l6.928 4A8 8 0 1 1 12 4z' fill='#4f46e5'/>
  <path d='M12 12V4a8 8 0 0 1 6.928 12l-6.928-4z' fill='#60a5fa'/>
</svg>
""", unsafe_allow_html=True)
        with st.expander("Quarterly Shareholding Pattern", expanded=True):
            st.dataframe(quarterly_df)
        st.markdown("""
<svg width='32' height='32' viewBox='0 0 24 24' fill='none' xmlns='http://www.w3.org/2000/svg'>
  <rect width='24' height='24' rx='12' fill='#e3eafe'/>
  <path d='M12 4v8l6.928 4A8 8 0 1 1 12 4z' fill='#4f46e5'/>
  <path d='M12 12V4a8 8 0 0 1 6.928 12l-6.928-4z' fill='#60a5fa'/>
</svg>
""", unsafe_allow_html=True)
        with st.expander("Yearly Shareholding Pattern", expanded=True):
            st.dataframe(yearly_df)
    else:
        st.info("Shareholding pattern data not available for this company.")
except Exception as e:
    st.info(f"Failed to fetch shareholding pattern: {e}")

# Insights, Business & Commentary Section - Organized
with st.expander("📰 Insights, Business & Commentary", expanded=True):
    # Analysis Section
    st.markdown("### 🧐 Analysis")
    st.write(
        "Pros: Stock is trading at 3.41 times its book value. The company has delivered a poor sales growth of 9.01% over past five years.\n"
        "Cons: The company has a low return on equity of 8.14% over last 3 years."
    )
    st.markdown(
        "*The pros and cons are machine generated. Please exercise caution and do your own analysis.*"
    )
    st.markdown("---")

    # (Optional) Add more sections as needed, e.g. Key Ratios, Alerts, etc.

# Document/report links
if links:
    st.markdown("---")
    st.header("📂 Documents")
    base_url = "https://www.screener.in"
    # Announcements
    if links['Announcements']:
        with st.expander("📢 Announcements", expanded=False):
            for title, href, summary in links['Announcements']:
                if href.startswith("/"):
                    href = base_url + href
                st.markdown(
                    f"<a href='{href}' target='_blank' style='color:#4f46e5;font-weight:600;font-size:1.1em'>{title}</a>",
                    unsafe_allow_html=True
                )
                if summary:
                    st.markdown(
                        f"<div style='color:#888;font-size:0.97em;margin-bottom:18px'>{summary}</div>",
                        unsafe_allow_html=True
                    )
    # Annual Reports
    if links['Annual Reports']:
        with st.expander("📅 Annual Reports", expanded=False):
            for text, href in links['Annual Reports']:
                if href.startswith("/"):
                    href = base_url + href
                st.markdown(f"- [{text}]({href})")
    # Credit Ratings
    if links['Credit Ratings']:
        with st.expander("🏦 Credit Ratings", expanded=False):
            for text, href in links['Credit Ratings']:
                if href.startswith("/"):
                    href = base_url + href
                # Only show the main title (remove extra newlines or 'from ...' if present)
                main_title = text.split('\n')[0].split('from')[0].strip()
                # Encode the URL so the full link is clickable, even with spaces/special chars
                from urllib.parse import quote
                encoded_href = quote(href, safe=':/?&=%')
                st.markdown(f"[{href}]({encoded_href})")
    # Concalls
    if links['Concalls']:
        # Find all doc types present in any entry (Transcript, Notes, PPT, REC, etc.)
        doc_types = set()
        for entry in links['Concalls']:
            doc_types.update([k for k in entry.keys() if k != 'date'])
        doc_types = sorted(doc_types, key=lambda x: ['Transcript','Notes','PPT','REC'].index(x) if x in ['Transcript','Notes','PPT','REC'] else 99)
        st.markdown("""
        <style>
        .concall-row {display: flex; align-items: center; margin-bottom: 14px;}
        .concall-date {font-weight: 600; color: #444; font-size: 1.15em; margin-right: 24px; min-width: 86px;}
        .concall-btn {margin-right: 8px; padding: 2.5px 16px; border-radius: 8px; border: 1.5px solid #4f46e5; color: #4f46e5; background: #fff; text-decoration: none; font-size: 1.06em; display: inline-block; transition: background 0.2s;}
        .concall-btn:visited {color: #4f46e5;}
        .concall-btn.disabled {color: #bbb; border-color: #eee; background: #f5f5f5; pointer-events: none;}
        </style>
        """, unsafe_allow_html=True)
        from datetime import datetime
        import calendar
        def parse_concall_date(date_str):
            try:
                parts = date_str.strip().split()
                if len(parts) == 2:
                    month_str, year_str = parts
                    month_num = list(calendar.month_abbr).index(month_str[:3].title())
                    return datetime(int(year_str), month_num, 1)
            except Exception:
                pass
            return datetime.min

        with st.expander("📞 Concalls", expanded=False):
            # Remove exact duplicates (same date and doc links)
            unique_concalls = []
            seen = set()
            for entry in links['Concalls']:
                # Use tuple of (date, Transcript, Notes, PPT, REC, etc.) as key
                key = (entry.get('date'),) + tuple(entry.get(dt) for dt in doc_types)
                if key not in seen:
                    seen.add(key)
                    unique_concalls.append(entry)
            for entry in sorted(unique_concalls, key=lambda x: parse_concall_date(x['date']), reverse=True):
                row_html = f'<div class="concall-row"><span class="concall-date">{entry["date"]}</span>'
                for doc_type in doc_types:
                    url = entry.get(doc_type)
                    if url:
                        row_html += f'<a class="concall-btn" href="{url}" target="_blank">{doc_type}</a>'
                    else:
                        row_html += f'<span class="concall-btn disabled">{doc_type}</span>'
                row_html += '</div>'
                st.markdown(row_html, unsafe_allow_html=True)

    else:
        st.info('No concalls found.')

    st.markdown("---")
    st.caption("")

elif symbol:
    st.error(f"No data available for symbol '{symbol}'. Please check the symbol or try another.")
else:
    st.info("Enter a company symbol (e.g., RELIANCE, TCS, INFY, SBIN) to view all available data beautifully categorized.")
