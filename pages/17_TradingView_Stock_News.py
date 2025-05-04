import streamlit as st
import requests
import time
import datetime
import re
import concurrent.futures
import threading
import websocket
import json
import socketio
from datetime import datetime, timezone
import random
import string
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Stock News", layout="centered")

st.markdown("""
# 📰 Real Time Stock News Feed


""")

# Country options for dropdown
country_options = {
    "Entire world": None,
    "USA": "US",
    "India": "IN",
    "Germany": "DE",
    "Japan": "JP",
    "Canada": "CA",
    "Hong Kong, China": "HK",
    "United Kingdom": "GB",
    "Turkey": "TR",
    # Add more as needed
}

# Use session state to track selected country
if 'selected_country' not in st.session_state:
    st.session_state['selected_country'] = "Entire world"

selected_country = st.selectbox(
    "Stocks country",
    options=list(country_options.keys()),
    index=list(country_options.keys()).index(st.session_state['selected_country']),
    format_func=lambda x: f"🌐 {x}" if x == "Entire world" else x,
    key="country_selectbox"
)

# If the user changes the country, update session state and rerun
if selected_country != st.session_state['selected_country']:
    st.session_state['selected_country'] = selected_country
    # Reset WebSocket thread so it will restart with new country
    st.session_state['ws_thread'] = None
    st.session_state['wsio_thread_started'] = False
    st.session_state['pushstream_thread_started'] = False
    st.cache_data.clear()
    st.rerun()

country_code = country_options[selected_country]

# Build the API URL dynamically
base_url = "https://news-mediator.tradingview.com/news-flow/v2/news?filter=lang%3Aen&filter=market%3Astock"
if country_code:
    NEWS_API_URL = f"{base_url}&filter=market_country%3A{country_code}&client=screener&streaming=true"
    news_flow_symbol = f"news-flow?market=stock&market_country={country_code.lower()}"
else:
    NEWS_API_URL = f"{base_url}&client=screener&streaming=true"
    news_flow_symbol = "news-flow?market=stock"

STORY_API_URL = "https://news-headlines.tradingview.com/v3/story"

search_query = st.text_input("", "", placeholder="🔍 Symbol or keyword", key="news_search", label_visibility="collapsed")

# Custom CSS for compact search box
st.markdown("""
<style>
div[data-testid="stTextInput"] input {
    min-width: 110px;
    width: 100%;
    max-width: none;
    font-size: 1.05rem;
    padding: 0.32em 0.8em;
    border-radius: 7px;
    border: 1.5px solid #b0b8c5;
    background: #fff;
    color: #222;
    margin-left: 0;
    margin-right: 0;
    display: block;
    box-shadow: 0 1px 8px 0 rgba(34,62,86,0.07);
}
</style>
""", unsafe_allow_html=True)

# Ensure session state is initialized at the very top
if 'realtime_news' not in st.session_state:
    st.session_state['realtime_news'] = []

def generate_session_id():
    # Generate a random session ID similar to TradingView's format
    random_num = ''.join(random.choices(string.digits, k=5))
    random_str = ''.join(random.choices(string.ascii_lowercase, k=5))
    return f"0.{random_num}.{int(time.time())}_sin1-charts-free-3-tvbs-{random_str}-2"

# WebSocket message handler
def on_message(ws, message):
    if message.startswith("~h~"):
        # Ignore heartbeat
        return
    print(f"[WebSocket] Received raw message: {message}")  # Terminal log
    st.write(f"Received raw message: {message}")  # Debug log
    if message.startswith('~m~'):
        # Extract the length prefix
        first_tilde = message.find('~m~')
        second_tilde = message.find('~m~', first_tilde + 3)
        length = int(message[first_tilde + 3:second_tilde])
        content = message[second_tilde + 3:second_tilde + 3 + length]
        print(f"[WebSocket] Extracted content: {content}")
        try:
            data = json.loads(content)
            print(f"[WebSocket] Parsed data: {data}")  # Terminal log
            st.write(f"Parsed data: {data}")  # Debug log
            # Log any error or info messages from the server
            if isinstance(data, dict) and (data.get('m') == 'error' or data.get('m') == 'info'):
                print(f"[WebSocket] Server message: {data}")
            # If we receive news data, add it to the session state
            if isinstance(data, dict) and ('headline' in data or 'title' in data):
                print(f"[WebSocket] Received news data: {data}")  # Terminal log
                st.write("Received news data, updating session state...")  # Debug log
                st.session_state['realtime_news'].append(data)
            # Keep only the latest 20
            st.session_state['realtime_news'] = st.session_state['realtime_news'][-20:]
            st.rerun()  # Force UI update
        except json.JSONDecodeError:
            print(f"[WebSocket] JSON decode error for content: {content}")
            st.write(f"Raw content: {content}")  # Debug log
    else:
        print(f"[WebSocket] Non-standard message: {message}")

def on_error(ws, error):
    print(f"[WebSocket] WebSocket error: {str(error)}")
    st.error(f"WebSocket error: {str(error)}")

def on_close(ws, close_status_code, close_msg):
    print(f"[WebSocket] WebSocket connection closed. Code: {close_status_code}, Message: {close_msg}")
    st.warning(f"WebSocket connection closed. Code: {close_status_code}, Message: {close_msg}")
    # Try to reconnect after a delay
    time.sleep(5)
    start_ws()

def on_open(ws):
    st.success("WebSocket connection established")
    session_id = 'qs_' + ''.join(random.choices(string.ascii_letters + string.digits, k=12))
    st.session_state['tv_quote_session_id'] = session_id
    quote_create_msg = {"m": "quote_create_session", "p": [session_id]}
    msg1 = f'~m~{len(json.dumps(quote_create_msg))}~m~{json.dumps(quote_create_msg)}'
    ws.send(msg1)
    time.sleep(1)
    add_symbols_msg = {"m": "quote_add_symbols", "p": [session_id, news_flow_symbol]}
    msg2 = f'~m~{len(json.dumps(add_symbols_msg))}~m~{json.dumps(add_symbols_msg)}'
    ws.send(msg2)

def start_ws():
    try:
        now = datetime.now(timezone.utc)
        date_str = now.strftime('%Y_%m_%d-%H_%M')
        ws_url = (
            "wss://data.tradingview.com/socket.io/websocket"
            "?from=news-flow%2F"
            "&market=stock"
            f"{'&market_country=' + country_code if country_code else ''}"
            f"&date={date_str}"
            "&EIO=3"
            "&transport=websocket"
        )
        ws = websocket.WebSocketApp(
            ws_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            header={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://in.tradingview.com/",
                "Origin": "https://in.tradingview.com",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache"
            }
        )
        ws_thread = threading.Thread(target=ws.run_forever, kwargs={'ping_interval': 30, 'ping_timeout': 10})
        ws_thread.daemon = True
        ws_thread.start()
        return ws_thread
    except Exception as e:
        st.error(f"Error in start_ws: {str(e)}")
        time.sleep(5)
        return start_ws()

# Initialize session state for WebSocket
if 'ws_thread' not in st.session_state:
    st.session_state['ws_thread'] = None

# Add a debug section to show connection status
st.sidebar.markdown("### Debug Info")
if st.session_state['ws_thread'] and st.session_state['ws_thread'].is_alive():
    st.sidebar.success("WebSocket thread is running")
else:
    st.sidebar.warning("WebSocket thread not running")

# Add a manual refresh button
if st.sidebar.button("🔄 Refresh Connection"):
    if st.session_state['ws_thread']:
        st.session_state['ws_thread'] = None
    st.rerun()

# Start or restart WebSocket if needed
if not st.session_state['ws_thread'] or not st.session_state['ws_thread'].is_alive():
    st.session_state['ws_thread'] = start_ws()

# Run the autorefresh every 4 seconds
count = st_autorefresh(interval=4000, key="news_refresh")

# Add auto-refresh every 5 seconds
st_autorefresh(interval=5000, key="news_autorefresh")

# Fetch news from TradingView API with caching
@st.cache_data(show_spinner=False)
def fetch_news():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://in.tradingview.com/",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    resp = requests.get(NEWS_API_URL, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()

# Add a manual refresh button
refresh = st.button('🔄 Refresh News', key='refresh_news')
if refresh:
    st.cache_data.clear()

data = fetch_news()
stories = data.get('items', [])

if stories:
    try:
        for item in stories:
            story_id = item.get('id')
            title = item.get('headline') or item.get('title')
            # Convert 'Bln Rupees' to Crore Rupees in the headline
            def convert_bln_to_crore(match):
                val = float(match.group(1))
                crore = int(round(val * 100))
                return f"₹{crore} Crore"
            def convert_mln_to_lakh_or_crore(match):
                val = float(match.group(1))
                lakh = val * 10
                if lakh >= 100:
                    crore = lakh / 100
                    # Show up to 2 decimal places if needed
                    if crore == int(crore):
                        crore_str = f"{int(crore)}"
                    else:
                        crore_str = f"{crore:.2f}".rstrip('0').rstrip('.')
                    return f"₹{crore_str} Crore"
                else:
                    # Show up to 2 decimal places if needed
                    if lakh == int(lakh):
                        lakh_str = f"{int(lakh)}"
                    else:
                        lakh_str = f"{lakh:.2f}".rstrip('0').rstrip('.')
                    return f"₹{lakh_str} Lakh"
            if title:
                # Replace all 'Bln Rupees' with crores
                title = re.sub(r"(\d+(?:\.\d+)?)\s*Bln Rupees", convert_bln_to_crore, title)
                # Replace all 'Mln Rupees' with lakhs or crores
                title = re.sub(r"(\d+(?:\.\d+)?)\s*Mln Rupees", convert_mln_to_lakh_or_crore, title)
            source = item.get('source', {}).get('display_name', '') if 'source' in item else ''
            ts = item.get('published', '')
            # Filter by search query (title/headline or related symbol, partial/case-insensitive)
            if search_query:
                query = search_query.lower().strip()
                symbol_match = False
                if 'relatedSymbols' in item and item['relatedSymbols']:
                    for s in item['relatedSymbols']:
                        symbol_val = str(s.get('symbol','')).lower()
                        if query in symbol_val:
                            symbol_match = True
                            break
                if not ((title and query in title.lower()) or symbol_match):
                    continue
            if story_id and title:
                # Beautiful card layout for news item
                card_html = """
                <div style="
                  background: #fff;
                  border-radius: 12px;
                  box-shadow: 0 1px 8px 0 rgba(60,72,90,0.06);
                  border: 1px solid #f0f0f0;
                  margin-bottom: 1.2rem;
                  padding: 1.1rem 1.3rem 1.1rem 1.3rem;
                  display: flex;
                  align-items: flex-start;
                  gap: 1.0rem;
                  transition: box-shadow 0.18s;
                ">
                  <div style="flex: 1;">
                    <div style="font-size:1.07rem;font-weight:600;color:#222;line-height:1.5;margin-bottom:0.28rem;">{title}</div>
                    {story_link}
                    <div style="margin: 0.3rem 0 0.15rem 0;">
                      <span style='color:#888;font-size:0.92rem;'>Published: {published}</span>
                      {urgency}
                    </div>
                    {badges}
                  </div>
                  <div style="text-align:center;min-width:70px;">
                    {provider_logo}

                  </div>
                </div>
                """
                # Prepare fields
                story_link = ""
                if 'storyPath' in item and item['storyPath']:
                    link = f"https://in.tradingview.com{item['storyPath']}"
                    story_link = f"<a href='{link}' target='_blank' style='color:#6EC1E4;font-weight:600;text-decoration:none;'>Read full story &#8599;</a>"
                published = ""
                if 'published' in item:
                    dt = datetime.fromtimestamp(item['published'])
                    published = dt.strftime('%Y-%m-%d %H:%M')
                urgency = ""
                if 'urgency' in item and item['urgency']:
                    urgency = f"<span style='color:#FF6B6B;font-size:0.98rem;margin-left:1rem;'>Urgency: {item['urgency']}</span>"
                badges = ""
                import urllib.parse
                if 'relatedSymbols' in item and item['relatedSymbols']:
                    badges = '<div style="margin-top:0.6rem; display: flex; flex-wrap: wrap; gap: 8px 8px;">' + ''.join([
                        f"<a href='https://in.tradingview.com/chart/?symbol={urllib.parse.quote(s.get('symbol',''))}&interval=D' target='_blank' rel='noopener'><span style='background:#3498db;color:#fff;border-radius:6px;padding:4px 12px;font-size:0.93rem;font-weight:500;display:inline-block;margin-bottom:4px;cursor:pointer;text-decoration:none;'>{s.get('symbol','')}</span></a>"
                        for s in item['relatedSymbols']]) + '</div>'
                provider_logo = ""
                provider_name = ""
                if 'provider' in item and item['provider']:
                    prov = item['provider']
                    provider_name = prov.get('name','')
                    provider_id = prov.get('id','').lower() if 'id' in prov else ''
                    # Use special logo for known providers
                    logo_map = {
                        
                        'reuters': 'https://s3.tradingview.com/news/logo/reuters--theme-light.svg',
                        'market-watch': 'https://s3.tradingview.com/news/logo/market-watch--theme-light.svg',
                        'dow-jones': 'https://s3.tradingview.com/news/logo/dow-jones--theme-light.svg',
                        'trading-economics': 'https://s3.tradingview.com/news/logo/trading-economics--theme-light.svg',
                        'forexlive': 'https://s3.tradingview.com/news/logo/forexlive--theme-light.svg',
                        'globenewswire': 'https://s3.tradingview.com/news/logo/globenewswire--theme-light.svg',
                        'gurufocus': 'https://s3.tradingview.com/news/logo/gurufocus--theme-light.svg',
                        'hse': 'https://s3.tradingview.com/news/logo/hse--theme-light.svg',
                        'ice': 'https://s3.tradingview.com/news/logo/ice--theme-light.svg',
                        'moneycontrol': 'https://s3.tradingview.com/news/logo/moneycontrol--theme-light.svg',
                        'mt-newswires': 'https://s3.tradingview.com/news/logo/mtnewswires--theme-light.svg',
                        'tradingview': 'https://s3.tradingview.com/news/logo/tradingview--theme-light.svg',
                        'marketbeat': 'https://s3.tradingview.com/news/logo/marketbeat--theme-light.svg',
                        'barchart': 'https://s3.tradingview.com/news/logo/barchart--theme-light.svg',
                        'cointelegraph': 'https://s3.tradingview.com/news/logo/cointelegraph--theme-light.svg',
                        'beincrypto': 'https://s3.tradingview.com/news/logo/beincrypto--theme-light.svg',
                        'zacks': 'https://s3.tradingview.com/news/logo/zacks--theme-light.svg',
                        'marketindex': 'https://s3.tradingview.com/news/logo/marketindex--theme-light.svg',
                        '11thestate': 'https://s3.tradingview.com/news/logo/11thestate--theme-light.svg',
                        'acceswire': 'https://s3.tradingview.com/news/logo/acceswire--theme-light.svg',
                        'acn': 'https://s3.tradingview.com/news/logo/acn--theme-light.svg',
                        'coindar': 'https://s3.tradingview.com/news/logo/coindar--theme-light.svg',
                        'coinmarketcal': 'https://s3.tradingview.com/news/logo/coinmarketcal--theme-light.svg',
                        'congressional_quarterly': 'https://s3.tradingview.com/news/logo/congressional_quarterly--theme-light.svg',
                        'cse': 'https://s3.tradingview.com/news/logo/cse--theme-light.svg',
                        'cryptobriefing': 'https://s3.tradingview.com/news/logo/cryptobriefing--theme-light.svg',
                        'cryptoglobe': 'https://s3.tradingview.com/news/logo/cryptoglobe--theme-light.svg',
                        'cryptonews': 'https://s3.tradingview.com/news/logo/cryptonews--theme-light.svg',
                        'cryptopotato': 'https://s3.tradingview.com/news/logo/cryptopotato--theme-light.svg',
                        'dailyfx': 'https://s3.tradingview.com/news/logo/dailyfx--theme-light.svg',
                        'etfcom': 'https://s3.tradingview.com/news/logo/etfcom--theme-light.svg',
                        'financemagnates': 'https://s3.tradingview.com/news/logo/financemagnates--theme-light.svg',
                        'financial_juice': 'https://s3.tradingview.com/news/logo/financial_juice--theme-light.svg',
                        'forexlive': 'https://s3.tradingview.com/news/logo/forexlive--theme-light.svg',
                        'globenewswire': 'https://s3.tradingview.com/news/logo/globenewswire--theme-light.svg',
                        'gurufocus': 'https://s3.tradingview.com/news/logo/gurufocus--theme-light.svg',
                        'hse': 'https://s3.tradingview.com/news/logo/hse--theme-light.svg',
                        'ice': 'https://s3.tradingview.com/news/logo/ice--theme-light.svg',
                        'investorplace': 'https://s3.tradingview.com/news/logo/investorplace--theme-light.svg',
                        'invezz': 'https://s3.tradingview.com/news/logo/invezz--theme-light.svg',
                        'jcn': 'https://s3.tradingview.com/news/logo/jcn--theme-light.svg',
                        'leverage_shares': 'https://s3.tradingview.com/news/logo/leverage_shares--theme-light.svg',
                        'lse': 'https://s3.tradingview.com/news/logo/lse--theme-light.svg',
                        'macenews': 'https://s3.tradingview.com/news/logo/macenews--theme-light.svg',
                        'miranda_partners': 'https://s3.tradingview.com/news/logo/miranda_partners--theme-light.svg',
                        'modular_finance': 'https://s3.tradingview.com/news/logo/modular_finance--theme-light.svg',
                        'nbd': 'https://s3.tradingview.com/news/logo/nbd--theme-light.svg',
                        'newsbtc': 'https://s3.tradingview.com/news/logo/newsbtc--theme-light.svg',
                        'newsfilecorp': 'https://s3.tradingview.com/news/logo/newsfilecorp--theme-light.svg',
                        'obi': 'https://s3.tradingview.com/news/logo/obi--theme-light.svg',
                        'polish_emitent': 'https://s3.tradingview.com/news/logo/polish_emitent--theme-light.svg',
                        'polymerupdate': 'https://s3.tradingview.com/news/logo/polymerupdate--theme-light.svg',
                        'pressetext': 'https://s3.tradingview.com/news/logo/pressetext--theme-light.svg',
                        'rse': 'https://s3.tradingview.com/news/logo/rse--theme-light.svg',
                        'see_news': 'https://s3.tradingview.com/news/logo/see_news--theme-light.svg',
                        'smallcaps': 'https://s3.tradingview.com/news/logo/smallcaps--theme-light.svg',
                        'stocknews': 'https://s3.tradingview.com/news/logo/stocknews--theme-light.svg',
                        'tlse': 'https://s3.tradingview.com/news/logo/tlse--theme-light.svg',
                        'the_block': 'https://s3.tradingview.com/news/logo/the_block--theme-light.svg',
                        'thenewswire': 'https://s3.tradingview.com/news/logo/thenewswire--theme-light.svg',
                        'todayq': 'https://s3.tradingview.com/news/logo/todayq--theme-light.svg',
                        'u_today': 'https://s3.tradingview.com/news/logo/u_today--theme-light.svg',
                        'valuewalk': 'https://s3.tradingview.com/news/logo/valuewalk--theme-light.svg',
                        'zawya': 'https://s3.tradingview.com/news/logo/zawya--theme-light.svg',
                        'zycrypto': 'https://s3.tradingview.com/news/logo/zycrypto--theme-light.svg',
                        'london-stock-exchange': 'https://s3.tradingview.com/news/logo/london-stock-exchange--theme-light.svg',
                        'rdp-lse': 'https://s3.tradingview.com/news/logo/rdp-lse--theme-light.svg',
                    }
                    if provider_id in logo_map:
                        provider_logo = f"<img src='{logo_map[provider_id]}' style='max-width:80px;max-height:54px;width:auto;height:auto;display:block;margin:0 auto 8px auto;background:#fff;padding:3px;border-radius:10px;' alt='{provider_name} logo'/>"
                    else:
                        logo_id = prov.get('logo_id')
                        if logo_id:
                            # Use an <img> tag with onerror fallback to initials
                            initials = provider_name[:2].upper() if provider_name else "?"
                            provider_logo = f"<img src='https://s3-symbol-logo.tradingview.com/{logo_id}.svg' style='width:60px;height:60px;border-radius:50%;background:#fff;padding:3px 3px;' alt='{provider_name} logo' onerror=\"this.onerror=null;this.style.display='none';document.getElementById('prov_{story_id}').style.display='flex';\">"
                            provider_logo += f"<div id='prov_{story_id}' style='display:none;justify-content:center;align-items:center;width:60px;height:60px;border-radius:50%;background:#6EC1E4;color:#fff;font-size:1.6rem;font-weight:bold;'>{initials}</div>"
                        else:
                            initials = provider_name[:2].upper() if provider_name else "?"
                            provider_logo = f"<div style='display:flex;justify-content:center;align-items:center;width:48px;height:48px;border-radius:50%;background:#6EC1E4;color:#fff;font-size:1.4rem;font-weight:bold;'>{initials}</div>"
                st.markdown(card_html.format(
                    title=title,
                    story_link=story_link,
                    published=published,
                    urgency=urgency,
                    badges=badges,
                    provider_logo=provider_logo,
                    provider_name=provider_name
                ), unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Failed to fetch news: {e}")
else:
    st.warning("No news headlines found in the 'items' array. TradingView may have changed their API.")

# --- Real-Time TradingView News via Socket.IO ---

def get_ws_url():
    now = datetime.now(timezone.utc)
    date_str = now.strftime('%Y_%m_%d-%H_%M')
    return (
        "wss://data.tradingview.com/socket.io/"
        "?from=news-flow%2F"
        "&market=stock"
        f"{'&market_country=' + country_code if country_code else ''}"
        f"&date={date_str}&EIO=3&transport=websocket"
    )

sio = None

def start_socketio():
    global sio
    sio = socketio.Client(logger=True, engineio_logger=True, reconnection=True)

    @sio.event
    def connect():
        st.success("Socket.IO connection established")
        # Emit join message to subscribe to the correct news-flow room for selected country
        sio.emit('join', {'room': news_flow_symbol})

    @sio.event
    def disconnect():
        st.warning("Socket.IO connection disconnected")

    @sio.on('*')
    def catch_all(event, data):
        st.info(f"Received event: {event}")

    @sio.on('news')
    def on_news(data):
        try:
            if isinstance(data, dict):
                st.session_state['realtime_news'].append(data)
                st.session_state['realtime_news'] = st.session_state['realtime_news'][-20:]
        except Exception as e:
            st.error(f"Error processing news: {str(e)}")

    try:
        ws_url = get_ws_url()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://in.tradingview.com/",
            "Origin": "https://in.tradingview.com"
        }
        sio.connect(ws_url, transports=['websocket'], headers=headers)
        sio.wait()
    except Exception as e:
        st.error(f"Socket.IO connection error: {str(e)}")

if 'wsio_thread_started' not in st.session_state:
    wsio_thread = threading.Thread(target=start_socketio, daemon=True)
    wsio_thread.start()
    st.session_state['wsio_thread_started'] = True

# Display real-time news (parsed)
st.markdown("""
### 
""")
with st.expander("Show latest real-time news (parsed)"):
    for item in reversed(st.session_state['realtime_news']):
        if isinstance(item, dict):
            title = item.get('headline') or item.get('title') or str(item)
            published = item.get('published')
            if published:
                try:
                    dt = datetime.fromtimestamp(published)
                    published = dt.strftime('%Y-%m-%d %H:%M')
                except Exception:
                    pass
            st.markdown(f"**{title}**")
            if published:
                st.caption(f"Published: {published}")
            st.markdown('---')
        else:
            st.code(str(item))

def listen_pushstream():
    def on_message(ws, message):
        print("[Pushstream] Received:", message)
    def on_error(ws, error):
        print("[Pushstream] Error:", error)
    def on_close(ws, close_status_code, close_msg):
        print("[Pushstream] Closed:", close_status_code, close_msg)
    def on_open(ws):
        print("[Pushstream] WebSocket opened")
    ws = websocket.WebSocketApp(
        "wss://pushstream.tradingview.com/message-pipe-ws/public",
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        header={
            "Origin": "https://in.tradingview.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
        }
    )
    ws.run_forever()

# Optionally, run this in a separate thread so it doesn't block the main app
import threading
if 'pushstream_thread_started' not in st.session_state:
    pushstream_thread = threading.Thread(target=listen_pushstream, daemon=True)
    pushstream_thread.start()
    st.session_state['pushstream_thread_started'] = True