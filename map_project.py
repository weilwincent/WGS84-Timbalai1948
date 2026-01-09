import streamlit as st
import numpy as np
import folium
from streamlit_folium import st_folium
import base64
import os

# 1. PAGE SETUP
st.set_page_config(page_title="SBEU 3893 - Geomatics Transformation", page_icon="📍", layout="wide")

# 2. CUSTOM STYLING (UTM Corporate Colors)
def set_bg_local(main_bg):
    if os.path.exists(main_bg):
        with open(main_bg, "rb") as f:
            bin_str = base64.b64encode(f.read()).decode()
        st.markdown(f"""
            <style>
            .stApp {{ background-image: url("data:image/png;base64,{bin_str}"); background-size: cover; background-attachment: fixed; }}
            [data-testid="stSidebar"] {{ background-color: #800000 !important; }} /* UTM Maroon */
            [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] p {{ color: #FFD700 !important; }} /* UTM Gold */
            .main .block-container {{ background-color: rgba(255, 255, 255, 0.95); padding: 2rem; border-radius: 20px; border: 2px solid #800000; }}
            iframe {{ width: 100% !important; border-radius: 10px; border: 1px solid #800000; }}
            </style>
            """, unsafe_allow_html=True)

if os.path.exists('background.jpg'):
    set_bg_local('background.jpg')

# 3. INITIALIZE SESSION STATE
if 'results' not in st.session_state:
    st.session_state.results = None
if 'balloons_fired' not in st.session_state:
    st.session_state.balloons_fired = False

# 4. MATH ENGINE: BURSA-WOLF 7-PARAMETER
def bursa_wolf_transform(lat, lon, h, dx, dy, dz, rx_s, ry_s, rz_s, s_ppm):
    # WGS84 Constants
    a_w, f_inv_w = 6378137.0, 298.257223563
    f_w = 1/f_inv_w
    e2w = (2*f_w) - (f_w**2)
    
    phi, lam = np.radians(lat), np.radians(lon)
    N = a_w / np.sqrt(1 - e2w * np.sin(phi)**2)
    
    # Geodetic to Cartesian
    Xw = (N + h) * np.cos(phi) * np.cos(lam)
    Yw = (N + h) * np.cos(phi) * np.sin(lam)
    Zw = (N * (1 - e2w) + h) * np.sin(phi)
    P_wgs = np.array([Xw, Yw, Zw])
    
    # 7-Parameter Transformation Logic
    T = np.array([dx, dy, dz])
    S = 1 + (s_ppm / 1000000)
    rx, ry, rz = np.radians(rx_s/3600), np.radians(ry_s/3600), np.radians(rz_s/3600)
    R = np.array([
        [1, rz, -ry],
        [-rz, 1, rx],
        [ry, -rx, 1]
    ])
    P_local = T + S * (R @ P_wgs)
    return P_local

# 5. SIDEBAR: LINK LOCAL UTM LOGO
if os.path.exists("utm.png"):
    st.sidebar.image("utm.png", use_container_width=True)
else:
    st.sidebar.title("📍 UTM GEOMATICS")

st.sidebar.divider()
st.sidebar.title("⚙️ Parameters")
dx = st.sidebar.number_input("dX (m)", value=596.096, format="%.3f")
dy = st.sidebar.number_input("dY (m)", value=-624.512, format="%.3f")
dz = st.sidebar.number_input("dZ (m)", value=2.779, format="%.3f")
rx_s = st.sidebar.number_input("rX (arc-sec)", value=-1.446460, format="%.6f")
ry_s = st.sidebar.number_input("rY (arc-sec)", value=-0.883120, format="%.6f")
rz_s = st.sidebar.number_input("rZ (arc-sec)", value=1.828440, format="%.6f")
scale_p = st.sidebar.number_input("Scale (ppm)", value=-10.454, format="%.6f")

# 6. MAIN UI
st.title("🛰️ Professional 7-Parameter Transformation Module")
st.write("SBEU 3893 - Geomatics Creative Map and Innovation Competition 20
