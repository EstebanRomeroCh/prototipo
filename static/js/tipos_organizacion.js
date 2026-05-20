// static/js/tipos_organizacion.js

let tiposCache = [];
let modalActualizar = null;

document.addEventListener("DOMContentLoaded", () => {
    const formOrganizacion = document.getElementById("formOrganizacion");
    const formActualizar = document.getElementById("formActualizarOrganizacion");

    const modalEl = document.getElementById("modalActualizarOrganizacion");
    if (modalEl && window.bootstrap) {
        modalActualizar = new bootstrap.Modal(modalEl);
    }

    // Cargar lista inicial
    cargarTiposOrganizacion();

    // Crear nuevo tipo
    if (formOrganizacion) {
        formOrganizacion.addEventListener("submit", (e) => {
            e.preventDefault();
            crearTipoOrganizacion();
        });
    }

    // Guardar cambios desde el modal
    if (formActualizar) {
        formActualizar.addEventListener("submit", (e) => {
            e.preventDefault();
            actualizarTipoOrganizacion();
        });
    }

    // Delegación de eventos para botones editar / eliminar
    document.addEventListener("click", (e) => {
        const btnEditar = e.target.closest(".btn-editar-organizacion");
        if (btnEditar) {
            const id = btnEditar.dataset.id;
            abrirModalEditar(id);
            return;
        }

        const btnEliminar = e.target.closest(".btn-eliminar-organizacion");
        if (btnEliminar) {
            const id = btnEliminar.dataset.id;
            confirmarEliminar(id);
            return;
        }
    });
});

// =========================
// Helpers
// =========================
function getTbody() {
    return document.querySelector("#tablaOrganizaciones tbody");
}

function limpiarFormularioPrincipal() {
    document.getElementById("nombreOrganizacion").value = "";
    document.getElementById("descripcionOrganizacion").value = "";
}

// =========================
// Cargar / pintar lista
// =========================
async function cargarTiposOrganizacion() {
    const tbody = getTbody();
    if (tbody) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="text-center">Cargando tipos de organización...</td>
            </tr>
        `;
    }

    try {
        const res = await fetch("/api/tipos_organizacion/");
        if (!res.ok) throw new Error("Error HTTP " + res.status);

        const data = await res.json();
        if (!data.success) throw new Error(data.message || "Error en la API");

        tiposCache = data.items || [];
        pintarTablaTipos(tiposCache);
    } catch (err) {
        console.error("Error al cargar tipos de organización:", err);
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center text-danger">
                        Error al cargar los tipos de organización.
                    </td>
                </tr>
            `;
        }
        if (typeof swal === "function") {
            swal("Error", "No se pudieron cargar los tipos de organización.", "error");
        }
    }
}

function pintarTablaTipos(items) {
    const tbody = getTbody();
    if (!tbody) return;

    tbody.innerHTML = "";

    if (!items || items.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="text-center">
                    No hay tipos de organización registrados.
                </td>
            </tr>
        `;
        return;
    }

    items.forEach((t) => {
        const tr = document.createElement("tr");
        tr.dataset.id = t.id_tipo_organizacion;

        tr.innerHTML = `
            <td>${t.id_tipo_organizacion}</td>
            <td>${t.nombre}</td>
            <td>${t.descripcion || ""}</td>
            <td>
                <button type="button"
                        class="btn btn-sm btn-success me-2 btn-editar-organizacion"
                        data-id="${t.id_tipo_organizacion}">
                    <i class="bi bi-pencil-square"></i>
                </button>
                <button type="button"
                        class="btn btn-sm btn-danger btn-eliminar-organizacion"
                        data-id="${t.id_tipo_organizacion}">
                    <i class="bi bi-trash"></i>
                </button>
                
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// =========================
 // Crear
// =========================
async function crearTipoOrganizacion() {
    const nombre = document.getElementById("nombreOrganizacion").value.trim();
    const descripcion = document.getElementById("descripcionOrganizacion").value.trim();

    if (!nombre) {
        if (typeof swal === "function") {
            swal("Atención", "El nombre del tipo de organización es obligatorio.", "warning");
        }
        return;
    }

    try {
        const res = await fetch("/api/tipos_organizacion/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                nombre,
                descripcion
            })
        });

        const data = await res.json();

        if (!res.ok || !data.success) {
            const msg = data.message || "Error al crear el tipo de organización.";
            if (typeof swal === "function") swal("Error", msg, "error");
            return;
        }

        if (typeof swal === "function") {
            swal("Éxito", "Tipo de organización creado correctamente.", "success");
        }

        limpiarFormularioPrincipal();
        // Recargar lista (o agregar al cache manualmente)
        cargarTiposOrganizacion();

    } catch (err) {
        console.error("Error creando tipo de organización:", err);
        if (typeof swal === "function") {
            swal("Error", "Error de comunicación con el servidor.", "error");
        }
    }
}

// =========================
// Abrir modal de edición
// =========================
function abrirModalEditar(id) {
    id = Number(id);
    const item = tiposCache.find((t) => t.id_tipo_organizacion === id);
    if (!item) return;

    document.getElementById("idOrganizacionModal").value = item.id_tipo_organizacion;
    document.getElementById("categoriaOrganizacionModal").value = item.nombre || "";
    document.getElementById("descripcionOrganizacionModal").value = item.descripcion || "";

    if (modalActualizar) {
        modalActualizar.show();
    }
}

// =========================
// Actualizar (desde modal)
// =========================
async function actualizarTipoOrganizacion() {
    const id = Number(document.getElementById("idOrganizacionModal").value);
    const nombre = document.getElementById("categoriaOrganizacionModal").value.trim();
    const descripcion = document.getElementById("descripcionOrganizacionModal").value.trim();

    if (!nombre) {
        if (typeof swal === "function") {
            swal("Atención", "El nombre del tipo de organización es obligatorio.", "warning");
        }
        return;
    }

    try {
        const res = await fetch(`/api/tipos_organizacion/${id}`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                nombre,
                descripcion
            })
        });

        const data = await res.json();

        if (!res.ok || !data.success) {
            const msg = data.message || "Error al actualizar el tipo de organización.";
            if (typeof swal === "function") swal("Error", msg, "error");
            return;
        }

        if (typeof swal === "function") {
            swal("Éxito", "Tipo de organización actualizado correctamente.", "success");
        }

        if (modalActualizar) {
            modalActualizar.hide();
        }

        // Recargar listado
        cargarTiposOrganizacion();

    } catch (err) {
        console.error("Error actualizando tipo de organización:", err);
        if (typeof swal === "function") {
            swal("Error", "Error de comunicación con el servidor.", "error");
        }
    }
}

// =========================
// Eliminar (soft delete)
// =========================
function confirmarEliminar(id) {
    if (typeof swal !== "function") {
        if (confirm("¿Eliminar este tipo de organización?")) {
            eliminarTipoOrganizacion(id);
        }
        return;
    }

    swal({
        title: "Confirmar eliminación",
        text: "El tipo de organización será marcado como Inactivo. ¿Desea continuar?",
        icon: "warning",
        buttons: ["Cancelar", "Sí, eliminar"],
        dangerMode: true
    }).then((confirmado) => {
        if (confirmado) {
            eliminarTipoOrganizacion(id);
        }
    });
}

async function eliminarTipoOrganizacion(id) {
    id = Number(id);

    try {
        const res = await fetch(`/api/tipos_organizacion/${id}`, {
            method: "DELETE"
        });

        const data = await res.json();

        if (!res.ok || !data.success) {
            const msg = data.message || "Error al eliminar el tipo de organización.";
            if (typeof swal === "function") swal("Error", msg, "error");
            return;
        }

        if (typeof swal === "function") {
            swal("Éxito", "Tipo de organización eliminado correctamente.", "success");
        }

        // Recargar listado
        cargarTiposOrganizacion();

    } catch (err) {
        console.error("Error eliminando tipo de organización:", err);
        if (typeof swal === "function") {
            swal("Error", "Error de comunicación con el servidor.", "error");
        }
    }
}
