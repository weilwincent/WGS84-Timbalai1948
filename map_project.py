import streamlit as st
import numpy as np
import folium
from streamlit_folium import st_folium
import base64
import os

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="SBEU 3893 - Borneo RSO Module", page_icon="📍", layout="wide")

# 2. GAYA CSS (Steel Blue Theme)
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

# 3. FUNGSI PEMBANTU (DMS)
def decimal_to_dms(deg, is_lat=True):
    abs_deg = abs(deg)
    d = int(abs_deg)
    m = int((abs_deg - d) * 60)
    s = round((abs_deg - d - m/60) * 3600, 4)
    direction = ("N" if deg >= 0 else "S") if is_lat else ("E" if deg >= 0 else "W")
    return f"{d}° {m:02d}' {s:07.4f}\" {direction}"

# 4. ENJIN MATEMATIK: HELMERT & RSO
def transform_to_rso(lat_in, lon_in, h_in, dx, dy, dz, rx_s, ry_s, rz_s, s_ppm):
    # --- A. WGS84 ke GDM2000 (Helmert 7-Parameter) ---
    a_w, f_w = 6378137.0, 1/298.257223563
    e2_w = 2*f_w - f_w**2
    phi, lam = np.radians(lat_in), np.radians(lon_in)
    N_w = a_w / np.sqrt(1 - e2_w * np.sin(phi)**2)
    Xw = (N_w + h_in) * np.cos(phi) * np.cos(lam)
    Yw = (N_w + h_in) * np.cos(phi) * np.sin(lam)
    Zw = (N_w * (1 - e2_w) + h_in) * np.sin(phi)
    
    T = np.array([dx, dy, dz])
    S = 1 + (s_ppm / 1000000)
    rx, ry, rz = np.radians(rx_s/3600), np.radians(ry_s/3600), np.radians(rz_s/3600)
    R = np.array([[1, rz, -ry], [-rz, 1, rx], [ry, -rx, 1]])
    P_gdm = T + S * (R @ np.array([Xw, Yw, Zw]))

    # --- B. Cartesian ke Geodetic (GRS80 Ellipsoid) ---
    a_g, f_g = 6378137.0, 1/298.257222101
    e2_g = 2*f_g - f_g**2
    x, y, z = P_gdm
    lon_g = np.arctan2(y, x)
    p = np.sqrt(x**2 + y**2)
    phi_g = np.arctan2(z, p * (1 - e2_g))
    for _ in range(5):
        N_g = a_g / np.sqrt(1 - e2_g * np.sin(phi_g)**2)
        phi_g = np.arctan2(z + e2_g * N_g * np.sin(phi_g), p)
    
    lat_out, lon_out = np.degrees(phi_g), np.degrees(lon_g)

    # --- C. Geodetic ke Borneo RSO Grid (Hotine Oblique Mercator) ---
    phi0 = np.radians(4.0)          # Lat origin
    lam0 = np.radians(115.0)        # Long origin
    k0 = 0.99984                    # Scale factor
    gamma0 = np.radians(18.745778)  # Azimuth / Rectified Angle (18° 44' 44.8")
    
    B = np.sqrt(1 + (e2_g * np.cos(phi0)**4) / (1 - e2_g))
    A = a_g * B * k0 * np.sqrt(1 - e2_g) / (1 - e2_g * np.sin(phi0)**2)
    t = np.tan(np.pi/4 - phi_g/2) / ((1 - np.sqrt(e2_g) * np.sin(phi_g)) / (1 + np.sqrt(e2_g) * np.sin(phi_g)))**(np.sqrt(e2_g)/2)
    t0 = np.tan(np.pi/4 - phi0/2) / ((1 - np.sqrt(e2_g) * np.sin(phi0)) / (1 + np.sqrt(e2_g) * np.sin(phi0)))**(np.sqrt(e2_g)/2)
    
    v = B * (lon_g - lam0)
    u = A * np.arctanh(np.sin(v) / np.cosh(B * np.log(t/t0)))
    
    # Rectification Step (Rotation to Grid North)
    east = u * np.cos(gamma0) + (A/B) * np.sin(gamma0) * np.sin(v)
    north = u * np.sin(gamma0) - (A/B) * np.cos(gamma0) * np.sin(v)
    
    # Borneo RSO False Easting/Northing (Sabah Standard)
    final_east = east + 590476.66
    final_north = north + 442857.65
    
    return lat_out, lon_out, final_east, final_north, P_gdm

# 5. SIDEBAR & SESSION STATE
if 'results' not in st.session_state: st.session_state.results = None

if os.path.exists("utm.png"): st.sidebar.image("utm.png", use_container_width=True)
st.sidebar.header("⚙️ Parameter Transform")
dx = st.sidebar.number_input("dX (m)", value=0.0, step=0.001)
dy = st.sidebar.number_input("dY (m)", value=0.0, step=0.001)
dz = st.sidebar.number_input("dZ (m)", value=0.0, step=0.001)
rx_s = st.sidebar.number_input("rX (sec)", value=0.0, step=0.0001)
ry_s = st.sidebar.number_input("rY (sec)", value=0.0, step=0.0001)
rz_s = st.sidebar.number_input("rZ (sec)", value=0.0, step=0.0001)
scale = st.sidebar.number_input("Scale (ppm)", value=0.0, step=0.0001)

# 6. ANTARAMUKA UTAMA
st.title("🛰️ Modul Transformasi Borneo RSO")
st.write("SBEU 3893: WGS84 ➔ GDM2000 ➔ Borneo RSO Grid")

col1, col2 = st.columns(2)
with col1:
    st.subheader("📥 Input: WGS84")
    lat_in = st.number_input("Latitud", value=5.9804, format="%.8f")
    lon_in = st.number_input("Longitud", value=116.0734, format="%.8f")
    h_in = st.number_input("Tinggi (m)", value=25.0, format="%.3f")
    
    if st.button("🚀 Proses & Papar Peta"):
        lat_g, lon_g, east, north, cart = transform_to_rso(lat_in, lon_in, h_in, dx, dy, dz, rx_s, ry_s, rz_s, scale)
        st.session_state.results = {
            "dms_lat": decimal_to_dms(lat_g, True), "dms_lon": decimal_to_dms(lon_g, False),
            "east": east, "north": north, "cart": cart,
            "orig_lat": lat_in, "orig_lon": lon_in
        }

with col2:
    if st.session_state.results:
        st.subheader("📤 Output: Borneo RSO & GDM")
        st.markdown(f"""
            <div class="result-card">
                <div class="result-label">BORNEO RSO (GRID)</div>
                <div class="result-value">TIMUR (E): {st.session_state.results['east']:.3f} m<br>UTARA (N): {st.session_state.results['north']:.3f} m</div>
            </div>
            <div class="result-card">
                <div class="result-label">GEODETIK (DMS)</div>
                <div class="result-value">{st.session_state.results['dms_lat']}<br>{st.session_state.results['dms_lon']}</div>
            </div>
            <div class="result-card">
                <div class="result-label">CARTESIAN (X, Y, Z)</div>
                <div class="result-value">
                X: {st.session_state.results['cart'][0]:.3f} m<br>
                Y: {st.session_state.results['cart'][1]:.3f} m<br>
                Z: {st.session_state.results['cart'][2]:.3f} m
                </div>
            </div>
        """, unsafe_allow_html=True)
        st.balloons()

# 7. VISUALISASI PETA
if st.session_state.results:
    st.divider()
    st.subheader("🗺️ Pengesahan Lokasi Visual")
    m = folium.Map(location=[st.session_state.results['orig_lat'], st.session_state.results['orig_lon']], zoom_start=15)
    folium.Marker(
        [st.session_state.results['orig_lat'], st.session_state.results['orig_lon']],
        popup=f"E: {st.session_state.results['east']:.2f}, N: {st.session_state.results['north']:.2f}",
        icon=folium.Icon(color='blue', icon='screenshot', prefix='fa')
    ).add_to(m)
    st_folium(m, use_container_width=True, height=450, key="borneo_rso_map")

# 8. FOOTER
st.markdown("""<div style="position: fixed; right: 20px; bottom: 20px; text-align: right; padding: 12px; background-color: rgba(255, 255, 255, 0.4); backdrop-filter: blur(10px); border-right: 5px solid #800000; border-radius: 8px; z-index: 1000;"><p style="color: #800000; font-weight: bold; margin: 0;">DEVELOPED BY:</p><p style="font-size: 13px; color: #002147; margin: 0;">Weil W. | Rebecca J. | Achellis L. | Nor Muhamad | Rowell B.S.</p><p style="font-size: 13px; font-weight: bold; color: #800000; margin-top: 5px;">SBEU 3893 - UTM</p></div>""", unsafe_allow_html=True)
