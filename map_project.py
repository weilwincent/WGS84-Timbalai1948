import streamlit as st
import numpy as np
import folium
from streamlit_folium import st_folium
import base64
import os

# 1. PAGE SETUP
st.set_page_config(page_title="SBEU 3893 - Geomatics Suite", page_icon="📍", layout="wide")

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

# 3. MATH ENGINE: UTM PROJECTION (Zone 50N - Sabah)
def latlon_to_utm(lat, lon):
    # WGS84 Ellipsoid
    a = 6378137.0
    f = 1/298.257223563
    k0 = 0.9996 # UTM Scale Factor
    
    phi = np.radians(lat)
    lam = np.radians(lon)
    lam0 = np.radians(117.0) # Central Meridian for Zone 50
    
    e2 = 2*f - f**2
    n = f / (2 - f)
    A = a / (1 + n) * (1 + (n**2)/4 + (n**4)/64)
    
    t = np.sinh(np.arctanh(np.sin(phi)) - (2*np.sqrt(n)/(1+n)) * np.arctanh(2*np.sqrt(n)/(1+n) * np.sin(phi)))
    xi = np.arctan(t / np.cos(lam - lam0))
    eta = np.arctanh(np.sin(lam - lam0) / np.sqrt(1 + t**2))
    
    east = 500000 + k0 * A * (eta + (n/2)*np.sin(2*xi)*np.cosh(2*eta))
    north = k0 * A * (xi + (n/2)*np.cos(2*xi)*np.sinh(2*eta))
    
    return east, north

# 4. MATH ENGINE: BORNEO RSO (Hotine Oblique Mercator)
def latlon_to_borneo_rso(lat, lon):
    # Everest 1830 Parameters (User Correction)
    a = 6377298.556
    f = 1/300.8017
    k0 = 0.99984
    phi0, lam0 = np.radians(4.0), np.radians(115.0)
    gamma0 = np.radians(18.745783) # Azimuth
    
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
    
    # Rectification Rotation
    east = v * np.cos(gamma0) + u * np.sin(gamma0) + 0.0 # Zero False Origin
    north = u * np.cos(gamma0) - v * np.sin(gamma0) + 0.0
    
    return east, north

# 5. INITIALIZE SESSION STATE
if 'results' not in st.session_state:
    st.session_state.results = None

# 6. SIDEBAR
st.sidebar.title("⚙️ Projection Info")
st.sidebar.markdown("**UTM:** Zone 50N (WGS84)\n\n**RSO:** Borneo RSO (Everest 1830)\n\n**False Origin:** 0,0")

# 7. MAIN UI
st.title("🛰️ Geomatics Chain Transformation")
st.write("WGS84 ➔ UTM ➔ Borneo RSO")

col_in, col_out = st.columns(2)
with col_in:
    st.subheader("📥 Input: WGS84")
    lat_in = st.number_input("Latitude", value=5.9804, format="%.8f")
    lon_in = st.number_input("Longitude", value=116.0734, format="%.8f")
    
    if st.button("🚀 Calculate Grid Coordinates"):
        e_utm, n_utm = latlon_to_utm(lat_in, lon_in)
        e_rso, n_rso = latlon_to_borneo_rso(lat_in, lon_in)
        st.session_state.results = {
            "e_utm": e_utm, "n_utm": n_utm,
            "e_rso": e_rso, "n_rso": n_rso,
            "lat": lat_in, "lon": lon_in
        }

with col_out:
    if st.session_state.results:
        st.subheader("📤 Output Grid Values")
        st.markdown(f"""
            <div class="result-card">
                <div class="result-label">UTM ZONE 50N (WGS84)</div>
                <div class="result-value">EAST: {st.session_state.results['e_utm']:.3f} m<br>NORTH: {st.session_state.results['n_utm']:.3f} m</div>
            </div>
            <div class="result-card">
                <div class="result-label">BORNEO RSO (Everest 1830)</div>
                <div class="result-value">EAST: {st.session_state.results['e_rso']:.3f} m<br>NORTH: {st.session_state.results['n_rso']:.3f} m</div>
            </div>
        """, unsafe_allow_html=True)
        st.balloons()

# 8. MAP
if st.session_state.results:
    st.divider()
    m = folium.Map(location=[st.session_state.results['lat'], st.session_state.results['lon']], zoom_start=14)
    folium.Marker([st.session_state.results['lat'], st.session_state.results['lon']], popup="Survey Point").add_to(m)
    st_folium(m, use_container_width=True, height=400, key="chain_map")

# 9. MATHEMATICAL PRINCIPLES
st.divider()
st.subheader("📖 Projection Logic")

with st.expander("Universal Transverse Mercator (UTM)"):
    st.write("UTM divides the Earth into 60 zones. Sabah falls into Zone 50 North. It uses a Transverse Mercator projection where the scale is constant along the Central Meridian.")
    st.latex(r"E = 500,000 + k_0 A [ \eta + \frac{n}{2} \sin(2\xi) \cosh(2\eta) ]")


with st.expander("Borneo Rectified Skew Orthomorphic (RSO)"):
    st.write("RSO is an Oblique Mercator projection. It is 'Rectified' because the grid is rotated to align with the geography of Borneo. This version uses the Everest 1830 ellipsoid.")
    st.latex(r"E = v \cos \gamma_0 + u \sin \gamma_0, \quad N = u \cos \gamma_0 - v \sin \gamma_0")

# 10. FOOTER
st.markdown("""<div style="position: fixed; right: 20px; bottom: 20px; text-align: right; padding: 12px; background-color: rgba(255, 255, 255, 0.4); backdrop-filter: blur(10px); border-right: 5px solid #800000; border-radius: 8px; z-index: 1000;"><p style="color: #800000; font-weight: bold; margin: 0;">DEVELOPED BY:</p><p style="font-size: 13px; color: #002147; margin: 0;">Weil W. | Rebecca J. | Achellis L. | Nor Muhamad | Rowell B.S.</p><p style="font-size: 13px; font-weight: bold; color: #800000; margin-top: 5px;">SBEU 3893 - UTM</p></div>""", unsafe_allow_html=True)
