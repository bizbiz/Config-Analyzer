/**
 * static/js/form_validation.js
 * Script commun pour la validation des formulaires
 */

/**
 * Initialise la validation d'un formulaire.
 * 
 * @param {string} formId - L'ID du formulaire à valider
 * @param {Object} options - Options de configuration
 * @param {string[]} options.requiredSelectors - Sélecteurs pour les champs obligatoires (défaut: 'input[required], select[required]')
 * @param {boolean} options.validateOnBlur - Valider lors de la perte de focus (défaut: true)
 * @param {boolean} options.validateOnInput - Valider lors de la saisie (défaut: true)
 * @param {boolean} options.validateOnSubmit - Valider lors de la soumission du formulaire (défaut: true)
 * @param {Function} options.onValidationFailed - Callback appelé quand la validation échoue
 * @param {Function} options.onValidationSuccess - Callback appelé quand la validation réussit
 */
function initFormValidation(formId, options = {}) {
    document.addEventListener('DOMContentLoaded', function() {
        const form = document.getElementById(formId);
        if (!form) return; // Sortir si le formulaire n'existe pas
        
        const {
            requiredSelectors = 'input[required], select[required]',
            validateOnBlur = true,
            validateOnInput = true,
            validateOnSubmit = true,
            onValidationFailed = null,
            onValidationSuccess = null
        } = options;
        
        const inputs = form.querySelectorAll(requiredSelectors);
        
        // Fonction pour valider un champ
        function validateField(field) {
            // Réinitialiser les messages d'erreur
            let parent = field.closest('.mb-3');
            if (!parent) return true; // Si on ne trouve pas le parent, on considère que c'est valide
            
            let feedbackElement = parent.querySelector('.invalid-feedback');
            
            field.classList.remove('is-invalid');
            
            // Vérifier si le champ est obligatoire et vide
            if (field.hasAttribute('required') && !field.value.trim()) {
                field.classList.add('is-invalid');
                if (feedbackElement) {
                    feedbackElement.textContent = 'Ce champ est obligatoire';
                } else {
                    // Créer un élément de feedback s'il n'existe pas
                    feedbackElement = document.createElement('div');
                    feedbackElement.className = 'invalid-feedback';
                    feedbackElement.textContent = 'Ce champ est obligatoire';
                    parent.appendChild(feedbackElement);
                }
                return false;
            }
            
            // Vérifier le pattern si défini
            if (field.hasAttribute('pattern') && field.value) {
                const pattern = new RegExp(field.getAttribute('pattern'));
                if (!pattern.test(field.value)) {
                    field.classList.add('is-invalid');
                    const errorMessage = field.getAttribute('title') || 'Format invalide';
                    
                    if (feedbackElement) {
                        feedbackElement.textContent = errorMessage;
                    } else {
                        // Créer un élément de feedback s'il n'existe pas
                        feedbackElement = document.createElement('div');
                        feedbackElement.className = 'invalid-feedback';
                        feedbackElement.textContent = errorMessage;
                        parent.appendChild(feedbackElement);
                    }
                    return false;
                }
            }
            
            return true;
        }
        
        // Valider lors de la perte de focus
        if (validateOnBlur) {
            inputs.forEach(input => {
                input.addEventListener('blur', function() {
                    validateField(this);
                });
            });
        }
        
        // Valider lors de la saisie
        if (validateOnInput) {
            inputs.forEach(input => {
                input.addEventListener('input', function() {
                    validateField(this);
                });
            });
        }
        
        // Valider lors de la soumission
        if (validateOnSubmit) {
            form.addEventListener('submit', function(event) {
                let isFormValid = true;
                
                inputs.forEach(input => {
                    if (!validateField(input)) {
                        isFormValid = false;
                    }
                });
                
                if (!isFormValid) {
                    event.preventDefault();
                    if (typeof onValidationFailed === 'function') {
                        onValidationFailed();
                    }
                } else if (typeof onValidationSuccess === 'function') {
                    onValidationSuccess();
                }
            });
        }
    });
}