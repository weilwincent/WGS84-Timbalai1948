import streamlit as st
import numpy as np
import folium
from streamlit_folium import st_folium
import base64
import os

# 1. PAGE SETUP
st.set_page_config(page_title="SBEU 3893 - Borneo RSO Suite", page_icon="📍", layout="wide")

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

# 3. HELPER FUNCTIONS
def decimal_to_dms(deg, is_lat=True):
    abs_deg = abs(deg)
    d = int(abs_deg); m = int((abs_deg - d) * 60); s = round((abs_deg - d - m/60) * 3600, 4)
    direction = ("N" if deg >= 0 else "S") if is_lat else ("E" if deg >= 0 else "W")
    return f"{d}° {m:02d}' {s:07.4f}\" {direction}"

# 4. RSO ENGINE (Calibrated with Everest 1830)
def latlon_to_borneo_rso(phi, lam):
    # --- UPDATED PARAMETERS (Everest 1830) ---
    a = 6377298.556                 
    inv_f = 300.8017
    f = 1 / inv_f
    
    k0 = 0.99984                    
    phi0 = np.radians(4.0)          
    lam0 = np.radians(115.0)        
    gamma0 = np.radians(18.745783)  
    
    # Official Sabah/Sarawak Offsets
    E0 = 590476.66                  
    N0 = 442857.65                  

    e2 = 2*f - f**2
    e = np.sqrt(e2)

    B = np.sqrt(1 + (e2 * np.cos(phi0)**4) / (1 - e2))
    A = a * B * k0 * np.sqrt(1 - e2) / (1 - e2 * np.sin(phi0)**2)
    
    t = np.tan(np.pi/4 - phi/2) / ((1 - e * np.sin(phi)) / (1 + e * np.sin(phi)))**(e/2)
    t0 = np.tan(np.pi/4 - phi0/2) / ((1 - e * np.sin(phi0)) / (1 + e * np.sin(phi0)))**(e/2)
    
    D = B * np.sqrt(1 - e2) / (np.cos(phi0) * np.sqrt(1 - e2 * np.sin(phi0)**2))
    F = D + np.sqrt(max(0, D**2 - 1))
    H = F * (t0**B)
    L = np.log(H / (t**B))
    
    u = (A / B) * np.arctan2(np.sinh(L), np.cos(B * (lam - lam0)))
    v = (A / B) * np.arctanh(np.sin(B * (lam - lam0)) / np.cosh(L))
    
    # Rectification Rotation
    east = v * np.cos(gamma0) + u * np.sin(gamma0) + E0
    north = u * np.cos(gamma0) - v * np.sin(gamma0) + N0
    
    return east, north

# 5. TRANSFORMATION ENGINE
def full_transformation(lat_in, lon_in, h_in, dx, dy, dz, rx_s, ry_s, rz_s, s_ppm):
    # WGS84 Geodetic -> Cartesian
    a_w, f_w = 6378137.0, 1/298.257223563
    e2_w = 2*f_w - f_w**2
    phi, lam = np.radians(lat_in), np.radians(lon_in)
    N_w = a_w / np.sqrt(1 - e2_w * np.sin(phi)**2)
    Xw = (N_w + h_in) * np.cos(phi) * np.cos(lam)
    Yw = (N_w + h_in) * np.cos(phi) * np.sin(lam)
    Zw = (N_w * (1 - e2_w) + h_in) * np.sin(phi)
    
    # Apply Helmert Shift
    T = np.array([dx, dy, dz]); S = 1 + (s_ppm / 1000000)
    rx, ry, rz = np.radians(rx_s/3600), np.radians(ry_s/3600), np.radians(rz_s/3600)
    R = np.array([[1, rz, -ry], [-rz, 1, rx], [ry, -rx, 1]])
    P_local = T + S * (R @ np.array([Xw, Yw, Zw]))
    
    # Cartesian -> Local Geodetic (Everest 1830)
    a_e = 6377298.556
    f_e = 1 / 300.8017
    e2_e = 2*f_e - f_e**2
    x, y, z = P_local
    lon_l = np.arctan2(y, x); p = np.sqrt(x**2 + y**2); phi_l = np.arctan2(z, p * (1 - e2_e))
    for _ in range(5):
        N_e = a_e / np.sqrt(1 - e2_e * np.sin(phi_l)**2)
        phi_l = np.arctan2(z + e2_e * N_e * np.sin(phi_l), p)
        
    east, north = latlon_to_borneo_rso(phi_l, lon_l)
    return np.degrees(phi_l), np.degrees(lon_l), east, north, P_local

# 6. SIDEBAR
if 'results' not in st.session_state: st.session_state.results = None
if os.path.exists("utm.png"): st.sidebar.image("utm.png", use_container_width=True)
st.sidebar.title("⚙️ Shift Parameters")
# Jika menggunakan Everest, anda mungkin perlu dx, dy, dz yang lebih besar (Standard: 596, -624, 2)
dx = st.sidebar.number_input("dX (m)", value=0.000, format="%.3f")
dy = st.sidebar.number_input("dY (m)", value=0.000, format="%.3f")
dz = st.sidebar.number_input("dZ (m)", value=0.000, format="%.3f")
rx_s = st.sidebar.number_input("rX (sec)", value=0.0000, format="%.4f")
ry_s = st.sidebar.number_input("r
