import streamlit as st
import geopandas as gpd
import pybdshadow
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
from streamlit_keplergl import keplergl_static
from keplergl import KeplerGl
from report_generator import generate_report

# ──────────────────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Saurya Sankulan – BIPV Assessment",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────
# CONSTANTS
# ──────────────────────────────────────────────────────────────
CO2_OFFSET_RATE_LBS_KWH = 0.85
AVG_HOME_KWH_PER_DAY = 30.0
TREE_CO2_ABSORB_LBS_PER_YEAR = 48.0      # ~48 lbs CO2 per tree per year
CAR_CO2_LBS_PER_DAY = 24.6               # avg US passenger car ~24.6 lbs/day
ELECTRICITY_PRICE_KWH = 0.15
PV_EFFICIENCY = 0.18
PERFORMANCE_RATIO = 0.75

# ──────────────────────────────────────────────────────────────
# CUSTOM CSS  – premium dark‑themed styling
# ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* ── Global ─────────────────────────────── */
    .block-container { padding-top: 1.5rem; }

    /* ── Metric cards ──────────────────────── */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 18px 22px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.25);
    }
    [data-testid="stMetricValue"] {
        color: #00d4ff;
        font-size: 1.7rem !important;
        font-weight: 700;
    }
    [data-testid="stMetricLabel"] {
        color: #c0c0d0 !important;
        font-weight: 500;
    }
    [data-testid="stMetricDelta"] {
        color: #7ee87e !important;
    }

    /* ── Sidebar ───────────────────────────── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1b2a 0%, #1b2838 100%);
    }
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #00d4ff;
    }

    /* ── Success banner ────────────────────── */
    .stAlert [data-testid="stNotification"] {
        border-radius: 10px;
    }

    /* ── Section dividers ──────────────────── */
    hr { border-color: rgba(255,255,255,0.06) !important; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────────────────────
st.markdown("## ☀️ Saurya Sankulan")
st.caption("Interactive Building‑Integrated Photovoltaic (BIPV) Assessment Tool  ·  LOD‑1 3D City Model")

# ──────────────────────────────────────────────────────────────
# 1. DATA LOADING
# ──────────────────────────────────────────────────────────────
@st.cache_data
def load_buildings(path):
    buildings = gpd.read_file(path)
    buildings = pybdshadow.bd_preprocess(buildings)
    return buildings

st.sidebar.header("📂 Data Source")
uploaded = st.sidebar.file_uploader(
    "Upload a GeoJSON city model",
    type=["json", "geojson"],
    help="Upload any LOD‑1 building footprint file. Leave empty to use the built‑in demo dataset."
)

if uploaded is not None:
    # Save temporarily so geopandas can read it
    import tempfile, os
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    tmp.write(uploaded.read())
    tmp.flush()
    buildings = load_buildings(tmp.name)
    os.unlink(tmp.name)
    st.sidebar.success(f"Loaded {len(buildings)} buildings from upload.")
else:
    buildings = load_buildings("bd_demo_2.json")

# Compute dataset bounds once
bounds = buildings.total_bounds  # [minx, miny, maxx, maxy]
dataset_center_lon = (bounds[0] + bounds[2]) / 2
dataset_center_lat = (bounds[1] + bounds[3]) / 2

# ──────────────────────────────────────────────────────────────
# 2. SIDEBAR — AREA SELECTION (Folium Map)
# ──────────────────────────────────────────────────────────────
st.sidebar.header("📍 Area Selection")
st.sidebar.caption("Click the map to choose a neighborhood center.")

selection_map = folium.Map(
    location=[dataset_center_lat, dataset_center_lon],
    zoom_start=15,
    tiles="CartoDB dark_matter",
    width="100%",
    height=260,
)

# Add a subtle rectangle showing the full dataset extent
folium.Rectangle(
    bounds=[[bounds[1], bounds[0]], [bounds[3], bounds[2]]],
    color="#00d4ff",
    fill=True,
    fill_opacity=0.08,
    weight=1,
    tooltip="Full dataset extent",
).add_to(selection_map)

map_data = st_folium(
    selection_map,
    width=280,
    height=260,
    returned_objects=["last_clicked"],
    key="area_selector",
)

# Determine selected center
if map_data and map_data.get("last_clicked"):
    sel_lat = map_data["last_clicked"]["lat"]
    sel_lon = map_data["last_clicked"]["lng"]
    st.sidebar.success(f"Selected: {sel_lat:.5f}, {sel_lon:.5f}")
else:
    sel_lat = dataset_center_lat
    sel_lon = dataset_center_lon
    st.sidebar.info("Using dataset center. Click the map to pick a different spot.")

# ──────────────────────────────────────────────────────────────
# 3. SIDEBAR — SIMULATION SETTINGS
# ──────────────────────────────────────────────────────────────
st.sidebar.header("⚙️ Simulation Settings")

sim_date = st.sidebar.date_input("Analysis Date", value=pd.to_datetime("2022-06-21"))
accuracy = st.sidebar.slider(
    "Grid Resolution (m)", 1, 10, 3,
    help="Smaller = more precise but slower. 3–5 m is recommended."
)
study_radius = st.sidebar.slider(
    "Study Area Radius (m)", 50, 1000, 200, step=50,
    help="Radius around the selected point to include in the analysis."
)

st.sidebar.header("🔧 Engineering Assumptions")
usable_area_pct = st.sidebar.slider(
    "Usable Roof Area (%)", 10, 100, 60,
    help="Accounts for HVAC equipment, setbacks, and maintenance paths."
) / 100.0

install_type = st.sidebar.selectbox(
    "Panel Installation", ["Flat (Flush Mount)", "Optimal Tilt (+15% Yield)"]
)
yield_multiplier = 1.15 if "Optimal" in install_type else 1.0

# ──────────────────────────────────────────────────────────────
# 4. FILTER BUILDINGS BY SELECTED AREA
# ──────────────────────────────────────────────────────────────
radius_deg = study_radius / 111000.0
bbox_buildings = buildings.cx[
    sel_lon - radius_deg : sel_lon + radius_deg,
    sel_lat - radius_deg : sel_lat + radius_deg,
]

# ──────────────────────────────────────────────────────────────
# 5. RUN SIMULATION
# ──────────────────────────────────────────────────────────────
run = st.sidebar.button("🚀 Run Simulation", type="primary", use_container_width=True)

if run:
    if len(bbox_buildings) == 0:
        st.error("No buildings found in the selected area. Try a larger radius or click a different spot on the map.")
        st.stop()

    with st.spinner(f"☁️ Simulating shadows for **{len(bbox_buildings)}** buildings …"):
        sunshine = pybdshadow.cal_sunshine(
            bbox_buildings,
            day=str(sim_date),
            roof=True,
            accuracy=accuracy,
        )

    # ── Energy Math ──────────────────────────────────────────
    point_area = accuracy ** 2
    sunshine["kWh_m2"] = sunshine["Hour"] * PV_EFFICIENCY * PERFORMANCE_RATIO
    sunshine["kWh_total"] = sunshine["kWh_m2"] * point_area * usable_area_pct * yield_multiplier

    total_kwh = sunshine["kWh_total"].sum()
    homes_powered = total_kwh / AVG_HOME_KWH_PER_DAY
    total_co2 = total_kwh * CO2_OFFSET_RATE_LBS_KWH
    total_savings = total_kwh * ELECTRICITY_PRICE_KWH
    trees_equivalent = (total_co2 * 365) / TREE_CO2_ABSORB_LBS_PER_YEAR
    cars_off_road = total_co2 / CAR_CO2_LBS_PER_DAY
    profitable_count = int((sunshine.groupby("building_id")["kWh_total"].sum() > 5.0).sum())

    # ── EXECUTIVE DASHBOARD ──────────────────────────────────
    st.markdown("---")
    st.subheader("📊 Executive Summary")

    r1c1, r1c2, r1c3, r1c4 = st.columns(4)
    r1c1.metric("Daily Solar Potential", f"{total_kwh:,.0f} kWh", "Total Neighborhood")
    r1c2.metric("Homes Powered", f"{homes_powered:,.0f}", "Average Households")
    r1c3.metric("CO₂ Prevented", f"{total_co2:,.0f} lbs", "Daily Offset")
    r1c4.metric("Daily Savings", f"${total_savings:,.2f}", "At $0.15/kWh")

    r2c1, r2c2, r2c3, r2c4 = st.columns(4)
    r2c1.metric("🌳 Trees Equivalent", f"{trees_equivalent:,.0f}", "Annual Planting Impact")
    r2c2.metric("🚗 Cars Off Road", f"{cars_off_road:,.1f}", "Daily Emission Match")
    r2c3.metric("🏠 Viable Buildings", f"{profitable_count}/{len(bbox_buildings)}", "Profitable Potential")
    r2c4.metric("⚡ Yield Boost", f"+{(yield_multiplier-1)*100:.0f}%", install_type.split('(')[0].strip())

    st.success(
        f"✅ Out of **{len(bbox_buildings)}** buildings analyzed, "
        f"**{profitable_count}** have enough unshaded roof space for a profitable solar installation."
    )
    st.markdown("---")

    # ── VISUALIZATIONS ───────────────────────────────────────
    tab_map, tab_heatmap, tab_charts = st.tabs(["🗺️ 3D Map", "🔥 2D Heatmap", "📈 Charts"])

    # ── Tab 1 : 3D KeplerGL Map (auto-zoomed) ───────────────
    with tab_map:
        st.subheader(f"3D Solar Irradiance  ·  {sim_date}")

        kepler_config = {
            "version": "v1",
            "config": {
                "mapState": {
                    "latitude": sel_lat,
                    "longitude": sel_lon,
                    "zoom": 16,
                    "pitch": 50,
                    "bearing": 20,
                },
                "mapStyle": {
                    "styleType": "dark",
                },
            },
        }

        map_3d = KeplerGl(height=550, config=kepler_config)
        map_3d.add_data(data=bbox_buildings.copy(), name="Buildings")
        map_3d.add_data(data=sunshine.copy(), name="Solar Intensity")
        keplergl_static(map_3d)

    # ── Tab 2 : 2D Heatmap (Plotly) ────────────────────────────
    with tab_heatmap:
        st.subheader("Rooftop Solar Hotspot Heatmap")

        # Extract centroids and energy for plotting
        heat_df = sunshine.copy()
        heat_df["lat"] = heat_df.geometry.centroid.y
        heat_df["lon"] = heat_df.geometry.centroid.x

        fig_heat = px.density_mapbox(
            heat_df,
            lat="lat",
            lon="lon",
            z="kWh_total",
            radius=10,
            zoom=16,
            center={"lat": sel_lat, "lon": sel_lon},
            mapbox_style="carto-darkmatter",
            color_continuous_scale="Turbo",
            height=550,
        )
        fig_heat.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            coloraxis_colorbar_title="kWh",
        )
        st.plotly_chart(fig_heat, use_container_width=True)

    # ── Tab 3 : Charts ───────────────────────────────────────
    with tab_charts:
        ch1, ch2 = st.columns(2)

        with ch1:
            st.subheader("Top Buildings by Daily Output")
            building_totals = (
                sunshine.groupby("building_id")["kWh_total"]
                .sum()
                .sort_values(ascending=False)
                .head(10)
                .reset_index()
            )
            building_totals.columns = ["Building", "Daily Energy (kWh)"]
            fig_bar = px.bar(
                building_totals,
                x="Building",
                y="Daily Energy (kWh)",
                color="Daily Energy (kWh)",
                color_continuous_scale="Turbo",
                text_auto=".0f",
            )
            fig_bar.update_layout(
                height=400,
                margin=dict(l=10, r=10, t=30, b=10),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#c0c0d0",
                xaxis_title="Building ID",
                yaxis_title="Energy (kWh)",
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with ch2:
            st.subheader("Estimated Hourly Generation Curve")
            hours = pd.DataFrame({"Time of Day": range(5, 20)})
            hours["Power Output (kWh)"] = total_kwh * (
                np.exp(-0.5 * ((hours["Time of Day"] - 12) / 2.5) ** 2)
                / (2.5 * np.sqrt(2 * np.pi))
            )
            fig_line = px.area(
                hours,
                x="Time of Day",
                y="Power Output (kWh)",
                markers=True,
                color_discrete_sequence=["#00d4ff"],
            )
            fig_line.update_layout(
                height=400,
                margin=dict(l=10, r=10, t=30, b=10),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#c0c0d0",
                xaxis=dict(dtick=1),
            )
            st.plotly_chart(fig_line, use_container_width=True)

    # ── PDF REPORT DOWNLOAD ──────────────────────────────────
    st.markdown("---")
    st.subheader("📥 Download Report")

    top_buildings_list = (
        sunshine.groupby("building_id")["kWh_total"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )
    top_list = list(zip(top_buildings_list.index.astype(str), top_buildings_list.values))

    pdf_bytes = generate_report(
        sim_date=str(sim_date),
        num_buildings=len(bbox_buildings),
        study_radius_m=study_radius,
        usable_area_pct=usable_area_pct,
        install_type=install_type,
        accuracy=accuracy,
        total_kwh=total_kwh,
        homes_powered=homes_powered,
        total_co2=total_co2,
        trees_equivalent=trees_equivalent,
        cars_off_road=cars_off_road,
        profitable_buildings=profitable_count,
        top_buildings_df=top_list,
    )

    st.download_button(
        label="📄 Download Executive PDF Report",
        data=pdf_bytes,
        file_name=f"saurya_sankulan_report_{sim_date}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

else:
    # ── Landing Page ─────────────────────────────────────────
    st.markdown("---")
    lc, rc = st.columns([2, 1])
    with lc:
        st.markdown("""
        ### How to Use
        1. **Upload a map** or use the built-in demo dataset.
        2. **Click the sidebar map** to select a neighborhood.
        3. Adjust **simulation settings** and **engineering assumptions**.
        4. Click **🚀 Run Simulation** to generate the assessment.
        5. **Download** a professional PDF report to print or share.
        """)
    with rc:
        st.info(
            f"📦 **Dataset loaded:** {len(buildings)} buildings\n\n"
            f"📍 Center: {dataset_center_lat:.4f}°N, {dataset_center_lon:.4f}°E"
        )