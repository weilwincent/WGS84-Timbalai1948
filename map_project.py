import streamlit as st
import numpy as np
import folium
from streamlit_folium import st_folium
import base64
import os

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="SBEU 3893 - Geomatics Suite", page_icon="📍", layout="wide")

# 2. GAYA VISUAL (Steel Blue Theme)
def set_bg_local(main_bg):
    if os.path.exists(main_bg):
        with open(main_bg, "rb") as f:
            bin_str = base64.b64encode(f.read()).decode()
        st.markdown(f"""
            <style>
            .stApp {{ background-image: url("data:image/png;base64,{bin_str}"); background-size: cover; background-attachment: fixed; }}
            [data-testid="stSidebar"] {{ background-color: #4682B4 !important; }}
            [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] p {{ color: white !important; }}
            .main .block-container {{ background-color: rgba(255, 255, 255, 0.95); padding: 2rem; border-radius: 20px; border: 1px solid #ddd; }}
            .result-card {{ background-color: #f0f8ff; padding: 15px; border-radius: 10px; border-left: 5px solid #800000; margin-bottom: 10px; }}
            .result-label {{ color: #800000; font-weight: bold; font-size: 14px; margin-bottom: 5px; }}
            .result-value {{ color: #333; font-size: 18px; font-family: 'Courier New', monospace; font-weight: bold; }}
            iframe {{ width: 100% !important; border-radius: 10px; }}
            </style>
            """, unsafe_allow_html=True)

if os.path.exists('background.jpg'):
    set_bg_local('background.jpg')

# 3. ENJIN MATEMATIK: UTM (
