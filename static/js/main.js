// Main JavaScript file for AEGIS

// Helper function to format timestamps
function formatTimestamp(timestamp) {
    if (!timestamp) return 'N/A';
    
    // Check if it's a Unix timestamp (number)
    if (typeof timestamp === 'number') {
        // Convert to milliseconds if needed (if timestamp is in seconds)
        if (timestamp < 10000000000) {
            timestamp *= 1000;
        }
        const date = new Date(timestamp);
        return date.toLocaleString();
    }
    
    // Handle ISO string format
    if (typeof timestamp === 'string' && timestamp.includes('T')) {
        const date = new Date(timestamp);
        return date.toLocaleString();
    }
    
    // Return as is if we can't parse it
    return timestamp;
}

// Helper function to create a status badge
function createStatusBadge(status) {
    let badgeClass = 'bg-secondary';
    
    if (status === 'normal') {
        badgeClass = 'bg-success';
    } else if (status === 'anomaly') {
        badgeClass = 'bg-warning';
    } else if (status === 'malware') {
        badgeClass = 'bg-danger';
    }
    
    return `<span class="badge ${badgeClass}">${status}</span>`;
}

// Function to show error messages
function showError(message, containerId = 'alert-container') {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const alertElement = document.createElement('div');
    alertElement.className = 'alert alert-danger alert-dismissible fade show';
    alertElement.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    container.appendChild(alertElement);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const bsAlert = new bootstrap.Alert(alertElement);
        bsAlert.close();
    }, 5000);
}

// Function to show success messages
function showSuccess(message, containerId = 'alert-container') {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const alertElement = document.createElement('div');
    alertElement.className = 'alert alert-success alert-dismissible fade show';
    alertElement.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    container.appendChild(alertElement);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const bsAlert = new bootstrap.Alert(alertElement);
        bsAlert.close();
    }, 5000);
}

// Add global alert container if not present
document.addEventListener('DOMContentLoaded', () => {
    if (!document.getElementById('alert-container')) {
        const alertContainer = document.createElement('div');
        alertContainer.id = 'alert-container';
        alertContainer.className = 'position-fixed top-0 end-0 p-3';
        alertContainer.style.zIndex = '1050';
        document.body.appendChild(alertContainer);
    }
});