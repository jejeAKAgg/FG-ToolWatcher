/* ═══════════════════════════════════════
   TABLE.JS — DataTables rendering
   FG-ToolWatcher Viewer
═══════════════════════════════════════ */

let dataTable = null;

function renderTable(rows) {
    const tbody = document.getElementById('table-body');

    tbody.innerHTML = rows.map(r => {
        const evo = (r['Evolution du prix'] || r['Évolution du prix'] || '-').trim();
        let badgeClass = 'badge-eq';
        if (evo.startsWith('+'))              badgeClass = 'badge-up';
        else if (evo.startsWith('-') && evo !== '-') badgeClass = 'badge-down';

        const soc     = r['Société']    || r['Company']  || '-';
        const ean     = r['EAN']                         || '-';
        const mpn     = r['MPN']                         || '-';
        const brand   = r['Marque']     || r['Brand']    || '-';
        const article = r['Article']                     || '-';
        const p_enr   = r['Prix enreigstré (TVA)'] || r['Prix enregistré (TVA)'] || '-';
        const p_det   = r['Prix détecté (TVA)']    || '-';
        const offres  = r['Offres']                      || '-';
        const verif   = r['Vérifié']    || r['Checked on'] || '-';
        const url     = r['ArticleURL'] || '#';

        const articleCell = url !== '#'
            ? `<a href="${url}" target="_blank" style="color:var(--accent2);text-decoration:none;" title="${article}">${article}</a>`
            : article;

        return `<tr>
            <td><span class="company-badge">${soc}</span></td>
            <td style="font-family:monospace;font-size:11px;color:var(--muted)">${ean}</td>
            <td style="font-family:monospace;font-size:11px;color:var(--muted)">${mpn}</td>
            <td style="color:var(--muted)">${brand}</td>
            <td class="col-article">${articleCell}</td>
            <td>${p_enr}</td>
            <td style="font-weight:700">${p_det}</td>
            <td><span class="badge ${badgeClass}">${evo}</span></td>
            <td><span class="offers-cell" title="${offres}">${offres}</span></td>
            <td style="color:var(--muted);font-size:11px">${verif}</td>
        </tr>`;
    }).join('');

    if (dataTable) {
        dataTable.destroy();
        dataTable = null;
    }

    dataTable = $('#results-table').DataTable({
        pageLength: 25,
        language: {
            search: '',
            searchPlaceholder: '',
            lengthMenu: 'Afficher _MENU_ lignes',
            info: '_START_ à _END_ sur _TOTAL_ résultats',
            paginate: { first: '«', last: '»', next: '›', previous: '‹' },
            emptyTable: 'Aucun résultat disponible',
            zeroRecords: 'Aucun résultat trouvé',
        },
        dom: '<"dt-bottom"lip>',
        searching: false,
        scrollX: false,   // we handle scroll via CSS .table-scroll wrapper
        autoWidth: false,
    });
}

function updateTable(rows) {
    renderTable(rows);
}
