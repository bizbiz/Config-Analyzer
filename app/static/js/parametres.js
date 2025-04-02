document.addEventListener('DOMContentLoaded', () => {
    const clientSelect = document.getElementById('clientSelect');
    
    clientSelect.addEventListener('change', loadParams);
    
    async function loadParams() {
        const response = await fetch(`/api/parametres/${clientSelect.value}`);
        const params = await response.json();
        
        const tbody = document.querySelector('#parametresTable tbody');
        tbody.innerHTML = params.map(param => `
            <tr>
                <td>${param.software}</td>
                <td>${param.version}</td>
                <td><pre>${param.config}</pre></td>
                <td>
                    <button class="btn btn-sm btn-danger" onclick="deleteParam(${param.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }
    
    window.deleteParam = async (paramId) => {
        await fetch(`/parametres/${paramId}`, { method: 'DELETE' });
        loadParams();
    };
    
    document.getElementById('paramForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        
        await fetch('/parametres', {
            method: 'POST',
            body: JSON.stringify(Object.fromEntries(formData)),
            headers: { 'Content-Type': 'application/json' }
        });
        
        $('#addParamModal').modal('hide');
        loadParams();
    });
    
    loadParams();
});
