import os
import logging
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib

from aegis.config import MODEL_FEATURES, MODEL_PATH
from aegis.ml_model import create_model, save_model

def generate_synthetic_data(n_samples=1000, contamination=0.1):
    """
    Generate synthetic normal and anomalous data for training the model.
    
    Args:
        n_samples: Number of samples to generate
        contamination: Proportion of anomalous samples
        
    Returns:
        DataFrame with synthetic data
    """
    # Calculate number of normal and anomalous samples
    n_normal = int(n_samples * (1 - contamination))
    n_anomalous = n_samples - n_normal
    
    # Generate normal data (centered around expected values with some variance)
    normal_data = pd.DataFrame({
        "temperature": np.random.normal(75, 5, n_normal),  # degrees Celsius
        "pressure": np.random.normal(100, 10, n_normal),   # kPa
        "rpm": np.random.normal(3000, 200, n_normal)       # revolutions per minute
    })
    
    # Generate anomalous data (with values outside normal ranges)
    anomalous_data = pd.DataFrame({
        "temperature": np.concatenate([
            np.random.normal(40, 5, n_anomalous // 3),     # much colder
            np.random.normal(110, 10, n_anomalous // 3),   # much hotter
            np.random.normal(75, 20, n_anomalous // 3)     # normal mean, high variance
        ]),
        "pressure": np.concatenate([
            np.random.normal(50, 10, n_anomalous // 3),    # much lower
            np.random.normal(150, 15, n_anomalous // 3),   # much higher
            np.random.normal(100, 30, n_anomalous // 3)    # normal mean, high variance
        ]),
        "rpm": np.concatenate([
            np.random.normal(1000, 200, n_anomalous // 3), # much slower
            np.random.normal(5000, 300, n_anomalous // 3), # much faster
            np.random.normal(3000, 800, n_anomalous // 3)  # normal mean, high variance
        ])
    })
    
    # Combine the datasets and shuffle
    all_data = pd.concat([normal_data, anomalous_data])
    all_data = all_data.sample(frac=1).reset_index(drop=True)  # shuffle
    
    return all_data

def train_and_save_model():
    """Generate synthetic data, train an Isolation Forest model, and save it."""
    logging.info("Generating synthetic training data...")
    training_data = generate_synthetic_data(n_samples=5000, contamination=0.1)
    
    logging.info(f"Training Isolation Forest model with {len(training_data)} samples...")
    model = create_model()
    model.fit(training_data[MODEL_FEATURES].values)
    
    logging.info("Saving model...")
    success = save_model(model)
    
    if success:
        logging.info(f"Model saved successfully to {MODEL_PATH}")
    else:
        logging.error("Failed to save model")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    train_and_save_model()
