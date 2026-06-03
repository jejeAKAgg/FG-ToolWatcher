/* ═══════════════════════════════════════
   STATS.JS — Stat cards
   FG-ToolWatcher Viewer
═══════════════════════════════════════ */

function updateStats(rows) {
    let up = 0, down = 0, eq = 0;
    const suppliers = new Set();

    rows.forEach(r => {
        const evo = (r['Evolution du prix'] || r['Évolution du prix'] || '').trim();
        const soc = r['Société'] || r['Company'] || '';
        if (soc) suppliers.add(soc);
        if (evo.startsWith('+'))              up++;
        else if (evo.startsWith('-') && evo !== '-') down++;
        else if (evo === '=')                 eq++;
    });

    document.getElementById('stat-total').textContent     = rows.length;
    document.getElementById('stat-up').textContent        = up;
    document.getElementById('stat-down').textContent      = down;
    document.getElementById('stat-eq').textContent        = eq;
    document.getElementById('stat-suppliers').textContent = suppliers.size;
}
