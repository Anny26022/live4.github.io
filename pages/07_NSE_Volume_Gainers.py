import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(
    page_title="NSE Volume Gainers",
    layout="centered",
    initial_sidebar_state="auto"
)

st.markdown("""
<div style='display:flex;align-items:center;justify-content:center;margin-bottom:0.5em;'>
  <svg xmlns='http://www.w3.org/2000/svg' width='48' height='48' viewBox='0 0 48 48' fill='none' style='margin-right:16px;'>
    <rect width='48' height='48' rx='12' fill='url(#vol-bg)'/>
    <g>
      <rect x='14' y='20' width='4' height='12' rx='2' fill='#29b6f6'/>
      <rect x='22' y='16' width='4' height='16' rx='2' fill='#43a047'/>
      <rect x='30' y='24' width='4' height='8' rx='2' fill='#ab47bc'/>
    </g>
    <defs>
      <linearGradient id='vol-bg' x1='0' y1='0' x2='48' y2='48' gradientUnits='userSpaceOnUse'>
        <stop stop-color='#23272F'/>
        <stop offset='1' stop-color='#181A20'/>
      </linearGradient>
    </defs>
  </svg>
  <span style='font-size:2.5rem;font-weight:700;color:#fff;'>NSE Volume Gainers</span>
</div>
<p style='text-align:center;margin-top:-0.75em;margin-bottom:2em;color:#aaa;font-size:1.1rem;'>Spot stocks with unusual volume spikes</p>
""", unsafe_allow_html=True)

st.markdown("""
<div style='background:linear-gradient(90deg,#fff0e1,#ffe8e8);border-radius:14px;padding:1.4em 1.8em;margin-bottom:1.6em;border:2px solid #ffd6cc;box-shadow:0 4px 18px rgba(255,111,97,0.12);display:flex;align-items:center;gap:1.2em;'>
  <span style='font-size:2.4rem;line-height:1.1;'>🚧</span>
  <span style='color:#b23c17;font-size:1.28rem;font-weight:700;'>This page is currently under development and is currently not working.<br>All features are temporarily disabled.</span>
</div>
""", unsafe_allow_html=True)
