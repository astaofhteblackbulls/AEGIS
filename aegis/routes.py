import os
import logging
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, current_app
from aegis.config import MODEL_FEATURES, ANOMALY_THRESHOLD, DEFAULT_LOG_ENTRIES
from aegis.ml_model import predict_anomaly, train_model_with_data, save_model, get_model

# Create Flask blueprints
api = Blueprint('api', __name__)
web = Blueprint('web', __name__)

# API Routes
@api.route('/ingest', methods=['POST'])
def ingest_data():
    """
    Endpoint to ingest sensor data.
    
    Expects JSON with:
    - timestamp
    - device_id
    - temperature
    - pressure
    - rpm
    
    Returns:
    - JSON with status and message
    """
    try:
        # Get the data
        data = request.json
        
        # Validate the data
        required_fields = ['device_id', 'timestamp', 'temperature', 'pressure', 'rpm']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "status": "error",
                    "message": f"Missing required field: {field}"
                }), 400
        
        # Process and store the data
        try:
            from aegis.models import db, Device, SensorData
            
            # Parse timestamp
            if isinstance(data['timestamp'], str):
                timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
            else:
                timestamp = datetime.fromtimestamp(data['timestamp'])
            
            # Get or create device
            device = Device.get_or_create(data['device_id'])
            device.update_last_seen()
            
            # Create sensor data entry
            sensor_data = SensorData.from_dict(data, device)
            
            # Save to database
            db.session.add(sensor_data)
            db.session.commit()
            
            return jsonify({
                "status": "success",
                "message": "Data ingested successfully"
            })
            
        except Exception as e:
            logging.error(f"Error processing data: {str(e)}")
            return jsonify({
                "status": "error",
                "message": f"Error processing data: {str(e)}"
            }), 500
    
    except Exception as e:
        logging.error(f"Error in ingest endpoint: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }), 500

@api.route('/detect', methods=['POST'])
def detect_anomaly():
    """
    Endpoint to detect anomalies in sensor data.
    
    Expects JSON with:
    - timestamp
    - device_id
    - temperature
    - pressure
    - rpm
    
    Returns:
    - JSON with anomaly detection results
    """
    try:
        # Get the data
        data = request.json
        
        # Validate the data
        required_fields = ['device_id', 'timestamp', 'temperature', 'pressure', 'rpm']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "status": "error",
                    "message": f"Missing required field: {field}"
                }), 400
        
        # Check if model is available
        model = get_model()
        if model is None:
            return jsonify({
                "status": "error",
                "message": "No trained model available for anomaly detection"
            }), 400
        
        # Process and detect anomalies
        try:
            from aegis.models import db, Device, SensorData, Anomaly
            from aegis.utils import check_for_malware
            
            # Parse timestamp
            if isinstance(data['timestamp'], str):
                timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
            else:
                timestamp = datetime.fromtimestamp(data['timestamp'])
            
            # Get or create device
            device = Device.get_or_create(data['device_id'])
            device.update_last_seen()
            
            # Create sensor data entry (store the data regardless of anomaly)
            sensor_data = SensorData.from_dict(data, device)
            db.session.add(sensor_data)
            
            # Detect anomaly
            is_anomaly, anomaly_score, message = predict_anomaly(data)
            
            # Convert NumPy float to Python float to avoid serialization issues
            if hasattr(anomaly_score, 'item'):
                anomaly_score = anomaly_score.item()
            
            # Check for potential malware if it's an anomaly
            is_potential_malware = False
            anomaly_count = 0
            
            if is_anomaly:
                # Check for malware patterns
                is_potential_malware, anomaly_count = check_for_malware(data['device_id'])
                
                # Store anomaly in database
                anomaly = Anomaly.from_dict(
                    data=data,
                    device=device,
                    anomaly_score=anomaly_score,
                    is_malware=is_potential_malware
                )
                db.session.add(anomaly)
                
                # Update device status if malware detected
                if is_potential_malware:
                    device.status = 'compromised'
            
            # Commit all database changes
            db.session.commit()
            
            # Prepare response
            result = {
                "status": "success",
                "device_id": data['device_id'],
                "timestamp": timestamp.isoformat(),
                "is_anomaly": bool(is_anomaly),
                "anomaly_score": float(anomaly_score),
                "threshold": float(ANOMALY_THRESHOLD),
                "message": message
            }
            
            # Add malware info if it's an anomaly
            if is_anomaly:
                result["is_potential_malware"] = bool(is_potential_malware)
                result["anomaly_count"] = int(anomaly_count)
                
                if is_potential_malware:
                    result["warning"] = "CRITICAL: Multiple anomalies detected in short timeframe. Possible malware activity!"
            
            return jsonify(result)
            
        except Exception as e:
            logging.error(f"Error processing anomaly detection: {str(e)}")
            return jsonify({
                "status": "error",
                "message": f"Error during anomaly detection: {str(e)}"
            }), 500
    
    except Exception as e:
        logging.error(f"Error in detect_anomaly endpoint: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }), 500

@api.route('/logs', methods=['GET'])
def get_logs():
    """
    Endpoint to retrieve recent logs.
    
    Query parameters:
    - count: Number of log entries to retrieve (default: DEFAULT_LOG_ENTRIES)
    - device_id: Optional device ID to filter logs
    
    Returns:
    - JSON with recent data logs and alerts
    """
    try:
        from aegis.models import SensorData, Anomaly, Device
        
        # Get query parameters
        count = request.args.get('count', DEFAULT_LOG_ENTRIES, type=int)
        device_id = request.args.get('device_id', None)
        
        # Query database
        if device_id:
            # Try to get the device
            device = Device.query.filter_by(device_id=device_id).first()
            if not device:
                return jsonify({
                    "status": "error",
                    "message": f"Device with ID {device_id} not found"
                }), 404
            
            # Get logs for specific device
            sensor_data = SensorData.query.filter_by(device_id=device.id).order_by(SensorData.timestamp.desc()).limit(count).all()
            anomalies = Anomaly.query.filter_by(device_id=device.id).order_by(Anomaly.timestamp.desc()).limit(count).all()
        else:
            # Get logs for all devices
            sensor_data = SensorData.query.order_by(SensorData.timestamp.desc()).limit(count).all()
            anomalies = Anomaly.query.order_by(Anomaly.timestamp.desc()).limit(count).all()
        
        # Convert to dictionaries
        data_logs = []
        for log in sensor_data:
            device = Device.query.get(log.device_id)
            data_logs.append({
                "timestamp": log.timestamp.isoformat(),
                "received_at": log.received_at.isoformat(),
                "device_id": device.device_id if device else None,
                "temperature": log.temperature,
                "pressure": log.pressure,
                "rpm": log.rpm
            })
        
        alerts = []
        for alert in anomalies:
            device = Device.query.get(alert.device_id)
            alerts.append({
                "timestamp": alert.timestamp.isoformat(),
                "detected_at": alert.detected_at.isoformat(),
                "device_id": device.device_id if device else None,
                "temperature": alert.temperature,
                "pressure": alert.pressure,
                "rpm": alert.rpm,
                "anomaly_score": alert.anomaly_score,
                "is_malware": alert.is_malware,
                "description": alert.description
            })
        
        return jsonify({
            "status": "success",
            "data_logs": data_logs,
            "alerts": alerts
        })
        
    except Exception as e:
        logging.error(f"Error in get_logs endpoint: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }), 500

@api.route('/train', methods=['POST'])
def train_model():
    """
    Endpoint to train a new model with provided data.
    
    Expects JSON with:
    - data: List of data points with MODEL_FEATURES columns
    
    Returns:
    - JSON with training results
    """
    try:
        # Get the data
        request_data = request.json
        
        if not request_data or 'data' not in request_data:
            return jsonify({
                "status": "error",
                "message": "Missing required field: data"
            }), 400
        
        # Convert to pandas DataFrame
        import pandas as pd
        import numpy as np
        
        data = pd.DataFrame(request_data['data'])
        
        # Check for required features
        missing_features = [f for f in MODEL_FEATURES if f not in data.columns]
        if missing_features:
            return jsonify({
                "status": "error",
                "message": f"Missing required features: {', '.join(missing_features)}"
            }), 400
        
        # Train new model
        # Already imported from aegis.ml_model
        
        model = train_model_with_data(data)
        success = save_model(model, training_data_size=len(data))
        
        if not success:
            return jsonify({
                "status": "error",
                "message": "Failed to save the trained model"
            }), 500
        
        return jsonify({
            "status": "success",
            "message": "Model trained and saved successfully",
            "details": {
                "n_samples": len(data),
                "features": MODEL_FEATURES
            }
        })
        
    except Exception as e:
        logging.error(f"Error in train_model endpoint: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }), 500

# API endpoint for model information
@api.route('/model', methods=['GET'])
def get_model_info():
    """
    Endpoint to get information about the currently active model.
    
    Returns:
    - JSON with model details
    """
    try:
        from aegis.models import ModelMetadata
        
        # Get the active model metadata
        model_metadata = ModelMetadata.get_active_model()
        
        if not model_metadata:
            return jsonify({
                "status": "warning",
                "message": "No active model found in database",
                "model": {
                    "version": "default",
                    "created_at": None,
                    "features": MODEL_FEATURES,
                    "training_samples": 0
                }
            })
        
        # Convert to dictionary
        import json
        model_data = {
            "version": model_metadata.version,
            "created_at": model_metadata.created_at.isoformat(),
            "features": json.loads(model_metadata.features) if model_metadata.features else MODEL_FEATURES,
            "parameters": json.loads(model_metadata.parameters) if model_metadata.parameters else {},
            "training_samples": model_metadata.training_samples,
            "performance_metrics": json.loads(model_metadata.performance_metrics) if model_metadata.performance_metrics else {}
        }
        
        return jsonify({
            "status": "success",
            "model": model_data
        })
        
    except Exception as e:
        logging.error(f"Error in get_model_info endpoint: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }), 500

# API endpoints for device management
@api.route('/devices', methods=['GET'])
def get_devices():
    """
    Endpoint to get all devices and their statuses.
    
    Returns:
    - JSON with devices and their details
    """
    try:
        from aegis.models import Device
        
        # Get all devices
        devices = Device.query.all()
        
        # Convert to list of dictionaries
        device_list = []
        for device in devices:
            device_list.append({
                "id": device.id,
                "device_id": device.device_id,
                "name": device.name,
                "description": device.description,
                "status": device.status,
                "last_seen": device.last_seen.isoformat() if device.last_seen else None,
                "created_at": device.created_at.isoformat()
            })
        
        return jsonify({
            "status": "success",
            "devices": device_list
        })
        
    except Exception as e:
        logging.error(f"Error in get_devices endpoint: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }), 500

@api.route('/devices/<device_id>', methods=['GET'])
def get_device(device_id):
    """
    Endpoint to get a specific device by its ID.
    
    Returns:
    - JSON with device details
    """
    try:
        from aegis.models import Device
        
        # Get the device
        device = Device.query.filter_by(device_id=device_id).first()
        
        if not device:
            return jsonify({
                "status": "error",
                "message": f"Device with ID {device_id} not found"
            }), 404
        
        # Convert to dictionary
        device_data = {
            "id": device.id,
            "device_id": device.device_id,
            "name": device.name,
            "description": device.description,
            "status": device.status,
            "last_seen": device.last_seen.isoformat() if device.last_seen else None,
            "created_at": device.created_at.isoformat()
        }
        
        return jsonify({
            "status": "success",
            "device": device_data
        })
        
    except Exception as e:
        logging.error(f"Error in get_device endpoint: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }), 500

@api.route('/devices/<device_id>', methods=['PUT'])
def update_device(device_id):
    """
    Endpoint to update a device's information.
    
    Expects JSON with device fields to update:
    - name (optional)
    - description (optional)
    - status (optional)
    
    Returns:
    - JSON with updated device details
    """
    try:
        from aegis.models import db, Device
        
        # Get the device
        device = Device.query.filter_by(device_id=device_id).first()
        
        if not device:
            return jsonify({
                "status": "error",
                "message": f"Device with ID {device_id} not found"
            }), 404
        
        # Get update data
        data = request.json
        
        # Update fields if provided
        if data.get('name') is not None:
            device.name = data['name']
            
        if data.get('description') is not None:
            device.description = data['description']
            
        if data.get('status') is not None:
            # Validate status
            valid_statuses = ['active', 'inactive', 'compromised']
            if data['status'] not in valid_statuses:
                return jsonify({
                    "status": "error",
                    "message": f"Invalid status: {data['status']}. Must be one of: {', '.join(valid_statuses)}"
                }), 400
                
            device.status = data['status']
        
        # Save changes
        db.session.commit()
        
        # Return updated device data
        device_data = {
            "id": device.id,
            "device_id": device.device_id,
            "name": device.name,
            "description": device.description,
            "status": device.status,
            "last_seen": device.last_seen.isoformat() if device.last_seen else None,
            "created_at": device.created_at.isoformat()
        }
        
        return jsonify({
            "status": "success",
            "message": "Device updated successfully",
            "device": device_data
        })
        
    except Exception as e:
        logging.error(f"Error in update_device endpoint: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }), 500

# Web Routes
@web.route('/')
def index():
    """Render the dashboard page"""
    return render_template('dashboard.html')

@web.route('/logs')
def logs_page():
    """Render the logs page"""
    return render_template('logs.html')

@web.route('/training')
def training_page():
    """Render the training page"""
    return render_template('training.html')

# Add a devices page
@web.route('/devices')
def devices_page():
    """Render the devices page"""
    from aegis.models import Device
    devices = Device.query.all()
    return render_template('devices.html', devices=devices)

# Training API endpoints for frontend
@api.route('/train-synthetic', methods=['POST'])
def train_synthetic():
    """Train model with synthetic data"""
    try:
        import time
        from aegis.train_model import generate_synthetic_data, create_model

        # Get parameters
        params = request.json or {}
        sample_count = int(params.get('sample_count', 5000))
        contamination = float(params.get('contamination', 0.1))
        
        # Validate parameters
        if sample_count < 1000 or sample_count > 50000:
            return jsonify({
                "status": "error",
                "message": "Sample count must be between 1,000 and 50,000"
            }), 400
            
        if contamination < 0.01 or contamination > 0.5:
            return jsonify({
                "status": "error",
                "message": "Contamination rate must be between 0.01 and 0.5"
            }), 400
        
        # Generate synthetic data
        start_time = time.time()
        training_data = generate_synthetic_data(n_samples=sample_count, contamination=contamination)
        
        # Create and train model
        from aegis.config import MODEL_FEATURES
        model = create_model()
        model.fit(training_data[MODEL_FEATURES].values)
        
        # Save the model with parameters
        parameters = {
            "n_samples": sample_count,
            "contamination": contamination
        }
        success = save_model(model, training_data_size=len(training_data), parameters=parameters)
        training_time = time.time() - start_time
        
        if not success:
            return jsonify({
                "status": "error",
                "message": "Failed to save the trained model"
            }), 500
        
        return jsonify({
            "status": "success",
            "message": "Model trained and saved successfully with synthetic data",
            "details": {
                "n_samples": len(training_data),
                "contamination": contamination,
                "features": MODEL_FEATURES,
                "training_time": training_time
            }
        })
        
    except Exception as e:
        logging.error(f"Error in train_synthetic endpoint: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }), 500

@api.route('/train-upload', methods=['POST'])
def train_upload():
    """Train model with uploaded data"""
    try:
        import time
        import pandas as pd
        from aegis.config import MODEL_FEATURES
        
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({
                "status": "error",
                "message": "No file uploaded"
            }), 400
            
        file = request.files['file']
        
        # Check if filename is empty
        if file.filename == '':
            return jsonify({
                "status": "error",
                "message": "No file selected"
            }), 400
            
        # Check if file is a CSV
        if not file.filename.endswith('.csv'):
            return jsonify({
                "status": "error",
                "message": "Uploaded file must be a CSV file"
            }), 400
        
        # Read the CSV file
        try:
            data = pd.read_csv(file)
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Error reading CSV file: {str(e)}"
            }), 400
        
        # Check for required features
        missing_features = [f for f in MODEL_FEATURES if f not in data.columns]
        if missing_features:
            return jsonify({
                "status": "error",
                "message": f"Missing required features in CSV: {', '.join(missing_features)}"
            }), 400
        
        # Create and train model
        start_time = time.time()
        model = train_model_with_data(data)
        
        # Save the model with metadata
        parameters = {
            "source": "uploaded_file",
            "filename": file.filename
        }
        success = save_model(model, training_data_size=len(data), parameters=parameters)
        training_time = time.time() - start_time
        
        if not success:
            return jsonify({
                "status": "error",
                "message": "Failed to save the trained model"
            }), 500
        
        return jsonify({
            "status": "success",
            "message": "Model trained and saved successfully with uploaded data",
            "details": {
                "n_samples": len(data),
                "features": MODEL_FEATURES,
                "training_time": training_time
            }
        })
        
    except Exception as e:
        logging.error(f"Error in train_upload endpoint: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }), 500

@api.route('/train-custom', methods=['POST'])
def train_custom():
    """Train model with custom parameters"""
    try:
        import time
        import numpy as np
        import pandas as pd
        from aegis.config import MODEL_FEATURES
        
        # Get parameters
        params = request.json or {}
        sample_count = int(params.get('sample_count', 5000))
        contamination = float(params.get('contamination', 0.1))
        normal_params = params.get('normal_params', {})
        
        # Validate parameters
        if sample_count < 1000 or sample_count > 50000:
            return jsonify({
                "status": "error",
                "message": "Sample count must be between 1,000 and 50,000"
            }), 400
            
        if contamination < 0.01 or contamination > 0.5:
            return jsonify({
                "status": "error",
                "message": "Contamination rate must be between 0.01 and 0.5"
            }), 400
        
        # Calculate number of normal and anomalous samples
        n_normal = int(sample_count * (1 - contamination))
        n_anomalous = sample_count - n_normal
        
        # Generate data with custom parameters
        # For temperature
        temp_mean = normal_params.get('temperature', {}).get('mean', 75)
        temp_var = normal_params.get('temperature', {}).get('var', 5)
        normal_temp = np.random.normal(temp_mean, temp_var, n_normal)
        anomalous_temp = np.concatenate([
            np.random.normal(temp_mean * 0.5, temp_var, n_anomalous // 3),
            np.random.normal(temp_mean * 1.5, temp_var * 2, n_anomalous // 3),
            np.random.normal(temp_mean, temp_var * 4, n_anomalous // 3)
        ])
        
        # For pressure
        pressure_mean = normal_params.get('pressure', {}).get('mean', 100)
        pressure_var = normal_params.get('pressure', {}).get('var', 10)
        normal_pressure = np.random.normal(pressure_mean, pressure_var, n_normal)
        anomalous_pressure = np.concatenate([
            np.random.normal(pressure_mean * 0.5, pressure_var, n_anomalous // 3),
            np.random.normal(pressure_mean * 1.5, pressure_var * 1.5, n_anomalous // 3),
            np.random.normal(pressure_mean, pressure_var * 3, n_anomalous // 3)
        ])
        
        # For RPM
        rpm_mean = normal_params.get('rpm', {}).get('mean', 3000)
        rpm_var = normal_params.get('rpm', {}).get('var', 200)
        normal_rpm = np.random.normal(rpm_mean, rpm_var, n_normal)
        anomalous_rpm = np.concatenate([
            np.random.normal(rpm_mean * 0.3, rpm_var, n_anomalous // 3),
            np.random.normal(rpm_mean * 1.7, rpm_var * 1.5, n_anomalous // 3),
            np.random.normal(rpm_mean, rpm_var * 4, n_anomalous // 3)
        ])
        
        # Create DataFrames
        normal_data = pd.DataFrame({
            "temperature": normal_temp,
            "pressure": normal_pressure,
            "rpm": normal_rpm
        })
        
        anomalous_data = pd.DataFrame({
            "temperature": anomalous_temp,
            "pressure": anomalous_pressure,
            "rpm": anomalous_rpm
        })
        
        # Combine and shuffle
        all_data = pd.concat([normal_data, anomalous_data])
        all_data = all_data.sample(frac=1).reset_index(drop=True)
        
        # Create and train model
        start_time = time.time()
        model = train_model_with_data(all_data)
        
        # Save the model with parameters
        parameters = {
            "n_samples": sample_count,
            "contamination": contamination,
            "normal_params": normal_params,
            "method": "custom"
        }
        success = save_model(model, training_data_size=len(all_data), parameters=parameters)
        training_time = time.time() - start_time
        
        if not success:
            return jsonify({
                "status": "error",
                "message": "Failed to save the trained model"
            }), 500
        
        return jsonify({
            "status": "success",
            "message": "Model trained and saved successfully with custom parameters",
            "details": {
                "n_samples": len(all_data),
                "normal_samples": n_normal,
                "anomalous_samples": n_anomalous,
                "contamination": contamination,
                "features": MODEL_FEATURES,
                "training_time": training_time
            }
        })
        
    except Exception as e:
        logging.error(f"Error in train_custom endpoint: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }), 500

def register_routes(app):
    """Register all API routes with the Flask app."""
    app.register_blueprint(api, url_prefix='/api')
    app.register_blueprint(web)