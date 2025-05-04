// Network topology visualization using vis.js
let network = null;

function initNetwork(container, nodes, edges) {
    const data = {
        nodes: new vis.DataSet(nodes),
        edges: new vis.DataSet(edges)
    };
    
    const options = {
        nodes: {
            shape: 'dot',
            size: 16,
            font: {
                size: 12,
                color: '#ffffff'
            }
        },
        edges: {
            width: 2,
            smooth: {
                type: 'continuous'
            }
        },
        physics: {
            stabilization: false,
            barnesHut: {
                gravitationalConstant: -80000,
                springConstant: 0.001,
                springLength: 200
            }
        },
        interaction: {
            hover: true,
            tooltipDelay: 200
        }
    };
    
    network = new vis.Network(container, data, options);
}

// File upload handling
document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('upload-form');
    const resultsSection = document.querySelector('.results-section');
    const resultsDiv = document.getElementById('results');
    const networkGraph = document.getElementById('networkGraph');

    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData();
        const fileInput = uploadForm.querySelector('input[type="file"]');
        
        // Add all selected files to FormData
        for (const file of fileInput.files) {
            formData.append('files', file);
        }

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData,
                headers: {
                    'Accept': 'application/json'
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Upload failed');
            }

            const data = await response.json();
            
            // Display results
            resultsSection.style.display = 'block';
            resultsDiv.innerHTML = `
                <h3>Verification Results</h3>
                <pre>${JSON.stringify(data.report, null, 2)}</pre>
            `;

            // Display topology
            if (data.topology && data.topology.nodes && data.topology.edges) {
                // Clear previous network if exists
                if (network) {
                    network.destroy();
                }
                // Initialize network visualization
                initNetwork(networkGraph, data.topology.nodes, data.topology.edges);
            } else {
                console.error('Invalid topology data:', data.topology);
            }

        } catch (error) {
            alert('Error: ' + error.message);
        }
    });
});

function displayResults(report) {
    const resultsDiv = document.getElementById('results');
    const results = report.report;
    
    let html = '<div class="results-container">';
    
    // Display overall status
    html += `
        <div class="card result-card">
            <h3>Verification Summary</h3>
            <div class="status-badge status-${results.overall_status.toLowerCase()}">
                ${results.overall_status}
            </div>
        </div>
    `;
    
    // Display individual checks
    results.checks.forEach(check => {
        html += `
            <div class="card result-card">
                <h4>${check.name}</h4>
                <div class="status-badge status-${check.status.toLowerCase()}">
                    ${check.status}
                </div>
                <p>${check.description}</p>
                ${check.details ? `<pre>${JSON.stringify(check.details, null, 2)}</pre>` : ''}
            </div>
        `;
    });
    
    // Add network graph container if topology data is available
    if (report.topology) {
        html += `
            <div class="card">
                <h3>Network Topology</h3>
                <div id="networkGraph" class="network-graph"></div>
            </div>
        `;
    }
    
    html += '</div>';
    resultsDiv.innerHTML = html;
}

function showError(message) {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = `
        <div class="alert alert-danger">
            Error: ${message}
        </div>
    `;
} 