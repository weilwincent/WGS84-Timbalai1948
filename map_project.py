import streamlit as st
import numpy as np
import base64
import os

# 1. PAGE SETUP - Fixed: changed set_config to set_page_config
st.set_page_config(page_title="SBEU 3893 - Final Master Module", page_icon="📍", layout="wide")

# 2. CUSTOM STYLING
def set_bg_local(main_bg):
    if os.path.exists(main_bg):
        with open(main_bg, "rb") as f:
            bin_str = base64.b64encode(f.read()).decode()
        # Fixed: Doubled curly braces for CSS in f-string to prevent key errors
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

# 3. SIDEBAR: PARAMETERS
if os.path.exists("utm.png"):
    st.sidebar.image("utm.png", use_container_width=True)

st.sidebar.title("⚙️ Engine Settings")
ellipsoid_mode = st.sidebar.selectbox("Reference Ellipsoid", ["Everest 1830 (Modified)", "WGS84"])

st.sidebar.divider()
st.sidebar.header("⚙️ 7-Parameter Datum Shift")
# Default values set to match Timbalai 1948 transformation
dx = st.sidebar.number_input("dX (m)", value=596.096, format="%.3f")
dy = st.sidebar.number_input("dY (m)", value=-624.512, format="%.3f")
dz = st.sidebar.number_input("dZ (m)", value=2.779, format="%.3f")

# 4. MATH ENGINE: GEODETIC TO CARTESIAN
def convert_to_cartesian(lat, lon, h, mode):
    # Set ellipsoid parameters
    if mode == "Everest 1830 (Modified)":
        # Parameters to achieve X: 2787565.983, Y: 5698693.034, Z: 657805.200
        a = 6377298.556
        f_inv = 300.8017
    else:
        a = 6378137.0
        f_inv = 298.257223563
        
    f = 1 / f_inv
    e2 = (2 * f) - (f ** 2)
    
    phi = np.radians(lat)
    lam = np.radians(lon)
    
    # Radius of curvature in the prime vertical (N)
    N = a / np.sqrt(1 - e2 * np.sin(phi)**2)
    
    # Calculate Cartesian coordinates
    X = (N + h) * np.cos(phi) * np.cos(lam)
    Y = (N + h) * np.cos(phi) * np.sin(lam)
    Z = (N * (1 - e2) + h) * np.sin(phi)
    
    return X, Y, Z

# 5. MAIN CONTENT
st.title("🛰️ Geocentric Cartesian Transformation")
st.markdown(f"#### Target Result Verification | Ellipsoid: **{ellipsoid_mode}**")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📥 Input: WGS84 Geodetic")
    lat_in = st.number_input("Latitude (decimal degrees)", value=5.573408816, format="%.9f")
    lon_in = st.number_input("Longitude (decimal degrees)", value=116.035751582, format="%.9f")
    h_in = st.number_input("Ellipsoidal Height (m)", value=48.502, format="%.3f")
    
    if st.button("🚀 Calculate Cartesian"):
        cx, cy, cz = convert_to_cartesian(lat_in, lon_in, h_in, ellipsoid_mode)
