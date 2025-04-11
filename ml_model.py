import os
import logging
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from typing import Dict, Any, Tuple, List, Optional
from aegis.config import MODEL_PATH, MODEL_FEATURES, ANOMALY_THRESHOLD

# Global model variable
isolation_forest_model = None

def load_model():
    """Load the pre-trained Isolation Forest model."""
    global isolation_forest_model
    
    try:
        if os.path.exists(MODEL_PATH):
            logging.info(f"Loading model from {MODEL_PATH}")
            isolation_forest_model = joblib.load(MODEL_PATH)
            logging.info("Model loaded successfully")
        else:
            logging.warning("Model file not found. You need to train the model first.")
            isolation_forest_model = None
    except Exception as e:
        logging.error(f"Error loading model: {str(e)}")
        isolation_forest_model = None

def get_model():
    """Get the loaded model instance."""
    global isolation_forest_model
    if isolation_forest_model is None:
        load_model()
    return isolation_forest_model

def predict_anomaly(data_point: Dict[str, Any]) -> Tuple[bool, float, str]:
    """
    Predict whether a data point is an anomaly using the trained Isolation Forest model.
    
    Args:
        data_point: Dictionary containing sensor data features
        
    Returns:
        Tuple of (is_anomaly, anomaly_score, message)
    """
    model = get_model()
    
    if model is None:
        return False, 0.0, "Model not loaded, unable to perform anomaly detection"
    
    try:
        # Extract features for prediction
        features = np.array([[data_point[feature] for feature in MODEL_FEATURES]])
        
        # Get anomaly score (lower score means more anomalous)
        anomaly_score = model.score_samples(features)[0]
        
        # Determine if it's an anomaly based on threshold
        is_anomaly = anomaly_score < ANOMALY_THRESHOLD
        
        if is_anomaly:
            message = f"Anomaly detected with score {anomaly_score:.4f}"
        else:
            message = f"Normal data point with score {anomaly_score:.4f}"
            
        return is_anomaly, anomaly_score, message
    
    except Exception as e:
        logging.error(f"Error during anomaly prediction: {str(e)}")
        return False, 0.0, f"Error during prediction: {str(e)}"

def create_model() -> IsolationForest:
    """Create a new Isolation Forest model with default parameters."""
    return IsolationForest(
        n_estimators=100,
        max_samples="auto",
        contamination=0.1,  # Expect about 10% anomalies
        random_state=42,
        verbose=0
    )

def train_model_with_data(data: pd.DataFrame) -> IsolationForest:
    """
    Train an Isolation Forest model with the provided data.
    
    Args:
        data: DataFrame containing training data with MODEL_FEATURES columns
        
    Returns:
        Trained IsolationForest model
    """
    model = create_model()
    
    # Extract features for training
    features = data[MODEL_FEATURES].values
    
    # Fit the model
    model.fit(features)
    
    return model

def save_model(model: IsolationForest, training_data_size: int = None, parameters: dict = None) -> bool:
    """
    Save the trained model to disk and store metadata in the database.
    
    Args:
        model: Trained IsolationForest model
        training_data_size: Number of samples used for training
        parameters: Dictionary of training parameters
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Save model to disk
        joblib.dump(model, MODEL_PATH)
        logging.info(f"Model saved to {MODEL_PATH}")
        
        # Store metadata in database
        try:
            # Only import here to avoid circular imports
            from aegis.models import db, ModelMetadata
            import json
            import flask
            
            # Check if we're in a Flask app context
            try:
                flask.current_app.name
                in_app_context = True
            except RuntimeError:
                in_app_context = False
                logging.warning("Not in Flask app context, skipping model metadata database entry")
                
            if in_app_context:
                # Deactivate all existing models
                ModelMetadata.deactivate_all()
                
                # Create new model metadata entry
                model_version = ModelMetadata.create_version()
                
                # Format parameters as JSON
                if parameters is None:
                    parameters = {}
                    
                # Add model parameters
                parameters.update({
                    "n_estimators": getattr(model, "n_estimators", 100),
                    "max_samples": getattr(model, "max_samples", "auto"),
                    "contamination": getattr(model, "contamination", 0.1),
                    "random_state": getattr(model, "random_state", 42)
                })
                
                # Create metadata record
                metadata = ModelMetadata(
                    version=model_version,
                    features=json.dumps(MODEL_FEATURES),
                    parameters=json.dumps(parameters),
                    training_samples=training_data_size or 0,
                    is_active=True
                )
                
                db.session.add(metadata)
                db.session.commit()
                logging.info(f"Model metadata saved to database with version {model_version}")
        except Exception as e:
            logging.error(f"Error saving model metadata to database: {str(e)}")
            # Continue even if metadata saving fails
        
        return True
    except Exception as e:
        logging.error(f"Error saving model: {str(e)}")
        return False