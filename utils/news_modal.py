import streamlit as st
from gnews import GNews
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd
import pytz
import concurrent.futures
import hashlib
import json
from datetime import datetime

# --- Caching helpers (copied from 13_RealTime_Stock_News.py) ---
@st.cache_data(ttl=300, show_spinner=False)
def cached_gnews_results(params_hash, method, query, topic, location, site):
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

def make_hash(obj):
    obj_str = json.dumps(obj, sort_keys=True, default=str)
    return hashlib.sha256(obj_str.encode()).hexdigest()

# --- Improved, clean compact news card CSS ---
st.markdown("""
<style>
.compact-news-card {
    margin-bottom: 1.1em !important;
    padding: 0.6em 0.9em 0.6em 0.9em !important;
    background: linear-gradient(120deg, rgba(36, 42, 60, 0.94) 60%, rgba(44,46,56,0.97) 100%);
    border-radius: 8px !important;
    box-shadow: 0 2px 10px 0 rgba(31, 38, 135, 0.10);
    border: 1px solid #23252622;
    transition: box-shadow 0.2s;
    width: 100%;
    max-width: 600px;
    box-sizing: border-box;
}
.compact-news-card .news-row {
    display: flex;
    align-items: center;
    gap: 0.7em;
    margin-bottom: 0.1em;
    flex-wrap: wrap;
}
.compact-news-card .news-title {
    font-size: 1.04rem;
    font-weight: 600;
    color: #5fa8d3 !important;
    text-decoration: none !important;
    word-break: break-word;
    flex: 1 1 180px;
}
.compact-news-card .news-title:hover {
    text-decoration: underline !important;
    color: #ffd700 !important;
}
.compact-news-card .news-sentiment {
    font-size: 0.98rem;
    font-weight: 500;
    margin-left: auto;
    min-width: 80px;
    text-align: right;
}
.compact-news-card .news-date {
    font-size: 0.93rem;
    color: #b0b0b0;
    margin-left: 1.7em;
    margin-top: 0.1em;
    word-break: break-word;
}
@media (max-width: 600px) {
    .compact-news-card {
        padding: 0.5em 0.2em 0.5em 0.2em !important;
        max-width: 98vw;
    }
    .compact-news-card .news-row {
        flex-direction: column;
        align-items: flex-start;
        gap: 0.3em;
    }
    .compact-news-card .news-title {
        font-size: 1rem;
        flex: 1 1 100%;
    }
    .compact-news-card .news-sentiment {
        font-size: 0.95rem;
        margin-left: 0;
        min-width: 0;
        text-align: left;
    }
    .compact-news-card .news-date {
        font-size: 0.89rem;
        margin-left: 0;
        margin-top: 0.15em;
    }
}
</style>
""", unsafe_allow_html=True)

# --- Improved, clean compact news card renderer ---
def render_compact_news_card(item, sentiment_label, sentiment_color):
    published = item.get('published date', 'N/A')
    try:
        published_str = pd.to_datetime(published).tz_localize('UTC').tz_convert('Asia/Kolkata').strftime('%a, %d %b %Y %I:%M:%S %p IST')
    except Exception:
        published_str = published
    st.markdown(f"""
        <div class="compact-news-card">
            <div class="news-row">
                <a href="{item.get('url','')}" target="_blank" class="news-title">{item.get('title','')}</a>
                <span class="news-sentiment" style="color:{sentiment_color};">{sentiment_label}</span>
            </div>
            <div class="news-date">{published_str}</div>
        </div>
    """, unsafe_allow_html=True)

def show_news_for_symbol(symbol, language_code="en", country_code="IN", period="7d", max_results=6, exclude_websites=None, date_filter=None):
    """
    Show compact news cards for a given stock symbol, with sentiment analysis and date filtering.
    """
    st.markdown(f"### 📰 News for `{symbol}`")
    sentiment_analyzer = SentimentIntensityAnalyzer()
    search_method = "By Keyword (Company/Stock)"
    params_hash = {
        'language_code': language_code,
        'country_code': country_code,
        'period': period,
        'max_results': max_results,
        'exclude_websites': exclude_websites or [],
    }
    try:
        with st.spinner("Fetching news..."):
            news_items = cached_gnews_results(params_hash, search_method, symbol, None, None, None)
            if date_filter:
                news_items = [item for item in news_items if 'published date' in item and str(date_filter) in item['published date']]
            if not news_items:
                st.info("No news articles found for this symbol.")
                return
            # Sort news_items by published date (descending: latest first)
            def parse_date(item):
                try:
                    return pd.to_datetime(item.get('published date', ''), utc=True)
                except Exception:
                    return pd.Timestamp.min
            news_items = sorted(news_items, key=parse_date, reverse=True)
            for idx, item in enumerate(news_items):
                description = item.get('description','') or item.get('title','')
                sentiment = sentiment_analyzer.polarity_scores(description)
                compound = sentiment['compound']
                if compound >= 0.2:
                    sentiment_label = 'Positive'
                    sentiment_color = '#27ae60'
                elif compound <= -0.2:
                    sentiment_label = 'Negative'
                    sentiment_color = '#e74c3c'
                else:
                    sentiment_label = 'Neutral'
                    sentiment_color = '#f1c40f'
                render_compact_news_card(item, sentiment_label, sentiment_color)
    except Exception as e:
        st.error(f"Failed to fetch news: {e}")
