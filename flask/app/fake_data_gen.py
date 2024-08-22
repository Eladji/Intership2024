import numpy as np
import pandas as pd
def generate_fake_data_main():
    def generate_fake_data(num_clients=300):
        np.random.seed(42)  # For reproducibility

        # Randomly generate latitudes and longitudes within France's approximate bounds
        latitudes = np.random.uniform(42.0, 51.0, num_clients)  # Latitude range for France
        longitudes = np.random.uniform(-5.0, 8.0, num_clients)  # Longitude range for France

        # Generate random purchase rates
        purchase_rates = np.random.uniform(1.0, 10.0, num_clients)  # Random purchase rates between 1 and 10

        # Combine into a DataFrame
        data = pd.DataFrame({
            'latitude': latitudes,
            'longitude': longitudes,
            'purchase_rate': purchase_rates
        })
        
        return data

    # Generate the fake data
    fake_data = generate_fake_data(num_clients=300)

    # Convert to the format needed by the training function
    client_positions = fake_data[['latitude', 'longitude']].values
    purchase_rates = fake_data['purchase_rate'].values

    # Display the first few rows of the generated data
    print(fake_data.head())

    # Use client_positions and purchase_rates for training
    return client_positions, purchase_rates