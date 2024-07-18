import pandas as pd
import numpy as np
import geopandas as gpd
from sklearn.cluster import KMeans
import folium
import joblib
from tqdm import tqdm

# Path to cache file
cache_file_boundaries = 'france_boundaries_cache.pkl'
cache_file_city = 'city_cache.pkl'

def load_france_boundaries(cache_file_boundaries):
    try:
        france_boundaries = joblib.load(cache_file_boundaries)
        print("Loaded France boundaries from cache.")
    except (FileNotFoundError, EOFError):
        print("Cache not found. Loading France boundaries from shapefile.")
        france_boundaries = gpd.read_file("FRA.zip")
        joblib.dump(france_boundaries, cache_file_boundaries)
        print("France boundaries cached.")
    return france_boundaries

def load_city(cache_file_city):
    try:
        city_data = joblib.load(cache_file_city)
        print("Loaded France city from cache.")
    except (FileNotFoundError, EOFError):
        print("Cache not found. Loading France city from CSV.")
        city = pd.read_csv('cities.csv')
        if 'latitude' in city.columns and 'longitude' in city.columns and 'label' in city.columns:
            city = city.dropna(subset=['latitude', 'longitude', 'label'])  # Ensure city_name is also considered
            city_coordonne = city[['latitude', 'longitude']].values
            city_names = city['label'].values  # Extract city names
            city_data = (city_coordonne, city_names)  # Store both coordinates and names
            joblib.dump(city_data, cache_file_city)
            print("France city cached.")
        else:
            raise KeyError("Required columns not found in the CSV file.")
    return city_data
# Generate fictitious delivery data
num_customers = 1000
np.random.seed(15)
delivery_data = pd.DataFrame({
    'customer_id': range(1, num_customers + 1),
    'latitude': np.random.uniform(42, 51, num_customers),
    'longitude': np.random.uniform(-5, 8, num_customers),
    'purchases': np.random.randint(1, 10, num_customers)
})

# Convert delivery data to GeoDataFrame
gdf_deliveries = gpd.GeoDataFrame(
    delivery_data, geometry=gpd.points_from_xy(delivery_data.longitude, delivery_data.latitude))

# Load France boundary shapefile
france_boundaries = load_france_boundaries(cache_file_boundaries)
city_coordonne = load_city(cache_file_city)
city_names = city_coordonne[1]
# Filter delivery points to be within France
with tqdm(total=gdf_deliveries.shape[0], desc="Filtering delivery points within France") as pbar:
    gdf_deliveries = gdf_deliveries[gdf_deliveries.within(france_boundaries.unary_union)]
    pbar.update(gdf_deliveries.shape[0])

# Cluster analysis to find optimal relay points
with tqdm(total=1, desc="Clustering analysis") as pbar:
    kmeans = KMeans(n_clusters=125, random_state=42)
    gdf_deliveries['cluster'] = kmeans.fit_predict(gdf_deliveries[['latitude', 'longitude']])
    pbar.update(1)

# Calculate cluster centers
with tqdm(total=1, desc="Calculating cluster centers") as pbar:
    cluster_centers = pd.DataFrame(kmeans.cluster_centers_, columns=['latitude', 'longitude'])
    pbar.update(1)

# Visualize with folium
map_center = [46.603354, 1.888334]  # Center of France
m = folium.Map(location=map_center, zoom_start=6)

# Add delivery points
for idx, row in tqdm(gdf_deliveries.iterrows(), total=gdf_deliveries.shape[0], desc="Adding delivery points"):
    folium.CircleMarker(
        location=[row['latitude'], row['longitude']],
        radius=3,
        color='blue',
        fill=True,
        fill_color='blue',
        fill_opacity=0.6
    ).add_to(m)

# Add cluster centers as relay points
for idx, row in tqdm(cluster_centers.iterrows(), total=cluster_centers.shape[0], desc="Adding relay points"):
    loca = np.array([row['latitude'], row['longitude']])
    distances = np.linalg.norm(city_coordonne[0] - loca, axis=1)
    closest_city_index = np.argmin(distances)
    closest_city_coords = city_coordonne[0][closest_city_index]

    if not np.isnan(closest_city_coords).any():  # Check for NaN values
        # Assuming city_names is a list of city names corresponding to city_coordonne
        closest_city_name = city_names[closest_city_index]
        folium.Marker(
            location=closest_city_coords,
            popup=f'Relay Point {idx + 1}: {closest_city_name}',  # Include city name in popup
            icon=folium.Icon(color='red')
        ).add_to(m)

# Save map
m.save('relay_points_map2.html')
