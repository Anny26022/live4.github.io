import streamlit as st

st.set_page_config(
    page_title="NSE Past IPO Issues",
    layout="centered",
    initial_sidebar_state="auto"
)

st.markdown("""
<div style='background:linear-gradient(90deg,#fff0e1,#ffe8e8);border-radius:14px;padding:1.4em 1.8em;margin-bottom:1.6em;border:2px solid #ffd6cc;box-shadow:0 4px 18px rgba(255,111,97,0.12);display:flex;align-items:flex-start;gap:1.2em;'>
  <span style='font-size:2.4rem;line-height:1.1;'>🚧</span>
  <div>
    <span style='color:#b23c17;font-size:1.22rem;font-weight:700;'>All features on this page are temporarily disabled.<br>Please check back later.</span>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style='display:flex;align-items:center;justify-content:center;margin-bottom:0.5em;'>
  <svg xmlns='http://www.w3.org/2000/svg' width='48' height='48' viewBox='0 0 48 48' fill='none' style='margin-right:16px;'>
    <rect width='48' height='48' rx='12' fill='url(#ipo-bg)'/>
    <g>
      <circle cx='24' cy='24' r='12' fill='#ff9800' fill-opacity='0.85'/>
      <path d='M24 14v10l8 5' stroke='#fff' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/>
    </g>
    <defs>
      <linearGradient id='ipo-bg' x1='0' y1='0' x2='48' y2='48' gradientUnits='userSpaceOnUse'>
        <stop stop-color='#23272F'/>
        <stop offset='1' stop-color='#181A20'/>
      </linearGradient>
    </defs>
  </svg>
  <span style='font-size:2.5rem;font-weight:700;color:#fff;'>NSE Past IPO Issues</span>
</div>
<p style='text-align:center;margin-top:-0.75em;margin-bottom:2em;color:#aaa;font-size:1.1rem;'>Historic IPOs and their market performance</p>
""", unsafe_allow_html=True)
