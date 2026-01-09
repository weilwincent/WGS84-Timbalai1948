import streamlit as st
import numpy as np
import base64
import os

# 1. PAGE SETUP
st.set_page_config(
    page_title="Timbalai 1948 Innovation Module", 
    page_icon="📍", 
    layout="wide"
)

# 2. FUNCTION: LOAD BACKGROUND (Cloud-Compatible)
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
            /* Sidebar Color: Sky Blue */
            [data-testid="stSidebar"] {{
                background-color: #87CEEB !important;
            }}
            /* Main Content Container (Glass effect) */
            .main .block-container {{
                background-color: rgba(255, 255, 255, 0.93);
                padding: 3rem;
                border-radius: 25px;
                margin-top: 30px;
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            }}
            </style>
            """,
            unsafe_allow_html=True
        )

# Apply styling and background
set_bg_local('background.jpg')

# 3. SIDEBAR: LOGO AND PARAMETERS
if os.path.exists("utm.png"):
    st.sidebar.image("utm.png", use_container_width=True)
else:
    st.sidebar.title("📍 UTM GEOMATICS")

st.sidebar.divider()
st.sidebar.header("⚙️ Timbalai 1948 Parameters")

# Input the 7-Parameters for Sabah/Sarawak
tx = st.sidebar.number_input("Translation dX (m)", value=-679.0)
ty = st.sidebar.number_input("Translation dY (m)", value=669.0)
tz = st.sidebar.number_input("Translation dZ (m)", value=-48.0)
scale = st.sidebar.number_input("Scale (ppm)", value=0.0)
rx_s = st.sidebar.number_input("rX (arc-sec)", value=0.0)
ry_s = st.sidebar.number_input("rY (arc-sec)", value=0.0)
rz_s = st.sidebar.number_input("rZ (arc-sec)", value=0.0)

# 4. MATH LOGIC: WGS84 TO CARTESIAN
A_WGS = 6378137.0
F_WGS = 1 / 298.257223563
E2_WGS = (2 * F_WGS) - (F_WGS ** 2)

def geodetic_to_cartesian(lat, lon, h):
    lat_r = np.radians(lat)
    lon_r = np.radians(lon)
    N = A_WGS / np.sqrt(1 - E2_WGS * np.sin(lat_r)**2)
    X = (N + h) * np.cos(lat_r) * np.cos(lon_r)
    Y = (N + h) * np.cos(lat_r) * np.sin(lon_r)
    Z = (N * (1 - E2_WGS) + h) * np.sin(lat_r)
    return X, Y, Z

# 5. MAIN CONTENT
st.title("🛰️ Coordinate Transformation Innovation")
st.markdown("### Geomatics Creative Map and Innovation Competition 2026")
st.markdown("<h4 style='color: #002147; font-weight: bold;'>Target: WGS84 Geodetic to Timbalai 1948 Cartesian</h4>", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.subheader("📥 Input: WGS84 (GPS)")
    lat_in = st.number_input("Latitude (Degrees)", value=5.000000, format="%.8f")
    lon_in = st.number_input("Longitude (Degrees)", value=115.000000, format="%.8f")
    h_in = st.number_input("Height (m)", value=0.0)
    
    if st.button("🚀 Run Transformation"):
        with col2:
            st.subheader("📤 Output: Timbalai 1948")
            xw, yw, zw = geodetic_to_cartesian(lat_in, lon_in, h_in)
            
            T = np.array([tx, ty, tz])
            s_fact = scale / 1000000
            rx = np.radians(rx_s / 3600)
            ry = np.radians(ry_s / 3600)
            rz = np.radians(rz_s / 3600)
            
            # Helmert Rotation Matrix
            R = np.array([[1, rz, -ry], [-rz, 1, rx], [ry, -rx, 1]])
            P_out = T + (1 + s_fact) * np.dot(R, np.array([xw, yw, zw]))
            
            st.success("Transformation Complete!")
            st.metric("Timbalai X", f"{P_out[0]:.3f} m")
            st.metric("Timbalai Y", f"{P_out[1]:.3f} m")
            st.metric("Timbalai Z", f"{P_out[2]:.3f} m")
            st.balloons()

# 6. THEORY SECTION
st.divider()
with st.expander("📖 View Mathematical Methodology"):
    st.write("Calculated using the Helmert 7-Parameter Model for datum shifts.")
    st.latex(r'''X_{Local} = T + (1 + S) \cdot R \cdot X_{WGS84}''')

# 7. DEVELOPER CREDITS (Transparent Glass Footer)
st.markdown(
    """
    <style>
    .footer-box {
        position: fixed;
        right: 20px;
        bottom: 20px;
        text-align: right;
        padding: 12px;
        background-color: rgba(255, 255, 255, 0.4); 
        backdrop-filter: blur(10px); 
        border-right: 5px solid #800000;
        border-radius: 8px;
        font-family: 'Arial';
        z-index: 1000;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .footer-text { font-size: 13px; color: #002147; margin: 0; line-height: 1.4; font-weight: bold; }
    .group-title { font-size: 14px; font-weight: bold; color: #800000; margin-bottom: 4px; }
    </style>
    <div class="footer-box">
        <div class="group-title">DEVELOPED BY:</div>
        <p class="footer-text">1. Weil W.</p>
        <p class="footer-text">2. Rebecca J.</p>
        <p class="footer-text">3. Achellis L.</p>
        <p class="footer-text">4. Nor Muhamad</p>
        <p class="footer-text">5. Rowell B.S</p>
        <p class="footer-text" style="margin-top:5px; color: #800000;"><b>3 SGHU - UTM FABU</b></p>
    </div>
    """,
    unsafe_allow_html=True
)