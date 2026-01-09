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

#
