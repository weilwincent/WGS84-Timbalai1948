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

# 4. RSO ENGINE (Zero False Origin)
def latlon_to_borneo_rso_zero(phi, lam):
    a = 6378137.0                   # GRS80 (GDM2000)
    f = 1/298.257222101
    k0 = 0.99984                    
    phi0 = np.radians(4.0)          
    lam0 = np.radians(115.0)        
    gamma0 = np.radians(18.745783)  
    
    # SET TO ZERO AS REQUESTED
    E0 = 0.0                        
    N0 = 0.0                        

    e2 = 2*f - f**2
    e = np.sqrt(e2)

    B = np.sqrt(1 + (e2 * np.cos(phi0)**4) / (1 - e2))
    A = a * B * k0 * np.sqrt(1 - e2) / (1 - e2 * np.sin(phi0)**2)
    
    t = np.tan(np.pi/4 - phi/2) / ((1 - e * np.sin(phi)) / (1 + e * np.sin(phi)))**(e/2)
    t0 = np.tan(np.pi/4 - phi0/2) / ((1 - e * np.sin(phi0)) / (1 + e * np.sin(phi0)))**(e/2)
    
    D = B * np.sqrt(1 - e2) / (np.cos(phi0) * np.sqrt(1 - e2 * np.sin(phi0)**2))
    F = D + np.sqrt(max(0, D**2 - 1))
    if phi0 < 0: F = D - np.sqrt(max(0, D**2 - 1))
    H = F * (t0**B)
    L = np.log(H / (t**B))
    
    u = (A / B) * np.arctan2(np.sqrt(np.cosh(L)**2 - np.cos(B * (lam - lam0))**2), np.cos(B * (lam - lam0)))
    if L < 0: u = -u
    v = (A / B) * np.log(np.cosh(L) - np.sinh(L) * np.sin(B * (lam - lam0)))
    
    # Rectification
    east = v * np.cos(gamma0) + u * np.sin(gamma0) + E0
    north = u * np.cos(gamma0) - v * np.sin(gamma0) + N0
    
    return east, north

# 5. TRANSFORMATION ENGINE
def full_transformation(lat_in, lon_in, h_in, dx, dy, dz):
    a_w, f_w = 6378137.0, 1/298.257223563
    e2_w = 2*f_w - f_w**2
    phi, lam = np.radians(lat_in), np.radians(lon_in)
    N_w = a_w / np.sqrt(1 - e2_w * np.sin(phi)**2)
    Xw = (N_w + h_in) * np.cos(phi) * np.cos(lam)
    Yw = (N_w + h_in) * np.cos(phi) * np.sin(lam)
    Zw = (N_w * (1 - e2_w) + h_in) * np.sin(phi)
    
    Xg, Yg, Zg = Xw + dx, Yw + dy, Zw + dz
    
    a_g, f_g = 6378137.0, 1/298.257222101
    e2_g = 2*f_g - f_g**2
    p = np.sqrt(Xg**2 + Yg**2)
    phi_g = np.arctan2(Zg, p * (1 - e2_g))
    for _ in range(5):
        N_g = a_g / np.sqrt(1 - e2_g * np.sin(phi_g)**2)
        phi_g = np.arctan2(Zg + e2_g * N_g * np.sin(phi_g), p)
    
    lon_g = np.arctan2(Yg, Xg)
    east, north = latlon_to_borneo_rso_zero(phi_g, lon_g)
    
    return np.degrees(phi_g), np.degrees(lon_g), east, north

# 6. APP UI
if 'results' not in st.session_state: st.session_state.results = None

st.title("🛰️ Borneo RSO (Zero False Origin)")
st.write("SBEU 3893 | Grid coordinates relative to True Origin")

c1, c2 = st.columns(2)
with c1:
    st.subheader("📥 Input: WGS84")
    lat_in = st.number_input("Latitude", value=5.9804, format="%.8f")
    lon_in = st.number_input("Longitude", value=116.0734, format="%.8f")
    h_in = st.number_input("Height (m)", value=25.0)
    if st.button("🚀 Calculate Grid"):
        lat_g, lon_g, east, north = full_transformation(lat_in, lon_in, h_in, 0, 0, 0)
        st.session_state.results = {
            "dms_lat": decimal_to_dms(lat_g), "dms_lon": decimal_to_dms(lon_g, False),
            "east": east, "north": north, "orig_lat": lat_in, "orig_lon": lon_in
        }

with c2:
    if st.session_state.results:
        st.subheader("📤 Output (True Origin)")
        st.markdown(f"""
            <div class="result-card">
                <div class="result-label">RAW RSO GRID (m)</div>
                <div class="result-value">E: {st.session_state.results['east']:.3f}<br>N: {st.session_state.results['north']:.3f}</div>
            </div>
        """, unsafe_allow_html=True)
        st.warning("Note: False Easting and Northing are set to 0.0.")

# 7. MAP
if st.session_state.results:
    st.divider()
    m = folium.Map(location=[st.session_state.results['orig_lat'], st.session_state.results['orig_lon']], zoom_start=15)
    folium.Marker([st.session_state.results['orig_lat'], st.session_state.results['orig_lon']], popup="Survey Point").add_to(m)
    st_folium(m, use_container_width=True, height=450, key="borneo_zero_map")
