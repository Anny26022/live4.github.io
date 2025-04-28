import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

base_url = "https://www.screener.in/screens/357649/all-listed-companies/?page={}"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}

results = []

for page in range(104, 198):  # Pages 104 to 197 inclusive
    url = base_url.format(page)
    print(f"Fetching {url}")
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        print(f"Failed to fetch page {page}")
        break

    soup = BeautifulSoup(resp.text, "html.parser")
    rows = soup.select("tr[data-row-company-id]")
    for row in rows:
        company_id = row.get("data-row-company-id")
        symbol = None
        link = row.find("a", href=True)
        if link:
            # /company/RELIANCE/consolidated/
            parts = link["href"].split("/")
            if len(parts) > 2:
                symbol = parts[2]
        if company_id and symbol:
            results.append({"Symbol": symbol, "CompanyID": company_id})

    time.sleep(0.7)  # Be polite

# Save to CSV (append to existing file if present)
import os
csv_path = "screener_all_listed_company_ids.csv"
if os.path.exists(csv_path):
    old_df = pd.read_csv(csv_path, dtype=str)
    new_df = pd.DataFrame(results)
    combined = pd.concat([old_df, new_df], ignore_index=True)
    combined.drop_duplicates(subset=["Symbol"], inplace=True)
    combined.to_csv(csv_path, index=False)
    print(f"Done! Found {len(combined)} companies. Saved to {csv_path}.")
else:
    df = pd.DataFrame(results)
    df.drop_duplicates(subset=["Symbol"], inplace=True)
    df.to_csv(csv_path, index=False)
    print(f"Done! Found {len(df)} companies. Saved to {csv_path}.")
