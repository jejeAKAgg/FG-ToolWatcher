/* ═══════════════════════════════════════
   MAIN.JS — Entry point & CSV loading
   FG-ToolWatcher Viewer
═══════════════════════════════════════ */

const CSV_PATH = '/api/results';

let allRows = [];
let activeFilter = 'all';

// ── Boot ──
document.addEventListener('DOMContentLoaded', () => {
    Papa.parse(CSV_PATH, {
        download: true,
        header: true,
        skipEmptyLines: true,
        complete: (results) => {
            allRows = results.data;
            // DEBUG — ouvre la console navigateur (F12) pour voir
            console.log("Headers lus par PapaParse:", Object.keys(results.data[0]));
            console.log("Première ligne:", results.data[0]);
            init();
        },
        error: () => {
            document.getElementById('loading').innerHTML = `
                <div style="text-align:center;color:#6b7280">
                    <div style="font-family:'Bebas Neue';font-size:32px;letter-spacing:2px;margin-bottom:12px;color:#2a2d35">
                        AUCUN RÉSULTAT
                    </div>
                    <p style="font-size:14px">Lancez d'abord une session de surveillance depuis FG-ToolWatcher.</p>
                </div>`;
        }
    });
});

function init() {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('app').style.display = 'block';

    // Meta
    const dates = allRows.map(r => r['Vérifié'] || r['Checked on'] || '').filter(Boolean);
    if (dates.length) document.getElementById('last-updated').textContent = dates[dates.length - 1];
    document.getElementById('result-count').textContent = `${allRows.length} résultats`;

    // Modules
    updateStats(allRows);
    renderTable(allRows);
    renderCharts(allRows);

    // Search
    document.getElementById('custom-search').addEventListener('input', function () {
        const q = this.value.toLowerCase();
        const filtered = getFilteredRows().filter(r =>
            Object.values(r).some(v => String(v).toLowerCase().includes(q))
        );
        updateTable(filtered);
    });

    // Filter buttons
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            activeFilter = this.dataset.filter;
            const q = document.getElementById('custom-search').value.toLowerCase();
            const filtered = getFilteredRows().filter(r =>
                !q || Object.values(r).some(v => String(v).toLowerCase().includes(q))
            );
            updateTable(filtered);
        });
    });
}

function getFilteredRows() {
    if (activeFilter === 'all') return allRows;
    return allRows.filter(r => {
        const evo = (r['Evolution du prix'] || r['Évolution du prix'] || '').trim();
        if (activeFilter === 'up')   return evo.startsWith('+');
        if (activeFilter === 'down') return evo.startsWith('-') && evo !== '-';
        if (activeFilter === 'eq')   return evo === '=';
        return true;
    });
}
