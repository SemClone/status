// Dashboard JavaScript for SEMCL.ONE PyPI Stats

let statsData = null;

// Color palette for charts
const COLORS = [
    '#2563eb', '#3b82f6', '#60a5fa', '#93c5fd',
    '#10b981', '#34d399', '#6ee7b7', '#a7f3d0',
    '#f59e0b', '#fbbf24', '#fcd34d', '#fde68a'
];

// Format number with commas
function formatNumber(num) {
    if (!num) return '0';
    return num.toLocaleString();
}

// Load stats from JSON file
async function loadStats() {
    try {
        const response = await fetch('data/stats.json');

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        statsData = await response.json();

        updateLastUpdated(statsData.last_updated);
        renderSummaryCards(statsData.packages);
        renderTrendsChart(statsData.packages);
        renderPackageDetails(statsData.packages);
        renderPythonVersionsChart(statsData.packages);
        renderSystemsChart(statsData.packages);
    } catch (error) {
        console.error('Error loading stats:', error);
        const errorMsg = `Error loading statistics: ${error.message}. Please check the browser console for details.`;
        document.getElementById('summaryCards').innerHTML =
            `<p style="color: red;">${errorMsg}</p>`;
    }
}

// Update last updated timestamp
function updateLastUpdated(timestamp) {
    const date = new Date(timestamp);
    const formatted = date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        timeZoneName: 'short'
    });
    const dateOnly = date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
    document.getElementById('lastUpdated').textContent = `Last updated: ${formatted}`;
    document.getElementById('footerUpdated').textContent = `Updated on ${dateOnly}`;
}

// Render summary cards
function renderSummaryCards(packages) {
    const container = document.getElementById('summaryCards');
    let html = '';

    for (const [pkgName, pkgData] of Object.entries(packages)) {
        const recent = pkgData.recent?.data || {};
        const lastDay = recent.last_day || 0;
        const lastWeek = recent.last_week || 0;
        const lastMonth = recent.last_month || 0;

        html += `
            <div class="package-card">
                <h3><a href="https://pypi.org/project/${pkgName}/" target="_blank">${pkgName}</a></h3>
                <div class="stat-row">
                    <span class="stat-label">Last Day:</span>
                    <span class="stat-value">${formatNumber(lastDay)}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Last Week:</span>
                    <span class="stat-value">${formatNumber(lastWeek)}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Last Month:</span>
                    <span class="stat-value">${formatNumber(lastMonth)}</span>
                </div>
            </div>
        `;
    }

    container.innerHTML = html;
}

// Render download trends chart
function renderTrendsChart(packages) {
    const ctx = document.getElementById('trendsChart').getContext('2d');

    // Prepare datasets for each package
    const datasets = [];
    let allDates = new Set();

    Object.entries(packages).forEach(([pkgName, pkgData], index) => {
        const overall = pkgData.overall?.data || [];

        // Filter out data with mirrors and collect dates
        const dataPoints = overall
            .filter(d => !d.category || d.category === 'without_mirrors')
            .map(d => {
                allDates.add(d.date);
                return {
                    x: d.date,
                    y: d.downloads || 0
                };
            })
            .sort((a, b) => a.x.localeCompare(b.x));

        if (dataPoints.length > 0) {
            datasets.push({
                label: pkgName,
                data: dataPoints,
                borderColor: COLORS[index % COLORS.length],
                backgroundColor: COLORS[index % COLORS.length] + '20',
                borderWidth: 2,
                tension: 0.1,
                fill: false
            });
        }
    });

    new Chart(ctx, {
        type: 'line',
        data: { datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'day',
                        displayFormats: {
                            day: 'MMM d'
                        }
                    },
                    title: {
                        display: true,
                        text: 'Date'
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Downloads'
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + formatNumber(context.parsed.y);
                        }
                    }
                }
            }
        }
    });
}

// Render package details section
function renderPackageDetails(packages) {
    const container = document.getElementById('packageDetails');
    let html = '';

    for (const [pkgName, pkgData] of Object.entries(packages)) {
        const recent = pkgData.recent?.data || {};

        html += `
            <div class="package-detail">
                <h3>${pkgName}</h3>
                <div class="stats-grid">
                    <div class="stat-row">
                        <span class="stat-label">Last Day:</span>
                        <span class="stat-value">${formatNumber(recent.last_day)}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Last Week:</span>
                        <span class="stat-value">${formatNumber(recent.last_week)}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Last Month:</span>
                        <span class="stat-value">${formatNumber(recent.last_month)}</span>
                    </div>
                </div>
            </div>
        `;
    }

    container.innerHTML = html;
}

// Render Python versions chart
function renderPythonVersionsChart(packages) {
    const ctx = document.getElementById('pythonVersionsChart').getContext('2d');

    // Aggregate Python version data across all packages
    const versionTotals = {};

    Object.values(packages).forEach(pkgData => {
        const pythonData = pkgData.python_versions?.data || [];
        pythonData.forEach(item => {
            if (item.category && item.category !== 'null') {
                versionTotals[item.category] = (versionTotals[item.category] || 0) + (item.downloads || 0);
            }
        });
    });

    // Sort by version and take top 10
    const sortedVersions = Object.entries(versionTotals)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10);

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: sortedVersions.map(v => v[0]),
            datasets: [{
                label: 'Downloads by Python Version',
                data: sortedVersions.map(v => v[1]),
                backgroundColor: COLORS,
                borderColor: COLORS.map(c => c),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Total Downloads'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Python Version'
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return 'Downloads: ' + formatNumber(context.parsed.y);
                        }
                    }
                }
            }
        }
    });
}

// Render operating systems chart
function renderSystemsChart(packages) {
    const ctx = document.getElementById('systemsChart').getContext('2d');

    // Aggregate system data across all packages
    const systemTotals = {};

    Object.values(packages).forEach(pkgData => {
        const systemData = pkgData.system?.data || [];
        systemData.forEach(item => {
            if (item.category && item.category !== 'null') {
                systemTotals[item.category] = (systemTotals[item.category] || 0) + (item.downloads || 0);
            }
        });
    });

    const sortedSystems = Object.entries(systemTotals)
        .sort((a, b) => b[1] - a[1]);

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: sortedSystems.map(s => s[0]),
            datasets: [{
                data: sortedSystems.map(s => s[1]),
                backgroundColor: COLORS,
                borderColor: '#ffffff',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = formatNumber(context.parsed);
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((context.parsed / total) * 100).toFixed(1);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// Load stats when page loads
document.addEventListener('DOMContentLoaded', loadStats);
