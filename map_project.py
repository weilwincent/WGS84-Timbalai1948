import streamlit as st
import numpy as np
import base64
import os
import folium
from streamlit_folium import st_folium

# 1. PAGE SETUP
# Fixed: Standard Streamlit command to prevent AttributeError
st.set_page_config(page_title="SBEU 3893 - 7-Parameter Module", page_icon="📍", layout="wide")

# 2. CUSTOM STYLING (Steel Blue Sidebar + Glass Effect)
def set_bg_local(main_bg):
    if os.path.exists(main_bg):
        with open(main_bg, "rb") as f:
            bin_str = base64.b64encode(f.read()).decode()
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: url("data:image/png;base64,{bin_str}");
                background-size: cover;
                background-attachment: fixed;
            }}
            [data-testid="stSidebar"] {{
                background-color: #4682B4 !important;
            }}
            [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] p {{
                color: white !important;
            }}
            .main .block-container {{
                background-color: rgba(255, 255, 255, 0.93);
                padding: 3rem;
                border-radius: 25px;
                margin-top: 30px;
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            }}
            /* Map width fix */
            iframe {{ width: 100% !important; border-radius: 15px; }}
            </style>
            """,
            unsafe_allow_html=True
        )

set_bg_local('background.jpg')

# 3. SIDEBAR: LOGO AND PARAMETERS
if os.path.exists("utm.png"):
    st.sidebar.image("utm.png", use_container_width=True)
else:
    st.sidebar.title("📍 UTM GEOMATICS")

st.sidebar.divider()
st.sidebar.header("⚙️ 7-Parameter Inputs")

dx = st.sidebar.number_input("dX (m)", value=596.096, format="%.3f")
dy = st.sidebar.number_input("dY (m)", value=-624.512, format="%.3f")
dz = st.sidebar.number_input("dZ (m)", value=2.779, format="%.3f")

rx_sec = st.sidebar.number_input("rX (arc-sec)", value=-1.446460, format="%.8f")
ry_sec = st.sidebar.number_input("rY (arc-sec)", value=-0.883120, format="%.8f")
rz_sec = st.sidebar.number_input("rZ (arc-sec)", value=1.828440, format="%.8f")
scale_ppm = st.sidebar.number_input("Scale (ppm)", value=-10.454, format="%.8f")

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
    T = np.array([dx, dy, dz])
    S = 1 + (s_ppm / 1000000)
    rx_rad = np.radians(rx / 3600)
    ry_rad = np.radians(ry / 3600)
    rz_rad = np.radians(rz / 3600)
    # Coordinate Frame Rotation Matrix
    R = np.array([
        [1, rz_rad, -ry_rad],
        [-rz_rad, 1, rx_rad],
        [ry_rad, -rx_rad, 1]
    ])
    return T + S * (R @ P_wgs)

# 5. MAIN CONTENT
st.title("🛰️ 7-Parameter Transformation module")
st.markdown("### Geomatics Creative Map and Innovation Competition 2026")

# Use Session State to keep the map and results visible
if 'processed' not in st.session_state:
    st.session_state.processed = False

col1, col2 = st.columns([1, 1])
with col1:
    st.subheader("📥 Input: WGS84")
    lat = st.number_input("Latitude", value=5.573408816, format="%.8f")
    lon = st.number_input("Longitude", value=116.035751582, format="%.8f")
    h = st.number_input("Height (m)", value=48.502, format="%.3f")
    
    if st.button("🚀 Transform & Map"):
        st.session_state.P_wgs = geodetic_to_cartesian(lat, lon, h)
        st.session_state.P_tim = bursa_wolf_transform(st.session_state.P_wgs, dx, dy, dz, rx_sec, ry_sec, rz_sec, scale_ppm)
        st.session_state.lat = lat
        st.session_state.lon = lon
        st.session_state.processed = True

with col2:
    if st.session_state.processed:
        st.subheader("📤 Output: Cartesian")
        st.success("Calculated!")
        st.metric("Timbalai X (m)", f"{st.session_state.P_tim[0]:.3f}")
        st.metric("Timbalai Y (m)", f"{st.session_state.P_tim[1]:.3f}")
        st.metric("Timbalai Z (m)", f"{st.session_state.P_tim[2]:.3f}")
        st.balloons()

# Dedicated Map Section below to prevent blank boxes
if st.session_state.processed:
    st.divider()
    st.subheader("🗺️ Visual Verification")
    m = folium.Map(location=[st.session_state.lat, st.session_state.lon], zoom_start=15)
    folium.Marker([st.session_state.lat, st.session_state.lon], popup="Input Location").add_to(m)
    # use_container_width ensures the map fills the space and removes blank boxes
    st_folium(m, use_container_width=True, height=400)

# 6. THEORY ELABORATION
st.divider()
with st.expander("📖 View Mathematical Model & Elaboration"):
    st.latex(r'''\mathbf{X}_{Local} = \mathbf{T} + (1+S) \mathbf{R} \mathbf{X}_{WGS84}''')
    st.markdown("""
    | Component | Elaboration |
    | :--- | :--- |
    | **dX, dY, dZ** | **Translation:** Adjusts the origin between datums. |
    | **rX, rY, rZ** | **Rotation:** Corrects axial misalignment in arc-seconds. |
    | **S (Scale)** | **Scale Factor:** Compensates for size distortion (ppm). |
    """)

# 7. DEVELOPER CREDITS
# Fixed: Proper string literal formatting to prevent SyntaxError
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
        <p class="footer-text">Weil W. | Rebecca J. | Achellis L. | Nor Muhamad | Rowell B.S.</p>
        <p class="footer-text" style="margin-top:5px; color: #800000;"><b>SBEU 3893 - UTM</b></p>
    </div>
    """, unsafe_allow_html=True
)
