# 1. Import necessary libraries
import geopandas as gpd
import pybdshadow
import keplergl
import os
from shapely.geometry import Point

print("--- Point Light Shadow Generation Script ---")

# 2. Load and preprocess the building data
try:
    # Replace 'bd_demo_2.json' with the name of your data file
    buildings = gpd.read_file('bd_demo_2.json')
except Exception as e:
    print(f"Error: Could not read the data file.")
    print(f"Please make sure a building data file is in the same folder as the script.")
    print(f"Details: {e}")
    exit()

buildings = pybdshadow.bd_preprocess(buildings)
print("Step 1: Building data loaded and preprocessed.")

# 3. Define the position (longitude, latitude) and height of the point light
pointlon, pointlat, pointheight = [120.608206, 31.300141, 200]
print(f"Step 2: Calculating shadows from a {pointheight}m high light source.")

# 4. Calculate the building shadows
shadows = pybdshadow.bdshadow_pointlight(buildings, pointlon, pointlat, pointheight)
print(f"Step 3: Shadow calculation complete. Found {len(shadows)} shadow geometries.")

# 5. Create a layer for the light source itself for visualization
light_source = gpd.GeoDataFrame([{'height': pointheight}],
                                 geometry=[Point(pointlon, pointlat)],
                                 crs="EPSG:4326")

# 6. Create and save an interactive 3D map
output_filename = 'pointlight_shadow_map.html'

# Create a KeplerGL map object
map_viz = keplergl.KeplerGl(height=600)
# Add the building data to the map
map_viz.add_data(data=buildings, name='Buildings')
# Add the shadow data to the map
map_viz.add_data(data=shadows, name='Shadows')
# Add the light source to the map
map_viz.add_data(data=light_source, name='Light Source')

# Save the map to an HTML file
map_viz.save_to_html(file_name=output_filename)

output_path = os.path.abspath(output_filename)
print(f"Step 4: Successfully saved interactive map to: {output_path}")
print("\nTo view the result, find this file on your computer and open it with a web browser.")
print("--- Script Finished ---")