// static/js/common.js
/**
 * Initialise les composants dynamiques communs
 */
function initCommonComponents() {
    // Initialiser tous les tableaux avec filtrage
    document.querySelectorAll('[data-list-filter]').forEach(initFilterForTable);
    
    // Initialiser les formulaires dynamiques
    initDynamicFormFields();
}

/**
 * Gestion des champs de formulaire dynamiques
 */
function initDynamicFormFields() {
    // Ajouter les écouteurs pour les boutons d'ajout/suppression
    document.querySelectorAll('[data-add-field]').forEach(btn => {
        btn.addEventListener('click', () => addDynamicField(
            btn.dataset.targetContainer,
            btn.dataset.templateId
        ));
    });
    
    // Délégation d'événement pour les boutons de suppression
    document.addEventListener('click', (e) => {
        if (e.target.matches('[data-remove-field]') || 
            e.target.closest('[data-remove-field]')) {
            const btn = e.target.matches('[data-remove-field]') ? 
                        e.target : e.target.closest('[data-remove-field]');
            removeDynamicField(btn);
        }
    });
}

// Initialiser au chargement
document.addEventListener('DOMContentLoaded', initCommonComponents);
