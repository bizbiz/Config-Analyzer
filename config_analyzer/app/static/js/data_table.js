// static/js/data_table.js

/**
 * Bibliothèque simplifiée pour gérer les tableaux de données
 * - Filtrage (recherche)
 * - Tri par colonne
 */

// État global pour les tableaux 
window.tableStates = {};

/**
 * Initialise un tableau complet avec tri et filtrage
 * @param {string} tableId - ID du tableau
 * @param {string} tbodyId - ID du tbody
 * @param {string} searchInputId - ID du champ de recherche
 */
function initDataTable(tableId, tbodyId, searchInputId) {
    console.log(`Initializing table ${tableId}`);
    
    // Vérifier l'existence des éléments de base
    const table = document.getElementById(tableId);
    const tbody = document.getElementById(tbodyId);
    const searchInput = document.getElementById(searchInputId);
    
    if (!table) {
        console.error(`Table #${tableId} not found`);
        return;
    }
    
    if (!tbody) {
        console.error(`Tbody #${tbodyId} not found for table #${tableId}`);
        return;
    }
    
    // Initialiser l'état du tableau
    window.tableStates[tableId] = {
        currentSortColumn: null,
        ascending: true,
        originalRows: Array.from(tbody.rows || []),
        filteredRows: Array.from(tbody.rows || []),
        searchTerm: ''
    };
    
    // Initialiser le tri
    initTableSorting(tableId, tbodyId);
    
    // Initialiser la recherche si l'input existe
    if (searchInput) {
        initTableSearch(tableId, searchInputId);
    }
}

/**
 * Initialise le tri sur les colonnes d'un tableau
 * @param {string} tableId - ID du tableau
 * @param {string} tbodyId - ID du tbody
 */
function initTableSorting(tableId, tbodyId) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const headers = table.querySelectorAll('th.sortable-header');
    console.log(`Found ${headers.length} sortable headers in table #${tableId}`);
    
    headers.forEach(header => {
        // Ajouter un style pour indiquer que la colonne est triable
        header.style.cursor = 'pointer';
        
        header.addEventListener('click', function() {
            // Obtenir l'index de la colonne depuis l'attribut data
            const columnIndex = parseInt(this.getAttribute('data-column-index') || '0', 10);
            console.log(`Sorting table #${tableId} by column ${columnIndex}`);
            
            // Récupérer l'état du tableau
            const state = window.tableStates[tableId];
            
            // Gérer la direction du tri
            if (state.currentSortColumn === columnIndex) {
                state.ascending = !state.ascending;
            } else {
                state.currentSortColumn = columnIndex;
                state.ascending = true;
            }
            
            // Mettre à jour les indicateurs visuels
            updateSortIndicators(table, columnIndex, state.ascending);
            
            // Trier les lignes
            sortTable(tableId, tbodyId, columnIndex, state.ascending);
        });
    });
}

/**
 * Met à jour les indicateurs visuels de tri
 * @param {HTMLElement} table - Élément table
 * @param {number} activeColumnIndex - Index de la colonne active
 * @param {boolean} ascending - Direction du tri
 */
function updateSortIndicators(table, activeColumnIndex, ascending) {
    // Réinitialiser tous les indicateurs
    const headers = table.querySelectorAll('th');
    headers.forEach(header => {
        header.classList.remove('active-sort');
        const indicator = header.querySelector('.sort-indicator');
        if (indicator) {
            indicator.textContent = '';
            indicator.classList.remove('asc', 'desc');
        }
    });
    
    // Mettre à jour l'indicateur de la colonne active
    const activeHeader = headers[activeColumnIndex];
    if (activeHeader) {
        activeHeader.classList.add('active-sort');
        const indicator = activeHeader.querySelector('.sort-indicator');
        if (indicator) {
            indicator.textContent = ascending ? ' ↑' : ' ↓';
            indicator.classList.add(ascending ? 'asc' : 'desc');
        }
    }
}

/**
 * Trie un tableau
 * @param {string} tableId - ID du tableau
 * @param {string} tbodyId - ID du tbody
 * @param {number} columnIndex - Index de la colonne à trier
 * @param {boolean} ascending - Direction du tri
 */
function sortTable(tableId, tbodyId, columnIndex, ascending) {
    const tbody = document.getElementById(tbodyId);
    if (!tbody) return;
    
    const rows = Array.from(tbody.rows);
    
    // Trier les lignes
    rows.sort((rowA, rowB) => {
        // Vérifier que l'index de colonne est valide
        if (columnIndex >= rowA.cells.length || columnIndex >= rowB.cells.length) {
            return 0;
        }
        
        // Obtenir le texte des cellules
        const cellA = rowA.cells[columnIndex].textContent.trim().toLowerCase();
        const cellB = rowB.cells[columnIndex].textContent.trim().toLowerCase();
        
        // Tentative de tri numérique si possible
        const numA = parseFloat(cellA.replace(/[^\d.-]/g, ''));
        const numB = parseFloat(cellB.replace(/[^\d.-]/g, ''));
        
        if (!isNaN(numA) && !isNaN(numB)) {
            return ascending ? numA - numB : numB - numA;
        }
        
        // Tri alphabétique
        if (cellA < cellB) return ascending ? -1 : 1;
        if (cellA > cellB) return ascending ? 1 : -1;
        return 0;
    });
    
    // Réorganiser les lignes dans le DOM
    rows.forEach(row => {
        tbody.appendChild(row);
    });
}

/**
 * Initialise un filtre de recherche pour un tableau
 * @param {string} tableId - ID du tableau
 * @param {string} inputId - ID du champ de recherche
 */
function initTableSearch(tableId, inputId) {
    const searchInput = document.getElementById(inputId);
    const table = document.getElementById(tableId);
    
    if (!searchInput || !table) {
        console.error(`Cannot initialize search: missing elements for table #${tableId}`);
        return;
    }
    
    console.log(`Initializing search for table #${tableId} with input #${inputId}`);
    
    // Déterminer le nombre de colonnes à filtrer
    const filterColumns = parseInt(table.getAttribute('data-filter-columns') || '3', 10);
    
    // Garder les lignes originales pour le filtrage
    const tbody = table.querySelector('tbody');
    if (!tbody) return;
    
    const originalRows = Array.from(tbody.rows);
    
    // Gestionnaire d'événement pour la recherche
    searchInput.addEventListener('input', function() {
        const filter = this.value.toLowerCase();
        let visibleCount = 0;
        
        originalRows.forEach(row => {
            let match = false;
            
            // Parcourir les colonnes à filtrer
            for (let i = 0; i < filterColumns && i < row.cells.length; i++) {
                const cell = row.cells[i];
                if (cell && cell.textContent.toLowerCase().includes(filter)) {
                    match = true;
                    break;
                }
            }
            
            // Afficher ou masquer la ligne
            row.style.display = match ? '' : 'none';
            if (match) visibleCount++;
        });
        
        // Mettre à jour un compteur de résultats (optionnel)
        updateResultsCount(tableId, visibleCount, originalRows.length);
    });
}

/**
 * Met à jour le compteur de résultats de recherche
 * @param {string} tableId - ID du tableau
 * @param {number} visible - Nombre d'éléments visibles
 * @param {number} total - Nombre total d'éléments
 */
function updateResultsCount(tableId, visible, total) {
    const counterId = `${tableId}-counter`;
    let counter = document.getElementById(counterId);
    
    // Créer le compteur s'il n'existe pas
    if (!counter) {
        counter = document.createElement('div');
        counter.id = counterId;
        counter.className = 'search-results-count small text-muted mt-1';
        
        const searchInput = document.querySelector(`#${tableId.replace('Table', 'SearchInput')}`);
        if (searchInput && searchInput.parentNode) {
            searchInput.parentNode.appendChild(counter);
        }
    }
    
    // Afficher le compteur si nécessaire
    if (visible < total) {
        counter.textContent = `Affichage de ${visible} sur ${total} éléments`;
        counter.style.display = 'block';
    } else {
        counter.style.display = 'none';
    }
}

// Initialisation automatique des tableaux
document.addEventListener('DOMContentLoaded', function() {
    // Cette partie est désormais redondante car l'initialisation
    // est faite directement via des scripts inline dans chaque tableau
});