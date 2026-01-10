import streamlit as st
import numpy as np
import folium
from streamlit_folium import st_folium
import base64
import os

# 1. PAGE SETUP
st.set_page_config(page_title="SBEU 3893 - Borneo RSO Module", page_icon="📍", layout="wide")

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
            .result-card {{ background-color: #f0f8ff; padding: 15px; border-radius: 10px; border-left: 5px solid #4682B4; margin-bottom: 10px; }}
            .result-label {{ color: #4682B4; font-weight: bold; font-size: 14px; margin-bottom: 5px; }}
            .result-value {{ color: #333; font-size: 18px; font-family: 'Courier New', monospace; font-weight: bold; }}
            iframe {{ width: 100% !important; border-radius: 10px; }}
            </style>
            """, unsafe_allow_html=True)

if os.path.exists('background.jpg'):
    set_bg_local('background.jpg')

# 3. HELPER FUNCTIONS
def decimal_to_dms(deg, is_lat=True):
    abs_deg = abs(deg)
    d = int(abs_deg); m = int((abs_deg - d) * 60); s = round((abs_deg - d - m/60) * 3600, 4)
    direction = ("N" if deg >= 0 else "S") if is_lat else ("E" if deg >= 0 else "W")
    return f"{d}° {m:02d}' {s:07.4f}\" {direction}"

# 4. MATH ENGINES
def helmert_to_gdm2000(lat, lon, h, dx, dy, dz):
    a_w, f_w = 6378137.0, 1/298.257223563
    e2_w = 2*f_w - f_w**2
    phi, lam = np.radians(lat), np.radians(lon)
    N_w = a_w / np.sqrt(1 - e2_w * np.sin(phi)**2)
    Xw = (N_w + h) * np.cos(phi) * np.cos(lam)
    Yw = (N_w + h) * np.cos(phi) * np.sin(lam)
    Zw = (N_w * (1 - e2_w) + h) * np.sin(phi)
    
    # Simple Translation Shift
    P_local = np.array([Xw + dx, Yw + dy, Zw + dz])
    
    a_g, f_g = 6378137.0, 1/298.257222101
    e2_g = 2*f_g - f_g**2; x, y, z = P_local
    lon_l = np.arctan2(y, x); p = np.sqrt(x**2 + y**2); phi_l = np.arctan2(z, p * (1 - e2_g))
    for _ in range(5):
        N_g = a_g / np.sqrt(1 - e2_g * np.sin(phi_l)**2)
        phi_l = np.arctan2(z + e2_g * N_g * np.sin(phi_l), p)
    return np.degrees(phi_l), np.degrees(lon_l)

def latlon_to_borneo_rso(lat, lon):
    # Borneo RSO Projection parameters (Sabah/Sarawak Standard)
    # Using Hotine Oblique Mercator simplified for display purposes
    lat_origin, lon_origin = 4.0, 115.0
    k0 = 0.99984
    # Metric conversion for Sabah region
    east = (lon - lon_origin) * 111320 * np.cos(np.radians(lat)) * k0 + 500000
    north = (lat - lat_origin) * 110574 * k0 + 500000
    return east, north

# 5. INITIALIZE SESSION STATE
if 'results' not in st.session_state:
    st.session_state.results = None
if 'balloons_fired' not in st.session_state:
    st.session_state.balloons_fired = False

# 6. SIDEBAR
if os.path.exists("utm.png"):
    st.sidebar.image("utm.png", use_container_width=True)
st.sidebar.title("⚙️ Parameters")
dx = st.sidebar.number_input("dX (m)", value=0.0)
dy = st.sidebar.number_input("dY (m)", value=0.0)
dz = st.sidebar.number_input("dZ (m)", value=0.0)

# 7. MAIN UI
st.title("🛰️ Professional Borneo RSO Module")
st.write("WGS84 ➔ GDM2000 ➔ Borneo RSO Grid")

col_in, col_out = st.columns(2)
with col_in:
    st.subheader("📥 Input: WGS84")
    lat_in = st.number_input("Latitude", value=5.5734, format="%.9f")
    lon_in = st.number_input("Longitude", value=116.0357, format="%.9f")
    h_in = st.number_input("Height (m)", value=4
