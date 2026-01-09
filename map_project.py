import streamlit as st
import numpy as np
import base64
import os

# 1. PAGE SETUP
st.set_page_config(page_title="7-Parameter Module", page_icon="📍", layout="wide")

# 2. CUSTOM STYLING (Darker Steel Blue Sidebar + Glass Effect)
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
st.sidebar.header("⚙️ Transformation Parameters")

# Standard Shifts for WGS84 to Timbalai 1948
dx = st.sidebar.number_input("dX (m)", value=679.0, format="%.3f")
dy = st.sidebar.number_input("dY (m)", value=-669.0, format="%.3f")
dz = st.sidebar.number_input("dZ (m)", value=48.0, format="%.3f")

# 4. MATH LOGIC: SIMPLE MOLODENSKY
# WGS84 Ellipsoid (Source)
a_w = 6378137.0
f_w = 1 / 298.257223563
# Everest 1830 Modified (Target - Timbalai 1948)
a_t = 6377298.556
f_t = 1 / 300.8017

def molodensky_transform(lat, lon, h, dx, dy, dz):
    phi = np.radians(lat)
    lam = np.radians(lon)
    
    da = a_t - a_w
    df = f_t - f_w
    
    e2 = 2 * f_w - f_w**2
    
    sin_phi = np.sin(phi)
    cos_phi = np.cos(phi)
    sin_lam = np.sin(lam)
    cos_lam = np.cos(lam)
    
    # Radius of curvature in meridian and prime vertical
    M = a_w * (1 - e2) / (1 - e2 * sin_phi**2)**1.5
    N = a_w / np.sqrt(1 - e2 * sin_phi**2)
    
    # Molodensky Formulas for shift in Geodetic Coordinates
    dphi = (-dx * sin_phi * cos_lam - dy * sin_phi * sin_lam + dz * cos_phi + (a_w * df + f_w * da) * np.sin(2 * phi)) / (M + h)
    dlam = (-dx * sin_lam + dy * cos_lam) / ((N + h) * cos_phi)
    dh = dx * cos_phi * cos_lam + dy * cos_phi * sin_lam + dz * sin_phi - (a_w * df + f_w * da) * sin_phi**2 + da
    
    return lat + np.degrees(dphi), lon + np.degrees(dlam), h + dh

# 5. MAIN CONTENT
st.title("🛰️ Coordinate Transformation Module")
st.markdown("### Geomatics Creative Map and Innovation Competition 2026")
st.markdown("<h4 style='color: #4682B4; font-weight: bold;'>Method: Simple Molodensky Transformation</h4>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.subheader("📥 Input: WGS84")
    lat_in = st.number_input("Latitude", value=5.573408816, format="%.8f")
    lon_in = st.number_input("Longitude", value=116.035751582, format="%.8f")
    h_in = st.number_input("Height (m)", value=48.502, format="%.3f")
    
    if st.button("🚀 Transform (Molodensky)"):
        with col2:
            st.subheader("📤 Output: Timbalai 1948")
            lat_out, lon_out, h_out = molodensky_transform(lat_in, lon_in, h_in, dx, dy, dz)
            
            st.success("Calculated!")
            st.metric("Timbalai Latitude", f"{lat_out:.8f}°")
            st.metric("Timbalai Longitude", f"{lon_out:.8f}°")
            st.metric("Timbalai Height (m)", f"{h_out:.3f}")
            st.balloons()

# 6. THEORY & FORMULA ELABORATION
st.divider()
with st.expander("📖 View Mathematical Model & Elaboration"):
    st.write("The Simple Molodensky transformation provides a direct method to shift geodetic coordinates between datums without converting to Cartesian $X, Y, Z$.")
    
    st.latex(r'''\Delta\phi = \frac{-dx\sin\phi\cos\lambda - dy\sin\phi\sin\lambda + dz\cos\phi + (adf+fda)\sin2\phi}{M+h}''')
    st.markdown("""
    | Component | Elaboration |
    | :--- | :--- |
    | **dX, dY, dZ** | Translation parameters from WGS84 to Timbalai 1948. |
    | **da, df** | Difference in semi-major axis and flattening between ellipsoids. |
    | **M, N** | Radii of curvature (Meridian and Prime Vertical). |
    """)

# 7. DEVELOPER CREDITS (Transparent Glass Footer)
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
        <p class="footer-text">Rowell B.S.</p>
        <p class="footer-text" style="margin-top:5px; color: #800000;"><b>SBEU 3893</b></p>
    </div>
    """, unsafe_allow_html=True

)
