import streamlit as st
import geopandas as gpd
import pybdshadow
import pandas as pd
from streamlit_keplergl import keplergl_static
from keplergl import KeplerGl

# --- PAGE CONFIG ---
st.set_page_config(page_title="Saurya Sankulan - BIPV Simulator", layout="wide")
st.title("🏙️ Saurya Sankulan: 3D City Solar Assessment")

# --- PARAMETERS & CONSTANTS ---
ELECTRICITY_PRICE_KWH = 0.15
CO2_OFFSET_RATE_LBS_KWH = 0.85

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
        # Using a fixed grid spacing based on accuracy to get point-level irradiation
        sunshine = pybdshadow.cal_sunshine(bbox_buildings, 
                                          day=str(sim_date), 
                                          roof=True, 
                                          accuracy=accuracy)
        
        # Calculate actual usable area per grid point
        # Point area = accuracy * accuracy (since it's a grid)
        point_area_m2 = accuracy * accuracy
        
        # Simple Energy Estimate:
        # sunshine['Hour'] contains hours of direct sunlight.
        # Assume max irradiance of 1000W/m2 (1kW/m2), derate 0.75 for system losses, and 0.18 for PV efficiency
        sunshine['kWh_m2'] = sunshine['Hour'] * 0.18 * 0.75
        
        # Scale to total energy based on area and user multipliers
        sunshine['kWh_total'] = sunshine['kWh_m2'] * point_area_m2 * usable_area_pct * yield_multiplier
        
        total_kwh = sunshine['kWh_total'].sum()
        total_savings = total_kwh * ELECTRICITY_PRICE_KWH
        total_co2 = total_kwh * CO2_OFFSET_RATE_LBS_KWH
        
        # --- 4. EXECUTIVE DASHBOARD ---
        st.markdown("---")
        st.subheader("Executive Summary")
        m1, m2, m3 = st.columns(3)
        m1.metric("Neighborhood Solar Potential", f"{total_kwh:,.0f} kWh", "Daily Generation")
        m2.metric("Estimated Monetary Value", f"${total_savings:,.2f}", "Daily Savings")
        m3.metric("CO2 Emissions Prevented", f"{total_co2:,.0f} lbs", "Daily Carbon Offset")
        st.markdown("---")
        
        # --- 5. VISUALIZATIONS ---
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader(f"3D Irradiance Mapping: {sim_date}")
            map_1 = KeplerGl(height=500)
            map_1.add_data(data=bbox_buildings.copy(), name='Buildings')
            map_1.add_data(data=sunshine.copy(), name='Solar Intensity')
            
            # Use predefined config if available, otherwise keplergl_static will use default
            keplergl_static(map_1)
            
        with col2:
            st.subheader("Comparative Analysis")
            # Calculate total kWh per building
            building_totals = sunshine.groupby('building_id')['kWh_total'].sum().sort_values(ascending=False).head(10)
            st.write("Top 10 High-Yield Buildings (Daily kWh):")
            st.bar_chart(building_totals)
            
            st.subheader("Hourly Generation Curve (Proxy)")
            # PyBDShadow calculates total sunny hours per grid point. We don't have the exact profile natively.
            # To simulate a curve, we'll plot a normal distribution approximating solar noon.
            # NOTE: this is an approximation for visualization purposes of the BIPV potential scale.
            hours = pd.DataFrame({'Hour': range(6, 19)})
            # A simple bell curve centered at noon (12:00) representing solar production
            import numpy as np
            hours['Production (kWh)'] = total_kwh * (np.exp(-0.5 * ((hours['Hour'] - 12) / 2.5) ** 2) / (2.5 * np.sqrt(2 * np.pi)))
            hours = hours.set_index('Hour')
            st.line_chart(hours)

else:
    st.info("Adjust the settings in the sidebar and click **'Run Simulation'** to generate the executive report.")