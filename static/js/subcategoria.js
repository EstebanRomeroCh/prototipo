// ==============================
// CONFIGURACIÓN INICIAL
// ==============================
let editandoSubcategoria = null;
let categorias = []; // Para almacenar las categorías cargadas
const formSubcategoria = document.getElementById('formSubcategoria');
const tablaSubcategorias = document.getElementById('tablaSubcategorias').querySelector('tbody');
const API_SUBCATEGORIAS = '/api/subcategorias';
const API_CATEGORIAS = '/api/categorias';

// ==============================
// CARGAR TODAS LAS SUBCATEGORÍAS
// ==============================
async function cargarSubcategorias() {
    try {
        const res = await fetch(API_SUBCATEGORIAS);
        const subcategorias = await res.json();

        tablaSubcategorias.innerHTML = '';
        subcategorias.forEach(sub => agregarFilaSubcategoria(sub));
    } catch (error) {
        console.error('Error cargando subcategorías:', error);
        swal("Error", "No se pudieron cargar las subcategorías", "error");
    }
}

// ==============================
// CARGAR CATEGORÍAS EN LOS SELECT
// ==============================
async function cargarCategoriasSelect() {
    try {
        const res = await fetch(API_CATEGORIAS);
        categorias = await res.json();

        const selectCrear = document.getElementById('categoriaSelect');
        const selectModal = document.getElementById('categoriaSubcategoriaModal');

        selectCrear.innerHTML = '<option value="">Selecciona una categoría</option>';
        selectModal.innerHTML = '<option value="">Selecciona una categoría</option>';

        categorias.forEach(cat => {
            const option = `<option value="${cat[0]}">${cat[1]}</option>`;
            selectCrear.innerHTML += option;
            selectModal.innerHTML += option;
        });
    } catch (error) {
        console.error('Error cargando categorías:', error);
    }
}

// ==============================
// AGREGAR FILA A LA TABLA
// ==============================
function agregarFilaSubcategoria(sub) {
    const row = document.createElement('tr');
    
    row.innerHTML = `
        <td class="col-id">${sub[0]}</td>
        <td class="col-nombre">${sub[1]}</td>
        <td class="col-descripcion">${sub[2]}</td>
        <td class="col-id-categoria">${sub[3]}</td>
        <td>
            <button class="btn btn-sm btn-success me-2" onclick="abrirModalEditarSubcategoria(${sub[0]})">
                <i class="bi bi-pencil-fill"></i>
            </button>
            <button class="btn btn-sm btn-danger" onclick="eliminarSubcategoria(${sub[0]})">
                <i class="bi bi-trash-fill"></i>
            </button>
        </td>
    `;
    tablaSubcategorias.appendChild(row);
}

// ==============================
// CREAR NUEVA SUBCATEGORÍA
// ==============================
formSubcategoria.addEventListener('submit', async function(e) {
    e.preventDefault();

    const nombre = document.getElementById('nombreSubcategoria').value.trim();
    const descripcion = document.getElementById('descripcionSubcategoria').value.trim();
    const id_categoria = document.getElementById('categoriaSelect').value;

    if (!nombre || !id_categoria) {
        swal("Error", "Todos los campos son obligatorios", "error");
        return;
    }

    try {
        const res = await fetch(API_SUBCATEGORIAS, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nombre, descripcion, id_categoria })
        });

        const data = await res.json();

        if (res.ok && data.success) {
            agregarFilaSubcategoria(data.subcategoria);
            formSubcategoria.reset();
            swal("Éxito", "Subcategoría creada correctamente", "success");
        } else {
            swal("Error", data.message || "No se pudo crear la subcategoría", "error");
        }
    } catch (error) {
        console.error('Error creando subcategoría:', error);
        swal("Error", "No se pudo crear la subcategoría", "error");
    }
});

// ==============================
// ABRIR MODAL PARA EDITAR
// ==============================
async function abrirModalEditarSubcategoria(id) {
    try {
        const res = await fetch(`${API_SUBCATEGORIAS}/${id}`);
        const sub = await res.json();

        document.getElementById('idSubcategoriaModal').value = sub[0];
        document.getElementById('nombreSubcategoriaModal').value = sub[1];
        document.getElementById('descripcionSubcategoriaModal').value = sub[2];
        document.getElementById('categoriaSubcategoriaModal').value = sub[3];

        editandoSubcategoria = Array.from(tablaSubcategorias.rows).find(
            row => row.querySelector('.col-id').textContent == id
        );

        const modal = new bootstrap.Modal(document.getElementById('modalActualizarSubcategoria'));
        modal.show();
    } catch (error) {
        console.error("Error cargando subcategoría:", error);
        swal("Error", "No se pudo cargar la subcategoría", "error");
    }
}

// ==============================
// ACTUALIZAR SUBCATEGORÍA
// ==============================
document.getElementById('formActualizarSubcategoria').addEventListener('submit', async function(e) {
    e.preventDefault();

    const id = document.getElementById('idSubcategoriaModal').value;
    const nombre = document.getElementById('nombreSubcategoriaModal').value.trim();
    const id_categoria = document.getElementById('categoriaSubcategoriaModal').value;
    const descripcion = document.getElementById('descripcionSubcategoriaModal').value.trim();

    if (!nombre || !id_categoria) {
        swal("Error", "Todos los campos son obligatorios", "error");
        return;
    }

    try {
        const res = await fetch(`${API_SUBCATEGORIAS}/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nombre, descripcion, id_categoria })
        });

        const data = await res.json();

        if (res.ok && data.success) {
            editandoSubcategoria.querySelector('.col-nombre').textContent = data.subcategoria[1];
            editandoSubcategoria.querySelector('.col-descripcion').textContent = data.subcategoria[2];
            editandoSubcategoria.querySelector('.col-id-categoria').textContent = data.subcategoria[3];

            const modal = bootstrap.Modal.getInstance(document.getElementById('modalActualizarSubcategoria'));
            modal.hide();

            swal("Actualizado", "Subcategoría actualizada correctamente", "success");
            editandoSubcategoria = null;
        } else {
            swal("Error", data.message || "No se pudo actualizar la subcategoría", "error");
        }
    } catch (error) {
        console.error('Error actualizando subcategoría:', error);
        swal("Error", "No se pudo actualizar la subcategoría", "error");
    }
});

// ==============================
// ELIMINAR SUBCATEGORÍA
// ==============================
async function eliminarSubcategoria(id) {
    const row = Array.from(tablaSubcategorias.rows).find(r => r.querySelector('.col-id').textContent == id);

    const confirm = await swal({
        title: "¿Está seguro?",
        text: "Esta acción no se puede deshacer",
        icon: "warning",
        buttons: true,
        dangerMode: true,
    });

    if (!confirm) return;

    try {
        const res = await fetch(`${API_SUBCATEGORIAS}/${id}`, { method: 'DELETE' });
        const data = await res.json();

        if (res.ok) {
            row.remove();
            swal("Eliminado", data.message || "Subcategoría eliminada", "success");
        } else {
            swal("Error", data.message || "No se pudo eliminar la subcategoría", "error");
        }
    } catch (error) {
        console.error('Error eliminando subcategoría:', error);
        swal("Error", "No se pudo eliminar la subcategoría", "error");
    }
}

// ==============================
// INICIALIZACIÓN
// ==============================
document.addEventListener('DOMContentLoaded', () => {
    cargarCategoriasSelect();
    cargarSubcategorias();
});
