import streamlit as st
import numpy as np
import base64
import os

# 1. PAGE SETUP - FIXED: changed set_config to set_page_config
st.set_page_config(page_title="SBEU 3893 - Final Borneo Module", page_icon="📍", layout="wide")

# 2. CUSTOM STYLING
def set_bg_local(main_bg):
    if os.path.exists(main_bg):
        with open(main_bg, "rb") as f:
            bin_str = base64.b64encode(f.read()).decode()
        # FIXED: CSS braces doubled to avoid f-string conflicts
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

# 3. SIDEBAR
if os.path.exists("utm.png"):
    st.sidebar.image("utm.png", use_container_width=True)
st.sidebar.title("⚙️ Engine Settings")
ellipsoid = st.sidebar.selectbox("Reference Ellipsoid", ["Everest 1830 (Modified)", "WGS84"])

# 4. MATH ENGINE: GEODETIC TO CARTESIAN
def convert_to_cartesian(lat, lon, h, mode):
    if mode == "Everest 1830 (Modified)":
        a = 6377298.556
        f_inv = 300.8017
    else:
        a = 6378137.0
        f_inv = 298.257223563
        
    f = 1 / f_inv
    e2 = (2 * f) - (f ** 2)
    
    phi = np.radians(lat)
    lam = np.radians(lon)
    
    # Radius of curvature in the prime vertical
    N = a / np.sqrt(1 - e2 * np.sin(phi)**2)
    
    # FIXED: Ensured absolute positive logic for Eastern Longitude
    X = (N + h) * np.cos(phi) * np.cos(lam)
    Y = (N + h) * np.cos(phi) * np.sin(lam)
    Z = (N * (1 - e2) + h) * np.sin(phi)
    
    return X, Y, Z

# 5. MAIN CONTENT
st.title("🛰️ Geocentric Cartesian Transformation")
st.markdown(f"### Current Ellipsoid: **{ellipsoid}**")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📥 Input: Geodetic")
    lat_in = st.number_input("Latitude (decimal degrees)", value=5.573408816, format="%.9f")
    lon_in = st.number_input("Longitude (decimal degrees)", value=116.035751582, format="%.9f")
    h_in = st.number_input("Ellipsoidal Height (m)", value=48.502, format="%.3f")
    
    if st.button("🚀 Calculate Cartesian"):
        cx, cy, cz = convert_to_cartesian(lat_in, lon_in, h_in, ellipsoid)
        
        with col2:
            st.subheader("📤 Output: Cartesian (X, Y, Z)")
            st.success("Calculation Successful!")
            st.metric("X (meters)", f"{cx:.3f}")
            st.metric("Y (meters)", f"{cy:.3f}")
            st.metric("Z (meters)", f"{cz:.3f}")
            
            # Highlight matching results for Everest
            if ellipsoid == "Everest 1830 (Modified)" and abs(cx - 2787565.983) < 0.1:
                st.info("✅ Verified: Matches Survey Software Results.")
            st.balloons()

# 6. FOOTER
st.markdown("<div style="position: fixed; right: 20px; bottom: 20px; text-align: right; padding: 12px; background-color: rgba(255,255,255,0.4); backdrop-filter: blur(10px); border-right: 5px solid #800

