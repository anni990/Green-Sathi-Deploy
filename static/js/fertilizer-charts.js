/**
 * Fertilizer Report Charts
 * This file contains functions to initialize and render charts for the fertilizer recommendation report
 */

function initializeCharts(data) {
    // Initialize all charts based on available data
    if (data.soilTestResults && data.soilTestResults.length > 0) {
        createSoilRadarChart(data.soilTestResults);
        createNPKPieChart(data.soilTestResults);
        createMicronutrientsPieChart(data.soilTestResults);
        createBasicPropertiesChart(data.soilTestResults);
    }
    
    if (data.deficiencyAnalysis && data.deficiencyAnalysis.length > 0) {
        createDeficiencyBarChart(data.deficiencyAnalysis);
        createDeficiencySeverityChart(data.deficiencyAnalysis);
    }
    
    if (data.fertilizerRecommendations && data.fertilizerRecommendations.length > 0) {
        createFertilizerDoseChart(data.fertilizerRecommendations);
        createNutrientCoverageChart(data.fertilizerRecommendations);
    }
}

// Shared chart configuration options
const chartOptions = {
    animation: {
        duration: 1500,
        easing: 'easeOutQuart'
    },
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        tooltip: {
            backgroundColor: 'rgba(255, 255, 255, 0.9)',
            titleColor: '#1f2937',
            bodyColor: '#374151',
            borderColor: '#e5e7eb',
            borderWidth: 1,
            padding: 10,
            boxPadding: 5,
            cornerRadius: 4,
            displayColors: true
        }
    }
};

// Chart color palettes
const statusColors = {
    'OPTIMAL': '#10b981', // Green
    'MODERATE': '#f59e0b', // Yellow
    'CRITICAL': '#ef4444', // Red
    'default': '#6b7280'   // Gray
};

const nutrientColors = {
    'Nitrogen': '#4ade80', // Light green
    'Phosphorus': '#60a5fa', // Light blue
    'Potassium': '#f472b6', // Pink
    'Zinc': '#a78bfa', // Purple
    'Iron': '#fb923c', // Orange
    'Copper': '#a1a1aa', // Gray
    'Manganese': '#fbbf24', // Yellow
    'Sulphur': '#2dd4bf', // Teal
    'Boron': '#94a3b8', // Slate
    'pH': '#475569', // Dark gray
    'EC': '#0ea5e9', // Sky blue
    'OC': '#84cc16'  // Lime
};

// Get the right color for a soil parameter
function getColorForParameter(parameter, status) {
    if (parameter.includes('Nitrogen')) return nutrientColors['Nitrogen'];
    if (parameter.includes('Phosphorus')) return nutrientColors['Phosphorus'];
    if (parameter.includes('Potassium')) return nutrientColors['Potassium'];
    if (parameter.includes('Zinc')) return nutrientColors['Zinc'];
    if (parameter.includes('Iron')) return nutrientColors['Iron'];
    if (parameter.includes('Copper')) return nutrientColors['Copper'];
    if (parameter.includes('Manganese')) return nutrientColors['Manganese'];
    if (parameter.includes('Sulphur')) return nutrientColors['Sulphur'];
    if (parameter.includes('Boron')) return nutrientColors['Boron'];
    if (parameter.includes('pH')) return nutrientColors['pH'];
    if (parameter.includes('EC')) return nutrientColors['EC'];
    if (parameter.includes('OC')) return nutrientColors['OC'];
    
    return status ? statusColors[status] || statusColors.default : statusColors.default;
}

/**
 * Create a radar chart for showing overall soil parameters
 */
function createSoilRadarChart(soilData) {
    const ctx = document.getElementById('soilRadarChart').getContext('2d');
    
    // Filter relevant soil parameters for the radar chart
    const relevantParams = soilData.filter(item => 
        ['pH', 'OC (%)', 'EC (dS/m)', 'Nitrogen (kg/ha)', 'Phosphorus (kg/ha)', 
         'Potassium (kg/ha)', 'Zinc (ppm)', 'Iron (ppm)'].includes(item.parameter)
    );
    
    // Normalize values to 0-100 scale for radar chart
    const maxValues = {
        'pH': 14,
        'OC (%)': 3,
        'EC (dS/m)': 4,
        'Nitrogen (kg/ha)': 500,
        'Phosphorus (kg/ha)': 50,
        'Potassium (kg/ha)': 400,
        'Zinc (ppm)': 10,
        'Iron (ppm)': 20
    };
    
    const normalizedData = relevantParams.map(item => ({
        parameter: item.parameter,
        value: item.value,
        normalizedValue: (item.value / (maxValues[item.parameter] || 100)) * 100,
        status: item.status
    }));
    
    new Chart(ctx, {
        type: 'radar',
        data: {
            labels: normalizedData.map(item => item.parameter),
            datasets: [{
                label: 'Soil Parameters',
                data: normalizedData.map(item => item.normalizedValue),
                backgroundColor: 'rgba(16, 185, 129, 0.2)',
                borderColor: '#10b981',
                borderWidth: 2,
                pointBackgroundColor: normalizedData.map(item => getColorForParameter(item.parameter, item.status)),
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: normalizedData.map(item => getColorForParameter(item.parameter, item.status)),
                pointRadius: 5
            }]
        },
        options: {
            ...chartOptions,
            scales: {
                r: {
                    angleLines: {
                        color: 'rgba(0, 0, 0, 0.1)',
                    },
                    suggestedMin: 0,
                    suggestedMax: 100,
                    ticks: {
                        display: false
                    }
                }
            },
            plugins: {
                ...chartOptions.plugins,
                tooltip: {
                    ...chartOptions.plugins.tooltip,
                    callbacks: {
                        title: function(tooltipItems) {
                            return tooltipItems[0].label;
                        },
                        label: function(context) {
                            const item = normalizedData[context.dataIndex];
                            return `Value: ${item.value}`;
                        },
                        afterLabel: function(context) {
                            const item = normalizedData[context.dataIndex];
                            return `Status: ${item.status}`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Create a pie chart for NPK distribution
 */
function createNPKPieChart(soilData) {
    const ctx = document.getElementById('npkPieChart').getContext('2d');
    
    // Filter NPK data
    const npkData = soilData.filter(item => 
        ['Nitrogen (kg/ha)', 'Phosphorus (kg/ha)', 'Potassium (kg/ha)'].includes(item.parameter)
    );
    
    if (npkData.length > 0) {
        new Chart(ctx, {
            type: 'pie',
            data: {
                labels: npkData.map(item => item.parameter.replace(' (kg/ha)', '')),
                datasets: [{
                    data: npkData.map(item => item.value),
                    backgroundColor: [
                        nutrientColors['Nitrogen'],
                        nutrientColors['Phosphorus'],
                        nutrientColors['Potassium']
                    ],
                    borderColor: '#ffffff',
                    borderWidth: 2
                }]
            },
            options: {
                ...chartOptions,
                plugins: {
                    ...chartOptions.plugins,
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 15,
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    },
                    tooltip: {
                        ...chartOptions.plugins.tooltip,
                        callbacks: {
                            label: function(context) {
                                const item = npkData[context.dataIndex];
                                const value = item.value;
                                const total = npkData.reduce((sum, item) => sum + item.value, 0);
                                const percentage = Math.round((value / total) * 100);
                                return `${item.parameter}: ${value} (${percentage}%)`;
                            },
                            afterLabel: function(context) {
                                const item = npkData[context.dataIndex];
                                return `Status: ${item.status}`;
                            }
                        }
                    }
                }
            }
        });
    }
}

/**
 * Create a pie chart for micronutrients
 */
function createMicronutrientsPieChart(soilData) {
    const ctx = document.getElementById('micronutrientsPieChart').getContext('2d');
    
    // Filter micronutrients data (all parameters with "ppm")
    const micronutrients = soilData.filter(item => 
        item.parameter.includes('ppm')
    );
    
    if (micronutrients.length > 0) {
        new Chart(ctx, {
            type: 'pie',
            data: {
                labels: micronutrients.map(item => item.parameter.replace(' (ppm)', '')),
                datasets: [{
                    data: micronutrients.map(item => item.value),
                    backgroundColor: micronutrients.map(item => getColorForParameter(item.parameter)),
                    borderColor: '#ffffff',
                    borderWidth: 2
                }]
            },
            options: {
                ...chartOptions,
                plugins: {
                    ...chartOptions.plugins,
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 15,
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    },
                    tooltip: {
                        ...chartOptions.plugins.tooltip,
                        callbacks: {
                            afterLabel: function(context) {
                                const item = micronutrients[context.dataIndex];
                                return `Status: ${item.status}`;
                            }
                        }
                    }
                }
            }
        });
    }
}

/**
 * Create a chart for pH, EC & OC
 */
function createBasicPropertiesChart(soilData) {
    const ctx = document.getElementById('basicPropertiesChart').getContext('2d');
    
    // Filter basic properties
    const basicProps = soilData.filter(item => 
        ['pH', 'EC (dS/m)', 'OC (%)'].includes(item.parameter)
    );
    
    if (basicProps.length > 0) {
        // Create custom scales based on property type
        const scales = {
            pH: {
                min: 0,
                max: 14,
                optimal: [6.5, 7.5],
                title: 'pH Scale'
            },
            EC: {
                min: 0,
                max: 4,
                optimal: [0.8, 1.5],
                title: 'EC (dS/m)'
            },
            OC: {
                min: 0,
                max: 3,
                optimal: [0.6, 1.0],
                title: 'Organic Carbon (%)'
            }
        };
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: basicProps.map(item => item.parameter.replace(' (dS/m)', '').replace(' (%)', '')),
                datasets: [{
                    label: 'Value',
                    data: basicProps.map(item => item.value),
                    backgroundColor: basicProps.map(item => {
                        if (item.parameter.includes('pH')) return nutrientColors['pH'];
                        if (item.parameter.includes('EC')) return nutrientColors['EC'];
                        if (item.parameter.includes('OC')) return nutrientColors['OC'];
                        return statusColors[item.status] || statusColors.default;
                    }),
                    borderWidth: 1
                }]
            },
            options: {
                ...chartOptions,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Value'
                        }
                    }
                },
                plugins: {
                    ...chartOptions.plugins,
                    tooltip: {
                        ...chartOptions.plugins.tooltip,
                        callbacks: {
                            afterLabel: function(context) {
                                const item = basicProps[context.dataIndex];
                                let range = '';
                                
                                if (item.parameter.includes('pH')) {
                                    range = `Optimal range: ${scales.pH.optimal[0]}-${scales.pH.optimal[1]}`;
                                } else if (item.parameter.includes('EC')) {
                                    range = `Optimal range: ${scales.EC.optimal[0]}-${scales.EC.optimal[1]}`;
                                } else if (item.parameter.includes('OC')) {
                                    range = `Optimal range: ${scales.OC.optimal[0]}-${scales.OC.optimal[1]}`;
                                }
                                
                                return [`Status: ${item.status}`, range];
                            }
                        }
                    }
                }
            }
        });
    }
}

/**
 * Create a bar chart for nutrient deficiency levels
 */
function createDeficiencyBarChart(deficiencyData) {
    const ctx = document.getElementById('deficiencyBarChart').getContext('2d');
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: deficiencyData.map(item => item.nutrient),
            datasets: [{
                label: 'Deficiency (kg/ha)',
                data: deficiencyData.map(item => item.deficiency),
                backgroundColor: deficiencyData.map(item => {
                    if (item.severity === 'CRITICAL') return statusColors['CRITICAL'];
                    if (item.severity === 'MODERATE') return statusColors['MODERATE'];
                    if (item.severity === 'OPTIMAL') return statusColors['OPTIMAL'];
                    return statusColors.default;
                }),
                borderWidth: 1
            }]
        },
        options: {
            ...chartOptions,
            indexAxis: 'y',
            scales: {
                x: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Deficiency Amount (kg/ha)'
                    }
                }
            },
            plugins: {
                ...chartOptions.plugins,
                tooltip: {
                    ...chartOptions.plugins.tooltip,
                    callbacks: {
                        afterLabel: function(context) {
                            const item = deficiencyData[context.dataIndex];
                            return [
                                `Severity: ${item.severity}`,
                                `Impact: ${item.impact}`
                            ];
                        }
                    }
                }
            }
        }
    });
}

/**
 * Create a radar chart for deficiency severity analysis
 */
function createDeficiencySeverityChart(deficiencyData) {
    const ctx = document.getElementById('deficiencySeverityChart').getContext('2d');
    
    // Convert severity to a numeric value for visualization
    const severityValues = {
        'OPTIMAL': 1,
        'MODERATE': 2,
        'CRITICAL': 3
    };
    
    // Add numeric severity value
    const enrichedData = deficiencyData.map(item => ({
        ...item,
        severityValue: severityValues[item.severity] || 0
    }));
    
    new Chart(ctx, {
        type: 'polarArea',
        data: {
            labels: enrichedData.map(item => item.nutrient),
            datasets: [{
                data: enrichedData.map(item => item.severityValue),
                backgroundColor: enrichedData.map(item => {
                    if (item.severity === 'CRITICAL') return `${statusColors['CRITICAL']}99`;
                    if (item.severity === 'MODERATE') return `${statusColors['MODERATE']}99`;
                    if (item.severity === 'OPTIMAL') return `${statusColors['OPTIMAL']}99`;
                    return `${statusColors.default}99`;
                }),
                borderColor: enrichedData.map(item => {
                    if (item.severity === 'CRITICAL') return statusColors['CRITICAL'];
                    if (item.severity === 'MODERATE') return statusColors['MODERATE'];
                    if (item.severity === 'OPTIMAL') return statusColors['OPTIMAL'];
                    return statusColors.default;
                }),
                borderWidth: 1
            }]
        },
        options: {
            ...chartOptions,
            scales: {
                r: {
                    ticks: {
                        display: false
                    },
                    max: 3
                }
            },
            plugins: {
                ...chartOptions.plugins,
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    ...chartOptions.plugins.tooltip,
                    callbacks: {
                        label: function(context) {
                            const item = enrichedData[context.dataIndex];
                            return `${item.nutrient}: ${item.severity}`;
                        },
                        afterLabel: function(context) {
                            const item = enrichedData[context.dataIndex];
                            return [
                                `Deficiency: ${item.deficiency} kg/ha`,
                                `Impact: ${item.impact}`
                            ];
                        }
                    }
                }
            }
        }
    });
}

/**
 * Create a chart for fertilizer dose recommendations
 */
function createFertilizerDoseChart(fertilizerData) {
    const ctx = document.getElementById('fertilizerDoseChart').getContext('2d');
    
    // Parse dose to get numeric values
    const processedData = fertilizerData.map(item => {
        let doseValue = 0;
        if (typeof item.dose === 'string') {
            const match = item.dose.match(/\d+(\.\d+)?/);
            if (match) {
                doseValue = parseFloat(match[0]);
            }
        }
        return {
            ...item,
            doseValue: doseValue
        };
    });
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: processedData.map(item => item.product),
            datasets: [{
                label: 'Recommended Dose (kg/ha)',
                data: processedData.map(item => item.doseValue),
                backgroundColor: processedData.map(item => 
                    item.type === 'Soil Amendment' ? 'rgba(16, 185, 129, 0.7)' : 'rgba(59, 130, 246, 0.7)'
                ),
                borderColor: processedData.map(item => 
                    item.type === 'Soil Amendment' ? 'rgb(16, 185, 129)' : 'rgb(59, 130, 246)'
                ),
                borderWidth: 1
            }]
        },
        options: {
            ...chartOptions,
            indexAxis: 'y',
            scales: {
                x: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Dose (kg/ha)'
                    }
                }
            },
            plugins: {
                ...chartOptions.plugins,
                tooltip: {
                    ...chartOptions.plugins.tooltip,
                    callbacks: {
                        afterLabel: function(context) {
                            const item = processedData[context.dataIndex];
                            return [
                                `Type: ${item.type}`,
                                `Purpose: ${item.purpose}`
                            ];
                        }
                    }
                }
            }
        }
    });
}

/**
 * Create a chart for nutrient coverage by fertilizers
 */
function createNutrientCoverageChart(fertilizerData) {
    const ctx = document.getElementById('nutrientCoverageChart').getContext('2d');
    
    // Extract nutrient coverage data
    const nutrients = new Set();
    const coverage = {};
    
    // Build nutrient sets and coverage data
    fertilizerData.forEach(item => {
        if (item.covers) {
            Object.keys(item.covers).forEach(nutrient => {
                nutrients.add(nutrient);
                
                if (!coverage[item.product]) {
                    coverage[item.product] = {};
                }
                
                // Extract numeric value using regex
                let value = 0;
                const match = item.covers[nutrient].match(/\d+(\.\d+)?/);
                if (match) {
                    value = parseFloat(match[0]);
                }
                
                coverage[item.product][nutrient] = value;
            });
        }
    });
    
    // If we have coverage data, create a stacked bar chart
    if (Object.keys(coverage).length > 0) {
        const nutrientsList = Array.from(nutrients);
        const products = Object.keys(coverage);
        
        // Create datasets for each nutrient
        const datasets = nutrientsList.map(nutrient => {
            return {
                label: nutrient,
                data: products.map(product => coverage[product][nutrient] || 0),
                backgroundColor: getColorForParameter(nutrient),
                borderColor: 'white',
                borderWidth: 1
            };
        });
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: products,
                datasets: datasets
            },
            options: {
                ...chartOptions,
                scales: {
                    x: {
                        stacked: true
                    },
                    y: {
                        stacked: true,
                        title: {
                            display: true,
                            text: 'Amount Covered (kg/ha)'
                        }
                    }
                },
                plugins: {
                    ...chartOptions.plugins,
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 10,
                            usePointStyle: true
                        }
                    }
                }
            }
        });
    } else {
        // Create simple fallback chart if no coverage data exists
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: fertilizerData.map(item => item.product),
                datasets: [{
                    label: 'Recommended Dose',
                    data: fertilizerData.map(item => {
                        const match = item.dose.toString().match(/\d+(\.\d+)?/);
                        return match ? parseFloat(match[0]) : 0;
                    }),
                    backgroundColor: 'rgba(59, 130, 246, 0.7)',
                    borderColor: 'rgb(59, 130, 246)',
                    borderWidth: 1
                }]
            },
            options: chartOptions
        });
    }
} 