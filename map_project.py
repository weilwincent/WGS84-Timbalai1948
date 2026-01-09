import streamlit as st
import numpy as np
import base64
import os

# 1. PAGE SETUP - FIXED TYPO
st.set_page_config(page_title="SBEU 3893 - Borneo RSO Module", page_icon="📍", layout="wide")

# 2. CUSTOM STYLING (Darker Steel Blue)
def set_bg_local(main_bg):
    if os.path.exists(main_bg):
        with open(main_bg, "rb") as f:
            bin_str = base64.b64encode(f.read()).decode()
        # FIXED: Doubled curly braces for CSS in f-string
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

set_bg_local('background.jpg')

# 3. SIDEBAR (Your specific 7-Parameters)
if os.path.exists("utm.png"):
    st.sidebar.image("utm.png", use_container_width=True)
st.sidebar.divider()
st.sidebar.header("⚙️ Datum Shift (WGS84 ➔ Timbalai)")
dx = st.sidebar.number_input("dX (m)", value=596.096, format="%.3f")
dy = st.sidebar.number_input("dY (m)", value=-624.512, format="%.3f")
dz = st.sidebar.number_input("dZ (m)", value=2.779, format="%.3f")
rx_s = st.sidebar.number_input("rX (sec)", value=-1.44646, format="%.5f")
ry_s = st.sidebar.number_input("rY (sec)", value=-0.88312, format="%.5f")
rz_s = st.sidebar.number_input("rZ (sec)", value=1.82844, format="%.5f")
scale_p = st.sidebar.number_input("Scale (ppm)", value=-10.454, format="%.4f")

# 4. MATH ENGINE: HOTINE OBLIQUE MERCATOR (BORNEO RSO)
def latlon_to_borneo_rso(lat, lon):
    a = 6377298.556
    f_inv = 300.8017
    f = 1/f_inv
    e2 = 2*f - f**2
    e = np.sqrt(e2)
    
    # User Projection Parameters
    lat0 = np.radians(4.0)
    lon0 = np.radians(115.0)
    k0 = 0.99984
    alpha_c = np.radians(53 + 18/60 + 56.9537/3600)
    gamma_c = np.radians(53 + 7/60 + 48.3685/3600)
    
    # Origin Shift for East Malaysia Grid
    FE = 590476.662  
    FN = 442857.652
    
    phi = np.radians(lat)
    lam = np.radians(lon)
    
    B = np.sqrt(1 + (e2 * np.cos(lat0)**4) / (1 - e2))
    A = (a * B * k0 * np.sqrt(1 - e2)) / (1 - e2 * np.sin(lat0)**2)
    t0 = np.tan(np.pi/4 - lat0/2) / ((1 - e*np.sin(lat0))/(1 + e*np.sin(lat0)))**(e/2)
    D = B * np.sqrt(1 - e2) / (np.cos(lat0) * np.sqrt(1 - e2 * np.sin(lat0)**2))
    F = D + np.sqrt
