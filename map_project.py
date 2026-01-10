import streamlit as st
import numpy as np
import folium
from streamlit_folium import st_folium
import base64
import os

# 1. PAGE SETUP
st.set_page_config(page_title="SBEU 3893 - GDM2000 Module", page_icon="📍", layout="wide")

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
            .main .block-container {{ background-color: rgba(255, 255, 255, 0.95); padding: 2rem; border-radius: 20px; border: 1px solid #ddd; }}
            
            .result-card {{
                background-color: #f0f8ff;
                padding: 15px;
                border-radius: 10px;
                border-left: 5px solid #4682B4;
                margin-bottom: 10px;
            }}
            .result-label {{ color: #4682B4; font-weight: bold; font-size: 14px; margin-bottom: 5px; }}
            .result-value {{ color: #333; font-size: 18px; font-family: 'Courier New', monospace; font-weight: bold; }}
            
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
    s = round((abs_deg - d - m/60) * 3600, 4)
    direction = ("N" if deg >= 0 else "S") if is_lat else ("E" if deg >= 0 else "W")
    return f"{d}° {m:02d}' {s:07.4f}\" {direction}"

# 4. MATH ENGINE: HELMERT (WGS84 to GDM2000)
def helmert_transformation(lat, lon, h, dx, dy, dz, rx_s, ry_s, rz_s, s_ppm):
    # WGS84 Constants
    a_w, f_w = 6378137.0, 1/298.257223563
    e2_w = (2*f_w) - (f_w**2)
    
    # Geodetic to Cartesian
    phi, lam = np.radians(lat), np.radians(lon)
    N_w = a_w / np.sqrt(1 - e2_w * np.sin(phi)**2)
    Xw = (N_w + h) * np.cos(phi) * np.cos(lam)
    Yw = (N_w + h) * np.cos(phi) * np.sin(lam)
    Zw = (N_w * (1 - e2_w) + h) * np.sin(phi)
    
    # Helmert Transformation to Local Cartesian
    T = np.array([dx, dy, dz])
    S = 1 + (s_ppm / 1000000)
    rx, ry, rz = np.radians(rx_s/3600), np.radians(ry_s/3600), np.radians(rz_s/3600)
    R = np.array([[1, rz, -ry], [-rz, 1, rx], [ry, -rx, 1]])
    P_local = T + S * (R @ np.array([Xw, Yw, Zw]))
    
    # Cartesian to Geodetic (GDM2000 Uses GRS80 Ellipsoid)
    a_g, f_g = 6378137.0, 1/298.257222101
    e2_g = (2*f_g) - (f_g**2)
    x, y, z = P_local
    lon_l = np.arctan2(y, x)
    p = np.sqrt(x**2 + y**2)
    phi_l = np.arctan2(z, p * (1 - e2_g))
    for _ in range(5):
        N_g = a_g / np.sqrt(1 - e2_g * np.sin(phi_l)**2)
        phi_l = np.arctan2(z + e2_g * N_g * np.sin(phi_l), p)
    
    return np.degrees(phi_l), np.degrees(lon_l), P_local

# 5. INITIALIZE SESSION STATE
if 'results' not in st.session_state:
    st.session_state.results = None
if 'balloons_fired' not in st.session_state:
    st.session_state.balloons_fired = False

# 6. SIDEBAR
if os.path.exists("utm.png"):
    st.sidebar.image("utm.png", use_container_width=True)
st.sidebar.title("⚙️ Parameters")
dx = st.sidebar.number_input("dX (m)", value=0.000, format="%.3f")
dy = st.sidebar.number_input("dY (m)", value=0.000, format="%.3f")
dz = st.sidebar.number_input("dZ (m)", value=0.000, format="%.3f")
rx_s = st.sidebar.number_input("rX (sec)", value=0.000, format="%.6f")
ry_s = st.sidebar.number_input("rY (sec)", value=0.000, format="%.6f")
rz_s = st.sidebar.number_input("rZ (sec)", value=0.000, format="%.6f")
scale_p = st.sidebar.number_input("Scale (ppm)", value=0.000, format="%.6f")

# 7. MAIN UI
st.title("🛰️ Coordinate Transformation Module")
st.write("WGS84 ➔ GDM2000 | Dual Output Format")

col_in, col_out = st.columns(2)
with col_in:
    st.subheader("📥 Input: WGS84")
    lat_in = st.number_input("Latitude (Decimal)", value=5.573408816, format="%.9f")
    lon_in = st.number_input("Longitude (Decimal)", value=116.035751582, format="%.9f")
    h_in = st.number_input("Height (m)", value=48.502, format="%.3f")
    
    if st.button("🚀 Transform Point"):
        st.session_state.balloons_fired = False 
        lat_t, lon_t, P_cart = helmert_transformation(lat_in, lon_in, h_in, dx, dy, dz, rx_s, ry_s, rz_s, scale_p)
        st.session_state.results = {
            "lat_dms": decimal_to_dms(lat_t, True),
            "lon_dms": decimal_to_dms(lon_t, False),
            "cart": P_cart,
            "h_t": h_in,
            "lat_orig": lat_in,
            "lon_orig": lon_in
        }

with col_out:
    if st.session_state.results:
        st.subheader("📤 Output: GDM2000")
        
        # Geodetic DMS Card
        st.markdown(f"""
            <div class="result-card">
                <div class="result-label">GEODETIC (DMS)</div>
                <div class="result-value">LAT: {st.session_state.results['lat_dms']}<br>LON: {st.session_state.results['lon_dms']}</div>
            </div>
        """, unsafe_allow_html=True)
        
        # Cartesian Card
        st.markdown(f"""
            <div class="result-card">
                <div class="result-label">CARTESIAN (X, Y, Z)</div>
                <div class="result-value">
                    X: {st.session_state.results['cart'][0]:.3f} m<br>
                    Y: {st.session_state.results['cart'][1]:.3f} m<br>
                    Z: {st.session_state.results['cart'][2]:.3f} m
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.metric("Height (m)", f
