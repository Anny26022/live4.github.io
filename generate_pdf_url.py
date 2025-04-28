import csv

# This script generates a Screener.in quarterly PDF URL for each company
# Format: https://www.screener.in/company/source/quarter/{COMPANYID}/{QUARTERMONTH}/{YEAR}

input_file = 'screener_all_listed_company_ids.csv'
output_file = 'generated_pdf_urls.csv'

# Set your desired quarter and year
quarter_month = '12'  # e.g., '12' for December quarter
year = '2022'

rows = []
with open(input_file, newline='', encoding='utf-8') as f:
    reader = csv.reader(f)
    for row in reader:
        if len(row) == 2:
            symbol, company_id = row
            url = f"https://www.screener.in/company/source/quarter/{company_id}/{quarter_month}/{year}"
            rows.append([symbol, company_id, url])

with open(output_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['SYMBOL', 'COMPANYID', 'PDF_URL'])
    writer.writerows(rows)

print(f"Generated {len(rows)} PDF URLs in {output_file}")
