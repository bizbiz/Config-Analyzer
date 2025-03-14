document.addEventListener('DOMContentLoaded', function () {
    const table = document.getElementById('configTable');
    const baseConfigId = table.dataset.baseConfigId;

    // ======== FONCTIONS UTILITAIRES ========

    /**
     * Met à jour les métadonnées affichées (nombre de paramètres et date de dernière modification)
     * @param {Object} data - Données contenant parameter_count et last_modified
     */
    function updateMetadata(data) {
        if (data.parameter_count !== undefined) {
            document.getElementById('parameter-count').textContent = data.parameter_count;
        }
        if (data.last_modified !== undefined) {
            document.getElementById('last-modified').textContent = data.last_modified;
        }
    }

    /**
     * Affiche une notification toast
     * @param {string} message - Message à afficher
     * @param {string} type - Type de notification (success, danger, warning, etc.)
     */
    function showToast(message, type) {
        const toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) {
            // Créer le conteneur s'il n'existe pas
            const newContainer = document.createElement('div');
            newContainer.id = 'toastContainer';
            newContainer.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999;';
            document.body.appendChild(newContainer);
            toastContainer = newContainer;
        }
        
        const toast = document.createElement('div');
        toast.className = `toast toast-${type} fade show`;
        toast.innerHTML = `
            <div class="toast-body">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>`;
        toastContainer.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }

    /**
     * Met à jour l'icône de note en fonction du contenu
     * @param {string} paramId - ID du paramètre
     * @param {string} notes - Contenu des notes
     */
    function updateNoteIcon(paramId, notes) {
        const paramNameLink = document.querySelector(`.param-name-link[data-param-id="${paramId}"]`);
        if (!paramNameLink) return;
        
        if (notes && notes.trim() !== '') {
            // S'il n'y a pas d'icône, l'ajouter
            if (!paramNameLink.querySelector('i.fa-comment-alt')) {
                const noteIcon = document.createElement('i');
                noteIcon.className = 'fas fa-comment-alt ml-1';
                noteIcon.style.cssText = 'color: white !important; text-shadow: -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000; margin-left: 5px;';
                paramNameLink.appendChild(noteIcon);
            }
        } else {
            // Si la note est vide, supprimer l'icône si elle existe
            const existingIcon = paramNameLink.querySelector('i.fa-comment-alt');
            if (existingIcon) {
                existingIcon.remove();
            }
        }
    }

    /**
     * Change l'état visuel de l'icône de synchronisation
     * @param {HTMLElement} row - Ligne du tableau contenant le paramètre
     * @param {string} status - État de synchronisation ('synced', 'modified', 'error')
     */
    function updateSyncIcon(row, status) {
        const paramId = row.dataset.paramId;
        const syncIcon = document.querySelector(`.sync-status-icon[data-param-id="${paramId}"] i`);
        if (!syncIcon) return;
        
        // Supprimer toutes les classes de couleur
        syncIcon.classList.remove('text-success', 'text-primary', 'text-danger', 'text-secondary');
        
        switch(status) {
            case 'synced': // Synchronisé (vert)
                syncIcon.classList.add('text-success');
                syncIcon.title = 'Synchronisé avec la base de données';
                break;
            case 'modified': // Modifié, pas synchronisé (bleu)
                syncIcon.classList.add('text-primary');
                syncIcon.title = 'Modifications non synchronisées';
                break;
            case 'error': // Erreur (rouge)
                syncIcon.classList.add('text-danger');
                syncIcon.title = 'Erreur de synchronisation';
                break;
            case 'unknown': // Inconnu (gris)
                syncIcon.classList.add('text-secondary');
                syncIcon.title = 'Paramètre non enregistré';
                break;
        }
    }

    // ======== CRÉATION ET MISE À JOUR DES PARAMÈTRES ========

    /**
     * Crée un nouveau paramètre
     * @param {HTMLElement} row - Ligne du tableau contenant les données du paramètre
     * @returns {Promise} - Promesse résolue après la création du paramètre
     */
    async function createNewParameter(row) {
        const formData = {};
        row.querySelectorAll('[data-field]').forEach(field => {
            formData[field.dataset.field] = field.value;
        });
        
        // Récupérer les notes si elles existent
        const notesRow = document.getElementById(`notes-row-undefined`);
        if (notesRow) {
            const notesTextarea = notesRow.querySelector('.notes-textarea');
            if (notesTextarea) {
                formData.notes = notesTextarea.value;
            }
        }

        try {
            const response = await fetch('/create_parameter', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ...formData,
                    base_config_file_id: baseConfigId
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`HTTP error! status: ${response.status}, message: ${errorData.message}`);
            }

            const result = await response.json();
            if (result.status === 'success') {
                row.dataset.paramId = result.new_param_id;
                
                // Mettre à jour l'icône de synchronisation
                updateSyncIcon(row, 'synced');
                
                // Mettre à jour l'ID de la ligne de notes
                const notesRow = document.getElementById('notes-row-undefined');
                if (notesRow) {
                    notesRow.id = `notes-row-${result.new_param_id}`;
                    const notesTextarea = notesRow.querySelector('.notes-textarea');
                    if (notesTextarea) {
                        notesTextarea.dataset.paramId = result.new_param_id;
                        notesTextarea.id = `notes-${result.new_param_id}`;
                    }
                }
                
                // Mettre à jour l'icône de note si nécessaire
                if (formData.notes) {
                    updateNoteIcon(result.new_param_id, formData.notes);
                }
                
                updateMetadata(result);
                showToast('Paramètre créé avec succès', 'success');
            }
        } catch (error) {
            updateSyncIcon(row, 'error');
            showToast(`Erreur lors de la création : ${error.message}`, 'danger');
        }
    }

    /**
     * Synchronise un paramètre existant avec la base de données
     * @param {string} paramId - ID du paramètre
     * @param {HTMLElement} row - Ligne du tableau contenant les données du paramètre
     */
    async function syncParameter(paramId, row) {
        try {
            // Récupérer les données du paramètre
            const formData = {};
            row.querySelectorAll('[data-field]').forEach(field => {
                formData[field.dataset.field] = field.value;
            });
            
            // Récupérer les notes si elles existent
            const notesTextarea = document.querySelector(`#notes-${paramId}`);
            if (notesTextarea) {
                formData.notes = notesTextarea.value;
            }
            
            // Créer une nouvelle route pour la synchronisation complète
            const response = await fetch(`/update_parameter_complete/${paramId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
            
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            const result = await response.json();
            if (result.status === 'success') {
                updateSyncIcon(row, 'synced');
                updateMetadata(result);
                
                // Mettre à jour l'icône de note
                updateNoteIcon(paramId, formData.notes);
                
                showToast('Synchronisation réussie', 'success');
            }
        } catch (error) {
            updateSyncIcon(row, 'error');
            showToast(`Erreur de synchronisation : ${error.message}`, 'danger');
        }
    }

    /**
     * Réinitialise un paramètre à ses valeurs d'origine
     * @param {string} paramId - ID du paramètre
     * @param {HTMLElement} row - Ligne du tableau contenant le paramètre
     */
    async function revertParameter(paramId, row) {
        try {
            const response = await fetch(`/get_initial_value/${paramId}`);
            const data = await response.json();

            row.querySelectorAll('[data-field]').forEach(field => {
                const key = field.dataset.field;
                field.value = data[key] || '';
            });
            
            // Réinitialiser également les notes
            const notesTextarea = document.querySelector(`#notes-${paramId}`);
            if (notesTextarea && data.notes !== undefined) {
                notesTextarea.value = data.notes || '';
            }

            updateSyncIcon(row, 'synced');
            showToast('Réinitialisation réussie', 'success');
        } catch (error) {
            showToast('Erreur lors de la réinitialisation', 'danger');
        }
    }

    // ======== GESTIONNAIRES D'ÉVÉNEMENTS ========

    // Détecter les modifications dans les champs de paramètres
    table.addEventListener('input', function (e) {
        const target = e.target.closest('[data-field]');
        if (target) {
            const row = target.closest('tr');
            updateSyncIcon(row, 'modified');
        }
    });

    // Détecter les modifications dans les zones de texte des notes
    document.querySelectorAll('.notes-textarea').forEach(textarea => {
        textarea.addEventListener('input', function() {
            const paramId = this.dataset.paramId;
            if (paramId === 'undefined') return;
            
            const row = document.querySelector(`tr[data-param-id="${paramId}"]`);
            if (row) {
                updateSyncIcon(row, 'modified');
            }
        });
    });

    // Gestion des clics sur les icônes de synchronisation
    document.addEventListener('click', async function(e) {
        const syncIcon = e.target.closest('.sync-status-icon');
        if (syncIcon) {
            const paramId = syncIcon.dataset.paramId;
            const row = document.querySelector(`tr[data-param-id="${paramId}"]`);
            
            if (paramId === 'undefined') {
                await createNewParameter(row);
            } else {
                await syncParameter(paramId, row);
            }
        }
    });

    // Gestion de l'affichage/masquage des notes
    document.querySelectorAll('.param-name-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const paramId = this.dataset.paramId;
            if (paramId === 'undefined') return;
            
            // Récupérer la ligne de notes pour ce paramètre
            const notesRow = document.getElementById(`notes-row-${paramId}`);
            if (!notesRow) return;
            
            // Si la ligne est déjà visible, la masquer
            if (notesRow.style.display === 'table-row') {
                notesRow.style.display = 'none';
            } 
            // Sinon, masquer toutes les autres lignes et afficher celle-ci
            else {
                // Masquer toutes les lignes de notes
                document.querySelectorAll('.notes-row').forEach(row => {
                    row.style.display = 'none';
                });
                
                // Afficher la ligne de notes pour ce paramètre
                notesRow.style.display = 'table-row';
            }
        });
    });

    // Initialisation : marquer tous les paramètres comme synchronisés au chargement
    document.querySelectorAll('tr.config-row').forEach(row => {
        const paramId = row.dataset.paramId;
        if (paramId && paramId !== 'undefined') {
            updateSyncIcon(row, 'synced');
        } else {
            updateSyncIcon(row, 'unknown');
        }
    });
});
