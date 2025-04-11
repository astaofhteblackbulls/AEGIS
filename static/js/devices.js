// AEGIS Devices Management JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Fetch all devices initially
    refreshDevicesList();
    
    // Set up refresh button
    document.getElementById('refreshDevices').addEventListener('click', refreshDevicesList);
    
    // Set up event listeners for dynamic elements
    setupEventDelegation();
    
    // Edit device form submission
    document.getElementById('saveDeviceButton').addEventListener('click', saveDeviceChanges);
});

// Refresh the devices list
function refreshDevicesList() {
    fetch('/api/devices')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updateDevicesTable(data.devices);
                updateDeviceCounters(data.devices);
            } else {
                showAlert('Error fetching devices: ' + data.message, 'danger');
            }
        })
        .catch(error => {
            console.error('Error fetching devices:', error);
            showAlert('Failed to connect to the server. Please try again later.', 'danger');
        });
}

// Update the devices table with new data
function updateDevicesTable(devices) {
    const devicesTable = document.getElementById('devicesTable');
    
    if (devices.length === 0) {
        devicesTable.innerHTML = `
            <tr>
                <td colspan="6" class="text-center">No devices found</td>
            </tr>
        `;
        return;
    }
    
    let tableHTML = '';
    
    devices.forEach(device => {
        // Format the last seen date
        const lastSeen = device.last_seen ? new Date(device.last_seen).toLocaleString() : 'Never';
        
        // Determine the status badge class
        let statusBadgeClass = 'bg-warning';
        if (device.status === 'active') statusBadgeClass = 'bg-success';
        else if (device.status === 'inactive') statusBadgeClass = 'bg-secondary';
        else if (device.status === 'compromised') statusBadgeClass = 'bg-danger';
        
        tableHTML += `
            <tr>
                <td>${device.device_id}</td>
                <td>${device.name || 'Unnamed Device'}</td>
                <td>${device.description || 'No description'}</td>
                <td><span class="badge ${statusBadgeClass}">${device.status}</span></td>
                <td>${lastSeen}</td>
                <td>
                    <button class="btn btn-sm btn-outline-info edit-device" data-device-id="${device.device_id}">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-primary view-device-data" data-device-id="${device.device_id}">
                        <i class="bi bi-graph-up"></i>
                    </button>
                </td>
            </tr>
        `;
    });
    
    devicesTable.innerHTML = tableHTML;
}

// Update device counters
function updateDeviceCounters(devices) {
    document.getElementById('totalDeviceCount').textContent = devices.length;
    
    // Count devices by status
    const activeCount = devices.filter(d => d.status === 'active').length;
    const inactiveCount = devices.filter(d => d.status === 'inactive').length;
    const compromisedCount = devices.filter(d => d.status === 'compromised').length;
    
    document.getElementById('activeDeviceCount').textContent = activeCount;
    document.getElementById('inactiveDeviceCount').textContent = inactiveCount;
    document.getElementById('compromisedDeviceCount').textContent = compromisedCount;
}

// Set up event delegation for dynamically created elements
function setupEventDelegation() {
    document.addEventListener('click', function(event) {
        // Handle edit device button clicks
        if (event.target.closest('.edit-device')) {
            const button = event.target.closest('.edit-device');
            const deviceId = button.getAttribute('data-device-id');
            openEditDeviceModal(deviceId);
        }
        
        // Handle view device data button clicks
        if (event.target.closest('.view-device-data')) {
            const button = event.target.closest('.view-device-data');
            const deviceId = button.getAttribute('data-device-id');
            openViewDeviceDataModal(deviceId);
        }
    });
}

// Open the edit device modal
function openEditDeviceModal(deviceId) {
    fetch(`/api/devices/${deviceId}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const device = data.device;
                
                // Populate the form
                document.getElementById('editDeviceId').value = device.device_id;
                document.getElementById('editDeviceName').value = device.name || '';
                document.getElementById('editDeviceDescription').value = device.description || '';
                document.getElementById('editDeviceStatus').value = device.status;
                
                // Update modal title
                document.getElementById('editDeviceModalLabel').textContent = `Edit Device: ${device.device_id}`;
                
                // Show the modal
                const modal = new bootstrap.Modal(document.getElementById('editDeviceModal'));
                modal.show();
            } else {
                showAlert(`Error fetching device details: ${data.message}`, 'danger');
            }
        })
        .catch(error => {
            console.error('Error fetching device details:', error);
            showAlert('Failed to load device details', 'danger');
        });
}

// Save device changes
function saveDeviceChanges() {
    const deviceId = document.getElementById('editDeviceId').value;
    const name = document.getElementById('editDeviceName').value;
    const description = document.getElementById('editDeviceDescription').value;
    const status = document.getElementById('editDeviceStatus').value;
    
    const data = {
        name: name,
        description: description,
        status: status
    };
    
    fetch(`/api/devices/${deviceId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.status === 'success') {
            // Close the modal
            bootstrap.Modal.getInstance(document.getElementById('editDeviceModal')).hide();
            
            // Refresh the devices list
            refreshDevicesList();
            
            // Show success message
            showAlert('Device updated successfully', 'success');
        } else {
            showAlert(`Error updating device: ${result.message}`, 'danger');
        }
    })
    .catch(error => {
        console.error('Error updating device:', error);
        showAlert('Failed to update device', 'danger');
    });
}

// Open the view device data modal
function openViewDeviceDataModal(deviceId) {
    // Update modal title
    document.getElementById('viewDeviceDataModalLabel').textContent = `Device Data: ${deviceId}`;
    
    // Show the modal
    const modal = new bootstrap.Modal(document.getElementById('viewDeviceDataModal'));
    modal.show();
    
    // Fetch logs for the device
    fetchDeviceData(deviceId);
}

// Fetch device data for display
function fetchDeviceData(deviceId) {
    fetch(`/api/logs?device_id=${deviceId}&count=20`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updateDeviceDataTable(data.data_logs, data.alerts);
                createDeviceDataChart(data.data_logs, data.alerts);
            } else {
                document.getElementById('deviceDataTable').innerHTML = `
                    <tr>
                        <td colspan="5" class="text-center">Error loading data: ${data.message}</td>
                    </tr>
                `;
            }
        })
        .catch(error => {
            console.error('Error fetching device data:', error);
            document.getElementById('deviceDataTable').innerHTML = `
                <tr>
                    <td colspan="5" class="text-center">Failed to load data. Please try again.</td>
                </tr>
            `;
        });
}

// Update device data table
function updateDeviceDataTable(dataLogs, alerts) {
    const table = document.getElementById('deviceDataTable');
    
    // Combine data logs and alerts, sort by timestamp (newest first)
    const combinedData = [...dataLogs, ...alerts].sort((a, b) => {
        return new Date(b.timestamp) - new Date(a.timestamp);
    });
    
    if (combinedData.length === 0) {
        table.innerHTML = `
            <tr>
                <td colspan="5" class="text-center">No data available</td>
            </tr>
        `;
        return;
    }
    
    let tableHTML = '';
    
    combinedData.forEach(item => {
        const timestamp = new Date(item.timestamp).toLocaleString();
        const isAnomaly = 'anomaly_score' in item;
        const anomalyBadge = isAnomaly 
            ? `<span class="badge bg-warning">Anomaly (${item.anomaly_score.toFixed(3)})</span>` 
            : '<span class="badge bg-success">Normal</span>';
        
        tableHTML += `
            <tr class="${isAnomaly ? 'table-warning' : ''}">
                <td>${timestamp}</td>
                <td>${item.temperature.toFixed(1)}°C</td>
                <td>${item.pressure.toFixed(1)} kPa</td>
                <td>${item.rpm.toFixed(0)}</td>
                <td>${anomalyBadge}</td>
            </tr>
        `;
    });
    
    table.innerHTML = tableHTML;
}

// Create chart for device data
function createDeviceDataChart(dataLogs, alerts) {
    // Combine and sort by timestamp (oldest first for chart)
    const combinedData = [...dataLogs, ...alerts].sort((a, b) => {
        return new Date(a.timestamp) - new Date(b.timestamp);
    });
    
    if (combinedData.length === 0) return;
    
    // Prepare chart data
    const labels = combinedData.map(item => new Date(item.timestamp).toLocaleString());
    const temperatureData = combinedData.map(item => item.temperature);
    const pressureData = combinedData.map(item => item.pressure);
    const rpmData = combinedData.map(item => item.rpm);
    
    // Get chart element
    const ctx = document.getElementById('deviceSensorChart').getContext('2d');
    
    // Destroy existing chart if exists
    if (window.deviceDataChart) {
        window.deviceDataChart.destroy();
    }
    
    // Create new chart
    window.deviceDataChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Temperature (°C)',
                    data: temperatureData,
                    borderColor: 'rgba(255, 99, 132, 1)',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    tension: 0.4,
                    pointRadius: 2
                },
                {
                    label: 'Pressure (kPa)',
                    data: pressureData,
                    borderColor: 'rgba(54, 162, 235, 1)',
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    tension: 0.4,
                    pointRadius: 2
                },
                {
                    label: 'RPM',
                    data: rpmData,
                    borderColor: 'rgba(255, 206, 86, 1)',
                    backgroundColor: 'rgba(255, 206, 86, 0.2)',
                    tension: 0.4,
                    pointRadius: 2
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'Sensor Data'
                }
            },
            scales: {
                y: {
                    beginAtZero: false
                }
            }
        }
    });
}

// Show an alert message
function showAlert(message, type) {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Insert at top of page
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto dismiss after 5 seconds
    setTimeout(() => {
        const bsAlert = new bootstrap.Alert(alertDiv);
        bsAlert.close();
    }, 5000);
}