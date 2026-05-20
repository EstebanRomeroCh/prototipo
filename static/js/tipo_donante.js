// Si registraste el blueprint con url_prefix='/api'
const API_TIPO_DONANTE = `${window.location.origin}/api/tipo_donante`;



// ==================== LISTAR TIPOS DE DONANTE ====================
async function tipo_donante() {
    try {
        const res = await fetch(API_TIPO_DONANTE);
        const tipos = await res.json();
        const tbody = document.getElementById('tbodytipo_donante');
        tbody.innerHTML = '';

        tipos.forEach(tipo => {
            const fila = document.createElement('tr');
            fila.innerHTML = `
                <td>${tipo.id_tipo}</td>
                <td>${tipo.nombre}</td>
                <td>${tipo.estado}</td>
                <td>${new Date(tipo.fecha_registro).toLocaleString()}</td>
                <td>
                    <button class="btn btn-sm btn-success me-2" onclick="abrirModalActualizar(${tipo.id_tipo}, '${tipo.nombre}', '${tipo.descripcion}', '${tipo.estado}')">
                        <i class="bi bi-pencil-fill"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="eliminarTipo(${tipo.id_tipo})">
                        <i class="bi bi-trash-fill"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(fila);
        });
    } catch (error) {
        console.error('Error al listar tipos de donante:', error);
    }
}

// ==================== CREAR TIPO DE DONANTE ====================
document.getElementById('formTipoDonante').addEventListener('submit', async (e) => {
    e.preventDefault();
    const nombre = document.getElementById('nombreTipo').value;
    const descripcion = document.getElementById('descripcionTipo').value;

    try {
        const res = await fetch(API_TIPO_DONANTE, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nombre, descripcion })
        });
        const data = await res.json();
        if (data.success) {
            swal("Éxito", "Tipo de donante creado!", "success");
            document.getElementById('formTipoDonante').reset();
            tipo_donante();
        } else {
            swal("Error", data.message, "error");
        }
    } catch (error) {
        console.error('Error al crear tipo de donante:', error);
    }
});

// ==================== ABRIR MODAL PARA ACTUALIZAR ====================
function abrirModalActualizar(id, nombre, descripcion, estado) {
    document.getElementById('idTipoDonanteModal').value = id;
    document.getElementById('nombreTipoDonanteModal').value = nombre;
    document.getElementById('descripcionTipoDonanteModal').value = descripcion;
    document.getElementById('estadoTipoDonanteModal').value = estado;

    const modal = new bootstrap.Modal(document.getElementById('modalActualizarCategoria'));
    modal.show();
}

// ==================== ACTUALIZAR TIPO DE DONANTE ====================
document.getElementById('formActualizartipodonante').addEventListener('submit', async (e) => {
    e.preventDefault();
    const id = document.getElementById('idTipoDonanteModal').value;
    const nombre = document.getElementById('nombreTipoDonanteModal').value;
    const descripcion = document.getElementById('descripcionTipoDonanteModal').value;
    const estado = document.getElementById('estadoTipoDonanteModal').value;

    try {
        const res = await fetch(`${API_TIPO_DONANTE}/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nombre, descripcion, estado })
        });
        const data = await res.json();
        if (data.success) {
            swal("Éxito", "Tipo de donante actualizado!", "success");
            tipo_donante();
            const modal = bootstrap.Modal.getInstance(document.getElementById('modalActualizarCategoria'));
            modal.hide();
        } else {
            swal("Error", data.message, "error");
        }
    } catch (error) {
        console.error('Error al actualizar tipo de donante:', error);
    }
});

// ==================== ELIMINAR TIPO DE DONANTE ====================
async function eliminarTipo(id) {
    const confirmacion = await swal({
        title: "¿Estás seguro?",
        text: "Una vez eliminado no se podrá recuperar!",
        icon: "warning",
        buttons: ["Cancelar", "Sí, eliminar"],
        dangerMode: true,
    });

    if (!confirmacion) return;

    try {
        const res = await fetch(`${API_TIPO_DONANTE}/${id}`, { method: 'DELETE' });
        const data = await res.json();

        if (data.success) {
            swal({
                title: "Eliminado",
                text: "El tipo de donante ha sido eliminado correctamente.",
                icon: "success",
                timer: 2000,
                buttons: false,
            });
            tipo_donante(); // Recarga la lista
        } else {
            // 🔴 Aquí mostramos el mensaje personalizado del backend
            swal({
                title: "No se puede eliminar",
                text: data.message || "Ocurrió un error desconocido.",
                icon: "error",
                button: "Entendido",
            });
        }
    } catch (error) {
        console.error('Error al eliminar tipo de donante:', error);
        swal({
            title: "Error del servidor",
            text: "No se pudo conectar con el backend.",
            icon: "error",
        });
    }
}

// ==================== INICIALIZAR ====================
document.addEventListener('DOMContentLoaded', tipo_donante);
