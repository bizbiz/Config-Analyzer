// config_analyzer/app/static/js/data_table.js

function initTableSearch(tableId, inputId, filterColumns = 3, rowSelector = 'tbody tr') {
    console.log(`Initializing search for table: ${tableId}, input: ${inputId}`);
    
    document.addEventListener("DOMContentLoaded", function() {
        const table = document.getElementById(tableId);
        const searchInput = document.getElementById(inputId);
        
        console.log(`Table element:`, table);
        console.log(`Search input element:`, searchInput);
        
        if (!table || !searchInput) {
            console.error(`Missing elements for table #${tableId} or input #${inputId}`);
            return;
        }
        
        // Récupérer les lignes du tableau
        const rows = table.querySelectorAll(rowSelector);
        console.log(`Found ${rows.length} rows in table`);
        
        searchInput.addEventListener("input", function() {
            const searchText = this.value.toLowerCase();
            console.log(`Search text: ${searchText}`);
            
            rows.forEach(row => {
                let found = false;
                
                // Limiter la recherche aux colonnes spécifiées (sauf la dernière = actions)
                const columns = row.querySelectorAll('td');
                const columnsToSearch = Math.min(columns.length - 1, filterColumns);
                
                for (let i = 0; i < columnsToSearch; i++) {
                    if (columns[i].textContent.toLowerCase().includes(searchText)) {
                        found = true;
                        break;
                    }
                }
                
                row.style.display = found ? "" : "none";
            });
        });
        
        console.log(`Search functionality initialized for table #${tableId}`);
    });
}