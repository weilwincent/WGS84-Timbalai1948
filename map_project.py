import streamlit as st
import numpy as np
import base64
import os

# 1. PAGE SETUP
st.set_page_config(page_title="7-Parameter RSO Module", page_icon="📍", layout="wide")

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
st.sidebar.header("⚙️ Datum Shift (WGS84 ➔ Timbalai)")

dx = st.sidebar.number_input("dX (m)", value=-679.0, format="%.3f")
dy = st.sidebar.number_input("dY (m)", value=669.0, format="%.3f")
dz = st.sidebar.number_input("dZ (m)", value=-48.0, format="%.3f")

# 4. MATH LOGIC: MOLODENSKY + RSO PROJECTION
# Constants for Everest 1830 (Modified)
a_tim = 6377298.556
f_tim = 1 / 300.8017
e2_tim = 2*f_tim - f_tim**2

def latlon_to_rso(lat, lon):
    """
    Borneo RSO Projection Logic
    """
    # Origin Constants for Borneo RSO
    lat0 = np.radians(4.0)
    lon0 = np.radians(115.0)
    k = 0.99984  # Scale factor at origin
    FE = 0.0     # ADJUSTED: False Easting
    FN = 0.0     # ADJUSTED: False Northing
    
    phi = np.radians(lat)
    lam = np.radians(lon)
    
    # Radius of Curvature & Projection Math
    N = a_tim / np.sqrt(1 - e2_tim * np.sin(phi)**2)
    T = np.tan(phi)**2
    C = e2_tim / (1 - e2_tim) * np.cos(phi)**2
    A = (lam - lon0) * np.cos(phi)
    
    # Meridian Distance Math
    M = a_tim * ((1 - e2_tim/4 - 3*e2_tim**2/64) * phi - (3*e2_tim/8 + 3*e2_tim**2/32) * np.sin(2*phi) + (15*e2_tim**2/256) * np.sin(4*phi))
    M0 = a_tim * ((1 - e2_tim/4 - 3*e2_tim**2/64) * lat0 - (3*e2_tim/8 + 3*e2_tim**2/32) * np.sin(2*lat0) + (15*e2_tim**2/256) * np.sin(4*lat0))
    
    easting = FE + k * N * (A + (1 - T + C) * A**3 / 6 + (5 - 18 * T + T**2 + 72 * C) * A**5 / 120)
    northing = FN + k * (M - M0 + N * np.tan(phi) * (A**2 / 2 + (5 - T + 9 * C + 4 * C**2) * A**4 / 24))
    
    return easting, northing

def molodensky_transform(lat, lon, h, dx, dy, dz):
    a_wgs = 6378137.0
    f_wgs = 1 / 298.257223563
    da = a_tim - a_wgs
    df = f_tim - f_wgs
    phi = np.radians(lat)
    lam = np.radians(lon)
    e2w = 2*f_wgs - f_wgs**2
    M = a_wgs * (1 - e2w) / (1 - e2w * np.sin(phi)**2)**1.5
    N = a_wgs / np.sqrt(1 - e2w * np.sin(phi)**2)
    dphi = (-dx*np.sin(phi)*np.cos(lam) - dy*np.sin(phi)*np.sin(lam) + dz*np.cos(phi) + (a_wgs*df + f_wgs*da)*np.sin(2*phi)) / (M + h)
    dlam = (-dx*np.sin(lam) + dy*np.cos(lam)) / ((N + h) * np.cos(phi))
    return lat + np.degrees(dphi), lon + np.degrees(dlam)

# 5. MAIN CONTENT
st.title("🛰️ Coordinate Transformation Module")
st.markdown("### Geomatics Creative Map and Innovation Competition 2026")
st.markdown("<h4 style='color: #4682B4; font-weight: bold;'>WGS84 Geodetic ➔ Timbalai 1948 RSO (Borneo)</h4>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.subheader("📥 Input: WGS84")
    lat_in = st.number_input("Latitude (Degrees)", value=5.57340882, format="%.8f")
    lon_in = st.number_input("Longitude (Degrees)", value=116.03575158, format="%.8f")
    h_in = st.number_input("Height (m)", value=48.502, format="%.3f")
    
    if st.button("🚀 Calculate Easting & Northing"):
        with col2:
            st.subheader("📤 Output: Borneo RSO")
            # Step 1: Shift Datum to Timbalai
            lat_t, lon_t = molodensky_transform(lat_in, lon_in, h_in, dx, dy, dz)
            # Step 2: Project to Easting/Northing
            e, n = latlon_to_rso(lat_t, lon_t)
            
            st.success("Transformation Successful!")
            st.metric("Easting (E)", f"{e:.3f} m")
            st.metric("Northing (N)", f"{n:.3f} m")
            st.info(f"Target Geodetic: {lat_t:.6f}, {lon_t:.6f}")
            st.balloons()

# 6. THEORY
st.divider()
with st.expander("📖 View Mathematical Process"):
    st.write("WGS84 Geodetic ➔ Molodensky Datum Shift ➔ Borneo RSO Projection (FE=0, FN=0).")
    
    st.latex(r'''E = FE + k N [A + (1 - T + C) \frac{A^3}{6} + ...]''')

# 7. FOOTER
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
        <p class="footer-text">1. Weil W.</p>
        <p class="footer-text">2. Rebecca J.</p>
        <p class="footer-text">3. Achellis L.</p>
        <p class="footer-text">4. Nor Muhamad</p>
        <p class="footer-text">5. Rowell B.S.</p>
        <p class="footer-text" style="margin-top:5px; color: #800000;"><b>SBEU 3893 - UTM</b></p>
    </div>
    """, unsafe_allow_html=True
)