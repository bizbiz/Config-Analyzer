// static/js/expand_form_table.js
document.addEventListener('DOMContentLoaded', function() {
    // Stocker les valeurs originales
    document.querySelectorAll('.param-value-input').forEach(input => {
        input.dataset.originalValue = input.value;
    });

    // Détection des modifications
    document.addEventListener('input', function(e) {
        if (e.target.matches('.param-value-input')) {
            const paramId = e.target.dataset.paramId;
            const notesRow = document.getElementById(`notes-row-${paramId}`);
            
            // Afficher ou masquer le bloc de notes
            if (e.target.value !== e.target.dataset.originalValue) {
                notesRow.style.display = 'table-row';
            } else {
                notesRow.style.display = 'none';
            }
        }
    });

    // Gestion du reset
    document.querySelectorAll('.reset-param').forEach(btn => {
        btn.addEventListener('click', function() {
            const paramId = this.dataset.paramId;
            const input = document.querySelector(`.param-value-input[data-param-id="${paramId}"]`);
            const notesRow = document.getElementById(`notes-row-${paramId}`);
            
            // Réinitialiser la valeur et masquer le bloc de notes
            input.value = input.dataset.originalValue;
            notesRow.style.display = 'none';
            notesRow.querySelector('textarea').value = '';
        });
    });
});
