import pandas as pd

csv1 = 'd:/TradingView-Screener-master/EQUITY_L.csv'
csv2 = 'd:/TradingView-Screener-master/Equity.csv'
output_csv = 'd:/TradingView-Screener-master/EQUITY_MASTER.csv'

df1 = pd.read_csv(csv1)
df2 = pd.read_csv(csv2)

# Normalize column names
for df in (df1, df2):
    df.columns = [col.strip().upper() for col in df.columns]

# For df1, SYMBOL is already present
if 'SYMBOL' in df1.columns:
    df1['SYMBOL'] = df1['SYMBOL'].astype(str).str.strip().str.upper()
else:
    raise ValueError("SYMBOL column not found in EQUITY_L.csv!")

# For df2, use SECURITY ID as SYMBOL
if 'SECURITY ID' in df2.columns:
    df2['SYMBOL'] = df2['SECURITY ID'].astype(str).str.strip().str.upper()
else:
    raise ValueError("SECURITY ID column not found in Equity.csv!")

# Robustly align NAME OF COMPANY column for df2
company_name_cols = ['NAME OF COMPANY', 'ISSUER NAME', 'SECURITY NAME', 'COMPANY NAME']
found = False
for col in company_name_cols:
    if col in df2.columns:
        df2['NAME OF COMPANY'] = df2[col]
        found = True
        print(f"[INFO] Using '{col}' for NAME OF COMPANY in Equity.csv")
        break
if not found:
    df2['NAME OF COMPANY'] = ''

# Ensure both have NAME OF COMPANY
if 'NAME OF COMPANY' not in df1.columns:
    df1['NAME OF COMPANY'] = ''
if 'NAME OF COMPANY' not in df2.columns:
    df2['NAME OF COMPANY'] = ''

# Debug: print rows containing 'FRONTIER' in symbol or company name
print("\n[DEBUG] In EQUITY_L.csv (df1):")
print(df1[df1['SYMBOL'].str.contains('FRONTIER', case=False, na=False)])
print(df1[df1['NAME OF COMPANY'].str.contains('FRONTIER', case=False, na=False)])
print("\n[DEBUG] In Equity.csv (df2):")
print(df2[df2['SYMBOL'].str.contains('FRONTIER', case=False, na=False)])
print(df2[df2['NAME OF COMPANY'].str.contains('FRONTIER', case=False, na=False)])

print(f"Unique in EQUITY_L.csv: {df1['SYMBOL'].nunique()} (Total rows: {len(df1)})")
print(f"Unique in Equity.csv: {df2['SYMBOL'].nunique()} (Total rows: {len(df2)})")

# Keep all columns, but ensure SYMBOL and NAME OF COMPANY are first
all_columns = list(dict.fromkeys(['SYMBOL', 'NAME OF COMPANY'] + list(df1.columns) + list(df2.columns)))
df1 = df1.reindex(columns=all_columns, fill_value='')
df2 = df2.reindex(columns=all_columns, fill_value='')

# Concatenate and deduplicate
combined = pd.concat([df1, df2], ignore_index=True)
combined = combined.drop_duplicates(subset=['SYMBOL'], keep='first')

print(f"Unique after merge: {combined['SYMBOL'].nunique()} (Total rows: {len(combined)})")

combined.to_csv(output_csv, index=False)
print(f"Merged CSVs. Unique symbols retained: {len(combined)}. Output: {output_csv}")
