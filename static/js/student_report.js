// Report JavaScript functionality
document.addEventListener('DOMContentLoaded', function () {
    
    // Initialize Chart
    initializeChart();
    
    // Initialize PDF Download
    initializePDFDownload();
});


// ===================================================================
// THIS IS THE MODIFIED FUNCTION
// ===================================================================
function initializeChart() {
    try {
        // Safely retrieve the data from our hidden div and parse it
        const chartDataElement = document.getElementById('chartData');
        
        if (!chartDataElement) {
            console.error('Chart data element not found');
            showChartError('Chart data element not found');
            return;
        }
        
        const scoresData = chartDataElement.dataset.scores;
        
        if (!scoresData || scoresData === '{}') {
            console.warn('No trait scores data available');
            showChartError('Chart data not available');
            return;
        }
        
        const traitScores = JSON.parse(scoresData);
        
        // Check if we have valid data
        const labels = Object.keys(traitScores);
        const data = Object.values(traitScores);
        
        if (labels.length === 0 || data.length === 0) {
            console.warn('Empty trait scores data');
            showChartError('No data available for chart');
            return;
        }
        
        const ctx = document.getElementById('aqPieChart');
        if (!ctx) {
            console.error('Chart canvas element not found');
            showChartError('Chart canvas not found');
            return;
        }

        // --- Make sure the plugin is registered ---
        Chart.register(ChartDataLabels);
        
        // Create the chart
        new Chart(ctx, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    label: 'AQ Trait Score',
                    data: data,
                    backgroundColor: [
                        'rgba(54, 162, 235, 0.8)', // Blue
                        'rgba(255, 159, 64, 0.8)', // Orange
                        'rgba(75, 192, 192, 0.8)', // Green
                        'rgba(255, 99, 132, 0.8)',  // Red
                        'rgba(153, 102, 255, 0.8)', // Purple
                        'rgba(255, 205, 86, 0.8)',  // Yellow
                        'rgba(201, 203, 207, 0.8)'  // Grey
                    ],
                    borderColor: '#ffffff',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: true,
                        text: 'Your AQ Trait Distribution'
                    },
                    // --- NEW CONFIGURATION TO SHOW MARKS ON THE CHART ---
                    datalabels: {
                        formatter: (value) => {
                            // This function returns the raw score to be displayed
                            return value *2;
                        },
                        color: '#fff', // Color of the text (your score)
                        font: {
                            weight: 'bold',
                            size: 16
                        }
                    }
                    // --- END OF NEW CONFIGURATION ---
                }
            }
        });
        
    } catch (error) {
        console.error('Error creating chart:', error);
        showChartError('Error loading chart');
    }
}

// ===================================================================
// NO CHANGES TO THE REST OF THE CODE
// ===================================================================

function showChartError(message) {
    const ctx = document.getElementById('aqPieChart');
    if (ctx) {
        const parent = ctx.parentElement;
        parent.innerHTML = `<p style="text-align: center; color: #666; padding: 20px;">${message}</p>`;
    }
}

function initializePDFDownload() {
    const downloadButton = document.getElementById('download-btn');
    const reportContent = document.getElementById('report-content');

    if (!downloadButton || !reportContent) {
        console.error('Download button or report content not found');
        return;
    }

    downloadButton.addEventListener('click', function () {
        handlePDFDownload(downloadButton, reportContent);
    });
}

function handlePDFDownload(button, content) {
    try {
        // Show loading state
        const originalText = button.textContent;
        button.textContent = 'Generating PDF...';
        button.disabled = true;

        // Get enrollment number from template or use default
        const enrollmentNo = getEnrollmentNumber();

        const options = {
            margin: [0.5, 0.3, 0.5, 0.3], // Increased top/bottom margin
            filename: `career_report_${enrollmentNo}.pdf`,
            image: { 
                type: 'jpeg', 
                quality: 0.98 
            },
            html2canvas: { 
                scale: 2, 
                useCORS: true 
            },
            jsPDF: { 
                unit: 'in', 
                format: 'a4', 
                orientation: 'portrait' 
            },
            pagebreak: { mode: ['avoid-all', 'css', 'legacy'] } 
        };
        
        // Generate PDF
        html2pdf()
            .from(content)
            .set(options)
            .save()
            .then(function() {
                // Success - reset button
                resetDownloadButton(button, originalText);
            })
            .catch(function(error) {
                // Error - show error state
                handleDownloadError(button, originalText, error);
            });
            
    } catch (error) {
        console.error('Download initialization error:', error);
        button.textContent = 'Download Error';
        button.disabled = false;
        
        // Reset after delay
        setTimeout(function() {
            button.textContent = 'Download Report as PDF';
        }, 3000);
    }
}

function handleDownloadError(button, originalText, error) {
    console.error('PDF generation error:', error);
    button.textContent = 'Downloading';
    button.disabled = false;
    
    // Reset button text after a delay
    setTimeout(function() {
        button.textContent = originalText;
    }, 3000);
}

function getEnrollmentNumber() {
    // Correctly read the enrollment number from the data attribute
    const reportContent = document.getElementById('report-content');
    if (reportContent && reportContent.dataset.enrollment) {
        return reportContent.dataset.enrollment;
    }
    
    // Fallback to timestamp if not found
    console.warn('Enrollment number not found in data attribute, using timestamp as fallback.');
    return new Date().getTime();
}

// Additional utility functions
function showMessage(message, type = 'info') {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${type}`;
    messageDiv.textContent = message;
    messageDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 10px 20px;
        border-radius: 4px;
        z-index: 1000;
        color: white;
        background-color: ${type === 'error' ? '#f44336' : '#4CAF50'};
    `;
    
    document.body.appendChild(messageDiv);
    
    // Remove message after 3 seconds
    setTimeout(function() {
        if (messageDiv.parentNode) {
            messageDiv.parentNode.removeChild(messageDiv);
        }
    }, 3000);
}

// Export functions for testing (if needed)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initializeChart,
        initializePDFDownload,
        showChartError,
        handlePDFDownload
    };
}