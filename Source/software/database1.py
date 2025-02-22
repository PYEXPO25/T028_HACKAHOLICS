import numpy as np
import pandas as pd
import pickle
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor

# Generate synthetic dataset
np.random.seed(42)
data = {
    "temperature": np.random.uniform(20, 40, 1000),
    "humidity": np.random.uniform(30, 90, 1000),
    "sensor_x": np.random.uniform(0, 100, 1000),
    "sensor_y": np.random.uniform(0, 100, 1000),
    "soil_moisture": np.random.uniform(20, 80, 1000),
}

df = pd.DataFrame(data)

# Split data
X = df[["temperature", "humidity", "sensor_x", "sensor_y"]]
y = df["soil_moisture"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Save model
with open("soil_moisture_model.pkl", "wb") as file:
    pickle.dump(model, file)
