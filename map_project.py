import streamlit as st
import numpy as np
import folium
from streamlit_folium import st_folium
import base64
import os

# 1. PAGE SETUP
st.set_page_config(page_title="SBEU 3893 - Molodensky DMS Module", page_icon="📍", layout="wide")

# 2. CUSTOM STYLING (Steel Blue Theme)
def set_bg_local(main_bg):
    if os.path.exists(main_bg):
        with open(main_bg, "rb") as f:
            bin_str = base64.b64encode(f.read()).decode()
        st.markdown(f"""
            <style>
            .stApp {{ background-image: url("data:image/png;base64,{bin_str}"); background-size: cover; background-attachment: fixed; }}
            [data-testid="stSidebar"] {{ background-color: #4682B4 !important; }}
            [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] p {{ color: white !important; }}
            .main .block-container {{ background-color: rgba(255, 255, 255, 0.93); padding: 2rem; border-radius: 20px; margin-top: 20px; }}
            iframe {{ width: 100% !important; border-radius: 10px; }}
            </style>
            """, unsafe_allow_html=True)

if os.path.exists('background.jpg'):
    set_bg_local('background.jpg')

# 3. HELPER FUNCTION: DECIMAL TO DMS
def decimal_to_dms(deg, is_lat=True):
    abs_deg = abs(deg)
    d = int(abs_deg)
    m = int((abs_deg - d) * 60)
    s = (abs_deg - d - m/60) * 3600
    if is_lat:
        direction = "N" if deg >= 0 else "S"
    else:
        direction = "E" if deg >= 0 else "W"
    return f"{d}° {m}' {s:.4f}\" {direction}"

# 4. MATH ENGINE: SIMPLE MOLODENSKY
def simple_molodensky_horizontal(lat, lon, h, dx, dy, dz):
    a, f = 6378137.0, 1/298.257223563
    a_
