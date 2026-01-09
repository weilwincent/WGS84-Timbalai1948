import streamlit as st
import numpy as np
import base64
import os

# 1. PAGE SETUP - Fixed AttributeError from your screenshot
st.set_page_config(page_title="SBEU 3893 - WGS84 Geocentric", page_icon="📍", layout="wide")

# 2. CUSTOM STYLING (Darker Steel Blue Sidebar)
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

if os.path.exists('background.jpg'):
    set_bg_local('background.jpg')

# 3. SIDEBAR
if os.path.exists("utm.png"):
    st.sidebar.image("utm.png", use_container_width=True)
st.sidebar.title("📍 Geocentric Engine")
st.sidebar.info("Converting Geodetic (Lat, Lon, H) to Geocentric Cartesian (X, Y, Z).")

# 4. MATH LOGIC: GEODETIC TO CARTESIAN (WGS84)
def geodetic_to_cartesian(lat, lon, h):
    # Standard WGS84 Ellipsoid Constants
    a = 6378137.0
    f = 1 / 298.257223563
    e2 = (2 * f) - (f ** 2)
    
    phi = np.radians(lat)
    lam = np.radians(lon)
    
    # Radius of curvature in the prime vertical
    N = a / np.sqrt(1 - e2 * np.sin(phi)**2)
    
    X = (N + h) * np.cos(phi) * np.cos(lam)
    Y = (N + h) * np.cos(phi) * np.sin(lam)
    Z = (N * (1 - e2) + h) * np.sin(phi)
    
    return X, Y, Z

# 5. MAIN CONTENT
st.title("🛰️ WGS84 Geocentric Conversion")
st.markdown("### Verification against Survey Software Results")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📥 Input: Geodetic")
    lat_in = st.number_input("Latitude", value=5.573408816, format="%.9f")
    lon_in = st.number_input("Longitude", value=116.035751582, format="%.9f")
    h_in = st.number_input("Height (m)", value=48.502, format="%.3f")
    
    if st.button("🚀 Convert to Cartesian"):
        X, Y, Z = geodetic_to_cartesian(lat_in, lon_in, h_in)
        
        with col2:
            st.subheader("📤 Output: Geocentric X, Y, Z")
            st.success("Conversion Complete!")
            # Displaying with high precision to match survey software
            st.metric("X (meters)", f"{X:.3f}")
            st.metric("Y (meters)", f"{Y:.3f}")
            st.metric("Z (meters)", f"{Z:.3f}")
            
            # Validation Check
            target_x = 2787565.983
            diff = abs(X - target_x)
            if diff < 1.0:
                st.info("✅ Matches Survey Software within tolerance.")
            else:
                st.warning(f"Note: Difference from target X is {diff:.3f}m")

# 7. DEVELOPER CREDITS
st.markdown("""<div style="position: fixed; right: 20px; bottom: 20px; text-align: right; padding: 12px; background-color: rgba(255,255,255,0.4); backdrop-filter: blur(10px); border-right: 5px solid #800000; border-radius: 8px; z-index: 1000;"><p style="color: #800000; font-weight: bold; margin: 0;">DEVELOPED BY:</p><p style="font-size: 13px; color: #002147; margin: 0;">Weil W., Rebecca J., Achellis L., Nor Muhamad, Rowell B.S.</p><p style="font-size: 13px; font-weight: bold; color: #800000; margin-top: 5px;">SBEU 3893 - UTM</p></div>""", unsafe_allow_html=True)
