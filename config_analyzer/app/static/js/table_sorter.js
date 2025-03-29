/**
 * Système de tri de tableau avancé
 * - Toutes les colonnes sont triables (sauf celles marquées no-sort)
 * - Affiche une flèche uniquement sur la colonne active
 * - Alterne entre tri ascendant et descendant
 */

// Stocke l'état de tri pour chaque tableau
const tableSortStates = {};

/**
 * Trie un tableau par colonne
 * @param {string} tableId - ID du tableau
 * @param {number} columnIndex - Index de la colonne à trier
 * @param {string} tbodyId - ID du tbody contenant les lignes
 */
function sortTableByColumn(tableId, columnIndex, tbodyId) {
    const tableBody = document.getElementById(tbodyId);
    if (!tableBody) return;
    
    // Initialiser l'état du tableau si nécessaire
    if (!tableSortStates[tableId]) {
        tableSortStates[tableId] = {
            currentColumn: null,
            ascending: true
        };
    }
    
    const state = tableSortStates[tableId];
    
    // Déterminer la direction de tri
    if (state.currentColumn === columnIndex) {
        // Si même colonne, inverser la direction
        state.ascending = !state.ascending;
    } else {
        // Si nouvelle colonne, trier en ascendant
        state.ascending = true;
        state.currentColumn = columnIndex;
    }
    
    // Trier les lignes
    const rows = Array.from(tableBody.rows);
    rows.sort((a, b) => {
        // S'assurer que la colonne existe dans les deux lignes
        if (columnIndex >= a.cells.length || columnIndex >= b.cells.length) {
            return 0;
        }
        
        const cellA = a.cells[columnIndex].innerText.toLowerCase();
        const cellB = b.cells[columnIndex].innerText.toLowerCase();
        
        // Tenter de trier numériquement si possible
        const numA = parseFloat(cellA.replace(/[^\d.-]/g, ''));
        const numB = parseFloat(cellB.replace(/[^\d.-]/g, ''));
        
        if (!isNaN(numA) && !isNaN(numB)) {
            return state.ascending ? numA - numB : numB - numA;
        }
        
        // Sinon, trier alphabétiquement
        if (cellA < cellB) return state.ascending ? -1 : 1;
        if (cellA > cellB) return state.ascending ? 1 : -1;
        return 0;
    });
    
    // Réorganiser les lignes
    tableBody.append(...rows);
    
    // Mettre à jour les indicateurs visuels
    updateSortIndicators(tableId, columnIndex, state.ascending);
}

/**
 * Met à jour les indicateurs visuels de tri
 * @param {string} tableId - ID du tableau
 * @param {number} activeColumn - Index de la colonne active
 * @param {boolean} ascending - Direction du tri
 */
function updateSortIndicators(tableId, activeColumn, ascending) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const headers = table.querySelectorAll('th');
    
    headers.forEach((header, index) => {
        // Supprimer tous les indicateurs existants
        const existingIndicator = header.querySelector('.sort-indicator');
        if (existingIndicator) {
            existingIndicator.remove();
        }
        
        // Ajouter l'indicateur uniquement sur la colonne active
        if (index === activeColumn) {
            const indicator = document.createElement('span');
            indicator.className = 'sort-indicator ms-1';
            indicator.innerHTML = ascending ? '&#9650;' : '&#9660;';
            header.appendChild(indicator);
        }
    });
}

/**
 * Initialise le tri sur toutes les colonnes d'un tableau
 * @param {string} tableId - ID du tableau
 * @param {string} tbodyId - ID du tbody
 */
function initSortableTable(tableId, tbodyId) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const headers = table.querySelectorAll('th');
    
    headers.forEach((header, index) => {
        // Ne pas ajouter de tri sur les colonnes d'actions
        if (header.classList.contains('no-sort')) return;
        
        // Rendre les en-têtes cliquables
        header.style.cursor = 'pointer';
        header.addEventListener('click', () => {
            sortTableByColumn(tableId, index, tbodyId);
        });
    });
}

// Fonction pour effacer les filtres
function clearFilters() {
    const searchInputs = document.querySelectorAll('input[id$="SearchInput"]');
    searchInputs.forEach(input => {
        input.value = '';
        input.dispatchEvent(new Event('keyup'));
    });
}