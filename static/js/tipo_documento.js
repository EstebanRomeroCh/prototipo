'use strict';

const STORAGE_KEY = 'paramsBancoAlimentos_v1';
const initialStructure = {
    document: [],
    gender: [],
    status: []
};

let systemParams = {};

// ================================
// LocalStorage
// ================================
function saveParams() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(systemParams));
}

function loadParams() {
    const raw = localStorage.getItem(STORAGE_KEY);
    systemParams = raw ? JSON.parse(raw) : { ...initialStructure };
}

// ================================
// Renderizado
// ================================
const paramsContainer = document.getElementById('paramsContainer');

function clearParamsGrid() {
    paramsContainer.innerHTML = '';
}

function createParamCard(type, param) {
    const card = document.createElement('article');
    card.className = 'param-card';
    card.dataset.type = type;
    card.dataset.code = param.code;

    card.innerHTML = `
        <div class="param-header">
            <span class="param-code">${param.code}</span>
            <span class="param-status ${param.status === 'active' ? 'status-active' : 'status-inactive'}">
                ${param.status === 'active' ? 'Activo' : 'Inactivo'}
            </span>
        </div>

        <h3 class="param-name">${param.name}</h3>
        <div class="param-desc">${param.description || ''}</div>

        <div class="param-actions">
            <button class="action-btn edit-btn" data-action="edit">
                <i class="fas fa-edit"></i> Editar
            </button>

            <button class="action-btn delete-btn" data-action="delete">
                <i class="fas fa-trash"></i> Desactivar
            </button>
        </div>
    `;

    return card;
}

function renderParams(filterType = 'all', searchTerm = '') {
    clearParamsGrid();

    const term = String(searchTerm).toLowerCase();

    Object.keys(systemParams).forEach(type => {
        systemParams[type].forEach(param => {
            if (filterType !== 'all' && filterType !== type) return;

            const name = String(param.name || '').toLowerCase();
            const code = String(param.code || '').toLowerCase();

            if (term && !name.includes(term) && !code.includes(term)) return;

            paramsContainer.appendChild(createParamCard(type, param));
        });
    });
}

function getActiveFilter() {
    const activeBtn = document.querySelector('.param-type-btn.active');
    return activeBtn ? activeBtn.dataset.type : 'all';
}

// ================================
// Backend: Tipo Documento
// ================================
async function cargarTiposDocumento() {
    try {
        const response = await fetch('/api/tipo_documento/');
        const data = await response.json();

        if (!data.success) {
            mostrarError(data.message || 'Error al cargar tipos de documento');
            return;
        }

        systemParams.document = data.items.map(t => ({
            id: t.id_tipo_doc,
            code: String(t.id_tipo_doc),
            name: t.nombre,
            description: t.descripcion || '',
            status: t.estado === 'activo' ? 'active' : 'inactive'
        }));

    } catch (error) {
        console.error('Error cargando tipos de documento:', error);
        mostrarError('Error al cargar tipos de documento');
    }
}

async function guardarTipoDocumento(nombre, descripcion) {
    try {
        const response = await fetch('/api/tipo_documento/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                nombre,
                descripcion
            })
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            mostrarError(data.message || 'Error al guardar el tipo de documento');
            return false;
        }

        mostrarExito(data.message || 'Tipo de documento guardado correctamente');
        await cargarTiposDocumento();
        renderParams('document');
        return true;

    } catch (error) {
        console.error(error);
        mostrarError('Error al guardar el tipo de documento');
        return false;
    }
}

async function editarTipoDocumento(id, nombre, descripcion) {
    try {
        const response = await fetch(`/api/tipo_documento/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                nombre,
                descripcion
            })
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            mostrarError(data.message || 'Error al actualizar el tipo de documento');
            return false;
        }

        mostrarExito(data.message || 'Tipo de documento actualizado correctamente');
        await cargarTiposDocumento();
        renderParams('document');
        return true;

    } catch (error) {
        console.error(error);
        mostrarError('Error al actualizar el tipo de documento');
        return false;
    }
}

async function eliminarTipoDocumento(id) {
    try {
        const response = await fetch(`/api/tipo_documento/${id}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            mostrarError(data.message || 'Error al desactivar el tipo de documento');
            return false;
        }

        mostrarExito(data.message || 'Tipo de documento desactivado correctamente');
        await cargarTiposDocumento();
        renderParams('document');
        return true;

    } catch (error) {
        console.error(error);
        mostrarError('Error al desactivar el tipo de documento');
        return false;
    }
}

// ================================
// Formulario
// ================================
document.getElementById('parameterForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const tipo = document.getElementById('paramType').value;
    const nombre = document.getElementById('name').value.trim();
    const descripcion = document.getElementById('description').value.trim();
    const editId = document.getElementById('editOldCode').value;

    if (!nombre) {
        mostrarAdvertencia('El nombre es obligatorio');
        return;
    }

    let operacionExitosa = false;

    if (tipo === 'document') {
        if (editId) {
            operacionExitosa = await editarTipoDocumento(editId, nombre, descripcion);
            if (operacionExitosa) {
                document.getElementById('editOldCode').value = '';
            }
        } else {
            operacionExitosa = await guardarTipoDocumento(nombre, descripcion);
        }
    } else {
        const code = Date.now().toString();

        systemParams[tipo].push({
            code,
            name: nombre,
            description: descripcion,
            status: 'active'
        });

        saveParams();
        renderParams(tipo);
        mostrarExito('Parámetro guardado correctamente');
        operacionExitosa = true;
    }

    if (operacionExitosa) {
        document.getElementById('parameterForm').reset();
        document.getElementById('modal').classList.remove('show');
    }
});

// ================================
// Acciones de la grilla
// ================================
paramsContainer.addEventListener('click', async (e) => {
    const btn = e.target.closest('button');
    if (!btn) return;

    const card = btn.closest('.param-card');
    if (!card) return;

    const type = card.dataset.type;
    const code = card.dataset.code;
    const action = btn.dataset.action;

    const param = systemParams[type]?.find(p => String(p.code) === String(code));
    if (!param) return;

    if (action === 'edit') {
        document.getElementById('paramType').value = type;
        document.getElementById('name').value = param.name;
        document.getElementById('description').value = param.description || '';
        document.getElementById('editOldCode').value = type === 'document' ? param.id : param.code;

        document.getElementById('modalTitle').textContent = 'Editar parámetro';
        document.getElementById('modal').classList.add('show');
        return;
    }

    if (action === 'delete') {
        if (type === 'document') {
            confirmarEliminacion(async () => {
                await eliminarTipoDocumento(param.id);
            });
        } else {
            confirmarEliminacion(() => {
                systemParams[type] = systemParams[type].filter(
                    p => String(p.code) !== String(code)
                );
                saveParams();
                renderParams(getActiveFilter());
                mostrarExito('Parámetro eliminado correctamente');
            });
        }
    }
});

// ================================
// Inicialización
// ================================
document.addEventListener('DOMContentLoaded', async () => {
    loadParams();
    await cargarTiposDocumento();
    renderParams('document');

    const modal = document.getElementById('modal');
    const form = document.getElementById('parameterForm');

    document.getElementById('openAdd').addEventListener('click', () => {
        form.reset();
        document.getElementById('editOldCode').value = '';
        document.getElementById('modalTitle').textContent = 'Agregar parámetro';
        modal.classList.add('show');
    });

    document.getElementById('closeModalBtn').addEventListener('click', () => {
        modal.classList.remove('show');
    });

    document.getElementById('searchInput').addEventListener('input', (e) => {
        renderParams(getActiveFilter(), e.target.value);
    });

    document.querySelectorAll('.param-type-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.param-type-btn')
                .forEach(b => b.classList.remove('active'));

            btn.classList.add('active');

            renderParams(
                btn.dataset.type,
                document.getElementById('searchInput').value
            );
        });
    });
});