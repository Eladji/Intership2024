import pandas as pd
import numpy as np
import geopandas as gpd
from sklearn.cluster import KMeans
import folium
import joblib
import requests
from tqdm import tqdm
from joblib import Parallel, delayed
from Model import relay_point
import json, os
from  dotenv import load_dotenv
load_dotenv()

# Path to cache files
cache_file_boundaries = 'france_boundaries_cache.pkl'
cache_file_city = 'city_cache.pkl'
api_url = 'http://overpass-api.de/api/interpreter?data=[out:json];area[name=%27France%27][admin_level=2];node[place=city](area);out%20body;'
    
def generate_relay_points() -> bool:
    try:
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

        def load_city(cache_file_city, api_url):
            try:
                city_data = joblib.load(cache_file_city)
                print("Loaded France city from cache.")
            except (FileNotFoundError, EOFError):
                print("Cache not found. Loading France city from JSON.")
                
                try:
                    response = requests.get(api_url)
                    response.raise_for_status()
                    city_json = response.json()
                except requests.RequestException as e:
                    print(f"Error fetching data from API: {e}")
                    return None
                
                city_elements = city_json.get('elements', [])
                city_df = pd.json_normalize(city_elements)
                
                if {'lat', 'lon', 'tags.name'}.issubset(city_df.columns):
                    city_df = city_df[['lat', 'lon', 'tags.name']]
                    city_df.columns = ['lat', 'lng', 'name']
                    city_df = city_df.dropna(subset=['lat', 'lng', 'name'])
                    
                    city_coordonne = city_df[['lat', 'lng']].values
                    city_names = city_df['name'].values
                    
                    city_data = (city_coordonne, city_names)
                    joblib.dump(city_data, cache_file_city)
                    print("France city cached.")
                else:
                    raise KeyError("Required columns not found in the JSON file.")
            
            return city_data
        def testing_date_gen():
            # Generate fictitious delivery data
            num_customers = 300
            np.random.seed(5)
            delivery_data = pd.DataFrame({
                'customer_id': range(1, num_customers + 1),
                'latitude': np.random.uniform(42, 51, num_customers),
                'longitude': np.random.uniform(-5, 8, num_customers),
                'purchases': np.random.randint(1, 10, num_customers)
            })
            return delivery_data
        delivery_data = testing_date_gen() #need to be replaced by the data from the database
        # Convert delivery data to GeoDataFrame
        gdf_deliveries = gpd.GeoDataFrame(
            delivery_data, geometry=gpd.points_from_xy(delivery_data.longitude, delivery_data.latitude))

        # Load France boundary shapefile and city data
        france_boundaries = load_france_boundaries(cache_file_boundaries)
        city_coordonne, city_names = load_city(cache_file_city, api_url)

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
                relay_point.create_relay_point(closest_city_name, closest_city_coords)
                #save relay point in the database 

        add_markers_to_map(gdf_deliveries, cluster_centers, city_coordonne, city_names, m)

        # Save map
        m.save('relay_points_map3.html')
        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False