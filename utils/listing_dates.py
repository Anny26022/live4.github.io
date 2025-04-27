import pandas as pd
import os
from functools import lru_cache

def get_listing_date_map(filepath=None):
    """
    Reads listing_dates.txt and returns a dictionary mapping stock symbols to their listing dates (as strings).
    Always looks in the same directory as this file (utils) by default.
    Uses LRU cache for efficiency.
    """
    import os
    import pandas as pd
    if filepath is None:
        filepath = os.path.join(os.path.dirname(__file__), 'listing_dates.txt')
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"listing_dates.txt not found at {filepath} (cwd: {os.getcwd()})")
    df = pd.read_csv(filepath, header=None, names=["stock_name", "listing_date"])
    # Standardize column names if header present
    if df.columns[0] != "stock_name":
        df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
    return dict(zip(df['stock_name'], df['listing_date']))

@lru_cache(maxsize=1)
def get_listing_date_map_cached():
    return get_listing_date_map()
