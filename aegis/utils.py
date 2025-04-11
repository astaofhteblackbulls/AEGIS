import os
import time
import logging
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from aegis.config import (
    DATA_LOG_PATH, 
    ALERTS_LOG_PATH, 
    REQUIRED_FIELDS,
    MALWARE_WINDOW_SECONDS,
    MALWARE_THRESHOLD_COUNT,
    DEFAULT_LOG_ENTRIES
)

def validate_data(data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate that the incoming data contains all required fields.
    
    Args:
        data: Dictionary containing the incoming data
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    missing_fields = [field for field in REQUIRED_FIELDS if field not in data]
    
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    
    # Check if numeric fields are actually numeric
    numeric_fields = ["temperature", "pressure", "rpm"]
    for field in numeric_fields:
        if not isinstance(data.get(field), (int, float)):
            return False, f"Field '{field}' must be numeric"
    
    return True, ""

def preprocess_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Preprocess the data for storage and analysis.
    
    Args:
        data: Dictionary containing the incoming data
        
    Returns:
        Preprocessed data dictionary
    """
    processed = data.copy()
    
    # Ensure timestamp is in the right format, convert if necessary
    if isinstance(processed.get("timestamp"), str):
        try:
            # Convert string timestamp to numeric timestamp if needed
            processed["timestamp"] = int(datetime.strptime(
                processed["timestamp"], 
                "%Y-%m-%dT%H:%M:%S"
            ).timestamp())
        except ValueError:
            # If parsing fails, assume it's already a numeric timestamp
            pass
    
    # Add received_at field for tracking
    processed["received_at"] = int(time.time())
    
    return processed

def log_data_point(data: Dict[str, Any]) -> bool:
    """
    Log a data point to the CSV log file.
    
    Args:
        data: Dictionary containing the data point to log
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Convert data to DataFrame row
        df = pd.DataFrame([data])
        
        # Check if log file exists
        file_exists = os.path.isfile(DATA_LOG_PATH)
        
        # Append to the CSV file
        df.to_csv(
            DATA_LOG_PATH, 
            mode='a', 
            header=not file_exists, 
            index=False
        )
        
        return True
    except Exception as e:
        logging.error(f"Error logging data point: {str(e)}")
        return False

def log_anomaly(data: Dict[str, Any], anomaly_score: float) -> bool:
    """
    Log an anomaly to the alerts log file.
    
    Args:
        data: Dictionary containing the anomalous data
        anomaly_score: The anomaly score from the model
        
    Returns:
        True if successful, False otherwise
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        device_id = data.get("device_id", "unknown")
        log_message = (
            f"[{timestamp}] ANOMALY DETECTED: Device {device_id}, "
            f"Score: {anomaly_score:.4f}, "
            f"Data: {', '.join([f'{k}={v}' for k, v in data.items() if k in ['temperature', 'pressure', 'rpm']])}"
        )
        
        with open(ALERTS_LOG_PATH, "a") as f:
            f.write(log_message + "\n")
            
        return True
    except Exception as e:
        logging.error(f"Error logging anomaly: {str(e)}")
        return False

def check_for_malware(device_id: str) -> Tuple[bool, int]:
    """
    Check if a device has multiple anomalies in a short time window,
    which might indicate malware interference.
    
    Args:
        device_id: The ID of the device to check
        
    Returns:
        Tuple of (is_potential_malware, anomaly_count)
    """
    try:
        # Read the alerts log to find recent anomalies
        if not os.path.exists(ALERTS_LOG_PATH):
            return False, 0
            
        with open(ALERTS_LOG_PATH, "r") as f:
            alert_lines = f.readlines()
        
        # Calculate time window (current time minus window size)
        current_time = datetime.now()
        window_start = current_time - timedelta(seconds=MALWARE_WINDOW_SECONDS)
        
        # Count anomalies for this device within the time window
        anomaly_count = 0
        
        for line in alert_lines:
            try:
                # Parse timestamp from log line
                timestamp_str = line.split('[')[1].split(']')[0]
                log_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                
                # Check if log is within time window
                if log_time >= window_start:
                    # Check if log is for this device
                    if f"Device {device_id}" in line:
                        anomaly_count += 1
            except Exception:
                # Skip lines that don't match the expected format
                continue
        
        # Determine if this could be malware
        is_potential_malware = anomaly_count >= MALWARE_THRESHOLD_COUNT
        
        return is_potential_malware, anomaly_count
    
    except Exception as e:
        logging.error(f"Error checking for malware: {str(e)}")
        return False, 0

def get_recent_logs(n: int = DEFAULT_LOG_ENTRIES) -> Dict[str, Any]:
    """
    Retrieve the most recent log entries.
    
    Args:
        n: Number of recent entries to retrieve
        
    Returns:
        Dictionary with data logs and alerts
    """
    result = {
        "data_logs": [],
        "alerts": []
    }
    
    # Get data logs
    try:
        if os.path.exists(DATA_LOG_PATH):
            df = pd.read_csv(DATA_LOG_PATH)
            if not df.empty:
                result["data_logs"] = df.tail(n).to_dict(orient='records')
    except Exception as e:
        logging.error(f"Error retrieving data logs: {str(e)}")
    
    # Get alert logs
    try:
        if os.path.exists(ALERTS_LOG_PATH):
            with open(ALERTS_LOG_PATH, "r") as f:
                alert_lines = f.readlines()
            result["alerts"] = alert_lines[-n:]
    except Exception as e:
        logging.error(f"Error retrieving alert logs: {str(e)}")
    
    return result
