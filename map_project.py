import streamlit as st
import numpy as np
import folium
from streamlit_folium import st_folium
import base64
import os

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="SBEU 3893 - Geomatics Suite", page_icon="📍", layout="wide")

# 2. GAYA VISUAL (Steel Blue Theme)
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

# 3. ENJIN MATEMATIK: UTM (Zone 50N - Sabah)
def latlon_to_utm(lat, lon):
    a = 6378137.0
    f = 1/298.257223563
    k0 = 0.9996 
    
    phi = np.radians(lat)
    lam = np.radians(lon)
    lam0 = np.radians(117.0) # Central Meridian Zone 50
    
    e2 = 2*f - f**2
    n = f / (2 - f)
    A = a / (1 + n) * (1 + (n**2)/4 + (n**4)/64)
    
    t = np.sinh(np.arctanh(np.sin(phi)) - (2*np.sqrt(n)/(1+n)) * np.arctanh(2*np.sqrt(n)/(1+n) * np.sin(phi)))
    xi = np.arctan(t / np.cos(lam - lam0))
    eta = np.arctanh(np.sin(lam - lam0) / np.sqrt(1 + t**2))
    
    east = 500000 + k0 * A * (eta + (n/2)*np.sin(2*xi)*np.cosh(2*eta))
    north = k0 * A * (xi + (n/2)*np.cos(2*xi)*np.sinh(2*eta))
    return east, north

# 4. ENJIN MATEMATIK: BORNEO RSO (Hotine Oblique Mercator)
def latlon_to_borneo_rso(lat, lon):
    a = 6378137.0
    f = 1/298.257222101
    k0 = 0.99984
    phi0, lam0 = np.radians(4.0), np.radians(115.0)
    gamma0 = np.radians(18.745783) # Rectified Azimuth
    
    e2 = 2*f - f**2
    e = np.sqrt(e2)
    phi, lam = np.radians(lat), np.radians(lon)

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
    
    east = v * np.cos(gamma0) + u * np.sin(gamma0)
    north = u * np.cos(gamma0) - v * np.sin(gamma0)
    return east, north

# 5. INITIALIZE SESSION STATE
if 'results' not in st.session_state:
    st.session_state.results = None

# 6. SIDEBAR
if os.path.exists("utm.png"):
    st.sidebar.image("utm.png", use_container_width=True)
st.sidebar.title("⚙️ Maklumat Projek")
st.sidebar.info("Sistem ini menggunakan Datum GDM2000 (GRS80) sebagai rujukan utama.")

# 7. ANTARAMUKA UTAMA
st.title("🛰️ Geomatics Chain Transformation")
st.write("WGS84 ➔ UTM (Zone 50N) ➔ Borneo RSO (Zero False Origin)")

col_in, col_out = st.columns(2)
with col_in:
    st.subheader("📥 Input: Koordinat WGS84")
    lat_in = st.number_input("Latitud (Decimal)", value=5.9804, format="%.8f")
    lon_in = st.number_input("Longitud (Decimal)", value=116.0734, format="%.8f")
    
    if st.button("🚀 Jana Koordinat Grid"):
        e_utm, n_utm = latlon_to_utm(lat_in, lon_in)
        e_rso, n_rso = latlon_to_borneo_rso(lat_in, lon_in)
        st.session_state.results = {
            "e_utm": e_utm, "n_utm": n_utm,
            "e_rso": e_rso, "n_rso": n_rso,
            "lat": lat_in, "lon": lon_in
        }

with col_out:
    if st.session_state.results:
        st.subheader("📤 Hasil Transformasi")
        st.markdown(f"""
            <div class="result-card">
                <div class="result-label">UTM ZONE 50N</div>
                <div class="result-value">EASTING: {st.session_state.results['e_utm']:.3f} m<br>NORTHING: {st.session_state.results['n_utm']:.3f} m</div>
            </div>
            <div class="result-card">
                <div class="result-label">BORNEO RSO (GRID)</div>
                <div class="result-value">EASTING: {st.session_state.results['e_rso']:.3f} m<br>NORTHING: {st.session_state.results['n_rso']:.3f} m</div>
            </div>
        """, unsafe_allow_html=True)
        st.balloons()

# 8. PETA VISUAL
if st.session_state.results:
    st.divider()
    m = folium.Map(location=[st.session_state.results['lat'], st.session_state.results['lon']], zoom_start=14)
    folium.Marker([st.session_state.results['lat'], st.session_state.results['lon']], popup="Survey Point").add_to(m)
    st_folium(m, use_container_width=True, height=400, key="geomatics_map")

# 9. MATEMATIK & FORMULA
st.divider()
st.subheader("📖 Prinsip Matematik")

with st.expander("Formula Unjuran"):
    st.write("**Universal Transverse Mercator (UTM)**")
    st.latex(r"E = 500,000 + k_0 A [ \eta + \frac{n}{2} \sin(2\xi) \cosh(2\eta) ]")
    
    st.write("**Borneo Rectified Skew Orthomorphic (RSO)**")
    st.latex(r"E = v \cos \gamma_0 + u \sin \gamma_0, \quad N = u \cos \gamma_0 - v \sin \gamma_0")
    

# 10. FOOTER
st.markdown("""<div style="position: fixed; right: 20px; bottom: 20px; text-align: right; padding: 12px; background-color: rgba(255, 255, 255, 0.4); backdrop-filter: blur(10px); border-right: 5px solid #800000; border-radius: 8px; z-index: 1000;"><p style="color: #800000; font-weight: bold; margin: 0;">DEVELOPED BY:</p><p style="font-size: 13px; color: #002147; margin: 0;">Weil W. | Rebecca J. | Achellis L. | Nor Muhamad | Rowell B.S.</p><p style="font-size: 13px; font-weight: bold; color: #800000; margin-top: 5px;">SBEU 3893 - UTM</p></div>""", unsafe_allow_html=True)
