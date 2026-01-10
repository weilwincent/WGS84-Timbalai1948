import streamlit as st
import numpy as np
import folium
from streamlit_folium import st_folium
import base64
import os

# 1. PAGE SETUP
st.set_page_config(page_title="SBEU 3893 - Borneo RSO Module", page_icon="📍", layout="wide")

# 2. CUSTOM STYLING
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

# 4. MATH ENGINE: HOTINE OBLIQUE MERCATOR (BORNEO RSO)
def latlon_to_borneo_rso(lat_deg, lon_deg):
    # Official JUPEM Borneo RSO Parameters
    a = 6378137.0                   # GRS80 (GDM2000)
    f = 1/298.257222101
    k0 = 0.99984                    # Scale factor
    phi0 = np.radians(4.0)          # Lat Origin
    lam0 = np.radians(115.0)        # Lon Origin
    gamma0 = np.radians(18.745783)  # Rectified Angle (18° 44' 44.82")
    E0, N0 = 0.0, 0.0               # Raw grid (Zero False Origin)

    e2 = 2*f - f**2
    e = np.sqrt(e2)
    phi, lam = np.radians(lat_deg), np.radians(lon_deg)

    # HOM Formulation
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
    
    # Rectification (Rotation to Grid)
    east = v * np.cos(gamma0) + u * np.sin(gamma0) + E0
    north = u * np.cos(gamma0) - v * np.sin(gamma0) + N0
    
    return east, north

# 5. INITIALIZE SESSION STATE
if 'results' not in st.session_state:
    st.session_state.results = None

# 6. SIDEBAR
if os.path.exists("utm.png"):
    st.sidebar.image("utm.png", use_container_width=True)
st.sidebar.title("⚙️ Parameters")
st.sidebar.info("Transformation uses GDM2000 (GRS80 Ellipsoid)")
dx = st.sidebar.number_input("dX (m)", value=0.0)
dy = st.sidebar.number_input("dY (m)", value=0.0)
dz = st.sidebar.number_input("dZ (m)", value=0.0)

# 7. MAIN UI
st.title("🛰️ Professional Borneo RSO Module")
st.write("WGS84 ➔ GDM2000 ➔ Borneo RSO Grid (Hotine Oblique Mercator)")

col_in, col_out = st.columns(2)
with col_in:
    st.subheader("📥 Input: WGS84")
    lat_in = st.number_input("Latitude", value=5.9804, format="%.9f")
    lon_in = st.number_input("Longitude", value=116.0734, format="%.9f")
    
    if st.button("🚀 Transform & Project"):
        # For GDM2000, we assume raw WGS84 inputs are very close, 
        # but user can apply dX/dY/dZ shift if needed.
        east, north = latlon_to_borneo_rso(lat_in, lon_in)
        st.session_state.results = {
            "lat_dms": decimal_to_dms(lat_in, True),
            "lon_dms": decimal_to_dms(lon_in, False),
            "east": east, "north": north,
            "lat_orig": lat_in, "lon_orig": lon_in
        }

with col_out:
    if st.session_state.results:
        st.subheader("📤 Output: Grid & Geodetic")
        st.markdown(f"""
            <div class="result-card">
                <div class="result-label">BORNEO RSO GRID (TRUE ORIGIN)</div>
                <div class="result-value">EAST: {st.session_state.results['east']:.3f} m<br>NORTH: {st.session_state.results['north']:.3f} m</div>
            </div>
            <div class="result-card">
                <div class="result-label">GDM2000 (DMS)</div>
                <div class="result-value">LAT: {st.session_state.results['lat_dms']}<br>LON: {st.session_state.results['lon_dms']}</div>
            </div>
        """, unsafe_allow_html=True)
        st.balloons()

# 8. MAP
if st.session_state.results:
    st.divider()
    st.subheader("🗺️ Visual Verification")
    m = folium.Map(location=[st.session_state.results['lat_orig'], st.session_state.results['lon_orig']], zoom_start=15)
    folium.Marker(
        [st.session_state.results['lat_orig'], st.session_state.results['lon_orig']], 
        popup=f"E: {st.session_state.results['east']:.2f}",
        icon=folium.Icon(color='blue', icon='screenshot', prefix='fa')
    ).add_to(m)
    st_folium(m, use_container_width=True, height=450, key="borneo_final_map")

# 9. FOOTER
st.markdown("""<div style="position: fixed; right: 20px; bottom: 20px; text-align: right; padding: 12px; background-color: rgba(255, 255, 255, 0.4); backdrop-filter: blur(10px); border-right: 5px solid #800000; border-radius: 8px; z-index: 1000;"><p style="color: #800000; font-weight: bold; margin: 0;">DEVELOPED BY:</p><p style="font-size: 13px; color: #002147; margin: 0;">Weil W. | Rebecca J. | Achellis L. | Nor Muhamad | Rowell B.S.</p><p style="font-size: 13px; font-weight: bold; color: #800000; margin-top: 5px;">SBEU 3893 - UTM</p></div>""", unsafe_allow_html=True)
