// Training page JavaScript functionality

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    // Set up event listeners
    document.getElementById('trainSyntheticBtn').addEventListener('click', trainWithSynthetic);
    document.getElementById('uploadDataBtn').addEventListener('click', trainWithUploadedData);
    document.getElementById('trainCustomBtn').addEventListener('click', trainWithCustom);
});

// Function to train with synthetic data
function trainWithSynthetic() {
    // Get parameters
    const sampleCount = parseInt(document.getElementById('syntheticSampleCount').value);
    const contamination = parseFloat(document.getElementById('syntheticContamination').value);
    
    // Validate parameters
    if (isNaN(sampleCount) || sampleCount < 1000 || sampleCount > 50000) {
        showError('Sample count must be between 1,000 and 50,000', 'trainingResults');
        return;
    }
    
    if (isNaN(contamination) || contamination < 0.01 || contamination > 0.5) {
        showError('Contamination rate must be between 0.01 and 0.5', 'trainingResults');
        return;
    }
    
    // Update UI
    showTrainingProgress('Generating synthetic data and training model...');
    
    // Make API request to train model with synthetic data
    fetch('/api/train-synthetic', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            sample_count: sampleCount,
            contamination: contamination
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            showTrainingSuccess(data);
        } else {
            showTrainingError(data.message);
        }
    })
    .catch(error => {
        console.error('Error training model:', error);
        showTrainingError(error.message);
    });
}

// Function to train with uploaded data
function trainWithUploadedData() {
    // Get file input
    const fileInput = document.getElementById('dataFile');
    
    // Check if a file is selected
    if (!fileInput.files || fileInput.files.length === 0) {
        showError('Please select a CSV file to upload', 'trainingResults');
        return;
    }
    
    const file = fileInput.files[0];
    
    // Check file type
    if (!file.name.toLowerCase().endsWith('.csv')) {
        showError('Please select a CSV file', 'trainingResults');
        return;
    }
    
    // Update UI
    showTrainingProgress('Uploading data and training model...');
    
    // Create FormData object
    const formData = new FormData();
    formData.append('file', file);
    
    // Make API request to train model with uploaded data
    fetch('/api/train-upload', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            showTrainingSuccess(data);
        } else {
            showTrainingError(data.message);
        }
    })
    .catch(error => {
        console.error('Error training model:', error);
        showTrainingError(error.message);
    });
}

// Function to train with custom parameters
function trainWithCustom() {
    // Get parameters
    const params = {
        sample_count: parseInt(document.getElementById('anomalySampleCount').value),
        contamination: parseFloat(document.getElementById('anomalyContamination').value),
        normal_params: {
            temperature: {
                mean: parseFloat(document.getElementById('normalTemp').value),
                var: parseFloat(document.getElementById('normalTempVar').value)
            },
            pressure: {
                mean: parseFloat(document.getElementById('normalPressure').value),
                var: parseFloat(document.getElementById('normalPressureVar').value)
            },
            rpm: {
                mean: parseFloat(document.getElementById('normalRPM').value),
                var: parseFloat(document.getElementById('normalRPMVar').value)
            }
        }
    };
    
    // Validate parameters
    if (isNaN(params.sample_count) || params.sample_count < 1000 || params.sample_count > 50000) {
        showError('Sample count must be between 1,000 and 50,000', 'trainingResults');
        return;
    }
    
    if (isNaN(params.contamination) || params.contamination < 0.01 || params.contamination > 0.5) {
        showError('Contamination rate must be between 0.01 and 0.5', 'trainingResults');
        return;
    }
    
    // Update UI
    showTrainingProgress('Generating data with custom parameters and training model...');
    
    // Make API request to train model with custom parameters
    fetch('/api/train-custom', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(params)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            showTrainingSuccess(data);
        } else {
            showTrainingError(data.message);
        }
    })
    .catch(error => {
        console.error('Error training model:', error);
        showTrainingError(error.message);
    });
}

// Function to show training progress
function showTrainingProgress(message) {
    const container = document.getElementById('trainingResults');
    container.innerHTML = `
        <div class="d-flex align-items-center">
            <div class="spinner-border text-info me-3" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <div>${message}</div>
        </div>
    `;
}

// Function to show training success
function showTrainingSuccess(data) {
    const container = document.getElementById('trainingResults');
    
    let content = `
        <div class="alert alert-success">
            <h5>Training Successful</h5>
            <p>${data.message}</p>
    `;
    
    // Add details if available
    if (data.details) {
        content += '<ul>';
        
        if (data.details.n_samples) {
            content += `<li>Number of samples: ${data.details.n_samples}</li>`;
        }
        
        if (data.details.features) {
            content += `<li>Features: ${data.details.features.join(', ')}</li>`;
        }
        
        if (data.details.training_time) {
            content += `<li>Training time: ${data.details.training_time.toFixed(2)} seconds</li>`;
        }
        
        content += '</ul>';
    }
    
    content += '</div>';
    
    container.innerHTML = content;
}

// Function to show training error
function showTrainingError(message) {
    const container = document.getElementById('trainingResults');
    container.innerHTML = `
        <div class="alert alert-danger">
            <h5>Training Failed</h5>
            <p>${message}</p>
        </div>
    `;
}