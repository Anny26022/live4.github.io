import os
import csv
import re
import requests

CSV_PATH = 'EQUITY_MASTER.csv'
LOGO_DIR = 'logos'
INDIA_FLAG_URL = 'https://s3-symbol-logo.tradingview.com/country/IN--big.svg'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

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

def logo_exists(url):
    try:
        resp = requests.get(url, timeout=2, stream=True, headers=HEADERS)
        ok = resp.status_code == 200
        resp.close()
        return ok
    except Exception as e:
        print(f"Logo fetch exception: {url} ({e})")
        return False

def tradingview_logo_url(company_name):
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
    return INDIA_FLAG_URL

def download_logo(symbol, company_name):
    url = tradingview_logo_url(company_name)
    out_path = os.path.join(LOGO_DIR, f"{symbol}.svg")
    try:
        resp = requests.get(url, timeout=4, stream=True, headers=HEADERS)
        if resp.status_code == 200:
            with open(out_path, 'wb') as f:
                for chunk in resp.iter_content(1024):
                    f.write(chunk)
            print(f"Downloaded: {symbol} -> {url}")
        else:
            print(f"Failed to download {symbol}: {url} (status {resp.status_code})")
        resp.close()
    except Exception as e:
        print(f"Exception for {symbol}: {url} ({e})")

def main():
    if not os.path.exists(LOGO_DIR):
        os.makedirs(LOGO_DIR)
    with open(CSV_PATH, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            symbol = row['SYMBOL'].strip()
            company_name = row['NAME OF COMPANY'].strip()
            download_logo(symbol, company_name)

if __name__ == '__main__':
    main()
