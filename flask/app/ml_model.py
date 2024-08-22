import numpy as np
import pycuda.driver as cuda
import pycuda.autoinit
from pycuda.compiler import SourceModule
import joblib  # Use joblib for saving and loading
import requests
import pandas as pd
import geopandas as gpd
from math import radians, sin, cos, sqrt, atan2
from fake_data_gen import generate_fake_data_main  # Import the function from fake-data-gen.py
from Model import relay_point
# Load city data and boundaries
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

# Corrected Haversine formula implemented in CUDA for geographical distance calculation
mod = SourceModule("""
__global__ void calculate_weighted_haversine(float *lat1, float *lon1, float *lat2, float *lon2, float *distances, float *purchase_rates, int num_clients, int num_relay_points) {
    int idx = threadIdx.x + blockIdx.x * blockDim.x;
    if (idx < num_clients) {
        float R = 6371.0; // Radius of Earth in kilometers
        float min_distance = 1e20;
        
        for (int j = 0; j < num_relay_points; ++j) {
            float dlat = (lat2[j] - lat1[idx]) * 0.017453292519943295; // Convert degrees to radians
            float dlon = (lon2[j] - lon1[idx]) * 0.017453292519943295; // Convert degrees to radians
            float a = sin(dlat/2) * sin(dlat/2) + cos(lat1[idx] * 0.017453292519943295) * cos(lat2[j] * 0.017453292519943295) * sin(dlon/2) * sin(dlon/2);
            float c = 2 * atan2(sqrt(a), sqrt(1-a));
            float distance = purchase_rates[idx] * R * c;
            if (distance < min_distance) {
                min_distance = distance;
            }
        }
        distances[idx] = min_distance;
    }
}
""")

calculate_weighted_haversine = mod.get_function("calculate_weighted_haversine")

def compute_weighted_haversine_distances(lat1, lon1, lat2, lon2, purchase_rates, num_relay_points):
    num_clients = len(lat1)
    
    # Ensure arrays are contiguous
    lat1 = np.ascontiguousarray(lat1)
    lon1 = np.ascontiguousarray(lon1)
    lat2 = np.ascontiguousarray(lat2)
    lon2 = np.ascontiguousarray(lon2)
    purchase_rates = np.ascontiguousarray(purchase_rates)
    
    # Allocate memory on the GPU
    lat1_gpu = cuda.mem_alloc(lat1.nbytes)
    lon1_gpu = cuda.mem_alloc(lon1.nbytes)
    lat2_gpu = cuda.mem_alloc(lat2.nbytes)
    lon2_gpu = cuda.mem_alloc(lon2.nbytes)
    distances_gpu = cuda.mem_alloc(num_clients * np.float32().nbytes)
    purchase_rates_gpu = cuda.mem_alloc(purchase_rates.nbytes)
    
    # Copy data to the GPU in one batch
    cuda.memcpy_htod(lat1_gpu, lat1)
    cuda.memcpy_htod(lon1_gpu, lon1)
    cuda.memcpy_htod(lat2_gpu, lat2)
    cuda.memcpy_htod(lon2_gpu, lon2)
    cuda.memcpy_htod(purchase_rates_gpu, purchase_rates)
    
    # Launch the kernel with a large block size
    block_size = 1024  # Increase block size to maximize GPU utilization
    grid_size = (num_clients + block_size - 1) // block_size
    calculate_weighted_haversine(
        lat1_gpu, lon1_gpu, lat2_gpu, lon2_gpu, distances_gpu, purchase_rates_gpu,
        np.int32(num_clients), np.int32(num_relay_points),
        block=(block_size, 1, 1), grid=(grid_size, 1)
    )
    
    # Copy the result back to the CPU in one batch
    distances = np.empty(num_clients, dtype=np.float32)
    cuda.memcpy_dtoh(distances, distances_gpu)
    
    # Free GPU memory
    lat1_gpu.free()
    lon1_gpu.free()
    lat2_gpu.free()
    lon2_gpu.free()
    distances_gpu.free()
    purchase_rates_gpu.free()
    
    return distances

def kmeans_with_cuda_geographic(client_positions, purchase_rates, city_positions, num_relay_points, num_iterations=100):
    num_clients = client_positions.shape[0]
    lat_clients, lon_clients = client_positions[:, 0], client_positions[:, 1]
    lat_cities, lon_cities = city_positions[:, 0], city_positions[:, 1]
    
    centroids_indices = np.random.choice(len(lat_cities), num_relay_points, replace=False)
    centroids_lat = lat_cities[centroids_indices]
    centroids_lon = lon_cities[centroids_indices]
    
    for _ in range(num_iterations):
        distances = compute_weighted_haversine_distances(
            lat_clients, lon_clients, centroids_lat, centroids_lon, purchase_rates, num_relay_points)
        
        clusters = [[] for _ in range(num_relay_points)]
        for i in range(num_clients):
            closest_relay = np.argmin(distances[i::num_clients])
            clusters[closest_relay].append(i)
        
       # Ensure single-element extraction for lat/lon assignments
        for j in range(num_relay_points):
         if clusters[j]:  # Avoid division by zero
            weighted_lat = np.sum(lat_clients[clusters[j]] * purchase_rates[clusters[j]])
            weighted_lon = np.sum(lon_clients[clusters[j]] * purchase_rates[clusters[j]])
            total_weight = np.sum(purchase_rates[clusters[j]])
            centroids_lat[j] = (weighted_lat / total_weight).item()  # Extract single element
            centroids_lon[j] = (weighted_lon / total_weight).item()  # Extract single element
            
        # Re-assign centroids to the nearest city
        centroids_indices = []
        for j in range(num_relay_points):
            distances_to_cities = np.sqrt((lat_cities - centroids_lat[j])**2 + (lon_cities - centroids_lon[j])**2)
            nearest_city_index = np.argmin(distances_to_cities)
            centroids_indices.append(nearest_city_index)
        centroids_lat = lat_cities[centroids_indices]
        centroids_lon = lon_cities[centroids_indices]
    
    return np.column_stack((centroids_lat, centroids_lon))
client_positions, purchase_rates = generate_fake_data_main()
def train_and_save_geographic_model(client_positions, purchase_rates, city_positions, num_relay_points, model_path, num_iterations=100):
    final_centroids = kmeans_with_cuda_geographic(client_positions, purchase_rates, city_positions, num_relay_points, num_iterations)
    joblib.dump(final_centroids, model_path)  # Save using joblib
    print("Geographically constrained model saved at", model_path)

def load_and_predict_geographic(model_path, client_positions, purchase_rates):
    centroids = joblib.load(model_path)  # Load using joblib
    
    lat_clients, lon_clients = client_positions[:, 0], client_positions[:, 1]
    lat_relay, lon_relay = centroids[:, 0], centroids[:, 1]
    
    distances = compute_weighted_haversine_distances(lat_clients, lon_clients, lat_relay, lon_relay, purchase_rates, len(centroids))
    
    return centroids

# Example usage:

# Load France boundary shapefile and city data
cache_file_boundaries = 'france_boundaries_cache.pkl'
cache_file_city = 'city_cache.pkl'
api_url = 'http://overpass-api.de/api/interpreter?data=[out:json];area[name=%27France%27][admin_level=2];node[place=city](area);out%20body;'

france_boundaries = load_france_boundaries(cache_file_boundaries)
city_coordonne, city_names = load_city(cache_file_city, api_url)

# # Example client data (client_positions and purchase_rates should be loaded from your dataset)
# client_positions = np.array([[48.8566, 2.3522], [43.2965, 5.3698], [45.7640, 4.8357]], dtype=np.float32)  # Example: Paris, Marseille, Lyon
# purchase_rates = np.array([1.0, 2.0, 1.5], dtype=np.float32)

# Filter delivery points to be within France
client_positions_gdf = gpd.GeoDataFrame(
    geometry=gpd.points_from_xy(client_positions[:, 1], client_positions[:, 0])
)
client_positions_gdf = client_positions_gdf[client_positions_gdf.within(france_boundaries.geometry.union_all())]

filtered_positions = np.column_stack((client_positions_gdf.geometry.y, client_positions_gdf.geometry.x))

# Train and save the model
train_and_save_geographic_model(filtered_positions, purchase_rates, city_coordonne, num_relay_points=2, model_path='geographic_relay_points_model.pkl')
def generate_relay_points() -> bool:
    new_client_positions, new_purchase_rates = generate_fake_data_main()
    try :
        relay_points = load_and_predict_geographic('geographic_relay_points_model.pkl', new_client_positions, new_purchase_rates)
        for i, point in enumerate(relay_points):
            relay_point.create_relay_point([point[0], point[1]])
            print(f"Relay point {i+1}: Latitude {point[0]}, Longitude {point[1]}")
            return True
    except Exception as e:
        print(f"Error generating relay points: {e}")
        return False