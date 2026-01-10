import streamlit as st
import numpy as np
import folium
from streamlit_folium import st_folium
import base64
import os

# 1. PAGE SETUP
st.set_page_config(page_title="SBEU 3893 - Borneo RSO & Cartesian", page_icon="📍", layout="wide")

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
            
            .result-card {{
                background-color: #f0f8ff;
                padding: 15px;
                border-radius: 10px;
                border-left: 5px solid #800000;
                margin-bottom: 10px;
            }}
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

# 4. MATH ENGINE: HOTINE OBLIQUE MERCATOR (BORNEO RSO)
def latlon_to_borneo_rso(phi_deg, lam_deg):
    # Official Borneo RSO Parameters (GDM2000/GRS80)
    a = 6378137.0
    f = 1/298.257222101
    k0 = 0.99984
    phi0 = np.radians(4.0)          # Lat Origin
    lam0 = np.radians(115.0)        # Lon Origin
    gamma0 = np.radians(18.745783)  # Alpha/Azimuth
    E0, N0 = 0.0, 0.0               # True Origin (User Request)

    e2 = 2*f - f**2
    e = np.sqrt(e2)
    phi, lam = np.radians(phi_deg), np.radians(lam_deg)

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

# 5. TRANSFORMATION ENGINE (WGS84 -> GDM2000 Cartesian)
def transform_to_cartesian(lat, lon, h, dx, dy, dz):
    a_w, f_w = 6378137.0, 1/298.257223563
    e2_w = 2*f_w - f_w**2
    phi, lam = np.radians(lat), np.radians(lon)
    N_w = a_w / np.sqrt(1 - e2_w * np.sin(phi)**2)
    Xw = (N_w + h) * np.cos(phi) * np.cos(lam)
    Yw = (N_w + h) * np.cos(phi) * np.sin(lam)
    Zw = (N_w * (1 - e2_w) + h) * np.sin(phi)
    
    # Apply Helmert Shift
    P_gdm = np.array([Xw + dx, Yw + dy, Zw + dz])
    
    # Cartesian -> GDM2000 Geodetic
    a_g, f_g = 6378137.0, 1/298.257222101
    e2_g = 2*f_g - f_g**2
    x, y, z = P_gdm
    lon_g = np.arctan2(y, x)
    p = np.sqrt(x**2 + y**2)
    phi_g = np.arctan2(z, p * (1 - e2_g))
    for _ in range(5):
        N_g = a_g / np.sqrt(1 - e2_g * np.sin(phi_g)**2)
        phi_g = np.arctan2(z + e2_g * N_g * np.sin(phi_g), p)
        
    return np.degrees(phi_g), np.degrees(lon_g), P_gdm

# 6. APP LOGIC
if 'results' not in st.session_state: st.session_state.results = None

if os.path.exists("utm.png"): st.sidebar.image("utm.png", use_container_width=True)
st.sidebar.title("⚙️ Parameters")
dx = st.sidebar.number_input("dX (m)", value=0.0)
dy = st.sidebar.number_input("dY (m)", value=0.0)
dz = st.sidebar.number_input("dZ (m)", value=0.0)

st.title("🛰️ Borneo RSO & Cartesian Module")
st.write("WGS84 ➔ GDM2000 ➔ Borneo RSO & Cartesian XYZ")

col1, col2 = st.columns(2)
with col1:
    st.subheader("📥 Input: WGS84")
    lat_in = st.number_input("Latitude", value=5.9804, format="%.9f")
    lon_in = st.number_input("Longitude", value=116.0734, format="%.9f")
    h_in = st.number_input("Height (m)", value=25.0)
    
    if st.button("🚀 Transform & Project"):
        lat_g, lon_g, P_cart = transform_to_cartesian(lat_in, lon_in, h_in, dx, dy, dz)
        east, north = latlon_to_borneo_rso(lat_g, lon_g)
        st.session_state.results = {
            "dms_lat": decimal_to_dms(lat_g), "dms_lon": decimal_to_dms(lon_g, False),
            "east": east, "north": north, "cart": P_cart,
            "lat_orig": lat_in, "lon_orig": lon_in
        }

with col2:
    if st.session_state.results:
        st.subheader("📤 Output: Grid & 3D Cartesian")
        st.markdown(f"""
            <div class="result-card">
                <div class="result-label">BORNEO RSO (GRID)</div>
                <div class="result-value">EAST: {st.session_state.results['east']:.3f} m<br>NORTH: {st.session_state.results['north']:.3f} m</div>
            </div>
            <div class="result-card">
                <div class="result-label">3D CARTESIAN (X, Y, Z)</div>
                <div class="result-value">
                    X: {st.session_state.results['cart'][0]:.3f} m<br>
                    Y: {st.session_state.results['cart'][1]:.3f} m<br>
                    Z: {st.session_state.results['cart'][2]:.3f} m
                </div>
            </div>
            <div class="result-card">
                <div class="result-label">GEODETIC (DMS)</div>
                <div class="result-value">LAT: {st.session_state.results['dms_lat']}<br>LON: {st.session_state.results['dms_lon']}</div>
            </div>
        """, unsafe_allow_html=True)
        st.balloons()

# 7. MAP
if st.session_state.results:
    st.divider()
    m = folium.Map(location=[st.session_state.results['lat_orig'], st.session_state.results['lon_orig']], zoom_start=15)
    folium.Marker([st.session_state.results['lat_orig'], st.session_state.results['lon_orig']], popup="Point").add_to(m)
    st_folium(m, use_container_width=True, height=450, key="borneo_rso_cartesian_map")

# 8. FOOTER
st.markdown("""<div style="position: fixed; right: 20px; bottom: 20px; text-align: right; padding: 12px; background-color: rgba(255, 255, 255, 0.4); backdrop-filter: blur(10px); border-right: 5px solid #800000; border-radius: 8px; z-index: 1000;"><p style="color: #800000; font-weight: bold; margin: 0;">DEVELOPED BY:</p><p style="font-size: 13px; color: #002147; margin: 0;">Weil W. | Rebecca J. | Achellis L. | Nor Muhamad | Rowell B.S.</p><p style="font-size: 13px; font-weight: bold; color: #800000; margin-top: 5px;">SBEU 3893 - UTM</p></div>""", unsafe_allow_html=True)
