import streamlit as st
import numpy as np
import folium
from streamlit_folium import st_folium
import base64
import os

# 1. PAGE SETUP
st.set_page_config(page_title="SBEU 3893 - Molodensky DMS Module", page_icon="📍", layout="wide")

# 2. CUSTOM STYLING (Steel Blue Theme)
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

# 3. HELPER FUNCTION: DECIMAL TO DMS
def decimal_to_dms(deg, is_lat=True):
    abs_deg = abs(deg)
    d = int(abs_deg)
    m = int((abs_deg - d) * 60)
    s = (abs_deg - d - m/60) * 3600
    
    if is_lat:
        direction = "N" if deg >= 0 else "S"
    else:
        direction = "E" if deg >= 0 else "W"
        
    return f"{d}° {m}' {s:.4f}\" {direction}"

# 4. MATH ENGINE: SIMPLE MOLODENSKY
def simple_molodensky_horizontal(lat, lon, h, dx, dy, dz):
    # WGS84 (Source) to Everest 1830 (Target)
    a, f = 6378137.0, 1/298.257223563
    a_t, f_t = 6377298.556, 1/300.8017
    
    da, df = a_t - a, f_t - f
    phi, lam = np.radians(lat), np.radians(lon)
    e2 = 2*f - f**2
    
    M = a * (1 - e2) / (1 - e2 * np.sin(phi)**2)**1.5
    N = a / np.sqrt(1 - e2 * np.sin(phi)**2)
    
    dphi = (-dx * np.sin(phi) * np.cos(lam) - dy * np.sin(phi) * np.sin(lam) + dz * np.cos(phi) + 
            (a * df + f * da) * np.sin(2*phi)) / (M + h)
    dlam = (-dx * np.sin(lam) + dy * np.cos(lam)) / ((N + h) * np.cos(phi))
    
    return lat + np.degrees(dphi), lon + np.degrees(dlam)

# 5. INITIALIZE SESSION STATE
if 'results' not in st.session_state:
    st.session_state.results = None
if 'balloons_fired' not in st.session_state:
    st.session_state.balloons_fired = False

# 6. SIDEBAR
if os.path.exists("utm.png"):
    st.sidebar.image("utm.png", use_container_width=True)
dx = st.sidebar.number_input("dX (m)", value=596.096, format="%.3f")
dy = st.sidebar.number_input("dY (m)", value=-624.512, format="%.3f")
dz = st.sidebar.number_input("dZ (m)", value=2.779, format="%.3f")

# 7. MAIN UI
st.title("🛰️ Molodensky Transformation (DMS Output)")
st.write("Horizontal Shift with Professional DMS Formatting")

col_in, col_out = st.columns(2)
with col_in:
    st.subheader("📥 Input: WGS84")
    lat_in = st.number_input("Latitude (Decimal)", value=5.573408816, format="%.9f")
    lon_in = st.number_input("Longitude (Decimal)", value=116.035751582, format="%.9f")
    h_in = st.number_input("Height (m)", value=48.502, format="%.3f")
    
    if st.button("🚀 Transform"):
        st.session_state.balloons_fired = False 
        lat_t, lon_t = simple_molodensky_horizontal(lat_in, lon_in, h_in, dx, dy, dz)
        st.session_state.results = {
            "lat_dms": decimal_to_dms(lat_t, True),
            "lon_dms": decimal_to_dms(lon_t, False),
            "h_t": h_in,
            "lat_orig": lat_in,
            "lon_orig": lon_in
        }

with col_out:
    if st.session_state.results:
        st.subheader("📤 Output: Timbalai 1948")
        st.info(f"**Latitude:** {st.session_state.results['lat_dms']}")
        st.info(f"**Longitude:** {st.session_state.results['lon_dms']}")
        st.metric("Height (m)", f"{st.session_state.results['h_t']:.3f}")
        
        if not st.session_state.balloons_fired:
            st.balloons()
            st.session_state.balloons_fired = True

# 8. MATHEMATICAL PRINCIPLES
st.divider()
st.subheader("📖 Mathematical Principles")
[Image of geodetic datum shift using Molodensky transformation]
with st.expander("View Conversion Logic", expanded=True):
    st.write("The output is converted from decimal degrees to DMS using:")
    st.latex(r"Degrees = \lfloor Decimal \rfloor")
    st.latex(r"Minutes = \lfloor (Decimal - Degrees) \times 60 \rfloor")
    st.latex(r"Seconds = (Decimal - Degrees - \frac{Minutes}{60}) \times 3600")

# 9. MAP ROW
if st.session_state.results:
    st.divider()
    st.subheader("🗺️ Visual Verification")
    m = folium.Map(location=[st.session_state.results['lat_orig'], st.session_state.results['lon_orig']], zoom_start=15)
    folium.Marker([st.session_state.results['lat_orig'], st.session_state.results['lon_orig']], 
                  popup=f"DMS: {st.session_state.results['lat_dms']}").add_to(m)
    st_folium(m, use_container_width=True, height=400)

# 10. FOOTER
st.markdown("""
    <div style="position: fixed; right: 20px; bottom: 20px; text-align: right; padding: 12px; 
    background-color: rgba(255, 255, 255, 0.4); backdrop-filter: blur(10px); border-right: 5px solid #800000; 
    border-radius: 8px; z-index: 1000;">
        <p style="color: #800000; font-weight: bold; margin: 0;">DEVELOPED BY:</p>
        <p style="font-size: 13px; color: #002147; margin: 0;">Weil W. | Rebecca J. | Achellis L. | Nor Muhamad | Rowell B.S.</p>
        <p style="font-size: 13px; font-weight: bold; color: #800000; margin-top: 5px;">SBEU 3893 - UTM</p>
    </div>
    """, unsafe_allow_html=True)
