// static/js/data_table.js

/**
 * Bibliothèque pour gérer les tableaux de données
 * - Filtrage (recherche)
 * - Tri par colonne
 * - Fonctionnalités de tableau interactif
 */

// Fonction d'initialisation globale
document.addEventListener('DOMContentLoaded', function() {
    console.log('Data Tables: Initializing all data tables');
    
    // Initialiser tous les tableaux de données
    document.querySelectorAll('table.data-table').forEach(table => {
        if (!table.id) {
            console.warn('Data Tables: Found table without ID, skipping');
            return;
        }
        
        console.log(`Data Tables: Processing table #${table.id}`);
        
        // Récupérer les attributs data-*
        const searchInputId = table.dataset.searchInput || null;
        const tbodyId = table.dataset.tbodyId || `${table.id}-body`;
        const filterColumns = parseInt(table.dataset.filterColumns || '3', 10);
        const isSortable = table.dataset.sortable !== 'false'; // Par défaut activé
        
        // Initialiser le filtrage si un input de recherche est spécifié
        if (searchInputId) {
            initTableSearch(table.id, searchInputId, filterColumns);
        }
        
        // Initialiser le tri si activé
        if (isSortable) {
            initTableSorting(table.id, tbodyId);
        }
    });
    
    // Initialiser également les champs de recherche avec attribut data-target-table
    document.querySelectorAll('input.table-search-input').forEach(input => {
        if (!input.id) {
            console.warn('Data Tables: Found search input without ID, skipping');
            return;
        }
        
        // Vérifier si l'initialisation n'a pas déjà été faite
        const targetTableId = input.dataset.targetTable;
        if (targetTableId && !input.dataset.initialized) {
            const table = document.getElementById(targetTableId);
            if (table) {
                const filterColumns = parseInt(table.dataset.filterColumns || '3', 10);
                initTableSearch(targetTableId, input.id, filterColumns);
                input.dataset.initialized = 'true';
            }
        }
    });
});

/**
 * Initialise le tri sur les colonnes d'un tableau
 * @param {string} tableId - ID du tableau
 * @param {string} tbodyId - ID du tbody
 */
function initTableSorting(tableId, tbodyId) {
    const table = document.getElementById(tableId);
    if (!table) {
        console.error(`Data Tables: Table #${tableId} not found for sorting`);
        return;
    }
    
    const tbody = document.getElementById(tbodyId) || table.querySelector('tbody');
    if (!tbody) {
        console.error(`Data Tables: Tbody for table #${tableId} not found`);
        return;
    }
    
    const headers = table.querySelectorAll('th.sortable-header');
    console.log(`Data Tables: Found ${headers.length} sortable headers in table #${tableId}`);
    
    // État de tri pour ce tableau
    const sortState = {
        currentColumn: null,
        ascending: true
    };
    
    headers.forEach(header => {
        // Ajouter un style pour indiquer que la colonne est triable
        header.style.cursor = 'pointer';
        
        header.addEventListener('click', function() {
            // Obtenir l'index de la colonne depuis l'attribut data
            const columnIndex = parseInt(this.getAttribute('data-column-index') || '0', 10);
            console.log(`Data Tables: Sorting table #${tableId} by column ${columnIndex}`);
            
            // Gérer la direction du tri
            if (sortState.currentColumn === columnIndex) {
                sortState.ascending = !sortState.ascending;
            } else {
                sortState.currentColumn = columnIndex;
                sortState.ascending = true;
            }
            
            // Mettre à jour les indicateurs visuels
            updateSortIndicators(table, columnIndex, sortState.ascending);
            
            // Trier les lignes
            sortTableRows(tbody, columnIndex, sortState.ascending);
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
 * Trie les lignes d'un tableau
 * @param {HTMLElement} tbody - Le corps du tableau contenant les lignes
 * @param {number} columnIndex - L'index de la colonne à trier
 * @param {boolean} ascending - La direction du tri (vrai pour ascendant)
 */
function sortTableRows(tbody, columnIndex, ascending) {
    if (!tbody) return;
    
    const rows = Array.from(tbody.rows);
    if (rows.length === 0) return;
    
    // Trier les lignes
    rows.sort((a, b) => {
        // Vérifier la validité des cellules
        if (columnIndex >= a.cells.length || columnIndex >= b.cells.length) {
            return 0;
        }
        
        // Extraire le contenu des cellules
        const cellA = a.cells[columnIndex].textContent.trim().toLowerCase();
        const cellB = b.cells[columnIndex].textContent.trim().toLowerCase();
        
        // Essayer un tri numérique d'abord
        const numA = parseFloat(cellA.replace(/[^\d.-]/g, ''));
        const numB = parseFloat(cellB.replace(/[^\d.-]/g, ''));
        
        if (!isNaN(numA) && !isNaN(numB)) {
            return ascending ? numA - numB : numB - numA;
        }
        
        // Sinon faire un tri alphabétique
        if (cellA < cellB) return ascending ? -1 : 1;
        if (cellA > cellB) return ascending ? 1 : -1;
        return 0;
    });
    
    // Réarranger les lignes dans le DOM
    rows.forEach(row => {
        tbody.appendChild(row);
    });
}

/**
 * Initialise un filtre de recherche pour un tableau
 * @param {string} tableId - ID du tableau
 * @param {string} inputId - ID du champ de recherche
 * @param {number} filterColumns - Nombre de colonnes à considérer pour la recherche
 */
function initTableSearch(tableId, inputId, filterColumns) {
    const table = document.getElementById(tableId);
    const searchInput = document.getElementById(inputId);
    
    if (!table || !searchInput) {
        console.error(`Data Tables: Missing elements for table #${tableId} or input #${inputId}`);
        return;
    }
    
    console.log(`Data Tables: Setting up search for table #${tableId} with input #${inputId}`);
    
    // Marquer cet input comme initialisé pour éviter les doubles init
    if (searchInput.dataset.initialized === 'true') {
        console.log(`Data Tables: Search input #${inputId} already initialized`);
        return;
    }
    
    // Récupérer le corps du tableau
    const tbody = table.querySelector('tbody');
    if (!tbody) {
        console.error(`Data Tables: Tbody not found for table #${tableId}`);
        return;
    }
    
    // Stocker les lignes originales
    const originalRows = Array.from(tbody.rows);
    
    // Attacher l'écouteur d'événements
    searchInput.addEventListener('input', function() {
        const filter = this.value.toLowerCase();
        let visibleCount = 0;
        
        originalRows.forEach(row => {
            let match = false;
            
            // Rechercher dans les premières colonnes selon filterColumns
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
        updateSearchResultsCount(tableId, visibleCount, originalRows.length);
    });
    
    // Marquer cet input comme initialisé
    searchInput.dataset.initialized = 'true';
}

/**
 * Met à jour le compteur de résultats de recherche
 * @param {string} tableId - ID du tableau
 * @param {number} visible - Nombre d'éléments visibles
 * @param {number} total - Nombre total d'éléments
 */
function updateSearchResultsCount(tableId, visible, total) {
    // ID du compteur basé sur l'ID du tableau
    const counterId = `${tableId}-counter`;
    
    // Trouver ou créer le compteur
    let counter = document.getElementById(counterId);
    if (!counter) {
        counter = document.createElement('div');
        counter.id = counterId;
        counter.className = 'search-results-count small text-muted mt-1';
        
        // Essayer de placer le compteur après le champ de recherche
        const searchInput = document.querySelector(`input[data-target-table="${tableId}"]`);
        if (searchInput && searchInput.parentNode) {
            searchInput.parentNode.appendChild(counter);
        }
    }
    
    // Mettre à jour le compteur
    if (visible < total) {
        counter.textContent = `Affichage de ${visible} sur ${total} éléments`;
        counter.style.display = 'block';
    } else {
        counter.style.display = 'none';
    }
}