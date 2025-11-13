// Wait for the DOM to be fully loaded before running scripts
document.addEventListener('DOMContentLoaded', () => {

    // --- Page Transition Logic ---
    document.body.classList.add('is-loaded');
    const allLinks = document.querySelectorAll('a');
    allLinks.forEach(link => {
        link.addEventListener('click', e => {
            const destination = link.getAttribute('href');
            if (destination && destination !== '#' && !destination.startsWith('javascript:')) {
                e.preventDefault();
                document.body.classList.remove('is-loaded');
                setTimeout(() => { window.location.href = destination; }, 500);
            }
        });
    });
    window.addEventListener('pageshow', event => {
        if (event.persisted) {
            document.body.classList.add('is-loaded');
        }
    });

    // --- Chart.js Pie Chart Logic ---
    const chartCanvas = document.getElementById('aqChart');
    if (chartCanvas) {
        try {
    // Correctly read the data from the canvas element's 'data-scores' attribute
    const scoresDataString = chartCanvas.dataset.scores;

    // Now, proceed with parsing and creating the chart
    if (scoresDataString && scoresDataString !== 'null' && scoresDataString.trim() !== '{}') {

                const scoresData = JSON.parse(scoresDataString);
                const labels = ['Control', 'Ownership', 'Reach', 'Endurance', 'Attitude'];
                const data = [
                    scoresData.control_score,
                    scoresData.ownership_score,
                    scoresData.reach_score,
                    scoresData.endurance_score,
                    scoresData.attitude_score
                ];

            

                // Set Chart.js global defaults for better text rendering in dark mode
                Chart.defaults.color = 'rgba(235, 235, 245, 0.7)';
                Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Inter", sans-serif';

                new Chart(chartCanvas, {
                    type: 'pie',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'AQ Score Breakdown',
                            data: data,
                            backgroundColor: [ // New Yellowish-Orange Palette
                                'rgba(255, 208, 0, 1)',  // Orange
                                'rgba(255, 204, 0, 0.8)',  // Yellow
                                'rgba(255, 59, 48, 0.8)',   // Red accent
                                'rgba(209, 140, 35, 0.8)',  // Lighter Orange
                                'rgba(255, 115, 0, 0.8)'   // Gold
                            ],
                            borderColor: 'rgba(44, 44, 46, 0.5)',
                            borderWidth: 1.5
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'bottom',
                                labels: {
                                    padding: 20,
                                    font: {
                                        size: 14
                                    }
                                }
                            },
                            title: {
                                display: false // The H2 in the card is enough
                            }
                        }
                    }
                });
            } else {
                console.error("Chart data is missing or empty, so the chart was not rendered.");
            }
        } catch (error) {
            console.error("Could not parse scores data for chart:", error);
        }
    }
});

