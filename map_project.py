import streamlit as st
import numpy as np
import folium
from streamlit_folium import st_folium
import base64
import os

# 1. PAGE SETUP
st.set_page_config(page_title="SBEU 3893 - Geomatics Suite", page_icon="📍", layout="wide")

# 2. CUSTOM STYLING (Steel Blue)
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

# 3. MATH ENGINE: UTM PROJECTION (Zone 50N - Sabah)
def latlon_to_utm(lat, lon):
    # WGS84 / GRS80 Ellipsoid
    a = 6378137.0
    f = 1/298.257223563
    k0 = 0.9996 # UTM Scale Factor
    
    phi = np.radians(lat)
    lam = np.radians(lon)
    lam0 = np.radians(117.0) # Central Meridian for Zone 50
    
    e2 = 2*f - f**2
    n = f / (2 - f)
    A = a / (1 + n) * (1 + (n**2)/4 + (n**4)/64)
    
    t = np.sinh(np.arctanh(np.sin(phi)) - (2*np.sqrt(n)/(1+n)) * np.arctanh(2*np.sqrt(n)/(1+n) * np.sin(phi)))
    xi = np.arctan(t / np.cos(lam - lam0))
    eta = np.arctanh(np.sin(lam - lam0) / np.sqrt(1 + t**2))
    
    east = 500000 + k0 * A * (eta + (n/2)*np.sin(2*xi)*np.cosh(2*eta))
    north = k0 * A * (xi + (n/2)*np.cos(2*xi)*np.sinh(2*eta))
    
    return east, north

# 4. MATH ENGINE: BORNEO RSO (Hotine Oblique Mercator)
def latlon_to_borneo_rso(lat, lon):
    a = 6378137.0
    f = 1/298.257222101
    k0 = 0.99984
    phi0, lam0 = np.radians(4.0), np.radians(115.0)
    gamma0 = np.radians(18.745783)
    
    e2 = 2*f - f**2
    e = np.sqrt(e
