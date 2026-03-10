import streamlit as st
import geopandas as gpd
import pybdshadow
import pandas as pd
from streamlit_keplergl import keplergl_static
from keplergl import KeplerGl

# --- PAGE CONFIG ---
st.set_page_config(page_title="BIPV Solar Simulator", layout="wide")
st.title("🏙️ LOD-1 3D City Solar Simulator")
st.sidebar.header("Simulation Settings")

# --- 1. DATA LOADING ---
@st.cache_data # This keeps the app fast by not reloading data on every click
def load_data():
    buildings = gpd.read_file('bd_demo_2.json')
    buildings = pybdshadow.bd_preprocess(buildings)
    return buildings

buildings = load_data()

# --- 2. SIDEBAR CONTROLS ---
sim_date = st.sidebar.date_input("Analysis Date", value=pd.to_datetime("2022-01-01"))
accuracy = st.sidebar.slider("Grid Accuracy (meters)", 1, 10, 2)

# --- 3. THE MATH (Sunshine Analysis) ---
if st.sidebar.button("Run Simulation"):
    with st.spinner("Calculating shadows..."):
        # We use the full dataset for the MVP
        sunshine = pybdshadow.cal_sunshine(buildings, 
                                          day=str(sim_date), 
                                          roof=True, 
                                          accuracy=accuracy)
        
        # Simple Energy Estimate
        sunshine['kWh_m2'] = sunshine['Hour'] * 0.18 * 0.75
        
        # --- 4. 3D VISUALIZATION ---
        st.subheader(f"3D Irradiance Mapping: {sim_date}")
        map_1 = KeplerGl(height=600)
        map_1.add_data(data=buildings, name='Buildings')
        map_1.add_data(data=sunshine, name='Solar Intensity')
        keplergl_static(map_1)

        # --- 5. REPORTING ---
        st.subheader("Comparative Analysis Report")
        top_buildings = sunshine.groupby('building_id')['kWh_m2'].sum().sort_values(ascending=False).head(10)
        st.write("Top 10 Buildings by Solar Potential (Daily kWh):")
        st.bar_chart(top_buildings)
else:
    st.info("Adjust the settings in the sidebar and click 'Run Simulation' to begin.")