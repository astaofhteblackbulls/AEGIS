// Dashboard JavaScript functionality

// Chart instances
let sensorChart = null;
let anomalyChart = null;

// Data storage
let deviceData = {};
let anomalyData = [];

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    // Initialize charts
    initCharts();
    
    // Initial data load
    loadDashboardData();
    
    // Set up event listeners
    document.getElementById('refreshDashboard').addEventListener('click', loadDashboardData);
    
    // Set up periodic refresh (every 30 seconds)
    setInterval(loadDashboardData, 30000);
    
    // Set up WebSocket connection for real-time updates
    setupWebSocket();
});

// Function to load dashboard data
function loadDashboardData() {
    // Fetch logs data
    fetch('/logs?count=50')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                updateDashboard(data.logs);
            } else {
                showError('Failed to load dashboard data: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error fetching dashboard data:', error);
            showError('Error loading dashboard data: ' + error.message);
        });
}

// Function to update the dashboard with data
function updateDashboard(logsData) {
    // Process the data
    processLogData(logsData);
    
    // Update the counters
    updateCounters();
    
    // Update the charts
    updateCharts();
    
    // Update the recent anomalies table
    updateAnomalyTable();
    
    // Update device filter dropdown
    updateDeviceFilter();
}

// Function to process log data
function processLogData(logsData) {
    // Process data logs
    const dataLogs = logsData.data_logs || [];
    
    // Reset device data
    deviceData = {};
    
    // Process each data log
    dataLogs.forEach(log => {
        const deviceId = log.device_id;
        
        // Initialize device data if not exists
        if (!deviceData[deviceId]) {
            deviceData[deviceId] = {
                temperatures: [],
                pressures: [],
                rpms: [],
                timestamps: []
            };
        }
        
        // Add data point
        deviceData[deviceId].temperatures.push(log.temperature);
        deviceData[deviceId].pressures.push(log.pressure);
        deviceData[deviceId].rpms.push(log.rpm);
        deviceData[deviceId].timestamps.push(log.timestamp);
    });
    
    // Process alert logs
    const alertLogs = logsData.alerts || [];
    anomalyData = [];
    
    // Process each alert log
    alertLogs.forEach(logEntry => {
        // Parse the log entry to extract data
        try {
            // Example format: [2023-01-01 12:00:00] ANOMALY DETECTED: Device device-001, Score: -0.7047, Data: temperature=120.5, pressure=150.2, rpm=5500
            const match = logEntry.match(/\[(.*?)\] ANOMALY DETECTED: Device (.*?), Score: (.*?), Data: (.*)/);
            
            if (match) {
                const timestamp = match[1];
                const deviceId = match[2];
                const score = parseFloat(match[3]);
                const dataStr = match[4];
                
                // Parse the data string to extract values
                const dataValues = {};
                dataStr.split(', ').forEach(item => {
                    const [key, value] = item.split('=');
                    dataValues[key] = parseFloat(value);
                });
                
                // Add to anomaly data
                anomalyData.push({
                    timestamp,
                    deviceId,
                    score,
                    temperature: dataValues.temperature,
                    pressure: dataValues.pressure,
                    rpm: dataValues.rpm,
                    malware: score < -0.6 // Simple threshold to identify potential malware
                });
            }
        } catch (error) {
            console.error('Error parsing alert log:', error);
        }
    });
    
    // Sort anomaly data by timestamp (newest first)
    anomalyData.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
}

// Function to update the counters
function updateCounters() {
    // Update device count
    document.getElementById('deviceCount').textContent = Object.keys(deviceData).length;
    
    // Update anomaly count
    document.getElementById('anomalyCount').textContent = anomalyData.length;
    
    // Update potential malware count
    const malwareCount = anomalyData.filter(a => a.malware).length;
    document.getElementById('malwareCount').textContent = malwareCount;
}

// Function to initialize charts
function initCharts() {
    // Initialize sensor data chart
    const sensorCtx = document.getElementById('sensorChart').getContext('2d');
    sensorChart = new Chart(sensorCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Temperature (°C)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    data: [],
                    tension: 0.1
                },
                {
                    label: 'Pressure (kPa)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    data: [],
                    tension: 0.1
                },
                {
                    label: 'RPM',
                    borderColor: 'rgba(255, 206, 86, 1)',
                    backgroundColor: 'rgba(255, 206, 86, 0.2)',
                    data: [],
                    tension: 0.1,
                    hidden: true // Hide RPM by default as it might have a different scale
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Time'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Value'
                    }
                }
            }
        }
    });
    
    // Initialize anomaly distribution chart
    const anomalyCtx = document.getElementById('anomalyChart').getContext('2d');
    anomalyChart = new Chart(anomalyCtx, {
        type: 'pie',
        data: {
            labels: ['Normal', 'Anomaly', 'Potential Malware'],
            datasets: [{
                data: [0, 0, 0],
                backgroundColor: [
                    'rgba(40, 167, 69, 0.6)',
                    'rgba(255, 193, 7, 0.6)',
                    'rgba(220, 53, 69, 0.6)'
                ],
                borderColor: [
                    'rgba(40, 167, 69, 1)',
                    'rgba(255, 193, 7, 1)',
                    'rgba(220, 53, 69, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
}

// Function to update charts
function updateCharts() {
    // Update sensor data chart
    updateSensorChart();
    
    // Update anomaly distribution chart
    updateAnomalyChart();
}

// Function to update sensor data chart
function updateSensorChart() {
    // Get selected device (for now, just use the first device)
    const deviceIds = Object.keys(deviceData);
    if (deviceIds.length === 0) return;
    
    const deviceId = deviceIds[0];
    const device = deviceData[deviceId];
    
    // Get the last 20 data points
    const last20Index = Math.max(0, device.timestamps.length - 20);
    const timestamps = device.timestamps.slice(last20Index).map(formatTimestamp);
    const temperatures = device.temperatures.slice(last20Index);
    const pressures = device.pressures.slice(last20Index);
    const rpms = device.rpms.slice(last20Index);
    
    // Update chart data
    sensorChart.data.labels = timestamps;
    sensorChart.data.datasets[0].data = temperatures;
    sensorChart.data.datasets[1].data = pressures;
    sensorChart.data.datasets[2].data = rpms;
    
    // Update the chart
    sensorChart.update();
}

// Function to update anomaly distribution chart
function updateAnomalyChart() {
    // Count normal, anomaly, and potential malware
    const totalDataPoints = Object.values(deviceData).reduce((acc, device) => acc + device.temperatures.length, 0);
    const anomalyCount = anomalyData.length;
    const malwareCount = anomalyData.filter(a => a.malware).length;
    const normalCount = totalDataPoints - anomalyCount;
    
    // Update chart data
    anomalyChart.data.datasets[0].data = [normalCount, anomalyCount - malwareCount, malwareCount];
    
    // Update the chart
    anomalyChart.update();
}

// Function to update the anomaly table
function updateAnomalyTable() {
    const tableBody = document.getElementById('anomalyTable');
    
    // Clear the table body
    tableBody.innerHTML = '';
    
    // Filter based on selected device (default to 'all')
    const selectedDevice = document.getElementById('anomalyFilter').value;
    const filteredAnomalies = selectedDevice === 'all' ? 
        anomalyData : 
        anomalyData.filter(a => a.deviceId === selectedDevice);
    
    // If no anomalies, show a message
    if (filteredAnomalies.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="7" class="text-center">No anomalies detected</td>';
        tableBody.appendChild(row);
        return;
    }
    
    // Add rows for each anomaly (limit to 10)
    filteredAnomalies.slice(0, 10).forEach(anomaly => {
        const row = document.createElement('tr');
        
        // Determine status
        let status = 'anomaly';
        if (anomaly.malware) {
            status = 'malware';
        }
        
        row.innerHTML = `
            <td>${formatTimestamp(anomaly.timestamp)}</td>
            <td>${anomaly.deviceId}</td>
            <td>${anomaly.temperature.toFixed(2)}</td>
            <td>${anomaly.pressure.toFixed(2)}</td>
            <td>${anomaly.rpm.toFixed(0)}</td>
            <td>${anomaly.score.toFixed(4)}</td>
            <td>${createStatusBadge(status)}</td>
        `;
        
        tableBody.appendChild(row);
    });
}

// Function to update device filter dropdown
function updateDeviceFilter() {
    const filterSelect = document.getElementById('anomalyFilter');
    const currentValue = filterSelect.value || 'all';
    
    // Get unique device IDs from anomaly data
    const deviceIds = [...new Set(anomalyData.map(a => a.deviceId))];
    
    // Clear existing options (except 'All Devices')
    while (filterSelect.options.length > 1) {
        filterSelect.remove(1);
    }
    
    // Add device options
    deviceIds.forEach(deviceId => {
        const option = document.createElement('option');
        option.value = deviceId;
        option.textContent = deviceId;
        filterSelect.appendChild(option);
    });
    
    // Restore selected value if possible
    if (deviceIds.includes(currentValue)) {
        filterSelect.value = currentValue;
    }
    
    // Add event listener for filter change
    filterSelect.addEventListener('change', updateAnomalyTable);
}

// Function to set up WebSocket connection
function setupWebSocket() {
    // Check if WebSocket is supported
    if ('WebSocket' in window) {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        const socket = new WebSocket(wsUrl);
        
        socket.onopen = function() {
            console.log('WebSocket connection established');
        };
        
        socket.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                
                // Handle different types of messages
                if (data.type === 'anomaly_alert') {
                    handleAnomalyAlert(data);
                } else if (data.type === 'system_status') {
                    handleSystemStatus(data);
                }
            } catch (error) {
                console.error('Error processing WebSocket message:', error);
            }
        };
        
        socket.onclose = function() {
            console.log('WebSocket connection closed');
            // Try to reconnect after 5 seconds
            setTimeout(setupWebSocket, 5000);
        };
        
        socket.onerror = function(error) {
            console.error('WebSocket error:', error);
        };
    } else {
        console.log('WebSocket is not supported by this browser.');
    }
}

// Function to handle anomaly alerts
function handleAnomalyAlert(data) {
    // Show notification
    showAlert(`Anomaly detected on device ${data.device_id} with score ${data.score.toFixed(4)}`);
    
    // Refresh dashboard data
    loadDashboardData();
}

// Function to handle system status updates
function handleSystemStatus(data) {
    // Update system status indicators if needed
    console.log('System status update:', data);
}

// Function to show alerts
function showAlert(message) {
    // Create alert element
    const alertElement = document.createElement('div');
    alertElement.className = 'toast align-items-center text-white bg-danger border-0';
    alertElement.setAttribute('role', 'alert');
    alertElement.setAttribute('aria-live', 'assertive');
    alertElement.setAttribute('aria-atomic', 'true');
    
    alertElement.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    // Add to container
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(container);
    }
    
    document.getElementById('toast-container').appendChild(alertElement);
    
    // Initialize and show toast
    const toast = new bootstrap.Toast(alertElement, { autohide: true, delay: 5000 });
    toast.show();
}