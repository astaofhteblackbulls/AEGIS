import os
import logging
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from aegis.models import db

# Create SocketIO instance
socketio = SocketIO()

def create_app():
    """Factory function to create and configure Flask application."""
    app = Flask(__name__)
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
    
    # Configure database
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    
    # Enable CORS for frontend integration
    CORS(app)
    
    # Configure logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Import and register routes
    from aegis.routes import register_routes
    register_routes(app)
    
    # Ensure log directories exist
    from aegis.config import DATA_LOG_PATH, ALERTS_LOG_PATH, MODEL_DIR
    os.makedirs(os.path.dirname(DATA_LOG_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(ALERTS_LOG_PATH), exist_ok=True)
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    # Initialize database
    db.init_app(app)
    
    # Load pre-trained model during app initialization
    from aegis.ml_model import load_model
    load_model()
    
    # Initialize SocketIO
    socketio.init_app(app, cors_allowed_origins="*")
    
    return app

# Function to emit an anomaly alert via WebSocket
def emit_anomaly_alert(data, anomaly_score, is_potential_malware=False, anomaly_count=0):
    """
    Emit an anomaly alert to all connected clients.
    
    Args:
        data: Dictionary containing the anomalous data
        anomaly_score: The anomaly score from the model
        is_potential_malware: Whether this might be malware
        anomaly_count: Number of anomalies for this device
    """
    alert_data = {
        "type": "anomaly_alert",
        "timestamp": data.get("timestamp"),
        "device_id": data.get("device_id", "unknown"),
        "temperature": data.get("temperature"),
        "pressure": data.get("pressure"),
        "rpm": data.get("rpm"),
        "score": anomaly_score,
        "is_potential_malware": is_potential_malware,
        "anomaly_count": anomaly_count
    }
    
    socketio.emit('aegis_alert', alert_data)
