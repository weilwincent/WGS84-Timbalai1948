import streamlit as st
import numpy as np
import folium
from streamlit_folium import st_folium
import base64
import os
from pyproj import CRS, Transformer

# =========================
# 1. PAGE SETUP
# =========================
st.set_page_config(
    page_title="SBEU 3893 - Geomatics Suite",
    page_icon="📍",
    layout="wide"
)

# =========================
# 2. CUSTOM STYLING
# =========================
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
        [data-testid="stSidebar"] p {{
            color: white !important;
        }}
        .main .block-container {{
            background-color: rgba(255,255,255,0.95);
            padding: 2rem;
            border-radius: 20px;
        }}
        .result-card {{
            background-color: #f0f8ff;
            padding: 15px;
            border-radius: 10px;
            border-left: 5px solid #4682B4;
            margin-bottom: 10px;
        }}
        .result-label {{
            color: #4682B4;
            font-weight: bold;
            font-size: 14px;
        }}
        .result-value {{
            font-size: 20px;
            font-family: 'Courier New', monospace;
            font-weight: bold;
        }}
        iframe {{
            width: 100% !important;
            border-radius: 10px;
        }}
        </style>
        """, unsafe_allow_html=True)

if os.path.exists("background.jpg"):
    set_bg_local("background.jpg")

# =========================
# 3. HELMERT TRANSFORMATION
# =========================
def helmert_transformation(lat, lon, h, dx, dy, dz, rx_s, ry_s, rz_s, s_ppm):
    # WGS84
    a_w, f_w = 6378137.0, 1 / 298.257223563
    e2_w = 2*f_w - f_w**2

    phi, lam = np.radians(lat), np.radians(lon)
    N = a_w / np.sqrt(1 - e2_w * np.sin(phi)**2)

    X = (N + h) * np.cos(phi) * np.cos(lam)
    Y = (N + h) * np.cos(phi) * np.sin(lam)
    Z = (N*(1 - e2_w) + h) * np.sin(phi)

    # Helmert parameters
    rx = np.radians(rx_s / 3600)
    ry = np.radians(ry_s / 3600)
    rz = np.radians(rz_s / 3600)
    S = 1 + s_ppm / 1_000_000

    R = np.array([
        [1,  rz, -ry],
        [-rz, 1,  rx],
        [ry, -rx, 1]
    ])

    T = np.array([dx, dy, dz])
    X2, Y2, Z2 = T + S * (R @ np.array([X, Y, Z]))

    # Everest 1830 (Timbalai 1948)
    a_e, f_e = 6377298.556, 1 / 300.8017
    e2_e = 2*f_e - f_e**2

    lon_t = np.arctan2(Y2, X2)
    p = np.sqrt(X2**2 + Y2**2)
    lat_t = np.arctan2(Z2, p * (1 - e2_e))

    for _ in range(5):
        N_e = a_e / np.sqrt(1 - e2_e * np.sin(lat_t)**2)
        lat_t = np.arctan2(Z2 + e2_e * N_e * np.sin(lat_t), p)

    return np.degrees(lat_t), np.degrees(lon_t)

# =========================
# 4. BORNEO RSO PROJECTION
# =========================
def timbalai_to_borneo_rso(lat, lon):
    crs_timbalai = CRS.from_proj4(
        "+proj=longlat +ellps=evrst30 +no_defs"
    )

    crs_rso = CRS.from_proj4(
        "+proj=rso +lat_0=4 +lon_0=115 "
        "+k=0.99984 "
        "+x_0=590476.87 +y_0=442857.65 "
        "+ellps=evrst30 +units=m +no_defs"
    )

    transformer = Transformer.from_crs(
        crs_timbalai, crs_rso, always_xy=True
    )

    E, N = transformer.transform(lon, lat)
    return E, N

# =========================
# 5. SESSION STATE
# =========================
if "results" not in st.session_state:
    st.session_state.results = None

# =========================
# 6. SIDEBAR PARAMETERS
# =========================
st.sidebar.header("Helmert Parameters")

dx = st.sidebar.number_input("dX (m)", value=596.096)
dy = st.sidebar.number_input("dY (m)", value=-624.512)
dz = st.sidebar.number_input("dZ (m)", value=2.779)

rx_s = st.sidebar.number_input("rX (arc-sec)", value=-1.446460)
ry_s = st.sidebar.number_input("rY (arc-sec)", value=-0.883120)
rz_s = st.sidebar.number_input("rZ (arc-sec)", value=1.828440)

scale_p = st.sidebar.number_input("Scale (ppm)", value=-10.454)

# =========================
# 7. MAIN UI
# =========================
st.title("🛰️ Coordinate Transformation Module")
st.write("WGS84 → Timbalai 1948 → **Borneo RSO**")

col_in, col_out = st.columns(2)

with col_in:
    st.subheader("📥 Input (WGS84)")
    lat = st.number_input("Latitude (Decimal Degrees)", value=5.573408816, format="%.9f")
    lon = st.number_input("Longitude (Decimal Degrees)", value=116.035751582, format="%.9f")
    h = st.number_input("Height (m)", value=48.502)

    if st.button("🚀 Transform"):
        lat_t, lon_t = helmert_transformation(
            lat, lon, h, dx, dy, dz, rx_s, ry_s, rz_s, scale_p
        )

        E, N = timbalai_to_borneo_rso(lat_t, lon_t)

        st.session_state.results = {
            "E": E,
            "N": N,
            "h": h,
            "lat": lat,
            "lon": lon
        }

with col_out:
    if st.session_state.results:
        st.subheader("📤 Output: Borneo RSO (Timbalai 1948)")

        st.markdown(f"""
        <div class="result-card">
            <div class="result-label">EASTING (m)</div>
            <div class="result-value">{st.session_state.results['E']:.3f}</div>
        </div>
        <div class="result-card">
            <div class="result-label">NORTHING (m)</div>
            <div class="result-value">{st.session_state.results['N']:.3f}</div>
        </div>
        """, unsafe_allow_html=True)

        st.metric("Height (m)", f"{st.session_state.results['h']:.3f} (Preserved)")

# =========================
# 8. MAP (VISUAL CHECK)
# =========================
if st.session_state.results:
    st.divider()
    st.subheader("🗺️ Visual Reference (WGS84)")
    m = folium.Map(
        location=[st.session_state.results["lat"], st.session_state.results["lon"]],
        zoom_start=14
    )
    folium.Marker(
        [st.session_state.results["lat"], st.session_state.results["lon"]],
        popup="WGS84 Input Point"
    ).add_to(m)
    st_folium(m, use_container_width=True, height=400)

# =========================
# 9. FOOTER
# =========================
st.markdown("""
<div style="position: fixed; right: 20px; bottom: 20px;
background-color: rgba(255,255,255,0.4);
padding: 12px; border-right: 5px solid #800000;
border-radius: 8px;">
<b>DEVELOPED BY:</b><br>
Weil W. | Rebecca J. | Achellis L. | Nor Muhamad | Rowell B.S.<br>
<b>SBEU 3893 - Geomatics</b>
</div>
""", unsafe_allow_html=True)
