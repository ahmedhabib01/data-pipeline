import pandas as pd
import os

# Load the full dataset
df = pd.read_csv('sample_data/iot_telemetry_data.csv')

# Create output folder
os.makedirs('sample_data/batches', exist_ok=True)

# Split into chunks of 1000 rows each, take first 5 chunks
chunk_size = 1000
for i, start in enumerate(range(0, 5000, chunk_size)):
    chunk = df.iloc[start:start + chunk_size]
    filename = f'sample_data/batches/sensor_batch_{i+1:03d}.csv'
    chunk.to_csv(filename, index=False)
    print(f'Created {filename} with {len(chunk)} rows')

print('Done! Sample batches created.')