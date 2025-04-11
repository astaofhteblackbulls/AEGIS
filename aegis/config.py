import os

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
MODEL_DIR = os.path.join(BASE_DIR, "model")

# Log file paths
DATA_LOG_PATH = os.path.join(LOGS_DIR, "data_log.csv")
ALERTS_LOG_PATH = os.path.join(LOGS_DIR, "alerts.log")

# Model file path
MODEL_PATH = os.path.join(MODEL_DIR, "model.pkl")

# Anomaly detection parameters
ANOMALY_THRESHOLD = -0.2  # Score below this is considered an anomaly

# Malware detection parameters
MALWARE_WINDOW_SECONDS = 300  # 5 minutes
MALWARE_THRESHOLD_COUNT = 3  # Number of anomalies within window to trigger malware alert

# Features used for anomaly detection
MODEL_FEATURES = ["temperature", "pressure", "rpm"]

# Required fields for data ingestion
REQUIRED_FIELDS = ["timestamp", "device_id", "temperature", "pressure", "rpm"]

# Number of recent log entries to return
DEFAULT_LOG_ENTRIES = 100
