document.addEventListener('DOMContentLoaded', function () {
    const table = document.getElementById('configTable');
    const baseConfigId = table.dataset.baseConfigId;

    // Met à jour les métadonnées affichées
    function updateMetadata(data) {
        if (data.parameter_count !== undefined) {
            document.getElementById('parameter-count').textContent = data.parameter_count;
        }
        if (data.last_modified !== undefined) {
            document.getElementById('last-modified').textContent = data.last_modified;
        }
    }


    // Change l'état visuel d'une ligne
    function toggleRowState(row, isModified) {
        const statusBtn = row.querySelector('.status-btn, .badge'); // Cible à la fois bouton et badge
        const revertBtn = row.querySelector('.revert-btn');

        if (isModified) {
            row.classList.add('modified');
            if (statusBtn) {
                // Gestion spécifique pour les badges "Inconnu"
                if (statusBtn.classList.contains('badge')) {
                    statusBtn.textContent = 'Modifications non sauvegardées';
                    statusBtn.classList.replace('bg-secondary', 'bg-warning');
                } else {
                    statusBtn.classList.replace('btn-success', 'btn-primary');
                    statusBtn.textContent = 'Mettre à jour';
                }
            }
            if (revertBtn) revertBtn.style.display = 'inline-block';
        } else {
            row.classList.remove('modified');
            if (statusBtn) {
                if (statusBtn.classList.contains('badge')) {
                    statusBtn.textContent = 'Inconnu';
                    statusBtn.classList.replace('bg-warning', 'bg-secondary');
                } else {
                    statusBtn.classList.replace('btn-primary', 'btn-success');
                    statusBtn.textContent = 'À jour';
                }
            }
            if (revertBtn) revertBtn.style.display = 'none';
        }
    }

    // Création d'un nouveau paramètre
    async function createNewParameter(row) {
        const formData = {};
        row.querySelectorAll('[data-field]').forEach(field => {
            formData[field.dataset.field] = field.value;
        });

        console.log('formData:', formData);
        console.log('baseConfigId:', baseConfigId);

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
                row.querySelector('.status-cell').innerHTML = `
                    <div class="btn-group">
                        <button class="btn btn-sm btn-success status-btn">À jour</button>
                        <button class="btn btn-sm btn-danger revert-btn" title="Réinitialiser" style="display: none;">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>`;
                toggleRowState(row, false);
                updateMetadata(result); // Met à jour les métadonnées après création
                showToast('Paramètre créé avec succès', 'success');
            }
        } catch (error) {
            showToast(`Erreur lors de la création : ${error.message}`, 'danger');
        }
    }

    // Gestion des modifications de champs
    table.addEventListener('input', function (e) {
        const target = e.target.closest('[data-field]');
        if (target) {
            const row = target.closest('tr');
            toggleRowState(row, true);
        }
    });

    // Gestion de la réinitialisation
    table.addEventListener('click', async function (e) {
        if (e.target.closest('.revert-btn')) {
            const row = e.target.closest('tr');
            const paramId = row.dataset.paramId;

            try {
                const response = await fetch(`/get_initial_value/${paramId}`);
                const data = await response.json();

                row.querySelectorAll('[data-field]').forEach(field => {
                    const key = field.dataset.field;
                    field.value = data[key] || '';
                });

                toggleRowState(row, false);
                showToast('Réinitialisation réussie', 'success');
            } catch (error) {
                showToast('Erreur lors de la réinitialisation', 'danger');
            }
        }
    });

    // Gestion des mises à jour
    table.addEventListener('click', async function (e) {
        if (e.target.closest('.status-btn, .badge')) {
            const row = e.target.closest('tr');
            const paramId = row.dataset.paramId;

            try {
                if (paramId === 'undefined') {
                    await createNewParameter(row);
                    return;
                }

                // Récupération des données
                const formData = {};
                row.querySelectorAll('[data-field]').forEach(field => {
                    formData[field.dataset.field] = field.value;
                });

                // Envoi des données
                const response = await fetch(`/update_parameter/${paramId}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                });

                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

                const result = await response.json();
                if (result.status === 'success') {
                    toggleRowState(row, false);
                    updateMetadata(result); // Met à jour les métadonnées après mise à jour
                    showToast('Mise à jour réussie', 'success');
                }
            } catch (error) {
                showToast(`Erreur lors de la mise à jour : ${error.message}`, 'danger');
            }
        }
    });

    // Affichage des notifications
    function showToast(message, type) {
        const toastContainer = document.getElementById('toastContainer');
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
});
