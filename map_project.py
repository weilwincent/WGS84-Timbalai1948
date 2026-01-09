import streamlit as st
import numpy as np
import base64
import os

# 1. PAGE SETUP
st.set_config(page_title="SBEU 3893 - Borneo RSO Module", page_icon="📍", layout="wide")

# 2. CUSTOM STYLING (Darker Steel Blue)
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

# 3. SIDEBAR (Updated with your 7-Parameters)
if os.path.exists("utm.png"):
    st.sidebar.image("utm.png", use_container_width=True)
st.sidebar.divider()
st.sidebar.header("⚙️ Datum Shift (WGS84 ➔ Timbalai)")
dx = st.sidebar.number_input("dX (m)", value=596.096, format="%.3f")
dy = st.sidebar.number_input("dY (m)", value=-624.512, format="%.3f")
dz = st.sidebar.number_input("dZ (m)", value=2.779, format="%.3f")
rx_s = st.sidebar.number_input("rX (sec)", value=-1.44646, format="%.5f")
ry_s = st.sidebar.number_input("rY (sec)", value=-0.88312, format="%.5f")
rz_s = st.sidebar.number_input("rZ (sec)", value=1.82844, format="%.5f")
scale_p = st.sidebar.number_input("Scale (ppm)", value=-10.454, format="%.4f")

# 4. MATH ENGINE: HOTINE OBLIQUE MERCATOR
def latlon_to_borneo_rso(lat, lon):
    # Everest 1830 Modified
    a = 6377298.556
    f_inv = 300.8017
    f = 1/f_inv
    e2 = 2*f - f**2
    e = np.sqrt(e2)
    
    # Projection Parameters
    lat0 = np.radians(4.0)
    lon0 = np.radians(115.0)
    k0 = 0.99984
    alpha_c = np.radians(53 + 18/60 + 56.9537/3600) # Azimuth
    gamma_c = np.radians(53 + 7/60 + 48.3685/3600) # Grid Angle
    
    # False Origin for Timbalai 1948 RSO Borneo
    FE = 0.0
    FN = 0.0
    
    phi = np.radians(lat)
    lam = np.radians(lon)
    
    # HOM/RSO Formula Constants
    B = np.sqrt(1 + (e2 * np.cos(lat0)**4) / (1 - e2))
    A = (a * B * k0 * np.sqrt(1 - e2)) / (1 - e2 * np.sin(lat0)**2)
    t0 = np.tan(np.pi/4 - lat0/2) / ((1 - e*np.sin(lat0))/(1 + e*np.sin(lat0)))**(e/2)
    D = B * np.sqrt(1 - e2) / (np.cos(lat0) * np.sqrt(1 - e2 * np.sin(lat0)**2))
    F = D + np.sqrt(max(0, D**2 - 1))
    E = F * (t0**B)
    
    # uc: natural origin shift along initial line
    uc = (A / B) * np.arctan2(np.sqrt(max(0, D**2 - 1)), np.cos(alpha_c))
    
    # Spherical transformation
    t = np.tan(np.pi/4 - phi/2) / ((1 - e*np.sin(phi))/(1 + e*np.sin(phi)))**(e/2)
    Q = E / (t**B)
    S = (Q - 1/Q) / 2
    T = (Q + 1/Q) / 2
    V = np.sin(B * (lam - lon0))
    U = (S * np.sin(alpha_c) - V * np.cos(alpha_c)) / T
    
    # Rectified Coordinates
    v = (A / (2 * B)) * np.log((1 - U) / (1 + U))
    u = (A / B) * np.arctan2((S * np.cos(alpha_c) + V * np.sin(alpha_c)), 1.0)
    
    # Final Rotation to Grid (E, N)
    u_rect = u - uc
    Easting = v * np.cos(gamma_c) + u_rect * np.sin(gamma_c) + FE
    Northing = u_rect * np.cos(gamma_c) - v * np.sin(gamma_c) + FN
    
    return Easting, Northing

def bursa_wolf_transform(lat, lon, h, dx, dy, dz, rx_s, ry_s, rz_s, scale_p):
    # Convert WGS84 Geodetic to Cartesian
    a_w = 6378137.0; f_w = 1/298.257223563; e2w = 2*f_w - f_w**2
    phi = np.radians(lat); lam = np.radians(lon)
    N = a_w / np.sqrt(1 - e2w * np.sin(phi)**2)
    Xw = (N + h) * np.cos(phi) * np.cos(lam)
    Yw = (N + h) * np.cos(phi) * np.sin(lam)
    Zw = (N * (1 - e2w) + h) * np.sin(phi)
    
    # 7-Parameter Transformation (Position Vector Convention)
    S = 1 + scale_p/1e6
    rx = np.radians(rx_s/3600); ry = np.radians(ry_s/3600); rz = np.radians(rz_s/3600)
    R = np.array([[1, -rz, ry], [rz, 1, -rx], [-ry, rx, 1]])
    
    P_local = np.array([dx, dy, dz]) + S * (R @ np.array([Xw, Yw, Zw]))
    
    # Convert back to Geodetic (Everest 1830 Mod)
    a_t = 6377298.556; f_t = 1/300.8017; e2t = 2*f_t - f_t**2
    x, y, z = P_local
    lon_t = np.arctan2(y, x)
    p = np.sqrt(x**2 + y**2)
    phi_t = np.arctan2(z, p * (1 - e2t))
    for _ in range(5):
        Nt = a_t / np.sqrt(1 - e2t * np.sin(phi_t)**2)
        phi_t = np.arctan2(z + e2t * Nt * np.sin(phi_t), p)
    ht = p / np.cos(phi_t) - Nt
    return np.degrees(phi_t), np.degrees(lon_t), ht

# 5. MAIN CONTENT
st.title("🛰️ Calibrated Borneo RSO Module")
st.markdown("### Geomatics Creative Map and Innovation Competition 2026")

col1, col2 = st.columns(2)
with col1:
    st.subheader("📥 Input: WGS84")
    lat_in = st.number_input("Latitude", value=5.573408816, format="%.9f")
    lon_in = st.number_input("Longitude", value=116.035751582, format="%.9f")
    h_in = st.number_input("Height (m)", value=48.502, format="%.3f")
    
    if st.button("🚀 Transform Coordinates"):
        with col2:
            st.subheader("📤 Output: Timbalai 1948 RSO")
            # Step 1: 7-Parameter Datum Shift
            lt, ln, ht = bursa_wolf_transform(lat_in, lon_in, h_in, dx, dy, dz, rx_s, ry_s, rz_s, scale_p)
            # Step 2: RSO Projection
            e, n = latlon_to_borneo_rso(lt, ln)
            
            st.success("Calculated Successfully!")
            st.metric("Easting (E)", f"{e:.3f} m")
            st.metric("Northing (N)", f"{n:.3f} m")
            st.metric("Height (h)", f"{ht:.3f} m")
            st.info(f"Geodetic: {lt:.6f}, {ln:.6f}")
            st.balloons()

# 6. THEORY

st.divider()
with st.expander("📖 View Mathematical Process"):
    st.write("WGS84 ➔ Bursa-Wolf 7-Parameter Shift ➔ Everest 1830 (Mod) ➔ Hotine Oblique Mercator Rotation.")

# 7. FOOTER
st.markdown("""<div style="position: fixed; right: 20px; bottom: 20px; text-align: right; padding: 12px; background-color: rgba(255,255,255,0.4); backdrop-filter: blur(10px); border-right: 5px solid #800000; border-radius: 8px; z-index: 1000;"><p style="color: #800000; font-weight: bold; margin: 0;">DEVELOPED BY:</p><p style="font-size: 13px; color: #002147; margin: 0;">Weil W., Rebecca J., Achellis L., Nor Muhamad, Rowell B.S.</p><p style="font-size: 13px; font-weight: bold; color: #800000; margin-top: 5px;">SBEU 3893 - UTM</p></div>""", unsafe_allow_html=True)
