import geopandas as gpd
import pybdshadow
import pandas as pd
import matplotlib.pyplot as plt

# 1. SETUP
print("Step 1: Loading data...")
buildings = gpd.read_file('bd_demo_2.json')
buildings = pybdshadow.bd_preprocess(buildings)

# Filter for the specific study area
bounds = [120.603, 31.303, 120.605, 31.305]
buildings_analysis = buildings.cx[bounds[0]:bounds[2], bounds[1]:bounds[3]].copy()

# 2. ANALYSIS
print("Step 2: Calculating roof sunshine hours...")
sunshine = pybdshadow.cal_sunshine(buildings_analysis,
                                   day='2022-01-01',
                                   roof=True,
                                   accuracy=1,
                                   precision=900)

# 3. ENERGY ESTIMATION
# Assumptions:
# - Efficiency (r) = 18% (Typical BIPV)
# - Performance Ratio (PR) = 0.75
# - Solar Constant (Irradiance) = ~1000 W/m2 at peak
r = 0.18
PR = 0.75
irradiance_per_hour = 1.0 # 1 kWh/m2 per hour of sunlight

# Calculate kWh per m2
sunshine['kWh_m2'] = sunshine['Hour'] * irradiance_per_hour * r * PR

print(f"Total potential Energy for area: {sunshine['kWh_m2'].sum():.2f} kWh/day")

# 4. VISUALIZATION
fig, ax = plt.subplots(figsize=(10, 8))
# Plot energy potential heatmap
sunshine.plot(ax=ax, column='kWh_m2', cmap='viridis', legend=True,
              legend_kwds={'label': "Estimated kWh per m2"})

buildings_analysis.plot(ax=ax, edgecolor='black', facecolor='none', alpha=0.5)
ax.set_title('BIPV Solar Energy Potential (kWh/m2) - Jan 1st')
plt.show()