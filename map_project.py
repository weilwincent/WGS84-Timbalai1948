import streamlit as st
import numpy as np
import base64
import os

# 1. PAGE SETUP
st.set_page_config(page_title="7-Parameter HOM Module", page_icon="📍", layout="wide")

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
            .main .block-container {{ background-color: rgba(255, 255, 255, 0.93); padding: 3rem; border-radius: 25px; margin-top: 30px; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3); }}
            </style>
            """, unsafe_allow_html=True)

set_bg_local('background.jpg')

# 3. SIDEBAR
if os.path.exists("utm.png"):
    st.sidebar.image("utm.png", use_container_width=True)
st.sidebar.divider()
st.sidebar.header("⚙️ Datum Shift (WGS84 ➔ Timbalai)")
dx = st.sidebar.number_input("dX (m)", value=-679.0, format="%.3f")
dy = st.sidebar.number_input("dY (m)", value=669.0, format="%.3f")
dz = st.sidebar.number_input("dZ (m)", value=-48.0, format="%.3f")

# 4. MATH LOGIC: HOTINE OBLIQUE MERCATOR (HOM)
def latlon_to_hom(lat, lon):
    # Everest 1830 (Modified)
    a = 6377298.556
    f = 1 / 300.8017
    e2 = 2*f - f**2
    e = np.sqrt(e2)
    
    # Your Parameters
    lat0 = np.radians(4.0)
    lon0 = np.radians(115.0)
    k0 = 0.99984
    alpha_c = np.radians(53 + 18/60 + 56.9537/3600) # Azimuth
    gamma_c = np.radians(53 + 7/60 + 48.3685/3600) # Grid Angle
    
    phi = np.radians(lat)
    lam = np.radians(lon)
    
    # 1. Calculate Constants
    B = np.sqrt(1 + (e2 * np.cos(lat0)**4) / (1 - e2))
    A = a * B * k0 * np.sqrt(1 - e2) / (1 - e2 * np.sin(lat0)**2)
    t0 = np.tan(np.pi/4 - lat0/2) / ((1 - e*np.sin(lat0)) / (1 + e*np.sin(lat0)))**(e/2)
    D = B * np.sqrt(1 - e2) / (np.cos(lat0) * np.sqrt(1 - e2 * np.sin(lat0)**2))
    F = D + np.sqrt(max(0, D**2 - 1))
    E = F * (t0**B)
    
    # 2. Transformation to Sphere
    t = np.tan(np.pi/4 - phi/2) / ((1 - e*np.sin(phi)) / (1 + e*np.sin(phi)))**(e/2)
    Q = E / (t**B)
    S = (Q - 1/Q) / 2
    T = (Q + 1/Q) / 2
    V = np.sin(B * (lam - lon0))
    U = (S * np.sin(alpha_c) - V * np.cos(alpha_c)) / T
    
    # 3. Rectified Coordinates (u, v)
    # v is perpendicular to the center line, u is along the center line
    v = (A / (2 * B)) * np.log((1 - U) / (1 + U))
    u = (A / B) * np.arctan2((S * np.cos(alpha_c) + V * np.sin(alpha_c)), 1.0)
    
    # 4. Final Rotation (Rectified to Grid)
    # This is where Easting (E) and Northing (N) are generated
    easting = v * np.cos(gamma_c) + u * np.sin(gamma_c)
    northing = u * np.cos(gamma_c) - v * np.sin(gamma_c)
    
    return easting, northing

def molodensky_transform(lat, lon, h, dx, dy, dz):
    a_w = 6378137.0; f_w = 1 / 298.257223563
    a_t = 6377298.556; f_t = 1 / 300.8017
    da = a_t - a_w; df = f_t - f_w
    phi = np.radians(lat); lam = np.radians(lon)
    e2w = 2*f_w - f_w**2
    M = a_w * (1 - e2w) / (1 - e2w * np.sin(phi)**2)**1.5
    N = a_w / np.sqrt(1 - e2w * np.sin(phi)**2)
    
    dphi = (-dx*np.sin(phi)*np.cos(lam) - dy*np.sin(phi)*np.sin(lam) + dz*np.cos(phi) + (a_w*df + f_w*da)*np.sin(2*phi)) / (M + h)
    dlam = (-dx*np.sin(lam) + dy*np.cos(lam)) / ((N + h) * np.cos(phi))
    dh = dx*np.cos(phi)*np.cos(lam) + dy*np.cos(phi)*np.sin(lam) + dz*np.sin(phi) - (a_w*df + f_w*da)*np.sin(phi)**2 + da
    
    return lat + np.degrees(dphi), lon + np.degrees(dlam), h + dh

# 5. MAIN CONTENT
st.title("🛰️ Professional HOM Transformation")
st.markdown("### Geomatics Creative Map and Innovation Competition 2026")

col1, col2 = st.columns(2)
with col1:
    st.subheader("📥 Input: WGS84")
    lat_in = st.number_input("Latitude", value=5.57340882, format="%.8f")
    lon_in = st.number_input("Longitude", value=116.03575158, format="%.8f")
    h_in = st.number_input("Height (m)", value=48.502)
    
    if st.button("🚀 Calculate Precise Grid"):
        with col2:
            st.subheader("📤 Output: Timbalai 1948 HOM")
            lat_t, lon_t, h_t = molodensky_transform(lat_in, lon_in, h_in, dx, dy, dz)
            e, n = latlon_to_hom(lat_t, lon_t)
            
            st.success("Calculated!")
            st.metric("Easting (E)", f"{e:.3f} m")
            st.metric("Northing (N)", f"{n:.3f} m")
            st.metric("Height (h)", f"{h_t:.3f} m")
            st.balloons()

# 7. FOOTER
st.markdown("""
    <div style="position: fixed; right: 20px; bottom: 20px; text-align: right; padding: 12px; 
    background-color: rgba(255,255,255,0.4); backdrop-filter: blur(10px); border-right: 5px solid #800000;
    border-radius: 8px; font-family: 'Arial'; z-index: 1000;">
        <p style="color: #800000; font-weight: bold; margin: 0;">DEVELOPED BY:</p>
        <p style="font-size: 13px; color: #002147; margin: 0;">Weil W., Rebecca J., Achellis L., Nor Muhamad, Rowell B.S.</p>
        <p style="font-size: 13px; font-weight: bold; color: #800000; margin-top: 5px;">SBEU 3893 - UTM</p>
    </div>
    """, unsafe_allow_html=True)
