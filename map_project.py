import streamlit as st
import numpy as np
import base64
import os

# 1. PAGE SETUP
st.set_page_config(page_title="7-Parameter Bursa-Wolf Module", page_icon="📍", layout="wide")

# 2. CUSTOM STYLING (Midnight Blue Sidebar + Glass Effect)
def set_bg_local(main_bg):
    if os.path.exists(main_bg):
        with open(main_bg, "rb") as f:
            bin_str = base64.b64encode(f.read()).decode()
        st.markdown(
            f"""
            <style>
            .stApp {{ background-image: url("data:image/png;base64,{bin_str}"); background-size: cover; background-attachment: fixed; }}
            [data-testid="stSidebar"] {{ background-color: #191970 !important; }}
            [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] p {{ color: white !important; }}
            .main .block-container {{ background-color: rgba(255, 255, 255, 0.93); padding: 3rem; border-radius: 25px; margin-top: 30px; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3); }}
            </style>
            """,
            unsafe_allow_html=True
        )

set_bg_local('background.jpg')

# 3. SIDEBAR: PARAMETERS
if os.path.exists("utm.png"):
    st.sidebar.image("utm.png", use_container_width=True)
st.sidebar.divider()
st.sidebar.header("⚙️ 7-Parameter Inputs")

# Translation
dx = st.sidebar.number_input("dX (m)", value=-679.0)
dy = st.sidebar.number_input("dY (m)", value=669.0)
dz = st.sidebar.number_input("dZ (m)", value=-48.0)
# Rotation (arc-seconds)
rx_sec = st.sidebar.number_input("rX (arc-sec)", value=0.0)
ry_sec = st.sidebar.number_input("rY (arc-sec)", value=0.0)
rz_sec = st.sidebar.number_input("rZ (arc-sec)", value=0.0)
# Scale (ppm)
scale_ppm = st.sidebar.number_input("Scale (ppm)", value=0.0)

# 4. MATH LOGIC: BURSA-WOLF 7-PARAMETER
A_WGS = 6378137.0
F_WGS = 1 / 298.257223563
E2_WGS = (2 * F_WGS) - (F_WGS ** 2)

def geodetic_to_cartesian(lat, lon, h):
    phi = np.radians(lat)
    lam = np.radians(lon)
    N = A_WGS / np.sqrt(1 - E2_WGS * np.sin(phi)**2)
    X = (N + h) * np.cos(phi) * np.cos(lam)
    Y = (N + h) * np.cos(phi) * np.sin(lam)
    Z = (N * (1 - E2_WGS) + h) * np.sin(phi)
    return np.array([X, Y, Z])

def bursa_wolf_transform(P_wgs, dx, dy, dz, rx, ry, rz, s_ppm):
    # Convert parameters
    T = np.array([dx, dy, dz])
    S = 1 + (s_ppm / 1000000)
    # Convert arc-seconds to radians
    rx_rad = np.radians(rx / 3600)
    ry_rad = np.radians(ry / 3600)
    rz_rad = np.radians(rz / 3600)
    
    # Rotation Matrix (Bursa-Wolf)
    R = np.array([
        [1, rz_rad, -ry_rad],
        [-rz_rad, 1, rx_rad],
        [ry_rad, -rx_rad, 1]
    ])
    
    # 7-Parameter Formula
    P_local = T + S * (R @ P_wgs)
    return P_local

# 5. MAIN CONTENT
st.title("🛰️ 7-Parameter Transformation Innovation")
st.markdown("### Geomatics Creative Map and Innovation Competition 2026")
st.markdown("<h4 style='color: #191970; font-weight: bold;'>Method: Bursa-Wolf 7-Parameter Model</h4>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.subheader("📥 Input: WGS84")
    lat = st.number_input("Latitude", value=5.0, format="%.8f")
    lon = st.number_input("Longitude", value=115.0, format="%.8f")
    h = st.number_input("Height (m)", value=0.0)
    
    if st.button("🚀 Transform (7-Param)"):
        with col2:
            st.subheader("📤 Output: Timbalai 1948")
            P_wgs = geodetic_to_cartesian(lat, lon, h)
            P_tim = bursa_wolf_transform(P_wgs, dx, dy, dz, rx_sec, ry_sec, rz_sec, scale_ppm)
            
            st.success("Calculated!")
            st.metric("Timbalai X", f"{P_tim[0]:.3f} m")
            st.metric("Timbalai Y", f"{P_tim[1]:.3f} m")
            st.metric("Timbalai Z", f"{P_tim[2]:.3f} m")
            st.balloons()

# 6. THEORY
st.divider()
with st.expander("📖 View Mathematical Model"):
    st.write("The 7-Parameter Bursa-Wolf model is defined as:")
    
    st.latex(r'''\begin{bmatrix} X \\ Y \\ Z \end{bmatrix}_{Local} = \begin{bmatrix} dX \\ dY \\ dZ \end{bmatrix} + (1+S) \begin{bmatrix} 1 & rZ & -rY \\ -rZ & 1 & rX \\ rY & -rX & 1 \end{bmatrix} \begin{bmatrix} X \\ Y \\ Z \end{bmatrix}_{WGS84}''')

# 7. DEVELOPER CREDITS
st.markdown(
    """
    <style>
    .footer-box {
        position: fixed; right: 20px; bottom: 20px; text-align: right; padding: 12px;
        background-color: rgba(255, 255, 255, 0.4); backdrop-filter: blur(10px); 
        border-right: 5px solid #800000; border-radius: 8px; font-family: 'Arial'; z-index: 1000;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1); border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .footer-text { font-size: 13px; color: #002147; margin: 0; line-height: 1.4; font-weight: bold; }
    .group-title { font-size: 14px; font-weight: bold; color: #800000; margin-bottom: 4px; }
    </style>
    <div class="footer-box">
        <div class="group-title">DEVELOPED BY:</div>
        <p class="footer-text">Weil W.</p>
        <p class="footer-text">Rebecca J.</p>
        <p class="footer-text">Achellis L.</p>
        <p class="footer-text">Nor Muhamad</p>
        <p class="footer-text">Rowell B.S</p>
        <p class="footer-text" style="margin-top:5px; color: #800000;"><b>SBEU 3893</b></p>
    </div>
    """, unsafe_allow_html=True
)