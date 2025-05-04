import sys
import streamlit as st
import traceback
import pytz
import concurrent.futures
from functools import lru_cache
import hashlib
import json

st.set_page_config(
    page_title="Real-Time Stock News",
    page_icon="📰",
    layout="centered",
    initial_sidebar_state="auto"
)

# Page Header with modern SVG (Material: Feed)
st.markdown("""
<div style='display:flex;align-items:center;justify-content:center;margin-bottom:0.5em;'>
  <svg xmlns='http://www.w3.org/2000/svg' width='48' height='48' viewBox='0 0 48 48' fill='none' style='margin-right:16px;'>
    <rect width='48' height='48' rx='12' fill='url(#realtime-bg)'/>
    <g>
      <rect x='12' y='16' width='24' height='4' rx='2' fill='#6d4cff'/>
      <rect x='12' y='24' width='16' height='4' rx='2' fill='#43a047'/>
      <rect x='12' y='32' width='8' height='4' rx='2' fill='#29b6f6'/>
    </g>
    <defs>
      <linearGradient id='realtime-bg' x1='0' y1='0' x2='48' y2='48' gradientUnits='userSpaceOnUse'>
        <stop stop-color='#23272F'/>
        <stop offset='1' stop-color='#181A20'/>
      </linearGradient>
    </defs>
  </svg>
  <span style='font-size:2.5rem;font-weight:700;color:#fff;'>RealTime Stock News</span>
</div>
<p style='text-align:center;margin-top:-0.75em;margin-bottom:2em;color:#aaa;font-size:1.1rem;'>Live updates on market news and events</p>
""", unsafe_allow_html=True)

from gnews import GNews
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd

# --- Import newspaper globally so ImportError triggers at startup, not per-article ---
try:
    from newspaper import Article
    NEWSPAPER3K_AVAILABLE = True
except Exception as e:
    st.error(f"Import failed: {e}")
    st.error(traceback.format_exc())
    NEWSPAPER3K_AVAILABLE = False

# --- Default popular news sites for quick selection ---
default_sites = [
    "moneycontrol.com",
    "reuters.com",
    "bloomberg.com",
    "cnbc.com",
    "economictimes.indiatimes.com",
    "business-standard.com"
]

# --- Fetch supported countries and languages ---
try:
    _gn = GNews()
    available_countries = _gn.AVAILABLE_COUNTRIES
    available_languages = _gn.AVAILABLE_LANGUAGES
except Exception:
    available_countries = {'India': 'IN', 'United States': 'US'}
    available_languages = {'english': 'en', 'hindi': 'hi'}

# --- Inject improved Material/Glass CSS for visibility and UX ---
st.markdown("""
<style>
/* === ENHANCED UI: Modern, Interactive, Material, Emoji Accents === */
body, .stApp {
    font-family: 'Roboto', Arial, sans-serif !important;
    background: #fff !important;
}

section[data-testid="stSidebar"] {
    background: #f8fafc !important;
    box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.08);
    border-right: 2px solid rgba(95,168,211,0.07);
    backdrop-filter: blur(8px);
    padding-top: 2.2rem !important;
    padding-bottom: 2.2rem !important;
    transition: background 0.4s;
}

.stSidebarContent {
    padding-left: 0.5rem !important;
    padding-right: 0.5rem !important;
}

.stButton > button {
    background: linear-gradient(90deg, #2563eb 0%, #3b82f6 100%);
    color: #fff;
    border: none;
    border-radius: 8px;
    font-weight: 700;
    font-size: 1.08rem;
    padding: 0.57rem 1.25rem;
    margin: 0.2rem 0 0.4rem 0;
    box-shadow: 0 2px 8px rgba(59,130,246,0.13);
    transition: background 0.3s, box-shadow 0.3s, transform 0.2s;
    letter-spacing: 0.01em;
    display: flex;
    align-items: center;
    gap: 0.6em;
}
.stButton > button:hover {
    background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%);
    box-shadow: 0 4px 18px rgba(59,130,246,0.16);
    transform: scale(1.06);
}

.stTextInput > div > input, .stTextArea > div > textarea, .stSelectbox > div > div {
    background: #fff !important;
    color: #222 !important;
    border-radius: 8px !important;
    border: 1.5px solid #b0b8c5 !important;
    font-size: 1.08rem !important;
    padding: 0.4rem 0.8rem !important;
    margin-bottom: 0.1rem !important;
    transition: border 0.2s, background 0.2s;
}
.stTextInput > div > input:focus, .stTextArea > div > textarea:focus, .stSelectbox > div > div:focus {
    border: 1.5px solid #2563eb !important;
    background: #f8fafc !important;
}

.stSelectbox > div > div {
    min-height: 2.15rem !important;
    height: 2.25rem !important;
    font-size: 1.08rem !important;
    border-radius: 8px !important;
    box-shadow: 0 1px 8px 0 rgba(59,130,246,0.11), 0 1px 0.5px 0 rgba(44,62,80,0.08) inset;
    background: #fff !important;
    font-weight: 600 !important;
    line-height: 1.19 !important;
    padding-left: 0.7rem !important;
    padding-right: 0.7rem !important;
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
    transition: box-shadow 0.25s, background 0.25s;
}
.stSelectbox > div > div span {
    font-size: 1.08rem !important;
    font-weight: 600 !important;
    padding-left: 0em;
}
.stSelectbox label {
    color: #2563eb !important;
    font-size: 1.01rem !important;
    font-weight: 800 !important;
    margin-bottom: 0.11rem !important;
    letter-spacing: 0.01em !important;
    text-shadow: none !important;
    display: flex;
    align-items: center;
    gap: 0.3em;
}
.stSelectbox svg {
    display: none !important;
}

/* News Card - Glass, Minimal, Animated, Emoji Accents */
.card-glossy {
    background: #f8fafc;
    box-shadow: 0 6px 32px 0 rgba(31, 38, 135, 0.08);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    border-radius: 16px;
    border: 1.4px solid #e0e7ef;
    margin-bottom: 1.1rem;
    padding: 1.3rem 1.1rem 1.1rem 1.1rem;
    transition: box-shadow 0.32s cubic-bezier(.4,0,.2,1), transform 0.32s cubic-bezier(.4,0,.2,1);
    animation: fadeInCard 0.8s cubic-bezier(.4,0,.2,1);
    position: relative;
    overflow: hidden;
}
.card-glossy:hover {
    box-shadow: 0 10px 40px 0 rgba(59,130,246,0.13);
    transform: translateY(-2.5px) scale(1.018);
    background: #f1f5f9;
}
.card-emoji {
    position: absolute;
    top: 1.1rem;
    right: 1.1rem;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
    background: currentColor;
    border: 1.2px solid #eee;
    box-shadow: none;
    opacity: 0.95;
    pointer-events: none;
    user-select: none;
    margin: 0;
    padding: 0;
    line-height: 1;
    transition: none;
}
@keyframes fadeInCard {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.stAlert {
    animation: fadeInCard 0.65s cubic-bezier(.4,0,.2,1);
}

::-webkit-scrollbar {
    width: 6px !important;
    background: #f8fafc;
}
::-webkit-scrollbar-thumb {
    background: #b0b8c5;
    border-radius: 8px;
    min-height: 30px;
}

/* Ensure high contrast for text and links */
.card-glossy, .card-glossy * {
    color: #222 !important;
}
.card-glossy a {
    color: #2563eb !important;
    text-decoration: none;
    font-weight: 700;
}
.card-glossy a:hover {
    color: #f59e42 !important;
    text-decoration: underline;
}

/* --- Cool, Compact, Super Responsive Search Bar --- */
.stTextInput.search-bar:before {
    display: none;
}
.stTextInput.search-bar input {
    background: #fff !important;
    border: 2px solid #b0b8c5 !important;
    border-radius: 2rem !important;
    font-size: 1.09rem !important;
    font-weight: 600;
    color: #222 !important;
    padding: 0.58rem 1rem 0.58rem 1rem !important;
    box-shadow: 0 2px 12px 0 rgba(44,62,80,0.07);
    transition: border 0.22s, box-shadow 0.22s, background 0.22s;
    outline: none !important;
    width: 100%;
    max-width: 420px;
    margin: 0.2rem auto 1.2rem auto;
    display: block;
    letter-spacing: 0.01em;
    box-sizing: border-box;
}
.stTextInput.search-bar input:focus {
    border: 2px solid #2563eb !important;
    background: #f8fafc !important;
    box-shadow: 0 4px 24px 0 rgba(59,130,246,0.10);
}
@media (max-width: 600px) {
  .stTextInput.search-bar input, .stTextInput.search-bar {
    max-width: 99vw;
    font-size: 0.99rem !important;
    padding-left: 1rem !important;
  }
}
</style>
""", unsafe_allow_html=True)

# --- Add CSS for ultra-compact, elegant emoji indicator ---
st.markdown("""
<style>
.card-glossy .card-emoji {
    font-size: 0.95rem !important;
    vertical-align: middle;
    margin-right: 0.16rem;
    margin-bottom: 0.04em;
    border-radius: 50%;
    background: rgba(95,168,211,0.07);
    padding: 0.07em 0.17em 0.07em 0.17em;
    display: inline-block;
    box-shadow: 0 0.5px 2px 0 rgba(95,168,211,0.04);
}
</style>
""", unsafe_allow_html=True)

# --- Caching helpers ---
def make_hash(obj):
    '''Create a hash for a dict/list to use as cache key.'''
    obj_str = json.dumps(obj, sort_keys=True, default=str)
    return hashlib.sha256(obj_str.encode()).hexdigest()

@st.cache_data(ttl=300, show_spinner=False)
def cached_gnews_results(params_hash, method, query, topic, location, site):
    # params_hash ensures cache is unique per filter set
    google_news = GNews(
        language=params_hash['language_code'],
        country=params_hash['country_code'],
        period=params_hash['period'],
        max_results=params_hash['max_results'],
        exclude_websites=params_hash['exclude_websites']
    )
    if method == "By Keyword (Company/Stock)":
        return google_news.get_news(query)
    elif method == "By Topic":
        return google_news.get_news_by_topic(topic)
    elif method == "By Location":
        return google_news.get_news_by_location(location)
    elif method == "By Site":
        return google_news.get_news_by_site(site)
    elif method == "Top News":
        return google_news.get_top_news()
    else:
        return []

@st.cache_data(ttl=300, show_spinner=False)
def cached_fetch_full_article(google_news, url):
    try:
        article_obj = google_news.get_full_article(url)
        if hasattr(article_obj, 'download'):
            article_obj.download()
        if hasattr(article_obj, 'parse'):
            article_obj.parse()
        return article_obj
    except Exception as e:
        return None

# --- Responsive, Compact, Modern Search Bar ---
search_query = st.text_input('Search News', '', key='search_bar',
    placeholder='Search for news, topics, stocks, etc...',
    help='Type keywords to search news',
    label_visibility='collapsed')

# --- Add Compact/Detailed View Toggle ---
view_mode = st.radio(
    "View Mode",
    ["Detailed", "Compact"],
    horizontal=True,
    index=1,
    key="news_view_mode"
)

# Add custom class to search bar
st.markdown('<style>div[data-testid="stTextInput"]:first-child {margin-bottom:0;}</style>', unsafe_allow_html=True)
st.markdown('<div class="stTextInput search-bar"></div>', unsafe_allow_html=True)

# --- Sidebar for filters ---
st.sidebar.header("Filters & Search Options")

search_method = st.sidebar.selectbox(
    "Search Method",
    [
        "By Keyword (Company/Stock)",
        "By Topic",
        "By Location",
        "By Site"
    ],
    index=0
)

language = st.sidebar.selectbox(
    "Language",
    options=sorted(available_languages.keys()),
    index=list(available_languages.values()).index('en') if 'en' in available_languages.values() else 0
)
language_code = available_languages[language]

country = st.sidebar.selectbox(
    "Country",
    options=sorted(available_countries.keys()),
    index=list(available_countries.values()).index('IN') if 'IN' in available_countries.values() else 0
)
country_code = available_countries[country].strip()

period = st.sidebar.text_input("Period (e.g. 1d, 7d, 12h, 1m, 1y)", value="7d")
max_results = st.sidebar.slider("Number of news articles", 3, 50, 6)

# --- Date and Time filter ---
with st.sidebar:
    st.markdown("**Filter by Date (optional)**")
    date_filter = st.date_input("Select a date (UTC)", value=None, help="Show only news published on this date.")
    st.markdown("**Filter by Time Range (IST, optional)**")
    start_time_ist = st.time_input("Start Time (IST)", value=pd.to_datetime("08:00:00").time())
    end_time_ist = st.time_input("End Time (IST)", value=pd.to_datetime("20:00:00").time())

# --- Website filter ---
st.sidebar.markdown("**Quick Select News Sites**")
default_sites_selected = st.sidebar.multiselect(
    "Add default sites to filter (show only these sites)",
    options=default_sites,
    default=[]
)

exclude_websites = st.sidebar.text_area("Exclude Websites (comma-separated domains)", value="", help="e.g. yahoo.com,cnn.com").split(",")
exclude_websites = [w.strip() for w in exclude_websites if w.strip()]

st.sidebar.markdown("---")

# --- Sentiment Analyzer ---
sentiment_analyzer = SentimentIntensityAnalyzer()

# --- Fetch and display news ---
if search_query:
    with st.spinner("Fetching news..."):
        try:
            params_hash = {
                'language_code': language_code,
                'country_code': country_code,
                'period': period,
                'max_results': max_results,
                'exclude_websites': exclude_websites,
            }
            hash_val = make_hash(params_hash)
            news_items = cached_gnews_results(params_hash, search_method, search_query, None, None, None)

            # --- Filter by default selected sites if any ---
            if default_sites_selected:
                # Make sure we match domain (not substring) and handle www. prefix
                def matches_site(item_url):
                    from urllib.parse import urlparse
                    try:
                        netloc = urlparse(item_url).netloc.lower()
                        # Remove www. if present
                        netloc = netloc[4:] if netloc.startswith('www.') else netloc
                        return any(site.lower().replace('www.', '').strip() in netloc for site in default_sites_selected)
                    except Exception:
                        return False
                news_items = [item for item in news_items if matches_site(item.get('url', ''))]

            # --- Sort news_items so latest is on top ---
            news_items = sorted(news_items, key=lambda x: pd.to_datetime(x.get('published date', '')), reverse=True)

            # --- Filter by date and 12-hour time range if selected (in IST) ---
            if date_filter:
                ist = pytz.timezone('Asia/Kolkata')
                date_filter_ist = pd.to_datetime(date_filter).replace(tzinfo=ist)
                def match_date(item):
                    try:
                        dt = pd.to_datetime(item.get('published date',''))
                        dt_ist = dt.tz_localize('UTC').tz_convert(ist)
                        date_match = dt_ist.strftime('%Y-%m-%d') == date_filter_ist.strftime('%Y-%m-%d')
                        time_match = True
                        if start_time_ist and end_time_ist:
                            t = dt_ist.time()
                            # Handles overnight ranges too
                            if start_time_ist <= end_time_ist:
                                time_match = start_time_ist <= t <= end_time_ist
                            else:
                                time_match = t >= start_time_ist or t <= end_time_ist
                        return date_match and time_match
                    except Exception:
                        return False
                news_items = [item for item in news_items if match_date(item)]

            if news_items:
                # --- Fetch full articles in parallel (much faster, now cached) ---
                article_objs = [None] * len(news_items)
                if NEWSPAPER3K_AVAILABLE:
                    urls = [item.get('url', '') for item in news_items]
                    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                        future_to_idx = {executor.submit(cached_fetch_full_article, GNews(language=language_code, country=country_code), url): idx for idx, url in enumerate(urls)}
                        for future in concurrent.futures.as_completed(future_to_idx):
                            idx = future_to_idx[future]
                            try:
                                article_objs[idx] = future.result()
                            except Exception:
                                article_objs[idx] = None
                for idx, item in enumerate(news_items):
                    description = item.get('description','') or item.get('title','')
                    sentiment = sentiment_analyzer.polarity_scores(description)
                    compound = sentiment['compound']
                    if compound >= 0.2:
                        sentiment_label = '😊 Positive'
                        sentiment_color = '#27ae60'
                    elif compound <= -0.2:
                        sentiment_label = '😞 Negative'
                        sentiment_color = '#e74c3c'
                    else:
                        sentiment_label = '😐 Neutral'
                        sentiment_color = '#f1c40f'
                    emoji = "\U0001F7E2" if sentiment_label == '😊 Positive' else ("\U0001F7E1" if sentiment_label == '😐 Neutral' else "\U0001F534")
                    published_str = pd.to_datetime(item.get('published date','')).tz_localize('UTC').tz_convert('Asia/Kolkata').strftime('%a, %d %b %Y %I:%M:%S %p IST')
                    if st.session_state.get('news_view_mode', 'Detailed') == 'Compact':
                        st.markdown(f"""
                            <div class="card-glossy">
                                <span class="card-emoji">{emoji}</span>
                                <a href="{item.get('url','')}" target="_blank">{item.get('title','')}</a><br/>
                                <span style="font-size:0.97rem;opacity:0.80;">{published_str}</span>
                                <span style="font-size:1.01rem;font-weight:600;color:{sentiment_color};margin-left:1em;">{sentiment_label}</span>
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                            <div class="card-glossy">
                                <span class="card-emoji">{emoji}</span>
                                <a href="{item.get('url','')}" target="_blank">{item.get('title','')}</a><br/>
                                <span style="font-size:0.97rem;opacity:0.80;">Published: {published_str}</span><br/>
                                <span style="font-size:0.97rem;opacity:0.80;">Publisher: {item.get('publisher','')}</span><br/>
                                <span style="font-size:1.01rem;font-weight:600;color:{sentiment_color};">Sentiment: {sentiment_label}</span><br/>
                                <div style="margin:0.7rem 0 0.7rem 0;font-size:1.07rem;line-height:1.62;">{item.get('description','')}</div>
                            </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No news articles found for your query.")
        except Exception as e:
            st.error(f"Failed to fetch news: {e}")
else:
    st.info("Configure your filters and enter a query to see the latest articles.")

st.markdown("""
---
**Powered by [GNews]**
""")
