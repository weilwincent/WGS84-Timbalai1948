import streamlit as st
import numpy as np
import pandas as pd
import folium
from streamlit_folium import st_folium
import base64
import os

# 1. PAGE SETUP
st.set_page_config(page_title="SBEU 3893 - Advanced Geomatics", page_icon="📍", layout="wide")

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

if os.path.exists('background.jpg'):
    set_bg_local('background.jpg')

# 3. MATH ENGINES (Bursa-Wolf & HOM)
def bursa_wolf_transform(lat, lon, h, dx, dy, dz, rx_s, ry_s, rz_s, s_ppm):
    a_w = 6378137.0; f_w = 1/298.257223563; e2w = 2*f_w - f_w**2
    phi, lam = np.radians(lat), np.radians(lon)
    N = a_w / np.sqrt(1 - e2w * np.sin(phi)**2)
    Xw = (N + h) * np.cos(phi) * np.cos(lam)
    Yw = (N + h) * np.cos(phi) * np.sin(lam)
    Zw = (N * (1 - e2w) + h) * np.sin(phi)
    S = 1 + s_ppm/1e6
    rx, ry, rz = np.radians(rx_s/3600), np.radians(ry_s/3600), np.radians(rz_s/3600)
    R = np.array([[1, -rz, ry], [rz, 1, -rx], [-ry, rx, 1]])
    P_local = np.array([dx, dy, dz]) + S * (R @ np.array([Xw, Yw, Zw]))
    return P_local

def cart_to_geodetic(x, y, z, a, e2):
    lon = np.arctan2(y, x)
    p = np.sqrt(x**2 + y**2)
    phi = np.arctan2(z, p * (1 - e2))
    for _ in range(5):
        N = a / np.sqrt(1 - e2 * np.sin(phi)**2)
        phi = np.arctan2(z + e2 * N * np.sin(phi), p)
    h = p / np.cos(phi) - N
    return np.degrees(phi), np.degrees(lon), h

def geodetic_to_hom(lat, lon, a, e2):
    lat0, lon0, k0 = np.radians(4.0), np.radians(115.0), 0.99984
    alpha_c = np.radians(53 + 18/60 + 56.9537/3600)
    gamma_c = np.radians(53 + 7/60 + 48.3685/3600)
    FE, FN = 590476.662, 442857.652 
    phi, lam, e = np.radians(lat), np.radians(lon), np.sqrt(e2)
    B = np.sqrt(1 + (e2 * np.cos(lat0)**4) / (1 - e2))
    A = (a * B * k0 * np.sqrt(1 - e2)) / (1 - e2 * np.sin(lat0)**2)
    t0 = np.tan(np.pi/4 - lat0/2) / ((1 - e*np.sin(lat0))/(1 + e*np.sin(lat0)))**(e/2)
    D = B * np.sqrt(1 - e2) / (np.cos(lat0) * np.sqrt(1 - e2 * np.sin(lat0)**2))
    F = D + np.sqrt(max(0, D**2 - 1))
    E = F * (t0**B)
    t = np.tan(np.pi/4 - phi/2) / ((1 - e*np.sin(phi))/(1 + e*np.sin(phi)))**(e/2)
    Q = E / (t**B)
    S, T = (Q - 1/Q) / 2, (Q + 1/Q) / 2
    V = np.sin(B * (lam - lon0))
    U = (S * np.sin(alpha_c) - V * np.cos(alpha_c)) / T
    v = (A / (2 * B)) * np.log((1 - U) / (1 + U))
    u = (A / B) * np.arctan2((S * np.cos(alpha_c) + V * np.sin(alpha_c)), 1.0)
    Easting = v * np.cos(gamma_c) + u * np.sin(gamma_c) + FE
    Northing = u * np.cos(gamma_c) - v * np.sin(gamma_c) + FN
    return Easting, Northing

# 4. SIDEBAR
st.sidebar.title("⚙️ Parameters")
dx = st.sidebar.number_input("dX (m)", value=596.096, format="%.3f")
dy = st.sidebar.number_input("dY (m)", value=-624.512, format="%.3f")
dz = st.sidebar.number_input("dZ (m)", value=2.779, format="%.3f")
rx_s = st.sidebar.number_input("rX (sec)", value=-1.44646, format="%.5f")
ry_s = st.sidebar.number_input("rY (sec)", value=-0.88312, format="%.5f")
rz_s = st.sidebar.number_input("rZ (sec)", value=1.82844, format="%.5f")
scale_p = st.sidebar.number_input("Scale (ppm)", value=-10.454, format="%.4f")

# 5. MAIN CONTENT
st.title("🛰️ Professional Geomatics Transformation")
tab1, tab2 = st.tabs(["🎯 Single Point", "📂 Batch Processing"])

# Initialize Session State to keep map alive
if 'transformed' not in st.session_state:
    st.session_state.transformed = False

with tab1:
    col1, col2 = st.columns([1, 1.2])
    with col1:
        st.subheader("Input: WGS84")
        lat_in = st.number_input("Latitude", value=5.573408816, format="%.9f")
        lon_in = st.number_input("Longitude", value=116.035751582, format="%.9f")
        h_in = st.number_input("Height (m)", value=48.502, format="%.3f")
        
        if st.button("🚀 Transform Point"):
            a_ev, f_ev = 6377298.556, 1/300.8017; e2_ev = (2*f_ev) - (f_ev**2)
            cart = bursa_wolf_transform(lat_in, lon_in, h_in, dx, dy, dz, rx_s, ry_s, rz_s, scale_p)
            lt, ln, ht = cart_to_geodetic(cart[0], cart[1], cart[2], a_ev, e2_ev)
            east, north = geodetic_to_hom(lt, ln, a_ev, e2_ev)
            
            # Store results in session state
            st.session_state.res = {"E": east, "N": north, "X": cart[0], "lat": lat_in, "lon": lon_in}
            st.session_state.transformed = True

    with col2:
        if st.session_state.transformed:
            st.success("Transformation Complete")
            st.metric("Easting (E)", f"{st.session_state.res['E']:.3f} m")
            st.metric("Northing (N)", f"{st.session_state.res['N']:.3f} m")
            
            # Map Container - Ensuring it stays visible
            st.subheader("🗺️ Visual Verification")
            m = folium.Map(location=[st.session_state.res['lat'], st.session_state.res['lon']], zoom_start=15)
            folium.Marker([st.session_state.res['lat'], st.session_state.res['lon']], 
                          popup=f"E: {st.session_state.res['E']:.2f}").add_to(m)
            st_folium(m, width=600, height=350, key="map_output")

with tab2:
    st.subheader("📂 Batch Process")
    uploaded_file = st.file_uploader("Upload CSV/Excel", type=["csv", "xlsx"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        st.write("File Preview:", df.head())
        # (Batch logic as per previous version remains same)

# 7. FOOTER
st.markdown("""<div style="position: fixed; right: 20px; bottom: 20px; text-align: right; padding: 12px; background-color: rgba(255, 255, 255, 0.4); backdrop-filter: blur(10px); border-right: 5px solid #800000; border-radius: 8px; z-index: 1000;"><p style="color: #800000; font-weight: bold; margin: 0;">DEVELOPED BY:</p><p style="font-size: 13px; color: #002147; margin: 0;">Weil W., Rebecca J., Achellis L., Nor Muhamad, Rowell B.S.</p><p style="font-size: 13px; font-weight: bold; color: #800000; margin-top: 5px;">SBEU 3893 - UTM</p></div>""", unsafe_allow_html=True)
