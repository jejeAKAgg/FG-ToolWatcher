/* ═══════════════════════════════════════
   CHARTS.JS — Chart.js visualizations
   FG-ToolWatcher Viewer
═══════════════════════════════════════ */

const CHART_COLORS = ['#2ecc71','#3498db','#e74c3c','#f39c12','#9b59b6','#1abc9c','#e67e22'];

let chartEvolution = null;
let chartSuppliers = null;

function renderCharts(rows) {
    _renderSuppliersChart(rows);
    _renderEvolutionChart(rows);
}

function _renderSuppliersChart(rows) {
    const counts = {};
    rows.forEach(r => {
        const s = r['Société'] || r['Company'] || 'Inconnu';
        counts[s] = (counts[s] || 0) + 1;
    });

    const ctx = document.getElementById('chart-suppliers').getContext('2d');
    if (chartSuppliers) chartSuppliers.destroy();

    chartSuppliers = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(counts),
            datasets: [{
                data: Object.values(counts),
                backgroundColor: CHART_COLORS,
                borderColor: '#16181c',
                borderWidth: 3,
                hoverOffset: 6,
            }]
        },
        options: {
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: '#6b7280',
                        font: { family: 'DM Sans', size: 12 },
                        padding: 16,
                        usePointStyle: true,
                    }
                }
            }
        }
    });
}

function _renderEvolutionChart(rows) {
    const evo = {};
    rows.forEach(r => {
        const s = r['Société'] || r['Company'] || 'Inconnu';
        if (!evo[s]) evo[s] = { up: 0, down: 0, eq: 0 };
        const e = (r['Evolution du prix'] || r['Évolution du prix'] || '-').trim();
        if (e.startsWith('+'))              evo[s].up++;
        else if (e.startsWith('-') && e !== '-') evo[s].down++;
        else                                evo[s].eq++;
    });

    const labels = Object.keys(evo);
    const ctx = document.getElementById('chart-evolution').getContext('2d');
    if (chartEvolution) chartEvolution.destroy();

    chartEvolution = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [
                {
                    label: '↑ Hausse',
                    data: labels.map(s => evo[s].up),
                    backgroundColor: 'rgba(231,76,60,0.75)',
                    borderRadius: 4,
                },
                {
                    label: '↓ Baisse',
                    data: labels.map(s => evo[s].down),
                    backgroundColor: 'rgba(46,204,113,0.75)',
                    borderRadius: 4,
                },
                {
                    label: '= Stable',
                    data: labels.map(s => evo[s].eq),
                    backgroundColor: 'rgba(107,114,128,0.4)',
                    borderRadius: 4,
                }
            ]
        },
        options: {
            plugins: {
                legend: {
                    labels: { color: '#6b7280', font: { family: 'DM Sans', size: 12 }, usePointStyle: true }
                }
            },
            scales: {
                x: {
                    ticks: { color: '#6b7280', font: { family: 'DM Sans' } },
                    grid: { color: '#2a2d35' }
                },
                y: {
                    ticks: { color: '#6b7280', font: { family: 'DM Sans' } },
                    grid: { color: '#2a2d35' },
                    beginAtZero: true
                }
            }
        }
    });
}
