import streamlit as st
import numpy as np
import folium
from streamlit_folium import st_folium
import base64
import os

# 1. PAGE SETUP
st.set_page_config(page_title="SBEU 3893 - Molodensky Module", page_icon="📍", layout="wide")

# 2. CUSTOM STYLING (Original Steel Blue)
def set_bg_local(main_bg):
    if os.path.exists(main_bg):
        with open(main_bg, "rb") as f:
            bin_str = base64.b64encode(f.read()).decode()
        st.markdown(f"""
            <style>
            .stApp {{ background-image: url("data:image/png;base64,{bin_str}"); background-size: cover; background-attachment: fixed; }}
            [data-testid="stSidebar"] {{ background-color: #4682B4 !important; }}
            [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] p {{ color: white !important; }}
            .main .block-container {{ background-color: rgba(255, 255, 255, 0.93); padding: 2rem; border-radius: 20px; margin-top: 20px; }}
            iframe {{ width: 100% !important; border-radius: 10px; }}
            </style>
            """, unsafe_allow_html=True)

if os.path.exists('background.jpg'):
    set_bg_local('background.jpg')

# 3. INITIALIZE SESSION STATE
if 'results' not in st.session_state:
    st.session_state.results = None
if 'balloons_fired' not in st.session_state:
    st.session_state.balloons_fired = False

# 4. MATH ENGINE: SIMPLE MOLODENSKY
def simple_molodensky(lat, lon, h, dx, dy, dz):
    # WGS84 (Source)
    a = 6378137.0
    f = 1 / 298.257223563
    # Everest 1830 (Target)
    a_t = 6377298.556
    f_t = 1 / 300.8017
    
    da = a_t - a
    df = f_t - f
    
    phi = np.radians(lat)
    lam = np.radians(lon)
    
    e2 = 2*f - f**2
    sin_phi = np.sin(phi)
    cos_phi = np.cos(phi)
    sin_lam = np.sin(lam)
    cos_lam = np.cos(lam)
    
    M = a * (1 - e2) / (1 - e2 * sin_phi**2)**1.5
    N = a / np.sqrt(1 - e2 * sin_phi**2)
    
    # Delta Latitude (radians)
    dphi = (-dx * sin_phi * cos_lam - dy * sin_phi * sin_lam + dz * cos_phi + 
            (a * df + f * da) * np.sin(2*phi)) / (M + h)
            
    # Delta Longitude (radians)
    dlam = (-dx * sin_lam + dy * cos_lam) / ((N + h) * cos_phi)
    
    # Delta Height (meters)
    dh = dx * cos_phi * cos_lam + dy * cos_phi * sin_lam + dz * sin_phi - (a * df + f * da) * sin_phi**2 + da
    
    return lat + np.degrees(dphi), lon + np.degrees(dlam), h + dh

# 5. SIDEBAR
if os.path.exists("utm.png"):
    st.sidebar.image("utm.png", use_container_width=True)

st.sidebar.title("⚙️ Molodensky Parameters")
st.sidebar.info("Simple Molodensky uses 3 translation shifts (dX, dY, dZ) between ellipsoids.")
dx = st.sidebar.number_input("dX (m)", value=596.096, format="%.3f")
dy = st.sidebar.number_input("dY (m)", value=-624.512, format="%.3f")
dz = st.sidebar.number_input("dZ (m)", value=2.779, format="%.3f")

# 6. MAIN UI
st.title("🛰️ Simple Molodensky Transformation")
st.write("WGS84 to Timbalai 1948 (Standard 3-Parameter Shift)")

col_in, col_out = st.columns(2)
with col_in:
    st.subheader("📥 Input: WGS84")
    lat_in = st.number_input("Latitude", value=5.573408816, format="%.9f")
    lon_in = st.number_input("Longitude", value=116.035751582, format="%.9f")
    h_in = st.number_input("Height (m)", value=48.502, format="%.3f")
    
    if st.button("🚀 Transform Point"):
        st.session_state.balloons_fired = False 
        lat_t, lon_t, h_t = simple_molodensky(lat_in, lon_in, h_in, dx, dy, dz)
        st.session_state.results = {"lat_t": lat_t, "lon_t": lon_t, "h_t": h_t, "lat_orig": lat_in, "lon_orig": lon_in}

with col_out:
    if st.session_state.results:
        st.subheader("📤 Output: Timbalai 1948")
        st.metric("Latitude", f"{st.session_state.results['lat_t']:.9f}°")
        st.metric("Longitude", f"{st.session_state.results['lon_t']:.9f}°")
        st.metric("Height (m)", f"{st.session_state.results['h_t']:.3f}")
        
        if not st.session_state.balloons_fired:
            st.balloons()
            st.session_state.balloons_fired = True

# 7. MATHEMATICAL FORMULA SECTION
st.divider()
st.subheader("📖 Mathematical Principles")
[Image of Molodensky transformation formulas for geodetic coordinates]
with st.expander("View Molodensky Equations", expanded=True):
    st.write("The Simple Molodensky equations calculate the change in curvilinear coordinates directly:")
    st.latex(r"\Delta \phi'' = \frac{-dx \sin \phi \cos \lambda - dy \sin \phi \sin \lambda + dz \cos \phi + (a \Delta f + f \Delta a) \sin 2\phi}{(M+h) \sin 1''}")
    st.latex(r"\Delta \lambda'' = \frac{-dx \sin \lambda + dy \cos \lambda}{(N+h) \cos \phi \sin 1''}")
    st.write("This method is efficient because it avoids the conversion to Cartesian $X, Y, Z$ first.")

# 8. MAP ROW
if st.session_state.results:
    st.divider()
    st.subheader("🗺️ Visual Verification")
    m = folium.Map(location=[st.session_state.results['lat_orig'], st.session_state.results['lon_orig']], zoom_start=15)
    folium.Marker([st.session_state.results['lat_orig'], st.
