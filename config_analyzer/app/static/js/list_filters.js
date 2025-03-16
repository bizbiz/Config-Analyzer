function initListFilter(searchInputId, tableId, columnsCount) {
    const input = document.getElementById(searchInputId);
    
    if (!input) return;  // Garde-fou si l'élément n'existe pas
    
    input.addEventListener('keyup', function() {
        const filter = this.value.toLowerCase();
        const rows = document.querySelectorAll(`#${tableId} tbody tr`);
        
        rows.forEach(row => {
            let match = false;
            for (let i = 0; i < columnsCount; i++) {
                const cell = row.cells[i];
                if (cell?.textContent.toLowerCase().includes(filter)) {
                    match = true;
                    break;
                }
            }
            row.style.display = match ? '' : 'none';
        });
    });
}

// Initialisation automatique pour les tables avec data-attributes
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('[data-list-filter]').forEach(table => {
        const inputId = table.dataset.filterInput;
        const columnsCount = parseInt(table.dataset.filterColumns, 10);
        initListFilter(inputId, table.id, columnsCount);
    });
});
