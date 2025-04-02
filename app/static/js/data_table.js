// config_analyzer/app/static/js/data_table.js

function initTableSearch(tableId, inputId, filterColumns = 3, rowSelector = 'tbody tr') {
    console.log(`Initializing search for table: ${tableId}, input: ${inputId}`);
    
    // S'assurer que cette fonction n'est appelée qu'une fois que le DOM est chargé
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            setupSearch(tableId, inputId, filterColumns, rowSelector);
            setupSorting(tableId);
        });
    } else {
        setupSearch(tableId, inputId, filterColumns, rowSelector);
        setupSorting(tableId);
    }
}

function setupSearch(tableId, inputId, filterColumns, rowSelector) {
    // Obtenir les éléments du DOM
    const table = document.getElementById(tableId);
    const searchInput = document.getElementById(inputId);
    
    if (!table) {
        console.error(`Table not found: #${tableId}`);
        return;
    }
    
    if (!searchInput) {
        console.error(`Search input not found: #${inputId}`);
        return;
    }
    
    console.log(`Table and search input found, setting up event listener`);
    
    // Stocker toutes les lignes d'origine pour référence
    const tbody = table.querySelector('tbody');
    if (!tbody) {
        console.error(`Tbody not found in table #${tableId}`);
        return;
    }
    
    const originalRows = Array.from(tbody.querySelectorAll(rowSelector || 'tr'));
    console.log(`Found ${originalRows.length} rows in table #${tableId}`);
    
    if (originalRows.length === 0) {
        console.warn(`No rows found in table #${tableId}`);
        return;
    }
    
    // Ajouter l'écouteur d'événement pour le champ de recherche
    searchInput.addEventListener('input', function() {
        const searchText = this.value.toLowerCase().trim();
        console.log(`Search input changed: "${searchText}"`);
        
        let matchCount = 0;
        
        originalRows.forEach(row => {
            let found = false;
            
            // Si searchText est vide, afficher toutes les lignes
            if (searchText === '') {
                found = true;
            } else {
                // Récupérer toutes les cellules sauf la dernière (actions)
                const cells = Array.from(row.cells);
                const cellsToSearch = cells.slice(0, Math.min(cells.length - 1, filterColumns));
                
                for (const cell of cellsToSearch) {
                    if (cell.textContent.toLowerCase().includes(searchText)) {
                        found = true;
                        break;
                    }
                }
            }
            
            // Afficher ou masquer la ligne
            row.style.display = found ? '' : 'none';
            if (found) matchCount++;
        });
        
        console.log(`Search results: ${matchCount} matches out of ${originalRows.length} rows`);
    });
    
    console.log(`Search functionality successfully set up for table #${tableId}`);
}

// Nouvelle fonction pour configurer le tri
function setupSorting(tableId) {
    const table = document.getElementById(tableId);
    if (!table) {
        console.error(`Table not found: #${tableId}`);
        return;
    }
    
    const thead = table.querySelector('thead');
    if (!thead) {
        console.error(`Thead not found in table #${tableId}`);
        return;
    }
    
    const tbody = table.querySelector('tbody');
    if (!tbody) {
        console.error(`Tbody not found in table #${tableId}`);
        return;
    }
    
    console.log(`Setting up sorting for table: ${tableId}`);
    
    // Trouver toutes les en-têtes triables
    const sortableHeaders = thead.querySelectorAll('.sortable-header');
    console.log(`Found ${sortableHeaders.length} sortable headers`);
    
    if (sortableHeaders.length === 0) {
        console.warn(`No sortable headers found in table #${tableId}`);
        return;
    }
    
    // Définir l'état de tri
    let currentSortColumn = null;
    let currentSortDirection = 'asc';
    
    // Ajouter des écouteurs d'événement pour chaque en-tête triable
    sortableHeaders.forEach(header => {
        const columnIndex = parseInt(header.dataset.columnIndex);
        console.log(`Adding click listener to header for column ${columnIndex}`);
        
        header.addEventListener('click', function() {
            // Supprimer la classe active de tous les en-têtes
            sortableHeaders.forEach(h => {
                h.classList.remove('active-sort');
                h.querySelector('.sort-indicator').classList.remove('asc', 'desc');
            });
            
            // Définir le sens du tri
            if (currentSortColumn === columnIndex) {
                // Inverser le sens si on clique sur la même colonne
                currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
            } else {
                // Nouveau tri, par défaut ascendant
                currentSortColumn = columnIndex;
                currentSortDirection = 'asc';
            }
            
            // Mettre à jour l'indicateur visuel
            header.classList.add('active-sort');
            header.querySelector('.sort-indicator').classList.add(currentSortDirection);
            
            // Trier les lignes
            sortTable(tbody, columnIndex, currentSortDirection);
            
            console.log(`Table sorted by column ${columnIndex} in ${currentSortDirection} order`);
        });
    });
    
    console.log(`Sorting functionality successfully set up for table #${tableId}`);
}

// Fonction pour trier le tableau
function sortTable(tbody, columnIndex, direction) {
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    // Fonction de comparaison pour trier les cellules
    const compareValues = (a, b) => {
        const cellA = a.cells[columnIndex].textContent.trim().toLowerCase();
        const cellB = b.cells[columnIndex].textContent.trim().toLowerCase();
        
        // Essayer de convertir en nombre si possible
        const numA = parseFloat(cellA);
        const numB = parseFloat(cellB);
        
        if (!isNaN(numA) && !isNaN(numB)) {
            return direction === 'asc' ? numA - numB : numB - numA;
        }
        
        // Sinon, trier comme des chaînes
        if (cellA < cellB) return direction === 'asc' ? -1 : 1;
        if (cellA > cellB) return direction === 'asc' ? 1 : -1;
        return 0;
    };
    
    // Trier les lignes
    rows.sort(compareValues);
    
    // Réinsérer les lignes dans le bon ordre
    rows.forEach(row => {
        tbody.appendChild(row);
    });
}