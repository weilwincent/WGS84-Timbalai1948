import streamlit as st
import numpy as np
import pandas as pd
import folium
from streamlit_folium import st_folium
import base64
import os

# 1. PAGE SETUP
st.set_page_config(page_title="SBEU 3893 - Geomatics Transformation", page_icon="📍", layout="wide")

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

# 4. MATH ENGINES
def bursa_wolf_transform(lat, lon, h, dx, dy, dz, rx_s, ry_s, rz_s, s_ppm):
    # WGS84 Constants
    a_w, f_inv_w = 6378137.0, 298.257223563
    f_w = 1/f_inv_w
    e2w = (2*f_w) - (f_w**2)
    
    phi, lam = np.radians(lat), np.radians(lon)
    N = a_w / np.sqrt(1 - e2w * np.sin(phi)**2)
    
    # Geodetic to Cartesian
    Xw = (N + h) * np.cos(phi) * np.cos(lam)
    Yw = (N + h) * np.cos(phi) * np.sin(lam)
    Zw = (N * (1 - e2w) + h) * np.sin(phi)
    P_wgs = np.array([Xw, Yw, Zw])
    
    # 7-Parameter Transformation
    T = np.array([dx, dy, dz])
    S = 1 + (s_ppm / 1000000)
    rx, ry, rz = np.radians(rx_s/3600), np.radians(ry_s/3600), np.radians(rz_s/3600)
    R = np.array([
        [1, rz, -ry],
        [-rz, 1, rx],
        [ry, -rx, 1]
    ])
    P_local = T + S * (R @ P_wgs)
    return P_local

# 5. SIDEBAR
st.sidebar.title("⚙️ Parameters")
dx = st.sidebar.number_input("dX (m)", value=596.096, format="%.3f")
dy = st.sidebar.number_input("dY (m)", value=-624.512, format="%.3f")
dz = st.sidebar.number_input("dZ (m)", value=2.779, format="%.3f")
rx_s = st.sidebar.number_input("rX (arc-sec)", value=-1.446460, format="%.6f")
ry_s = st.sidebar.number_input("rY (arc-sec)", value=-0.883120, format="%.6f")
rz_s = st.sidebar.number_input("rZ (arc-sec)", value=1.828440, format="%.6f")
scale_p = st.sidebar.number_input("Scale (ppm)", value=-10.454, format="%.6f")

# 6. MAIN UI
st.title("🛰️ 7-Parameter Transformation Module")

col_in, col_out = st.columns(2)
with col_in:
    st.subheader("📥 Input: WGS84")
    lat_in = st.number_input("Latitude", value=5.573408816, format="%.9f")
    lon_in = st.number_input("Longitude", value=116.035751582, format="%.9f")
    h_in = st.number_input("Height (m)", value=48.502, format="%.3f")
    
    if st.button("🚀 Transform Point"):
        st.session_state.balloons_fired = False 
        P_tim = bursa_wolf_transform(lat_in, lon_in, h_in, dx, dy, dz, rx_s, ry_s, rz_s, scale_p)
        st.session_state.results = {"X": P_tim[0], "Y": P_tim[1], "Z": P_tim[2], "lat": lat_in, "lon": lon_in}

with col_out:
    if st.session_state.results:
        st.subheader("📤 Output: Timbalai 1948")
        st.metric("Timbalai X (m)", f"{st.session_state.results['X']:.3f}")
        st.metric("Timbalai Y (m)", f"{st.session_state.results['Y']:.3f}")
        st.metric("Timbalai Z (m)", f"{st.session_state.results['Z']:.3f}")
        
        if not st.session_state.balloons_fired:
            st.balloons()
            st.session_state.balloons_fired = True

# 7. MATHEMATICAL FORMULA SECTION
st.divider()
st.subheader("📖 Mathematical Principles")
with st.expander("View Transformation Formulas", expanded=True):
    st.markdown("### 1. Geodetic to Cartesian Conversion")
    st.write("First, the input Geodetic coordinates are converted to Earth-Centered, Earth-Fixed (ECEF) Cartesian coordinates:")
    st.latex(r"X = (N + h) \cos \phi \cos \lambda")
    st.latex(r"Y = (N + h) \cos \phi \sin \lambda")
    st.latex(r"Z = [N(1 - e^2) + h] \sin \phi")
    st.write("Where $N$ is the radius of curvature in the prime vertical:")
    st.latex(r"N = \frac{a}{\sqrt{1 - e^2 \sin^2 \phi}}")
    
    st.divider()
    st.markdown("### 2. Bursa-Wolf 7-Parameter Model")
    st.write("The coordinates are shifted to the local datum (Timbalai 1948) using translation, rotation, and scale factors:")
    st.latex(r"\mathbf{X}_{Local} = \mathbf{T} + (1+S) \mathbf{R} \mathbf{X}_{WGS84}")
    st.write("Where $\mathbf{R}$ is the rotation matrix:")
    st.latex(r'''R = \begin{bmatrix} 1 & r_z & -r_y \\ -r_z & 1 & r_x \\ r_y & -r_x & 1 \end{bmatrix}''')

# 8. MAP ROW
if st.session_state.results:
    st.divider()
    st.subheader("🗺️ Visual Verification")
    m = folium.Map(location=[st.session_state.results['lat'], st.session_state.results['lon']], zoom_start=15)
    folium.Marker([st.session_state.results['lat'], st.session_state.results['lon']], popup="Survey Point").add_to(m)
    st_folium(m, use_container_width=True, height=400, key="borneo_map")

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
