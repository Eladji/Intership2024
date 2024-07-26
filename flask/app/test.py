import pandas as pd
import numpy as np
import geopandas as gpd
from sklearn.cluster import KMeans
import folium
import joblib
from tqdm import tqdm
from joblib import Parallel, delayed

# Path to cache files
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
            city = city.dropna(subset=['latitude', 'longitude', 'label'])
            city_coordonne = city[['latitude', 'longitude']].values
            city_names = city['label'].values
            city_data = (city_coordonne, city_names)
            joblib.dump(city_data, cache_file_city)
            print("France city cached.")
        else:
            raise KeyError("Required columns not found in the CSV file.")
    return city_data

# Generate fictitious delivery data
num_customers = 10000
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

# Load France boundary shapefile and city data
france_boundaries = load_france_boundaries(cache_file_boundaries)
city_coordonne, city_names = load_city(cache_file_city)

# Filter delivery points to be within France
gdf_deliveries = gdf_deliveries[gdf_deliveries.within(france_boundaries.unary_union)]

# Cluster analysis to find optimal relay points
kmeans = KMeans(n_clusters=150, random_state=42)
gdf_deliveries['cluster'] = kmeans.fit_predict(gdf_deliveries[['latitude', 'longitude']])

# Calculate cluster centers
cluster_centers = pd.DataFrame(kmeans.cluster_centers_, columns=['latitude', 'longitude'])

# Visualize with folium
map_center = [46.603354, 1.888334]  # Center of France
m = folium.Map(location=map_center, zoom_start=6)

# Add delivery points and cluster centers
def add_markers_to_map(gdf, cluster_centers, city_coordonne, city_names, m):
    for idx, row in gdf.iterrows():
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=3,
            color='blue',
            fill=True,
            fill_color='blue',
            fill_opacity=0.6
        ).add_to(m)
    
    for idx, row in cluster_centers.iterrows():
        loca = np.array([row['latitude'], row['longitude']])
        distances = np.linalg.norm(city_coordonne - loca, axis=1)
        closest_city_index = np.argmin(distances)
        closest_city_coords = city_coordonne[closest_city_index]

        if not np.isnan(closest_city_coords).any():
            closest_city_name = city_names[closest_city_index]
            folium.Marker(
                location=closest_city_coords,
                popup=f'Relay Point {idx + 1}: {closest_city_name}',
                icon=folium.Icon(color='red')
            ).add_to(m)

add_markers_to_map(gdf_deliveries, cluster_centers, city_coordonne, city_names, m)

# Save map
m.save('relay_points_map2.html')
