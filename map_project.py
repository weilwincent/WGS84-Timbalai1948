import streamlit as st
import numpy as np
import base64
import os

# 1. PAGE SETUP
st.set_page_config(page_title="Timbalai 1948 Molodensky Module", page_icon="📍", layout="wide")

# 2. CUSTOM STYLING (Dark Blue Sidebar + Glass Effect)
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

# 3. SIDEBAR: LOGO AND MOLODENSKY PARAMETERS
if os.path.exists("utm.png"):
    st.sidebar.image("utm.png", use_container_width=True)
st.sidebar.divider()
st.sidebar.header("⚙️ Molodensky Parameters")

# Standard WGS84 to Timbalai 1948 Shifts (Sabah/Sarawak)
dx = st.sidebar.number_input("dX (m)", value=-679.0)
dy = st.sidebar.number_input("dY (m)", value=669.0)
dz = st.sidebar.number_input("dZ (m)", value=-48.0)

# 4. ELLIPSOID CONSTANTS
# WGS84
a_wgs = 6378137.0
f_wgs = 1 / 298.257223563
# Timbalai (Everest 1830 Modified)
a_tim = 6377276.345
f_tim = 1 / 300.8017

def molodensky_transform(lat, lon, h, dx, dy, dz):
    phi = np.radians(lat)
    lam = np.radians(lon)
    
    da = a_tim - a_wgs
    df = f_tim - f_wgs
    
    e2 = 2*f_wgs - f_wgs**2
    sin_phi = np.sin(phi)
    cos_phi = np.cos(phi)
    sin_lam = np.sin(lam)
    cos_lam = np.cos(lam)
    
    # Radius of curvature in prime vertical and meridian
    M = a_wgs * (1 - e2) / (1 - e2 * sin_phi**2)**1.5
    N = a_wgs / np.sqrt(1 - e2 * sin_phi**2)
    
    # Molodensky Formulas for dPhi, dLam, dH
    dphi = (-dx*sin_phi*cos_lam - dy*sin_phi*sin_lam + dz*cos_phi + 
            (a_wgs*df + f_wgs*da)*np.sin(2*phi)) / (M + h)
            
    dlam = (-dx*sin_lam + dy*cos_lam) / ((N + h) * cos_phi)
    
    dh = dx*cos_phi*cos_lam + dy*cos_phi*sin_lam + dz*sin_phi - (a_wgs*df + f_wgs*da)*sin_phi**2 + da
    
    return lat + np.degrees(dphi), lon + np.degrees(dlam), h + dh

# 5. MAIN CONTENT
st.title("🛰️ Molodensky Transformation Innovation")
st.markdown("### Geomatics Creative Map and Innovation Competition 2026")
st.markdown("<h4 style='color: #191970;'>WGS84 Geodetic ➔ Timbalai 1948 Geodetic</h4>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.subheader("📥 Input: WGS84")
    lat_in = st.number_input("Latitude", value=5.000000, format="%.8f")
    lon_in = st.number_input("Longitude", value=115.000000, format="%.8f")
    h_in = st.number_input("Ellipsoidal Height (m)", value=0.0)
    
    if st.button("🚀 Transform (Molodensky)"):
        with col2:
            st.subheader("📤 Output: Timbalai 1948")
            lat_out, lon_out, h_out = molodensky_transform(lat_in, lon_in, h_in, dx, dy, dz)
            
            st.success("Transformation Successful!")
            st.metric("Timbalai Latitude", f"{lat_out:.8f}°")
            st.metric("Timbalai Longitude", f"{lon_out:.8f}°")
            st.metric("Timbalai Height", f"{h_out:.3f} m")
            st.balloons()

# 6. THEORY (Important for your Report)
with st.expander("📖 Why Molodensky?"):
    st.write("The Molodensky method is an abridged datum transformation that operates directly on geodetic coordinates.")
    st.latex(r'''\Delta\phi = \frac{-dx\sin\phi\cos\lambda - dy\sin\phi\sin\lambda + dz\cos\phi + (adf+fda)\sin2\phi}{M+h}''')

# 7. DEVELOPER CREDITS
st.markdown(
    f"""
    <div style="position: fixed; right: 20px; bottom: 20px; text-align: right; padding: 12px; 
    background-color: rgba(255, 255, 255, 0.4); backdrop-filter: blur(10px); border-right: 5px solid #800000;
    border-radius: 8px; font-family: 'Arial'; z-index: 1000;">
        <p style="color: #800000; font-weight: bold; margin: 0;">DEVELOPED BY:</p>
        <p style="font-size: 13px; color: #191970; margin: 0;">Weil W., Rebecca J., Achellis L., Nor Muhamad, Rowell B.S</p>
        <p style="font-size: 13px; font-weight: bold; color: #800000; margin-top: 5px;">3 SGHU - UTM FABU</p>
    </div>
    """, unsafe_allow_html=True
)