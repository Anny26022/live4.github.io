import requests
import pandas as pd
from bs4 import BeautifulSoup
import datetime
from typing import List, Dict, Optional
import logging
import time
import functools
import os
import json
import numpy as np

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (pd.Timestamp, np.datetime64)):
            return str(obj)
        return super().default(obj)

class BSEAnnouncements:
    def __init__(self):
        self.base_url = "https://www.bseindia.com/corporates/ann.html"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.api_url = "https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w"
        self.ann_page_url = "https://www.bseindia.com/corporates/ann.html"
        self.browser_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Referer': 'https://www.bseindia.com/',
            'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'X-Requested-With': 'XMLHttpRequest'
        }
        # Initialize session once during class initialization
        self.session = requests.Session()
        self.session.headers.update(self.browser_headers)
        # Cache directory
        self.cache_dir = "cache"
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        logger.info("BSEAnnouncements initialized")

    def _get_cache_key(self, from_date, to_date, category, scrip, subcategory, page):
        """Generate a unique cache key for the API call parameters"""
        return f"{from_date}_{to_date}_{category}_{scrip}_{subcategory}_{page}"

    def _get_cache_path(self, cache_key):
        """Get the cache file path for a given cache key"""
        return os.path.join(self.cache_dir, f"{cache_key}.json")

    def _load_from_cache(self, cache_key):
        """Load data from cache if available and not expired"""
        cache_path = self._get_cache_path(cache_key)
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    data = json.load(f)
                    cache_time = datetime.datetime.fromisoformat(data['timestamp'])
                    if (datetime.datetime.now() - cache_time).total_seconds() < 3600:  # 1 hour cache
                        return pd.DataFrame(data['data'])
            except Exception as e:
                logger.warning(f"Error loading from cache: {str(e)}")
        return None

    def _save_to_cache(self, cache_key, df):
        """Save data to cache"""
        try:
            cache_path = self._get_cache_path(cache_key)
            # Ensure the cache directory exists
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            # Convert all Timestamp objects to strings in DataFrame columns
            df_serializable = df.copy()
            for col in df_serializable.select_dtypes(include=['datetime', 'datetimetz']):
                df_serializable[col] = df_serializable[col].astype(str)
            data = {
                'timestamp': datetime.datetime.now().isoformat(),
                'data': df_serializable.to_dict(orient='records')
            }
            with open(cache_path, 'w') as f:
                json.dump(data, f, cls=EnhancedJSONEncoder)
        except Exception as e:
            logger.warning(f"Error saving to cache: {str(e)}")

    def fetch_announcements(self, 
                          from_date: Optional[str] = None,
                          to_date: Optional[str] = None,
                          category: Optional[str] = None,
                          sub_category: Optional[str] = None,
                          security_name: Optional[str] = None) -> pd.DataFrame:
        """
        Fetch announcements from BSE website
        
        Args:
            from_date: Start date in DD/MM/YYYY format
            to_date: End date in DD/MM/YYYY format
            category: Category filter (e.g., 'Board Meeting', 'Result')
            sub_category: Sub-category filter
            security_name: Company name or security code
            
        Returns:
            DataFrame containing announcements
        """
        try:
            # Prepare parameters
            params = {
                'Segment': 'Equity',
                'Type': 'Announcement',
                'FromDate': from_date or '',
                'ToDate': to_date or '',
                'Category': category or '',
                'SubCategory': sub_category or '',
                'SecurityName': security_name or ''
            }
            
            logger.info(f"Making request to BSE with params: {params}")
            
            # Make request
            response = requests.get(self.base_url, params=params, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            logger.info(f"Response status code: {response.status_code}")
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract announcements
            announcements = []
            table = soup.find('table', {'class': 'table'})
            
            if not table:
                logger.warning("No table found in the response")
                return pd.DataFrame()
                
            rows = table.find_all('tr')[1:]  # Skip header row
            logger.info(f"Found {len(rows)} rows in the table")
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 4:
                    try:
                        announcement = {
                            'Date': cols[0].text.strip(),
                            'Company': cols[1].text.strip(),
                            'Category': cols[2].text.strip(),
                            'Subject': cols[3].text.strip(),
                            'Link': cols[3].find('a')['href'] if cols[3].find('a') else ''
                        }
                        announcements.append(announcement)
                    except Exception as e:
                        logger.error(f"Error processing row: {str(e)}")
                        continue
            
            logger.info(f"Successfully processed {len(announcements)} announcements")
            return pd.DataFrame(announcements)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            raise Exception(f"Failed to fetch announcements: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise Exception(f"An unexpected error occurred: {str(e)}")

    def get_announcement_details(self, announcement_url: str) -> Dict:
        """
        Get detailed information for a specific announcement
        
        Args:
            announcement_url: URL of the announcement
            
        Returns:
            Dictionary containing detailed announcement information
        """
        try:
            logger.info(f"Fetching announcement details from: {announcement_url}")
            response = requests.get(announcement_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            details = {}
            
            # Extract details based on the actual HTML structure
            content_div = soup.find('div', {'class': 'announcement-content'})
            if content_div:
                details['content'] = content_div.text.strip()
            else:
                details['content'] = "Content not found"
            
            attachments = []
            for a in soup.find_all('a', {'class': 'attachment'}):
                if 'href' in a.attrs:
                    attachments.append(a['href'])
            details['attachments'] = attachments
            
            logger.info("Successfully fetched announcement details")
            return details
            
        except Exception as e:
            logger.error(f"Error fetching announcement details: {str(e)}")
            return {'error': str(e)}

    def fetch_announcements_api(
        self,
        from_date: Optional[str] = None,  # format: DD/MM/YYYY
        to_date: Optional[str] = None,    # format: DD/MM/YYYY
        category: Optional[str] = "-1",
        page: int = 1,
        scrip: str = "",
        subcategory: str = "-1",
        max_retries: int = 3,
        timeout: int = 60
    ) -> pd.DataFrame:
        """Fetch announcements from the BSE API with caching"""
        cache_key = self._get_cache_key(from_date, to_date, category, scrip, subcategory, page)
        cached_data = self._load_from_cache(cache_key)
        if cached_data is not None:
            return cached_data

        def to_bse_date(dt_str):
            if not dt_str:
                return ""
            try:
                # First try DD/MM/YYYY format
                return datetime.datetime.strptime(dt_str, "%d/%m/%Y").strftime("%Y%m%d")
            except Exception:
                try:
                    # If that fails, try YYYYDDMM format
                    dt = datetime.datetime.strptime(dt_str, "%Y%d%m")
                    # Convert to DD/MM/YYYY first
                    dd_mm_yyyy = dt.strftime("%d/%m/%Y")
                    # Then convert to YYYYMMDD
                    return datetime.datetime.strptime(dd_mm_yyyy, "%d/%m/%Y").strftime("%Y%m%d")
                except Exception:
                    return dt_str

        params = {
            "pageno": page,
            "strCat": category if category else "",
            "strPrevDate": to_bse_date(from_date),
            "strScrip": scrip or "",
            "strSearch": "P",
            "strToDate": to_bse_date(to_date),
            "strType": "C",
            "subcategory": subcategory if subcategory else ""
        }

        retry_count = 0
        last_error = None

        while retry_count < max_retries:
            try:
                # Add a small delay to avoid hitting rate limits
                time.sleep(0.2) 
                response = self.session.get(
                    self.api_url, 
                    params=params, 
                    timeout=timeout
                )
                response.raise_for_status()
                
                try:
                    data = response.json()
                except Exception as e:
                    logger.error(f"Failed to parse JSON response: {str(e)}")
                    logger.error(f"Raw response: {response.text[:500]}")
                    raise Exception(f"API did not return valid JSON. Raw response: {response.text[:500]}")
                
                df = pd.DataFrame(data.get("Table", []))
                # Normalize DT_TM to datetime (preserve time if present)
                if 'DT_TM' in df.columns:
                    df['DT_TM'] = pd.to_datetime(df['DT_TM'], errors='coerce')
                
                # Save to cache before returning
                self._save_to_cache(cache_key, df)
                return df

            except requests.exceptions.Timeout as e:
                last_error = e
                retry_count += 1
                wait_time = min(2 ** retry_count, 10)  # Cap maximum wait time at 10 seconds
                logger.warning(f"Request timed out. Retrying in {wait_time} seconds... (Attempt {retry_count}/{max_retries})")
                time.sleep(wait_time)
                
            except requests.exceptions.RequestException as e:
                last_error = e
                retry_count += 1
                wait_time = min(2 ** retry_count, 10)
                logger.warning(f"Request failed: {str(e)}. Retrying in {wait_time} seconds... (Attempt {retry_count}/{max_retries})")
                time.sleep(wait_time)
                
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                raise

        if last_error:
            raise Exception(f"Failed to fetch announcements after {max_retries} attempts. Last error: {str(last_error)}")
        return pd.DataFrame()

    def fetch_all_announcements_api(self, from_date, to_date, category="-1", scrip="", subcategory="-1") -> pd.DataFrame:
        """
        Fetch all announcements from the BSE API endpoint, aggregating results from all pages.
        Handles date ranges longer than 30 days by making multiple API calls in chunks.
        """
        def parse_date(date_str):
            return datetime.datetime.strptime(date_str, "%d/%m/%Y")
        
        def format_date(date):
            return date.strftime("%d/%m/%Y")
        
        # Parse dates
        start_date = parse_date(from_date)
        end_date = parse_date(to_date)
        
        # Calculate date range in days
        date_range = (end_date - start_date).days
        
        # Only split into chunks if date range is longer than 30 days
        if date_range <= 30:
            date_chunks = [(start_date, end_date)]
        else:
            # Calculate number of 30-day chunks needed
            date_chunks = []
            current_start = start_date
            while current_start < end_date:
                current_end = min(current_start + datetime.timedelta(days=29), end_date)
                date_chunks.append((current_start, current_end))
                current_start = current_end + datetime.timedelta(days=1)
        
        all_results = []
        total_chunks = len(date_chunks)
        
        for i, (chunk_start, chunk_end) in enumerate(date_chunks, 1):
            logger.info(f"Fetching chunk {i}/{total_chunks}: {format_date(chunk_start)} to {format_date(chunk_end)}")
            
            chunk_results = []
            page = 1
            total_pages = None
            
            while True:
                # Check if we have cached data for this chunk and page
                cache_key = self._get_cache_key(
                    format_date(chunk_start),
                    format_date(chunk_end),
                    category,
                    scrip,
                    subcategory,
                    page
                )
                cached_data = self._load_from_cache(cache_key)
                
                if cached_data is not None:
                    df = cached_data
                else:
                    df = self.fetch_announcements_api(
                        from_date=format_date(chunk_start),
                        to_date=format_date(chunk_end),
                        category=category,
                        page=page,
                        scrip=scrip,
                        subcategory=subcategory
                    )
                
                if df.empty:
                    break
                    
                chunk_results.append(df)
                
                # Get total pages from the first row if available
                if total_pages is None and 'TotalPageCnt' in df.columns:
                    total_pages = df['TotalPageCnt'].iloc[0]
                if total_pages is not None and page >= total_pages:
                    break
                if len(df) < 20:  # API default page size is 20
                    break
                page += 1
            
            if chunk_results:
                all_results.extend(chunk_results)
        
        if all_results:
            return pd.concat(all_results, ignore_index=True)
        else:
            return pd.DataFrame()

    @staticmethod
    def parse_datetime_column(df, col_name):
        """
        Robustly parse a datetime column in a DataFrame using pandas' 'mixed' format,
        which handles ISO8601 strings with or without microseconds. Assumes IST.
        Also tries BSE's 'DD-MM-YYYY HH:MM:SS' format for any unparsed values.
        """
        if col_name in df.columns:
            df[col_name] = pd.to_datetime(df[col_name], format='mixed', errors='coerce')
            # Fallback: try parsing with '%d-%m-%Y %H:%M:%S' for any NaT values
            mask_nat = df[col_name].isna() & df[col_name].notnull()
            if mask_nat.any():
                df.loc[mask_nat, col_name] = pd.to_datetime(df.loc[mask_nat, col_name], format='%d-%m-%Y %H:%M:%S', errors='coerce')
        return df 