import streamlit as st
import numpy as np
import base64
import os

# 1. PAGE SETUP
st.set_page_config(page_title="SBEU 3893 - Borneo RSO Module", page_icon="📍", layout="wide")

# 2. CUSTOM STYLING (Darker Steel Blue)
def set_bg_local(main_bg):
    if os.path.exists(main_bg):
        with open(main_bg, "rb") as f:
            bin_str = base64.b64encode(f.read()).decode()
        st.markdown(f"""
            <style>
            .stApp {{
                background-image: url("data:image/png;base64,{bin_str}");
                background-size: cover;
                background-attachment: fixed;
            }}
            [data-testid="stSidebar"] {{
                background-color: #4682B4 !important;
            }}
            [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] p {{
                color: white !important;
            }}
            .main .block-container {{
                background-color: rgba(255, 255, 255, 0.93);
                padding: 3rem;
                border-radius: 25px;
                margin-top: 30px;
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            }}
            </style>
            """, unsafe_allow_html=True)

if os.path.exists('background.jpg'):
    set_bg_local('background.jpg')

# 3. SIDEBAR: PARAMETERS & TOGGLE
if os.path.exists("utm.png"):
    st.sidebar.image("utm.png", use_container_width=True)

st.sidebar.title("⚙️ Engine Settings")
ellipsoid_choice = st.sidebar.radio(
    "Select Reference Ellipsoid:",
    ("WGS84 (Global)", "Everest 1830 (Modified/Timbalai)")
)

st.sidebar.divider()
st.sidebar.header("⚙️ 7-Parameter Datum Shift")
dx = st.sidebar.number_input("dX (m)", value=596.096, format="%.3f")
dy = st.sidebar.number_input("dY (m)", value=-624.512, format="%.3f")
dz = st.sidebar.number_input("dZ (m)", value=2.779, format="%.3f")
rx_s = st.sidebar.number_input("rX (sec)", value=-1.44646, format="%.5f")
ry_s = st.sidebar.number_input("rY (sec)", value=-0.88312, format="%.5f")
rz_s = st.sidebar.number_input("rZ (sec)", value=1.82844, format="%.5f")
scale_p = st.sidebar.number_input("Scale (ppm)", value=-10.454, format="%.4f")

# Define active ellipsoid parameters
if ellipsoid_choice == "WGS84 (Global)":
    a_active = 6378137.0
    finv_active = 298.257223563
else:
    a_active = 6377298.556
    finv_active = 300.8017

f_active = 1 / finv_active
e2_active = (2 * f_active) - (f_active ** 2)

# 4. MATH ENGINES
def bursa_wolf_transform(lat, lon, h, dx, dy, dz, rx_s, ry_s, rz_s, s_ppm):
    # WGS84 Constants
    a_w = 6378137.0; f_w = 1/298.257223563; e2w = 2*f_w - f_w**2
    phi = np.radians(lat); lam = np.radians(lon)
    N = a_w / np.sqrt(1 - e2w * np.sin(phi)**2)
    
    # Geodetic to Cartesian (WGS84)
    Xw = (N + h) * np.cos(phi) * np.cos(lam)
    Yw = (N + h) * np.cos(phi) * np.sin(lam)
    Zw = (N * (1 - e2w) + h) * np.sin(phi)
    
    # Transform
    S = 1 + s_ppm/1e6
    rx = np.radians(rx_s/3600); ry = np.radians(ry_s/3600); rz = np.radians(rz_s/3600)
    R = np.array([[1, -rz, ry], [rz, 1, -rx], [-ry, rx, 1]])
    
    P_local = np.array([dx, dy, dz]) + S * (R @ np.array([Xw, Yw, Zw]))
    
    # Cartesian to Geodetic (Everest 1830)
    x, y, z = P_local
    lon_t = np.arctan2(y, x)
    p = np.sqrt(x**2 + y**2)
    phi_t = np.arctan2(z, p * (1 - e
