import streamlit as st
import numpy as np
import base64
import os

# 1. PAGE SETUP
st.set_page_config(page_title="7-Parameter HOM Module", page_icon="📍", layout="wide")

# 2. CUSTOM STYLING (Darker Steel Blue Sidebar + Glass Effect)
def set_bg_local(main_bg):
    if os.path.exists(main_bg):
        with open(main_bg, "rb") as f:
            bin_str = base64.b64encode(f.read()).decode()
        st.markdown(f"""
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
            """, unsafe_allow_html=True)

set_bg_local('background.jpg')

# 3. SIDEBAR: PARAMETERS
if os.path.exists("utm.png"):
    st.sidebar.image("utm.png", use_container_width=True)
else:
    st.sidebar.title("📍 UTM GEOMATICS")

st.sidebar.divider()
st.sidebar.header("⚙️ Datum Shift (WGS84 ➔ Timbalai)")
dx = st.sidebar.number_input("dX (m)", value=-679.0, format="%.3f")
dy = st.sidebar.number_input("dY (m)", value=669.0, format="%.3f")
dz = st.sidebar.number_input("dZ (m)", value=-48.0, format="%.3f")

# 4. MATH LOGIC: MOLODENSKY + HOTINE OBLIQUE MERCATOR (HOM)
def molodensky_transform(lat, lon, h, dx, dy, dz):
    # Everest 1830 (Modified) Constants
    a_t = 6377298.556; f_t = 1 / 300.8017
    # WGS84 Constants
    a_w = 6378137.0; f_w = 1 / 298.257223563
    
    da = a_t - a_w; df = f_t - f_w
    phi = np.radians(lat); lam = np.radians(lon)
    e2w = 2*f_w - f_w**2
    
    M = a_w * (1 - e2w) / (1 - e2w * np.sin(phi)**2)**1.5
    N = a_w / np.sqrt(1 - e2w * np.sin(phi)**2)
    
    dphi = (-dx*np.sin(phi)*np.cos(lam) - dy*np.sin(phi)*np.sin(lam) + dz*np.cos(phi) + (a_w*df + f_w*da)*np.sin(2*phi)) / (M + h)
    dlam = (-dx*np.sin(lam) + dy*np.cos(lam)) / ((N + h) * np.cos(phi))
    dh = dx*np.cos(phi)*np.cos(lam) + dy*np.cos(phi)*np.sin(lam) + dz*np.sin(phi) - (a_w*df + f_w*da)*np.sin(phi)**2 + da
    
    return lat + np.degrees(dphi), lon + np.degrees(dlam), h + dh

def latlon_to_hom(lat, lon):
    # Constants for Everest 1830 (Modified)
    a = 6377298.556; f = 1 / 300.8017
    e2 = 2*f - f**2; e = np.sqrt(e2)
    
    # Projection Parameters (Your Specific Request)
    lat0 = np.radians(4.0); lon0 = np.radians(115.0); k0 = 0.99984
    alpha_c = np.radians(53 + 18/60 + 56.9537/3600) # Azimuth
    gamma_c = np.radians(53 + 7/60 + 48.3685/3600) # Grid Angle
    FE = 0.0; FN = 0.0
    
    phi = np.radians(lat); lam = np.radians(lon)
    
    # HOM Intermediate Calculations
    B = np.sqrt(1 + (e2 * np.cos(lat0)**4) / (1 - e2))
    A = a * B * k0 * np.sqrt(1 - e2) / (1 - e2 * np.sin(lat0)**2)
    t0 = np.tan(np.pi/4 - lat0/2) / ((1 - e*np.sin(lat0)) / (1 + e*np.sin(lat0)))**(e/2)
    D = B * np.sqrt(1 - e2) / (np.cos(lat0) * np.sqrt(1 - e2 * np.sin(lat0)**2))
    F = D + np.sqrt(max(0, D**2 - 1))
    E = F * (t0**B)
    
    t = np.tan(np.pi/4 - phi/2) / ((1 - e*np.sin(phi)) / (1 + e*np.sin(phi)))**(e/2)
    Q = E / (t**B)
    S = (Q - 1/Q) / 2; T = (Q + 1/Q) / 2
    V = np.sin(B * (lam - lon0))
    U = (S * np.sin(alpha_c) - V * np.cos(alpha_c)) / T
    
    # Rectified Coordinates (u, v)
    v = (A / (2 * B)) * np.log((1 - U) / (1 + U))
    u = (A / B) * np.atan2((S * np.cos(alpha_c) + V * np.sin(alpha_c)), 1.0)
    
    # Final Rotation to Easting and Northing
    easting = v * np.cos(gamma_c) + u * np.sin(gamma_c) + FE
    northing = u * np.cos(gamma_c) - v * np.sin(gamma_c) + FN
    
    return easting, northing

# 5. MAIN CONTENT
st.title("🛰️ Professional HOM Transformation Module")
st.markdown("### Geomatics Creative Map and Innovation Competition 2026")
st.markdown("<h4 style='color: #4682B4; font-weight: bold;'>WGS84 Geodetic ➔ Timbalai 1948 HOM Grid</h4>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.subheader("📥 Input: WGS84")
    lat_in = st.number_input("Latitude", value=5.57340882, format="%.8f")
    lon_in = st.number_input("Longitude", value=116.03575158, format="%.8f")
    h_in = st.number_input("Height (m)", value=48.502, format="%.3f")
    
    if st.button("🚀 Calculate HOM Grid & Height"):
        with col2:
            st.subheader("📤 Output: Timbalai 1948")
            # Datum Shift
            lat_t, lon_t, h_t = molodensky_transform(lat_in, lon_in, h_in, dx, dy, dz)
            # HOM Projection
            e, n = latlon_to_hom(lat_t, lon_t)
            
            st.success("Calculated Successfully!")
            st.metric("Easting (E)", f"{e:.3f} m")
            st.metric("Northing (N)", f"{n:.3f} m")
            st.metric("Transformed Height (h)", f"{h_t:.3f} m")
            st.info(f"Target Geodetic: {lat_t:.6f}, {lon_t:.6f}")
            st.balloons()

# 6. THEORY ELABORATION
st.divider()
with st.expander("📖 View Mathematical Model & Elaboration"):
    st.write("This module utilizes the **Hotine Oblique Mercator (HOM)** projection, specifically designed for regions like Borneo that are not aligned with the North-South axis.")
    
    st.markdown("""
    | Parameter | Value |
    | :--- | :--- |
    | **Ellipsoid** | Everest 1830 (Modified) |
    | **Scale Factor** | 0.99984 |
    | **Azimuth** | 53°18'56.9537" |
    | **Grid Angle** | 53°07'48.3685" |
    | **Origin** | N 4.0°, E 115.0° |
    """)
    st.latex(r'''\mathbf{X}_{Rectified} = \mathbf{T}_{rotate}(\gamma_c) \cdot \begin{bmatrix} u \\ v \end{bmatrix}''')

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
        <p class="footer-text" style="margin-top:5px; color: #800000;"><b>SBEU 3893 - UTM</b></p>
    </div>
    """, unsafe_allow_html=True
)
