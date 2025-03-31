// config_analyzer/app/static/js/data_table.js

function initTableSearch(tableId, inputId, columnIndexes = [], rowSelector = 'tbody tr') {
    const table = document.getElementById(tableId);
    const searchInput = document.getElementById(inputId);
    
    if (!table || !searchInput) {
        console.error(`Data Tables: Missing elements for table #${tableId} or input #${inputId}`);
        return;
    }
    
    // Récupérer le tbody
    const tbody = table.querySelector('tbody');
    if (!tbody) {
        console.error(`Data Tables: Tbody not found for table #${tableId}`);
        return;
    }
    
    // Stocker les lignes originales
    const originalRows = Array.from(tbody.querySelectorAll(rowSelector));
    
    // Attacher l'écouteur d'événement input
    searchInput.addEventListener('input', function() {
        const searchText = this.value.toLowerCase();
        let visibleCount = 0;
        
        // Si aucun index de colonne n'est spécifié, recherche dans toutes les colonnes
        // sauf la dernière (actions)
        const searchColumns = columnIndexes.length > 0 
            ? columnIndexes 
            : Array.from({ length: Math.max(0, originalRows[0]?.cells.length - 1 || 0) }, (_, i) => i);
        
        originalRows.forEach(row => {
            let visible = false;
            
            // Rechercher dans les colonnes spécifiées
            for (const colIndex of searchColumns) {
                if (colIndex >= row.cells.length) continue;
                
                const cell = row.cells[colIndex];
                const cellText = cell.textContent.toLowerCase();
                
                if (cellText.includes(searchText)) {
                    visible = true;
                    break;
                }
            }
            
            // Afficher ou masquer la ligne
            row.style.display = visible ? '' : 'none';
            if (visible) visibleCount++;
        });
        
        // Mettre à jour le compteur (si nécessaire)
        const counterElement = document.getElementById(`${tableId}-counter`);
        if (counterElement) {
            if (visibleCount < originalRows.length) {
                counterElement.textContent = `Affichage de ${visibleCount} sur ${originalRows.length} éléments`;
                counterElement.style.display = 'block';
            } else {
                counterElement.style.display = 'none';
            }
        }
    });
}