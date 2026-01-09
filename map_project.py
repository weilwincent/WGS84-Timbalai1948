import streamlit as st
import numpy as np
import folium
from streamlit_folium import st_folium
import base64
import os

# 1. PAGE SETUP
st.set_page_config(page_title="SBEU 3893 - Geomatics Module", page_icon="📍", layout="wide")

# 2. CUSTOM STYLING (Original Steel Blue)
def set_bg_local(main_bg):
    if os.path.exists(main_bg):
        with open(main_bg, "rb") as f:
            bin_str = base64.b64encode(f.read()).decode()
        st.markdown(f"""
            <style>
            .stApp {{ background-image: url("data:image/png;base64,{bin_str}"); background-size: cover; background-attachment: fixed; }}
            [data-testid="stSidebar"] {{ background-color: #4682B4 !important; }}
            [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] p {{ color: white !important; }}
            .main .block-container {{ background-color: rgba(255, 255, 255, 0.93); padding: 2rem; border-radius: 20px; margin-top: 20px; }}
            iframe {{ width: 100% !important; border-radius: 10px; }}
            </style>
            """, unsafe_allow_html=True)

if os.path.exists('background.jpg'):
    set_bg_local('background.jpg')

# 3. INITIALIZE SESSION STATE
if 'results' not in st.session_state:
    st.session_state.results = None
if 'balloons_fired' not in st.session_state:
    st.session_state.balloons_fired = False

# 4. MATH ENGINE: FULL DATUM TRANSFORMATION (BURSA-WOLF + REVERSE GEODETIC)
def full_transformation(lat, lon, h, dx, dy, dz, rx_s, ry_s, rz_s, s_ppm):
    # WGS84 Constants
    a_w, f_w = 6378137.0, 1/298.257223563
    e2_w = (2*f_w) - (f_w**2)
    
    # 1. WGS84 Geodetic to Cartesian
    phi, lam = np.radians(lat), np.radians(lon)
    N_w = a_w / np.sqrt(1 - e2_w * np.sin(phi)**2)
    Xw = (N_w + h) * np.cos(phi) * np.cos(lam)
    Yw = (N_w + h) * np.cos(phi) * np.sin(lam)
    Zw = (N_w * (1 - e2_w) + h) * np.sin(phi)
    
    # 2. Bursa-Wolf 7-Parameter Shift
    T = np.array([dx, dy, dz])
    S = 1 + (s_ppm / 1000000)
    rx, ry, rz = np.radians(rx_s/3600), np.radians(ry_s/3600), np.radians(rz_s/3600)
    R = np.array([[1, rz, -ry], [-rz, 1, rx], [ry, -rx, 1]])
    P_tim_cart = T + S * (R @ np.array([Xw, Yw, Zw]))
    
    # 3. Cartesian to Timbalai Geodetic (Everest 1830 Ellipsoid)
    # Everest 1830 Parameters
    a_e, f_e = 6377298.556, 1/300.8017
    e2_e = (2*f_e) - (f_e**2)
    
    x, y, z = P_tim_cart
    lon_tim = np.arctan2(y, x)
    p = np.sqrt(x**2 + y**2)
    phi_tim = np.arctan2(z, p * (1 - e2_e))
    
    # Iterative calculation for high precision latitude
    for _ in range(5):
        N_e = a_e / np.sqrt(1 - e2_e * np.sin(phi_tim)**2)
        phi_tim = np.arctan2(z + e2_e * N_e * np.sin(phi_tim), p)
    
    h_tim = p / np.cos(phi_tim) - N_e
    return np.degrees(phi_tim), np.degrees(lon_tim), h_tim

# 5. SIDEBAR
if os.path.exists("utm.png"):
    st.sidebar.image("utm.png", use_container_width=True)

st.sidebar.title("⚙️ Parameters")
dx = st.sidebar.number_input("dX (m)", value=596.096, format="%.3f")
dy = st.sidebar.number_input("dY (m)", value=-624.512, format="%.3f")
dz = st.sidebar.number_input("dZ (m)", value=2.779, format="%.3f")
rx_s = st.sidebar.number_input("rX (arc-sec)", value=-1.446460, format="%.6f")
ry_s = st.sidebar.number_input("rY (arc-sec)", value=-0.883120, format="%.6f")
rz_s = st.sidebar.number_input("rZ (arc-sec)", value=1.828440, format="%.6f")
scale_p = st.sidebar.number_input("Scale (ppm)", value=-10.454, format="%.6f")

# 6. MAIN UI
st.title("🛰️ Geodetic Datum Transformation")
st.write("WGS84 to Timbalai 1948 (Lat/Long Output)")

col_in, col_out = st.columns(2)
with col_in:
    st.subheader("📥 Input: WGS84")
    lat_in = st.number_input("Latitude", value=5.573408816, format="%.9f")
    lon_in = st.number_input("Longitude", value=116.035751582, format="%.9f")
    h_in = st.number_input("Height (m)", value=48.502, format="%.3f")
    
    if st.button("🚀 Transform to Timbalai"):
        st.session_state.balloons_fired = False 
        lat_t, lon_t, h_t = full_transformation(lat_in, lon_in, h_in, dx, dy, dz, rx_s, ry_s, rz_s, scale_p)
        st.session_state.results = {"lat_t": lat_t, "lon_t": lon_t, "h_t": h_t, "lat_orig": lat_in, "lon_orig": lon_in}

with col_out:
    if st.session_state.results:
        st.subheader("📤 Output: Timbalai 1948")
        st.metric("Latitude", f"{st.session_state.results['lat_t']:.9f}°")
        st.metric("Longitude", f"{st.session_state.results['lon_t']:.9f}°")
        st.metric("Height (m)", f"{st.session_state.results['h_t']:.3f}")
        
        if not st.session_state.balloons_fired:
            st.balloons()
            st.session_state.balloons_fired = True

# 7. MATHEMATICAL FORMULAS
st.divider()
st.subheader("📖 Mathematical Principles")
with st.expander("View Reverse Geodetic Formula", expanded=True):
    st.write("To convert Cartesian back to Latitude ($\phi$), we use the iterative Bowring's method:")
    st.latex(r"\phi_{i+1} = \arctan \left( \frac{Z + e^2 N_i \sin \phi_i}{p} \right)")
    st.write("Where $p = \sqrt{X^2 + Y^2}$ and $N$ is the radius of curvature.")

# 8. MAP ROW
if st.session_state.results:
    st.divider()
    st.subheader("🗺️ Visual Verification")
    m = folium.Map(location=[st.session_state.results['lat_orig'], st.session_state.results['lon_orig']], zoom_start=15)
    folium.Marker([st.session_state.results['lat_orig'], st.session_state.results['lon_orig']], popup="Survey Point").add_to(m)
    st_folium(m, use_container_width=True, height=400)

# 9. FOOTER
st.markdown("""
    <div style="position: fixed; right: 20px; bottom: 20px; text-align: right; padding: 12px; 
    background-color: rgba(255, 255, 255, 0.4); backdrop-filter: blur(10px); border-right: 5px solid #800000; 
    border-radius: 8px; z-index: 1000;">
        <p style="color: #800000; font-weight: bold; margin: 0;">DEVELOPED BY:</p>
        <p style="font-size: 13px; color: #002147; margin: 0;">Weil W. | Rebecca J. | Achellis L. | Nor Muhamad | Rowell B.S.</p>
        <p style="font-size: 13px; font-weight: bold; color: #800000; margin-top: 5px;">SBEU 3893 - UTM</p>
    </div>
    """, unsafe_allow_html=True)
