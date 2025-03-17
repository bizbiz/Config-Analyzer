// Indicateur global pour éviter les initialisations multiples
window.initializedTables = window.initializedTables || {};

/**
 * Filtre des éléments dans un tableau
 * @param {string} inputId - ID du champ de recherche
 * @param {string} tableId - ID du tableau à filtrer
 * @param {number} columnsCount - Nombre de colonnes à considérer pour la recherche
 */
function filterItems(inputId, tableId, columnsCount) {
    const input = document.getElementById(inputId);
    
    if (!input) return;  // Garde-fou si l'élément n'existe pas
    
    const filter = input.value.toLowerCase();
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
}

/**
 * Initialise un filtre de recherche sur un tableau
 * @param {string} tableId - ID du tableau à filtrer
 * @param {string} inputId - ID du champ de recherche
 * @param {Array} columnIndexes - Indices des colonnes à rechercher (si vide, toutes les colonnes sauf la dernière)
 * @param {string} rowSelector - Sélecteur pour les lignes à filtrer
 */
function initTableSearch(tableId, inputId, columnIndexes = [], rowSelector = 'tbody tr') {
    // Éviter l'initialisation multiple
    if (window.initializedTables[tableId + '_' + inputId]) {
        console.log(`Table ${tableId} already initialized with input ${inputId}`);
        return;
    }
    
    const searchInput = document.getElementById(inputId);
    const table = document.getElementById(tableId);
    
    if (!searchInput || !table) {
        console.error(`Missing elements for search initialization: ${!searchInput ? 'Input not found' : 'Table not found'}`);
        return;
    }
    
    searchInput.addEventListener('keyup', function() {
        const filter = this.value.toLowerCase();
        const rows = table.querySelectorAll(rowSelector);
        
        rows.forEach(row => {
            let match = false;
            
            // Si aucun index de colonne n'est spécifié, recherche dans toutes les colonnes sauf la dernière
            const indexes = columnIndexes.length > 0 ? columnIndexes : 
                            Array.from({length: row.cells.length - 1}, (_, i) => i);
            
            for (let i of indexes) {
                if (row.cells[i] && row.cells[i].textContent.toLowerCase().includes(filter)) {
                    match = true;
                    break;
                }
            }
            
            row.style.display = match ? '' : 'none';
        });
    });
    
    // Marquer cette table comme initialisée
    window.initializedTables[tableId + '_' + inputId] = true;
    console.log(`Successfully initialized search for table ${tableId}`);
}

// Initialisation automatique pour les tables avec data-attributes
document.addEventListener('DOMContentLoaded', function() {
    console.log("Searching for tables with data-list-filter attribute...");
    const tables = document.querySelectorAll('[data-list-filter]');
    console.log(`Found ${tables.length} tables to initialize`);
    
    tables.forEach(table => {
        const inputId = table.dataset.filterInput;
        const columnsCount = parseInt(table.dataset.filterColumns, 10);
        console.log(`Initializing table #${table.id} with input #${inputId} and ${columnsCount} columns`);
        
        const indexes = Array.from({ length: columnsCount }, (_, i) => i);
        initTableSearch(table.id, inputId, indexes);
    });
});