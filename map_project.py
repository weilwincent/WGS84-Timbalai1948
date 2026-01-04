import streamlit as st
import numpy as np
import base64

# 1. PAGE SETUP
st.set_page_config(
    page_title="Timbalai 1948 Innovation Module", 
    page_icon="📍", 
    layout="wide"
)

# 2. FUNCTION: LOAD LOCAL BACKGROUND IMAGE
def set_bg_local(main_bg):
    try:
        with open(main_bg, "rb") as f:
            bin_str = base64.b64encode(f.read()).decode()
        st.markdown(
            f"""
            <style>
            /* Main App Background */
            .stApp {{
                background-image: url("data:image/png;base64,{bin_str}");
                background-size: cover;
                background-attachment: fixed;
            }}
            
            /* Sky Blue Sidebar Styling */
            [data-testid="stSidebar"] {{
                background-color: #87CEEB !important;
            }}
            
            /* Glassmorphism container for main content readability */
            .main .block-container {{
                background-color: rgba(255, 255, 255, 0.93);
                padding: 3rem;
                border-radius: 25px;
                margin-top: 30px;
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            }}
            
            /* Sidebar Text Color */
            [data-testid="stSidebar"] .stMarkdown {{
                color: #003366;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
    except FileNotFoundError:
        st.warning("⚠️ background.jpg not found on Desktop.")

# Apply background and styles
set_bg_local('background.jpg')

# 3. SIDEBAR: LOGO AND PARAMETERS
try:
    st.sidebar.image("utm.png", use_container_width=True)
except:
    st.sidebar.header("📍 UTM GEOMATICS")

st.sidebar.divider()
st.sidebar.header("⚙️ Timbalai 1948 Parameters")
st.sidebar.write("Input the 7-Parameters for Sabah/Sarawak:")

# Default Timbalai 1948 parameters (Common values)
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

# DARKENED TARGET TEXT FOR BETTER VISIBILITY
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
            
            R = np.array([[1, rz, -ry], [-rz, 1, rx], [ry, -rx, 1]])
            P_wgs = np.array([xw, yw, zw])
            P_out = T + (1 + s_fact) * np.dot(R, P_wgs)
            
            st.success("Transformation Complete!")
            st.metric("Timbalai X", f"{P_out[0]:.3f} m")
            st.metric("Timbalai Y", f"{P_out[1]:.3f} m")
            st.metric("Timbalai Z", f"{P_out[2]:.3f} m")
            st.balloons()

# 6. DOCUMENTATION
st.divider()
with st.expander("📖 View Mathematical Methodology"):
    st.write("This module performs a transformation between ellipsoids using the **Helmert 7-Parameter Model**.")
    st.latex(r'''X_{Local} = T + (1 + S) \cdot R \cdot X_{WGS84}''')