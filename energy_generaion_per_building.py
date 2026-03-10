import geopandas as gpd
import pybdshadow
import pandas as pd
import matplotlib.pyplot as plt

# 1. SETUP
print("Step 1: Loading data...")
buildings = gpd.read_file('bd_demo_2.json')
buildings = pybdshadow.bd_preprocess(buildings)

# Filter for the study area
bounds = [120.603, 31.303, 120.605, 31.305]
buildings_analysis = buildings.cx[bounds[0]:bounds[2], bounds[1]:bounds[3]].copy()

# 2. ANALYSIS
accuracy = 1 # 1 meter grid
print(f"Step 2: Calculating roof sunshine (Accuracy: {accuracy}m)...")
sunshine = pybdshadow.cal_sunshine(buildings_analysis,
                                   day='2022-01-01',
                                   roof=True,
                                   accuracy=accuracy,
                                   precision=900)

# 3. ENERGY AGGREGATION
# Constants
r = 0.18           # 18% Efficiency
PR = 0.75          # Performance Ratio
Irradiance = 1.0   # 1 kWh/m2 per hour (Standard test condition proxy)
cell_area = accuracy**2 

print("Step 3: Aggregating energy per building...")

# Group the grid points by building_id and sum the hours
building_stats = sunshine.groupby('building_id')['Hour'].sum().reset_index()

# Calculate Total kWh for each building
# Formula: (Sum of Hours in all grid cells) * (Area of one cell) * Efficiency * PR * Irradiance
building_stats['total_kWh'] = building_stats['Hour'] * cell_area * r * PR * Irradiance

# Merge results back to the building shapes
buildings_energy = buildings_analysis.merge(building_stats, on='building_id', how='left')
buildings_energy['total_kWh'] = buildings_energy['total_kWh'].fillna(0)

# 4. VISUALIZATION
fig, ax = plt.subplots(figsize=(12, 10))

# Plot buildings colored by total energy output
buildings_energy.plot(ax=ax, column='total_kWh', cmap='YlOrRd', legend=True,
                      legend_kwds={'label': "Total Building Energy (kWh/day)"},
                      edgecolor='black')

# Add labels for the top energy producers
for x, y, label in zip(buildings_energy.centroid.x, buildings_energy.centroid.y, buildings_energy['total_kWh']):
    if label > 0:
        ax.text(x, y, f"{label:.1f}", fontsize=8, ha='center')

ax.set_title('BIPV Potential: Total Energy Generated per Building (Jan 1st)')
plt.show()

print(f"Total Area Energy Production: {buildings_energy['total_kWh'].sum():.2f} kWh/day")