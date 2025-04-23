import pandas as pd
import os
from functools import lru_cache

def get_listing_date_map(filepath=None):
    """
    Reads listing_dates.txt and returns a dictionary mapping stock symbols to their listing dates (as strings).
    If filepath is None, assumes listing_dates.txt is in the project root.
    Uses LRU cache for efficiency.
    """
    if filepath is None:
        filepath = os.path.join(os.path.dirname(__file__), 'listing_dates.txt')
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"listing_dates.txt not found at {filepath}")
    df = pd.read_csv(filepath)
    # Standardize column names
    df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
    # Build mapping
    return dict(zip(df['stock_name'], df['listing_date']))

@lru_cache(maxsize=1)
def get_listing_date_map_cached():
    return get_listing_date_map()
