"""
Database models for AEGIS.
"""
import os
import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Device(db.Model):
    """Model for industrial IoT devices being monitored."""
    __tablename__ = 'devices'

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    last_seen = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='active')  # active, inactive, compromised
    
    # Relationships
    sensor_data = db.relationship('SensorData', backref='device', lazy=True, cascade="all, delete-orphan")
    anomalies = db.relationship('Anomaly', backref='device', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Device {self.device_id}>'
    
    @classmethod
    def get_or_create(cls, device_id):
        """Get an existing device or create a new one if it doesn't exist."""
        device = cls.query.filter_by(device_id=device_id).first()
        if not device:
            device = cls(device_id=device_id)
            db.session.add(device)
            db.session.commit()
        return device
    
    def update_last_seen(self):
        """Update the last seen timestamp for the device."""
        self.last_seen = datetime.datetime.utcnow()
        db.session.commit()

class SensorData(db.Model):
    """Model for storing sensor data from devices."""
    __tablename__ = 'sensor_data'

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    received_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    temperature = db.Column(db.Float, nullable=False)
    pressure = db.Column(db.Float, nullable=False)
    rpm = db.Column(db.Float, nullable=False)
    
    def __repr__(self):
        return f'<SensorData {self.device_id} at {self.timestamp}>'
    
    @classmethod
    def from_dict(cls, data, device):
        """Create a SensorData instance from a dictionary."""
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
        return cls(
            device_id=device.id,
            timestamp=timestamp,
            temperature=data.get('temperature'),
            pressure=data.get('pressure'),
            rpm=data.get('rpm')
        )

class Anomaly(db.Model):
    """Model for storing detected anomalies."""
    __tablename__ = 'anomalies'

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    detected_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    anomaly_score = db.Column(db.Float, nullable=False)
    is_malware = db.Column(db.Boolean, default=False)
    temperature = db.Column(db.Float, nullable=False)
    pressure = db.Column(db.Float, nullable=False)
    rpm = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<Anomaly {self.device_id} at {self.timestamp} (score: {self.anomaly_score})>'
    
    @classmethod
    def from_dict(cls, data, device, anomaly_score, is_malware=False):
        """Create an Anomaly instance from a dictionary."""
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        # Convert NumPy types to Python native types
        if hasattr(anomaly_score, 'item'):
            anomaly_score = float(anomaly_score.item())
        else:
            anomaly_score = float(anomaly_score)
            
        temperature = float(data.get('temperature', 0))
        pressure = float(data.get('pressure', 0))
        rpm = float(data.get('rpm', 0))
            
        return cls(
            device_id=device.id,
            timestamp=timestamp,
            anomaly_score=anomaly_score,
            is_malware=bool(is_malware),
            temperature=temperature,
            pressure=pressure,
            rpm=rpm
        )

class ModelMetadata(db.Model):
    """Model for storing information about trained machine learning models."""
    __tablename__ = 'model_metadata'

    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    features = db.Column(db.Text, nullable=False)  # JSON string of features
    parameters = db.Column(db.Text, nullable=True)  # JSON string of parameters
    training_samples = db.Column(db.Integer, nullable=False)
    performance_metrics = db.Column(db.Text, nullable=True)  # JSON string of metrics
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<ModelMetadata {self.version} created at {self.created_at}>'
    
    @classmethod
    def create_version(cls):
        """Generate a new model version number."""
        timestamp = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return f"model-{timestamp}"
    
    @classmethod
    def get_active_model(cls):
        """Get the currently active model metadata."""
        return cls.query.filter_by(is_active=True).order_by(cls.created_at.desc()).first()
    
    @classmethod
    def deactivate_all(cls):
        """Deactivate all existing models."""
        models = cls.query.all()
        for model in models:
            model.is_active = False
        db.session.commit()