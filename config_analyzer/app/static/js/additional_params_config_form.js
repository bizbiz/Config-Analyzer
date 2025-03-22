// static/js/additional_params_config_form.js

// Déclaration des fonctions dans la portée globale
function showValueField() {
    const type = document.getElementById('type').value;
    const config = window.APP_CONFIG?.currentConfig || {};

    // Masquer tous les conteneurs
    document.querySelectorAll('#valueField, #enumContainer, #numericRangeFields, #enumMultipleChoice')
        .forEach(el => el.style.display = 'none');

    try {
        if (type === 'text') {
            createTextInput(config);
            document.getElementById('valueField').style.display = 'block';
        } 
        else if (type === 'numeric') {
            createNumericInputs(config);
            document.getElementById('valueField').style.display = 'block';
            document.getElementById('numericRangeFields').style.display = 'block';
        }
        else if (type === 'enum') {
            createEnumInputs(config);
            document.getElementById('enumContainer').style.display = 'block';
            document.getElementById('enumMultipleChoice').style.display = 'block';
        }
    } catch (error) {
        console.error('Erreur lors de l\'affichage des champs :', error);
    }
}

function createTextInput(config) {
    const valueField = document.getElementById('valueField');
    const values = config.configuration_values || [];
    valueField.innerHTML = `
        <label for="value" class="form-label">Valeur par défaut :</label>
        <input type="text" 
               id="value" 
               name="value" 
               class="form-control"
               value="${values[0] || ''}">
    `;
}

function createNumericInputs(config) {
    const valueField = document.getElementById('valueField');
    const values = config.configuration_values || [];
    valueField.innerHTML = `
        <label for="value" class="form-label">Valeur par défaut :</label>
        <input type="number" 
               id="value" 
               name="value" 
               class="form-control"
               value="${values[0] || ''}">
    `;
}

function createEnumInputs(config) {
    const enumContainer = document.getElementById('enumContainer');
    const values = (config.configuration_values || []).slice(2);
    
    // Réinitialisation du contenu
    enumContainer.innerHTML = `
        <label class="form-label">Valeurs d'énumération :</label>
        <div id="enumFieldsContainer"></div>
        <div class="mt-2">
            <button type="button" class="btn btn-sm btn-outline-secondary" onclick="addEnumField()">
                <i class="fas fa-plus me-1"></i>Ajouter une valeur
            </button>
        </div>
    `;

    const container = enumContainer.querySelector('#enumFieldsContainer');
    
    if(values.length === 0) {
        addEnumField();
    } else {
        values.forEach(value => addEnumField(value));
    }
}

window.addEnumField = function(prefilledValue = '') {
    const container = document.getElementById('enumFieldsContainer');
    
    const newField = document.createElement('div');
    newField.className = 'enum-value mb-2';
    newField.innerHTML = `
        <div class="input-group">
            <input type="text" 
                   name="enum_values[]" 
                   class="form-control" 
                   placeholder="Valeur possible"
                   value="${prefilledValue}">
            <button type="button" 
                    class="btn btn-outline-danger" 
                    onclick="removeEnumField(this)">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    container.appendChild(newField);
};


window.removeEnumField = function(button) {
    const fieldDiv = button.closest('.enum-value');
    if(fieldDiv) fieldDiv.remove();
};

// Initialisation sécurisée
document.addEventListener('DOMContentLoaded', function() {
    window.APP_CONFIG = window.APP_CONFIG || {
        currentConfig: {
            configuration_values: [] // Valeur par défaut cruciale
        }
    };
    showValueField();
});
