// Chart instances
let commodityDistributionChart = null;
let marketComparisonChart = null;
let priceRangesChart = null;
let varietyPriceRangeChart = null;
let marketMinMaxChart = null;

// Function to show error message
function showError(message, isFatal = false) {
    const errorDiv = document.getElementById('error-message');
    if (!errorDiv) {
        const div = document.createElement('div');
        div.id = 'error-message';
        div.className = 'bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4';
        div.innerHTML = `
            <strong class="font-bold">Error!</strong>
            <span class="block sm:inline">${message}</span>
            ${isFatal ? '<button class="absolute top-0 bottom-0 right-0 px-4 py-3" onclick="this.parentElement.remove()">×</button>' : ''}
        `;
        document.querySelector('.container').insertBefore(div, document.querySelector('.container').firstChild);
    } else {
        errorDiv.innerHTML = `
            <strong class="font-bold">Error!</strong>
            <span class="block sm:inline">${message}</span>
            ${isFatal ? '<button class="absolute top-0 bottom-0 right-0 px-4 py-3" onclick="this.parentElement.remove()">×</button>' : ''}
        `;
    }
}

// Function to show loading state
function showLoading(show = true) {
    const loadingDiv = document.getElementById('loading-indicator');
    if (show) {
        if (!loadingDiv) {
            const div = document.createElement('div');
            div.id = 'loading-indicator';
            div.className = 'fixed top-0 left-0 w-full h-full bg-gray-900 bg-opacity-50 flex items-center justify-center z-50';
            div.innerHTML = `
                <div class="bg-white p-4 rounded-lg shadow-lg">
                    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
                    <p class="mt-2 text-gray-700">Loading data...</p>
                </div>
            `;
            document.body.appendChild(div);
        }
    } else if (loadingDiv) {
        loadingDiv.remove();
    }
}

// Function to update filter options
function updateFilterOptions(data) {
    try {
        const commodities = [...new Set(data.table_data.map(item => item.commodity))];
        const markets = [...new Set(data.table_data.map(item => item.market))];

        const commoditySelect = document.getElementById('commodity-filter');
        const marketSelect = document.getElementById('market-filter');
        const selectedCommodity = commoditySelect?.value || '';
        const selectedMarket = marketSelect?.value || '';

        if (commoditySelect) {
            commoditySelect.innerHTML = '<option value="">Available Commodities</option>' +
                commodities.map(c => `<option value="${c}"${selectedCommodity === c ? ' selected' : ''}>${c}</option>`).join('');
        }

        if (marketSelect) {
            marketSelect.innerHTML = '<option value="">All Nearest Markets</option>' +
                markets.map(m => `<option value="${m}"${selectedMarket === m ? ' selected' : ''}>${m}</option>`).join('');
        }
    } catch (error) {
        console.error('Error updating filter options:', error);
        showError('Failed to update filter options');
    }
}

// Function to load nearest districts
async function loadNearestDistricts() {
    try {
        showLoading(true);
        const response = await fetch('/api/advance-mandi/nearest-districts');

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to load nearest districts');
        }

        const data = await response.json();

        if (!data || !Array.isArray(data)) {
            throw new Error('Invalid data received from server');
        }

        // Update nearest districts info
        const districtsList = document.getElementById('nearest-districts');
        if (districtsList) {
            districtsList.innerHTML = data.map(district => `
                <div class="bg-white p-4 rounded-lg shadow hover:shadow-lg transition-shadow">
                    <h3 class="font-semibold text-lg text-gray-800">${district.district_name}</h3>
                    <p class="text-gray-600">${district.state_name}</p>
                    <p class="text-blue-600 font-medium">${district.distance ? district.distance.toFixed(2) : 'N/A'} km</p>
                </div>
            `).join('');
        }

        return data;
    } catch (error) {
        console.error('Error loading nearest districts:', error);
        showError(error.message, true);
        return null;
    } finally {
        showLoading(false);
    }
}

// Function to load mandi data
async function loadMandiData() {
    try {
        showLoading(true);
        const commodity = document.getElementById('commodity-filter')?.value || '';
        const market = document.getElementById('market-filter')?.value || '';

        const response = await fetch(`/api/advance-mandi/district-data?commodity=${commodity}&market=${market}`);

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to load mandi data');
        }

        const data = await response.json();

        if (!data || typeof data !== 'object') {
            throw new Error('Invalid data received from server');
        }

        // Update charts based on filters
        updateCharts(data, commodity, market);

        // Update data table
        if (data.table_data) {
            updateDataTable(data.table_data);
        }

        // Update filter options
        if (data.table_data) {
            updateFilterOptions(data);
        }

        return data;
    } catch (error) {
        console.error('Error loading mandi data:', error);
        showError(error.message);
        return null;
    } finally {
        showLoading(false);
    }
}

// Function to update charts and table based on filters
function updateCharts(data, commodity, market) {
    // Hide all chart containers first
    const pieContainer = document.getElementById('commodity-distribution-chart-container');
    const marketCompContainer = document.getElementById('market-comparison-chart')?.parentElement?.parentElement;
    const priceRangesContainer = document.getElementById('price-ranges-chart')?.parentElement?.parentElement;
    // Custom containers for new charts
    let varietyPriceRangeContainer = document.getElementById('variety-price-range-container');
    if (!varietyPriceRangeContainer) {
        varietyPriceRangeContainer = document.createElement('div');
        varietyPriceRangeContainer.id = 'variety-price-range-container';
        varietyPriceRangeContainer.className = 'bg-white rounded-lg shadow-md p-6 w-full mb-8';
        varietyPriceRangeContainer.style.display = 'none';
        varietyPriceRangeContainer.innerHTML = `
            <h3 class="text-xl font-semibold text-gray-800 mb-4">Price Range by Variety</h3>
            <div class="w-full h-96"><canvas id="variety-price-range-chart"></canvas></div>
        `;
        // Insert after priceRangesContainer
        priceRangesContainer?.parentNode?.insertBefore(varietyPriceRangeContainer, priceRangesContainer?.nextSibling);
    }
    // Hide all
    if (pieContainer) pieContainer.style.display = 'none';
    if (marketCompContainer) marketCompContainer.style.display = 'none';
    if (priceRangesContainer) priceRangesContainer.style.display = 'none';
    if (varietyPriceRangeContainer) varietyPriceRangeContainer.style.display = 'none';

    // 1. Both filters are all: show pie, price ranges by commodity, table
    if (!commodity && !market) {
        if (pieContainer) pieContainer.style.display = 'block';
        if (priceRangesContainer) priceRangesContainer.style.display = 'block';
        // Hide others
    }
    // 2. Commodity selected: show market price comparison, price range by variety, table
    else if (commodity && !market) {
        if (marketCompContainer) marketCompContainer.style.display = 'block';
        if (varietyPriceRangeContainer) varietyPriceRangeContainer.style.display = 'block';
        // Hide others
    }
    // 3. Market selected: show pie, price ranges by commodity, min/max price bar chart for market, table
    else if (!commodity && market) {
        if (pieContainer) pieContainer.style.display = 'block';
        if (priceRangesContainer) priceRangesContainer.style.display = 'block';
        // Show min/max price bar chart for market (reuse marketCompContainer for this)
        if (marketCompContainer) marketCompContainer.style.display = 'block';
    }
    // 4. Both selected: treat as commodity selected (show marketComp and variety price range)
    else if (commodity && market) {
        if (marketCompContainer) marketCompContainer.style.display = 'block';
        if (varietyPriceRangeContainer) varietyPriceRangeContainer.style.display = 'block';
    }

    // Update charts
    if (!commodity && !market) {
        updateCommodityDistributionChart(data.commodity_distribution);
        updatePriceRangesChart(data.price_ranges);
    } else if (commodity && !market) {
        updateMarketComparisonChart(data.market_comparison);
        updateVarietyPriceRangeChart(data.table_data, commodity);
    } else if (!commodity && market) {
        updateCommodityDistributionChart(data.commodity_distribution);
        updatePriceRangesChart(data.price_ranges);
        updateMarketMinMaxChart(data.table_data, market);
    } else if (commodity && market) {
        updateMarketComparisonChart(data.market_comparison);
        updateVarietyPriceRangeChart(data.table_data, commodity);
    }
}

// Function to update data table
let currentPage = 1;
const rowsPerPage = 10;
let allMandiData = [];

function updateDataTable(data) {
    allMandiData = data;
    currentPage = 1;
    renderMandiTable();
}

function renderMandiTable() {
    const tbody = document.getElementById('mandi-data-table');
    tbody.innerHTML = '';

    const startIndex = (currentPage - 1) * rowsPerPage;
    const endIndex = Math.min(startIndex + rowsPerPage, allMandiData.length);
    const pageData = allMandiData.slice(startIndex, endIndex);

    document.getElementById('startIndex').textContent = allMandiData.length === 0 ? 0 : startIndex + 1;
    document.getElementById('endIndex').textContent = endIndex;
    document.getElementById('totalItems').textContent = allMandiData.length;

    pageData.forEach(item => {
        const row = document.createElement('tr');
        row.className = "hover:bg-gray-50";
        row.innerHTML = `
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${item.market}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${item.commodity}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${item.variety || '-'}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${item.grade || '-'}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">₹${item.min_price}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">₹${item.max_price}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">₹${item.modal_price}</td>
        `;
        tbody.appendChild(row);
    });

    updatePageNumbers();
    document.getElementById('prevPageBtn').disabled = currentPage === 1;
    document.getElementById('nextPageBtn').disabled = currentPage >= Math.ceil(allMandiData.length / rowsPerPage);
}

function updatePageNumbers() {
    const totalPages = Math.ceil(allMandiData.length / rowsPerPage);
    const pageNumbersContainer = document.getElementById('pageNumbers');
    pageNumbersContainer.innerHTML = '';

    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(totalPages, startPage + 4);
    if (endPage - startPage < 4) startPage = Math.max(1, endPage - 4);

    if (startPage > 1) {
        addPageNumber(1);
        if (startPage > 2) addEllipsis();
    }

    for (let i = startPage; i <= endPage; i++) {
        addPageNumber(i);
    }

    if (endPage < totalPages) {
        if (endPage < totalPages - 1) addEllipsis();
        addPageNumber(totalPages);
    }
}

function addPageNumber(pageNum) {
    const container = document.getElementById('pageNumbers');
    const btn = document.createElement('button');
    btn.className = `px-3 py-1 text-sm border rounded ${pageNum === currentPage ? 'bg-green-200 border-green-500 text-green-700' : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'}`;
    btn.textContent = pageNum;
    btn.addEventListener('click', () => {
        currentPage = pageNum;
        renderMandiTable();
    });
    container.appendChild(btn);
}

function addEllipsis() {
    const container = document.getElementById('pageNumbers');
    const span = document.createElement('span');
    span.className = 'px-3 py-1 text-sm text-gray-500';
    span.textContent = '...';
    container.appendChild(span);
}

document.getElementById('prevPageBtn').addEventListener('click', () => {
    if (currentPage > 1) {
        currentPage--;
        renderMandiTable();
    }
});

document.getElementById('nextPageBtn').addEventListener('click', () => {
    const totalPages = Math.ceil(allMandiData.length / rowsPerPage);
    if (currentPage < totalPages) {
        currentPage++;
        renderMandiTable();
    }
});

// Utility: Dynamically set chart canvas height based on data
function setResponsiveChartHeight(canvas, labels, baseHeight = 350, perLabel = 30, minHeight = 350, maxHeight = 700) {
    if (!canvas) return;
    let height = baseHeight;
    if (labels && labels.length) {
        height = Math.max(minHeight, Math.min(maxHeight, baseHeight + (labels.length - 8) * perLabel));
    }
    // canvas.parentElement.style.height = height + 'px';
    // canvas.height = height;
}

// Function to update commodity distribution chart
function updateCommodityDistributionChart(data) {
    try {
        const container = document.getElementById('commodity-distribution-chart-container');
        const canvas = document.getElementById('commodity-distribution-chart');
        if (!canvas || !container) {
            console.warn('Commodity distribution chart canvas/container not found');
            return;
        }
        setResponsiveChartHeight(canvas, data.labels, 350, 25, 300, 600);
        // Center the chart vertically and horizontally
        container.style.display = 'flex';
        container.style.flexDirection = 'column';
        container.style.alignItems = 'center';
        container.style.justifyContent = 'center';
        // Chart area
        const chartArea = canvas.parentElement;
        chartArea.style.display = 'flex';
        chartArea.style.alignItems = 'center';
        chartArea.style.justifyContent = 'center';
        chartArea.style.width = '100%';
        chartArea.style.height = '100%';
        // Destroy existing chart if it exists
        if (commodityDistributionChart) {
            commodityDistributionChart.destroy();
        }
        commodityDistributionChart = new Chart(canvas.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: data.labels,
                datasets: [{
                    data: data.data,
                    backgroundColor: [
                        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40',
                        '#8BC34A', '#E91E63', '#00BCD4', '#FFC107', '#9C27B0', '#CDDC39', '#FF5722', '#607D8B', '#795548'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { font: { size: 13 } }
                    },
                    title: {
                        display: true,
                        // text: 'Commodity Distribution',
                        font: { size: 18 }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error updating commodity distribution chart:', error);
    }
}

// Function to update market comparison chart
function updateMarketComparisonChart(data) {
    try {
        const canvas = document.getElementById('market-comparison-chart');
        if (!canvas) {
            console.warn('Market comparison chart canvas not found');
            return;
        }
        // Destroy both possible charts using this canvas
        if (marketComparisonChart) {
            marketComparisonChart.destroy();
            marketComparisonChart = null;
        }
        if (marketMinMaxChart) {
            marketMinMaxChart.destroy();
            marketMinMaxChart = null;
        }
        setResponsiveChartHeight(canvas, data.labels, 350, 30, 300, 800);
        const ctx = canvas.getContext('2d');
        marketComparisonChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Average Price',
                    data: data.data,
                    backgroundColor: '#36A2EB',
                    borderColor: '#2196F3',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    title: {
                        display: true,
                        text: 'Market Price Comparison',
                        font: { size: 18 }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Price (₹/Quintal)',
                            font: { size: 13 }
                        }
                    },
                    x: {
                        ticks: {
                            maxRotation: 45,
                            minRotation: 45,
                            autoSkip: false
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error updating market comparison chart:', error);
    }
}

// Function to update price ranges chart
function updatePriceRangesChart(data) {
    try {
        const canvas = document.getElementById('price-ranges-chart');
        if (!canvas) {
            console.warn('Price ranges chart canvas not found');
            return;
        }
        setResponsiveChartHeight(canvas, data.labels, 350, 30, 300, 800);
        const ctx = canvas.getContext('2d');
        if (priceRangesChart) {
            priceRangesChart.destroy();
        }
        const datasets = [{
            label: 'Price Range',
            data: data.labels.map((label, index) => ({
                x: label,
                y: data.data[index].avg,
                min: data.data[index].min,
                max: data.data[index].max
            })),
            backgroundColor: 'rgba(54, 162, 235, 0.5)',
            borderColor: 'rgb(54, 162, 235)',
            borderWidth: 1
        }];
        priceRangesChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Price Ranges by Commodity',
                        font: { size: 18 }
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                const data = context.dataset.data[context.dataIndex];
                                return [
                                    `Average: ₹${data.y}`,
                                    `Min: ₹${data.min}`,
                                    `Max: ₹${data.max}`
                                ];
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Price (₹/Quintal)',
                            font: { size: 13 }
                        }
                    },
                    x: {
                        ticks: {
                            maxRotation: 45,
                            minRotation: 45,
                            autoSkip: false
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error updating price ranges chart:', error);
    }
}

// New: Price range by variety (min/max bars)
function updateVarietyPriceRangeChart(tableData, commodity) {
    const canvas = document.getElementById('variety-price-range-chart');
    if (!canvas) return;
    // Filter for selected commodity
    const filtered = tableData.filter(row => row.commodity === commodity);
    const varieties = [...new Set(filtered.map(row => row.variety || 'Unknown'))];
    const minPrices = varieties.map(v => {
        const rows = filtered.filter(row => (row.variety || 'Unknown') === v);
        return Math.min(...rows.map(r => r.min_price));
    });
    const maxPrices = varieties.map(v => {
        const rows = filtered.filter(row => (row.variety || 'Unknown') === v);
        return Math.max(...rows.map(r => r.max_price));
    });
    setResponsiveChartHeight(canvas, varieties, 350, 30, 300, 800);
    const ctx = canvas.getContext('2d');
    if (varietyPriceRangeChart) varietyPriceRangeChart.destroy();
    varietyPriceRangeChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: varieties,
            datasets: [
                { label: 'Min Price', data: minPrices, backgroundColor: '#4BC0C0' },
                { label: 'Max Price', data: maxPrices, backgroundColor: '#FF6384' }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: { display: true, text: `Price Range by Variety for ${commodity}`, font: { size: 18 } },
                tooltip: { mode: 'index', intersect: false }
            },
            scales: {
                y: { beginAtZero: true, title: { display: true, text: 'Price (₹/Quintal)', font: { size: 13 } } },
                x: { ticks: { maxRotation: 45, minRotation: 45, autoSkip: false } }
            }
        }
    });
}

// Function to update min/max price bar chart for selected market
function updateMarketMinMaxChart(tableData, market) {
    const canvas = document.getElementById('market-comparison-chart');
    if (!canvas) return;
    // Destroy both possible charts using this canvas
    if (marketComparisonChart) {
        marketComparisonChart.destroy();
        marketComparisonChart = null;
    }
    if (marketMinMaxChart) {
        marketMinMaxChart.destroy();
        marketMinMaxChart = null;
    }
    // Filter for selected market
    const filtered = tableData.filter(row => row.market === market);
    const commodities = [...new Set(filtered.map(row => row.commodity))];
    const minPrices = commodities.map(c => {
        const rows = filtered.filter(row => row.commodity === c);
        return Math.min(...rows.map(r => r.min_price));
    });
    const maxPrices = commodities.map(c => {
        const rows = filtered.filter(row => row.commodity === c);
        return Math.max(...rows.map(r => r.max_price));
    });
    setResponsiveChartHeight(canvas, commodities, 350, 30, 300, 800);
    const ctx = canvas.getContext('2d');
    marketMinMaxChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: commodities,
            datasets: [
                { label: 'Min Price', data: minPrices, backgroundColor: '#4BC0C0' },
                { label: 'Max Price', data: maxPrices, backgroundColor: '#FF6384' }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: { display: true, text: `Min/Max Price by Commodity in ${market}`, font: { size: 18 } },
                tooltip: { mode: 'index', intersect: false }
            },
            scales: {
                y: { beginAtZero: true, title: { display: true, text: 'Price (₹/Quintal)', font: { size: 13 } } },
                x: { ticks: { maxRotation: 45, minRotation: 45, autoSkip: false } }
            }
        }
    });
}

// Initialize the page
document.addEventListener('DOMContentLoaded', async () => {
    try {
        // Load initial data
        const districts = await loadNearestDistricts();
        if (districts) {
            await loadMandiData();
        }

        // Set up filter button
        const filterButton = document.getElementById('apply-filters');
        if (filterButton) {
            filterButton.addEventListener('click', loadMandiData);
        }
    } catch (error) {
        console.error('Error initializing page:', error);
        showError('Failed to initialize page', true);
    }
}); 