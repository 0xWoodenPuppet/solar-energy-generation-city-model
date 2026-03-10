# ## 1. SETUP AND DATA PREPARATION ##
import pandas as pd
import geopandas as gpd
import pybdshadow
import matplotlib.pyplot as plt

print("Step 1: Loading and preprocessing data...")
# Read building data from the JSON file in the same folder
buildings = gpd.read_file('bd_demo_2.json')

# Preprocess the data (cleans geometry, adds building_id)
buildings = pybdshadow.bd_preprocess(buildings)
print("Data loaded and preprocessed successfully.\n")


# ## 2. GENERATE SHADOW FOR A SPECIFIC TIME ##
print("Step 2: Calculating shadow for a specific moment...")
# Define a specific time. We'll use a local timezone and convert to UTC.
date = pd.to_datetime('2022-01-01 12:45:00').tz_localize('Asia/Shanghai')
date_utc = date.tz_convert('UTC')

# Calculate the shadows cast by the sun at that moment
shadows = pybdshadow.bdshadow_sunlight(buildings, date_utc)
print("Shadow calculation complete.\n")

# Visualize the buildings and their shadows
print("Step 3: Visualizing the single-moment shadow...")
fig1, ax1 = plt.subplots(figsize=(10, 10))
buildings.plot(ax=ax1, color='lightgrey', edgecolor='black')
shadows.plot(ax=ax1, color='black', alpha=0.5)
ax1.set_title(f'Building Shadows on {date.strftime("%Y-%m-%d %H:%M")}')
# plt.show()


# ## 3. ANALYZE SUNSHINE DURATION OVER A DAY ##
print("Step 4: Analyzing sunshine duration for a full day...")
# For faster analysis, let's select a smaller area
bounds = [120.603, 31.303, 120.605, 31.305]
buildings_analysis = buildings.cx[bounds[0]:bounds[2], bounds[1]:bounds[3]]

# Calculate total sunshine hours on the GROUND for a winter day
# accuracy=1 means a 1x1 meter grid, precision=900 means check every 15 mins
sunshine_winter = pybdshadow.cal_sunshine(buildings_analysis,
                                          day='2022-01-01',
                                          roof=True,
                                          accuracy=1,
                                          precision=900)
print("Sunshine analysis complete.\n")

# Visualize the sunshine duration as a heatmap
print("Step 5: Visualizing sunshine duration heatmap...")
fig2, ax2 = plt.subplots(figsize=(10, 8))

# Plot the sunshine heatmap
sunshine_winter.plot(ax=ax2, column='Hour', cmap='plasma', legend=True,
                     legend_kwds={'label': "Hours of Sunlight", 'orientation': "horizontal"})

# Overlay the building outlines for context
buildings_analysis.plot(ax=ax2, edgecolor='black', facecolor='none')

ax2.set_title('Sunshine Duration on Ground (Winter: Jan 1st)')
plt.show()

print("\nAnalysis finished! 🎉")