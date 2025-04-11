// Logs page JavaScript functionality

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    // Initial data load
    loadLogData();
    
    // Set up event listeners
    document.getElementById('refreshLogs').addEventListener('click', loadLogData);
    document.getElementById('logCountSelector').addEventListener('change', loadLogData);
    
    // Set up periodic refresh (every 60 seconds)
    setInterval(loadLogData, 60000);
});

// Function to load log data
function loadLogData() {
    // Get selected count
    const count = document.getElementById('logCountSelector').value;
    
    // Fetch logs data
    fetch(`/logs?count=${count}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                updateLogViews(data.logs);
            } else {
                showError('Failed to load logs: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error fetching logs:', error);
            showError('Error loading logs: ' + error.message);
        });
}

// Function to update log views
function updateLogViews(logsData) {
    // Update data logs table
    updateDataLogTable(logsData.data_logs || []);
    
    // Update alert logs
    updateAlertLogs(logsData.alerts || []);
}

// Function to update data log table
function updateDataLogTable(dataLogs) {
    const tableBody = document.getElementById('dataLogTable');
    
    // Clear the table body
    tableBody.innerHTML = '';
    
    // If no data logs, show a message
    if (dataLogs.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="6" class="text-center">No data logs available</td>';
        tableBody.appendChild(row);
        return;
    }
    
    // Sort by timestamp (newest first)
    dataLogs.sort((a, b) => b.received_at - a.received_at);
    
    // Add rows for each data log
    dataLogs.forEach(log => {
        const row = document.createElement('tr');
        
        row.innerHTML = `
            <td>${formatTimestamp(log.timestamp)}</td>
            <td>${log.device_id}</td>
            <td>${log.temperature.toFixed(2)}</td>
            <td>${log.pressure.toFixed(2)}</td>
            <td>${log.rpm.toFixed(0)}</td>
            <td>${formatTimestamp(log.received_at)}</td>
        `;
        
        tableBody.appendChild(row);
    });
}

// Function to update alert logs
function updateAlertLogs(alertLogs) {
    const alertLogsContainer = document.getElementById('alertLogs');
    
    // Clear the container
    alertLogsContainer.innerHTML = '';
    
    // If no alert logs, show a message
    if (alertLogs.length === 0) {
        alertLogsContainer.innerHTML = '<div class="text-center text-secondary">No alert logs available</div>';
        return;
    }
    
    // Add entries for each alert log
    alertLogs.forEach(log => {
        const logEntry = document.createElement('div');
        logEntry.className = 'alert-entry';
        
        // Highlight potential malware alerts
        if (log.includes('ANOMALY DETECTED') && log.includes('Score: -0.')) {
            const score = parseFloat(log.match(/Score: (-?\d+\.\d+)/)[1]);
            
            if (score < -0.6) {
                logEntry.className += ' text-danger';
            } else {
                logEntry.className += ' text-warning';
            }
        }
        
        logEntry.textContent = log;
        alertLogsContainer.appendChild(logEntry);
    });
}