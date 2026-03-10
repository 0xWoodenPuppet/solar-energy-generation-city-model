import geopandas as gpd
import pybdshadow
import matplotlib.pyplot as plt

# --- 1. Load and Prepare Building Data ---

# Load building data from a file.
# Note: This line assumes 'bd_demo_2.json' is in the same folder as your script.
buildings = gpd.read_file('bd_demo_2.json')

# Preprocess the data (cleans geometry, adds building_id)
buildings = pybdshadow.bd_preprocess(buildings)

# --- 2. Plot the Buildings ---

# Create a plot to visualize the building footprints
buildings.plot(figsize=(10, 10))

# Display the plot
plt.show()

print("Script finished successfully and plotted the buildings!")