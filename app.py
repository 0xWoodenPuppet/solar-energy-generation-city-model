import streamlit as st
import geopandas as gpd
import pybdshadow
import pandas as pd
import plotly.express as px
from streamlit_keplergl import keplergl_static
from keplergl import KeplerGl

# --- PAGE CONFIG ---
st.set_page_config(page_title="Saurya Sankulan - BIPV Simulator", layout="wide")
st.title("🏙️ Saurya Sankulan: 3D City Solar Assessment")

# --- PARAMETERS & CONSTANTS ---
CO2_OFFSET_RATE_LBS_KWH = 0.85
AVG_HOME_KWH_PER_DAY = 30.0

st.sidebar.header("Simulation Settings")

# --- 1. DATA LOADING ---
@st.cache_data
def load_data():
    buildings = gpd.read_file('bd_demo_2.json')
    buildings = pybdshadow.bd_preprocess(buildings)
    return buildings

buildings = load_data()

# --- 2. SIDEBAR CONTROLS ---
st.sidebar.subheader("Environment Constraints")
sim_date = st.sidebar.date_input("Analysis Date", value=pd.to_datetime("2022-06-21"))
accuracy = st.sidebar.slider("Calculation Accuracy (m)", min_value=1, max_value=10, value=3, help="Lower value is more accurate but takes longer. 3-5m is recommended for block-level analysis.")

st.sidebar.subheader("Area & Performance Optimization")
study_area_extent = st.sidebar.slider("Study Area Radius (m)", 50, 1000, 200, step=50, help="Simulate a targeted radius around the neighborhood center to speed up performance dramatically.")

st.sidebar.subheader("Engineering Assumptions")
usable_area_pct = st.sidebar.slider("Usable Roof Area (%)", 10, 100, 60, help="Accounting for HVAC, shading setbacks, and maintenance paths.") / 100.0
install_type = st.sidebar.selectbox("Installation Type", ["Flat (Flush Mount)", "Optimal Tilt (+15% Yield)"])
yield_multiplier = 1.15 if install_type == "Optimal Tilt (+15% Yield)" else 1.0

# Calculate Center Point and Filter by Bounding Box Radius
# 1 degree is roughly 111,000 meters
radius_deg = study_area_extent / 111000.0
bounds = buildings.total_bounds # [minx, miny, maxx, maxy]
center_x, center_y = (bounds[0]+bounds[2])/2, (bounds[1]+bounds[3])/2

# Filter buildings that intersect the bounding box around center
bbox_buildings = buildings.cx[center_x - radius_deg: center_x + radius_deg, center_y - radius_deg: center_y + radius_deg]

# --- 3. THE MATH (Sunshine Analysis) ---
if st.sidebar.button("Run Simulation", type="primary"):
    with st.spinner(f"Simulating shadows for {len(bbox_buildings)} buildings..."):
        
        # Calculate shadows for the bounded area
        sunshine = pybdshadow.cal_sunshine(bbox_buildings, 
                                          day=str(sim_date), 
                                          roof=True, 
                                          accuracy=accuracy)
        
        # Calculate actual usable area per grid point
        point_area_m2 = accuracy * accuracy
        
        # Simple Energy Estimate
        sunshine['kWh_m2'] = sunshine['Hour'] * 0.18 * 0.75
        
        # Scale to total energy based on area and user multipliers
        sunshine['kWh_total'] = sunshine['kWh_m2'] * point_area_m2 * usable_area_pct * yield_multiplier
        
        total_kwh = sunshine['kWh_total'].sum()
        homes_powered = total_kwh / AVG_HOME_KWH_PER_DAY
        total_co2 = total_kwh * CO2_OFFSET_RATE_LBS_KWH
        
        # --- 4. EXECUTIVE DASHBOARD ---
        st.markdown("---")
        st.subheader("Executive Summary")
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Neighborhood Potential", f"{total_kwh:,.0f} kWh", "Daily Generation")
        m2.metric("Homes Powered", f"{homes_powered:,.0f} Average Homes", "Equivalent daily energy")
        m3.metric("Environmental Impact", f"{total_co2:,.0f} lbs", "Daily CO2 Offset")
        st.markdown("---")

        # Profitable Installations Metric
        profitable_buildings = (sunshine.groupby('building_id')['kWh_total'].sum() > 5.0).sum()
        st.success(f"Out of {len(bbox_buildings)} buildings in this neighborhood, {profitable_buildings} have sufficient unshaded roof space for a profitable solar installation.")

        # --- 5. VISUALIZATIONS ---
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader(f"3D Irradiance Mapping: {sim_date}")
            map_1 = KeplerGl(height=500)
            map_1.add_data(data=bbox_buildings.copy(), name='Buildings')
            map_1.add_data(data=sunshine.copy(), name='Solar Intensity')
            keplergl_static(map_1)
            
        with col2:
            st.subheader("Comparative Analysis")
            building_totals = sunshine.groupby('building_id')['kWh_total'].sum().sort_values(ascending=False).head(10)
            st.write("Top 10 High-Yield Buildings (Daily kWh):")
            st.bar_chart(building_totals)
            
            st.subheader("Hourly Generation Curve")
            hours = pd.DataFrame({'Hour': range(6, 19)})
            import numpy as np
            hours['Production (kWh)'] = total_kwh * (np.exp(-0.5 * ((hours['Hour'] - 12) / 2.5) ** 2) / (2.5 * np.sqrt(2 * np.pi)))
            fig = px.line(hours, x='Hour', y='Production (kWh)', markers=True)
            fig.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Adjust the settings in the sidebar and click **'Run Simulation'** to generate the executive report.")