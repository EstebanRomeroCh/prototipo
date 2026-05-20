// static/js/parroquias.js

// ==============================
// Referencias globales
// ==============================
let tiposOrganizacionCache = [];
let tiposDocumentoCache = [];

let parroquiasTableBody = null;
let formParroquia = null;
let modalActualizar = null;
let formActualizarParroquia = null;

// ==============================
// Helpers
// ==============================

function mostrarErrorSwal(titulo, mensaje) {
    if (typeof swal === "function") {
        swal(titulo || "Error", mensaje || "Ocurrió un error", "error");
    } else {
        alert((titulo ? titulo + ": " : "") + (mensaje || "Error"));
    }
}

function mostrarOkSwal(titulo, mensaje) {
    if (typeof swal === "function") {
        swal(titulo || "OK", mensaje || "Operación realizada correctamente.", "success");
    } else {
        alert((titulo ? titulo + ": " : "") + (mensaje || "OK"));
    }
}

// Obtener texto visible de un <select>
function getSelectedText(selectEl) {
    if (!selectEl) return "";
    const opt = selectEl.options[selectEl.selectedIndex];
    return opt ? opt.textContent.trim() : "";
}

// ==============================
// Cargar combos (tipos org / tipo doc)
// ==============================

async function cargarTiposOrganizacion() {
    try {
        const res = await fetch("/parroquias/api/tipos_organizacion");
        if (!res.ok) throw new Error("HTTP " + res.status);
        const data = await res.json();
        if (!data.success) throw new Error(data.message || "Error en tipos de organización");

        tiposOrganizacionCache = data.items || [];

        const selectPrincipal = document.getElementById("tipo_organizacion");
        const selectModal = document.getElementById("categoriaParroquiaModal");

        if (selectPrincipal) {
            selectPrincipal.innerHTML = `<option value="">Tipo de organización</option>`;
            tiposOrganizacionCache.forEach(t => {
                const opt = document.createElement("option");
                opt.value = t.id_tipo_organizacion;
                opt.textContent = t.nombre;
                selectPrincipal.appendChild(opt);
            });
        }

        if (selectModal) {
            selectModal.innerHTML = `<option value="">Selecciona un tipo</option>`;
            tiposOrganizacionCache.forEach(t => {
                const opt = document.createElement("option");
                opt.value = t.id_tipo_organizacion;
                opt.textContent = t.nombre;
                selectModal.appendChild(opt);
            });
        }

    } catch (err) {
        console.error("Error cargando tipos de organización:", err);
        mostrarErrorSwal("Error", "No se pudieron cargar los tipos de organización.");
    }
}

async function cargarTiposDocumento() {
    try {
        const res = await fetch("/parroquias/api/tipos_documento");
        if (!res.ok) throw new Error("HTTP " + res.status);
        const data = await res.json();
        if (!data.success) throw new Error(data.message || "Error en tipos de documento");

        tiposDocumentoCache = data.items || [];

        const selectPrincipal = document.getElementById("tipoDocumento");
        // OJO: en tu modal hay 3 selects con id="tipo", usamos el primero (tipo documento)
        const selectModal = document.querySelector("#modalActualizarParroquia select[id='tipo']");

        if (selectPrincipal) {
            selectPrincipal.innerHTML = `<option value="">Tipo de documento</option>`;
            tiposDocumentoCache.forEach(t => {
                const opt = document.createElement("option");
                opt.value = t.id_tipo_doc;
                opt.textContent = t.nombre;
                selectPrincipal.appendChild(opt);
            });
        }

        if (selectModal) {
            selectModal.innerHTML = `<option value="">Selecciona un tipo</option>`;
            tiposDocumentoCache.forEach(t => {
                const opt = document.createElement("option");
                opt.value = t.id_tipo_doc;
                opt.textContent = t.nombre;
                selectModal.appendChild(opt);
            });
        }

    } catch (err) {
        console.error("Error cargando tipos de documento:", err);
        mostrarErrorSwal("Error", "No se pudieron cargar los tipos de documento.");
    }
}

// ==============================
// API Colombia (Departamentos / Municipios) - FORM PRINCIPAL
// ==============================

const selectDeptos = document.getElementById("departamentos");
const selectMunicipios = document.getElementById("municipios");

async function cargarDepartamentosColombia() {
    if (!selectDeptos) return;

    try {
        const res = await fetch("https://api-colombia.com/api/v1/Department");
        const data = await res.json();

        selectDeptos.innerHTML = `<option selected disabled>Departamentos</option>`;

        data.forEach(depto => {
            const option = document.createElement("option");
            option.value = depto.id;
            option.textContent = depto.name;
            selectDeptos.appendChild(option);
        });
    } catch (err) {
        console.error("Error cargando departamentos:", err);
        selectDeptos.innerHTML = `<option disabled>Error al cargar departamentos</option>`;
    }
}

async function traer() {
    if (!selectDeptos || !selectMunicipios) return;

    const id = selectDeptos.value;
    if (!id) return;

    selectMunicipios.innerHTML = '<option selected disabled>Cargando...</option>';
    selectMunicipios.disabled = true;

    try {
        const res = await fetch(`https://api-colombia.com/api/v1/Department/${id}/cities`);
        const data = await res.json();

        selectMunicipios.innerHTML = "";
        if (!data || data.length === 0) {
            selectMunicipios.innerHTML = '<option disabled>No hay municipios</option>';
            return;
        }

        selectMunicipios.disabled = false;

        const defaultOption = document.createElement("option");
        defaultOption.text = "Seleccione un municipio";
        defaultOption.disabled = true;
        defaultOption.selected = true;
        selectMunicipios.appendChild(defaultOption);

        data.forEach(city => {
            const option = document.createElement("option");
            option.value = city.id;
            option.textContent = city.name;
            selectMunicipios.appendChild(option);
        });
    } catch (err) {
        console.error("Error cargando municipios:", err);
        selectMunicipios.innerHTML = '<option disabled>Error al cargar</option>';
    }
}

// Hacer traer() global porque lo usas en el HTML: onchange="traer()"
window.traer = traer;

// ==============================
// LISTAR PARROQUIAS
// ==============================

async function cargarParroquias() {
    if (!parroquiasTableBody) return;

    parroquiasTableBody.innerHTML = `
        <tr>
            <td colspan="7" class="text-center">Cargando parroquias...</td>
        </tr>
    `;

    try {
        const res = await fetch("/parroquias/api/listar");
        if (!res.ok) throw new Error("HTTP " + res.status);
        const data = await res.json();
        if (!data.success) throw new Error(data.message || "Error al listar");

        pintarTablaParroquias(data.parroquias || []);
    } catch (err) {
        console.error("Error cargando parroquias:", err);
        parroquiasTableBody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center text-danger">
                    Error al cargar las parroquias.
                </td>
            </tr>
        `;
    }
}

function pintarTablaParroquias(parroquias) {
    parroquiasTableBody.innerHTML = "";

    if (!parroquias || parroquias.length === 0) {
        parroquiasTableBody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center">
                    No hay parroquias registradas.
                </td>
            </tr>
        `;
        return;
    }

    parroquias.forEach(p => {
        const tr = document.createElement("tr");

        // Guardamos datos completos en data-*
        tr.dataset.idParroquia = p.id_parroquia;
        tr.dataset.idTipoOrganizacion = p.id_tipo_organizacion;
        tr.dataset.idTipoDocumento = p.id_tipo_doc;

        tr.dataset.nombre = p.nombre || "";
        tr.dataset.nombreEncargado = p.nombre_encargado || "";
        tr.dataset.numeroDocumento = p.numero_documento || "";
        tr.dataset.telefono = p.telefono || "";
        tr.dataset.direccion = p.direccion || "";
        tr.dataset.correo = p.correo || "";
        tr.dataset.familiasAtendidas = p.familias_atendidas || "";
        tr.dataset.departamento = p.departamento || "";
        tr.dataset.municipio = p.municipio || "";
        tr.dataset.estado = p.estado || "Activo";

        tr.innerHTML = `
            <td>${p.id_parroquia}</td>
            <td>${p.nombre || ""}</td>
            <td>${p.tipo_organizacion || ""}</td>
            <td>${p.nombre_encargado || ""}</td>
            <td>${p.telefono || ""}</td>
            <td>${p.municipio || ""}</td>
            <td>
                <button type="button"
                        class="btn btn-sm btn-success me-2 btn-editar-parroquia">
                        <i class="bi bi-pencil-fill"></i>
                
                </button>
                <button type="button"
                        class="btn btn-sm btn-danger btn-eliminar-parroquia ms-1">
                        <i class="bi bi-trash-fill"></i>
                    
                </button>
                
            </td>
        `;

        parroquiasTableBody.appendChild(tr);
    });
}

// ==============================
// CREAR PARROQUIA
// ==============================

async function onSubmitCrearParroquia(evt) {
    evt.preventDefault();

    const nombre = document.getElementById("nombreParroquia")?.value.trim() || "";
    const idTipoOrg = document.getElementById("tipo_organizacion")?.value || "";
    const nombreEncargado = document.getElementById("nombrePadre")?.value.trim() || "";
    const idTipoDoc = document.getElementById("tipoDocumento")?.value || "";
    const numeroDocumento = document.getElementById("numeroDocumento")?.value.trim() || "";
    const telefono = document.getElementById("telefono")?.value.trim() || "";
    const direccion = document.getElementById("direccion")?.value.trim() || "";
    const correo = document.getElementById("correo")?.value.trim() || "";
    const familiasAtendidas = Number(
        document.getElementById("familiasAtendidas")?.value || 0
    );

    const departamentoNombre = getSelectedText(selectDeptos);
    const municipioNombre = getSelectedText(selectMunicipios);

    if (!nombre || !nombreEncargado || !numeroDocumento) {
        mostrarErrorSwal("Validación", "Nombre de parroquia, encargado y documento son obligatorios.");
        return;
    }
    if (!idTipoOrg || !idTipoDoc) {
        mostrarErrorSwal("Validación", "Debe seleccionar tipo de organización y tipo de documento.");
        return;
    }

    const payload = {
        id_tipo_organizacion: Number(idTipoOrg),
        tipo_doc_id: Number(idTipoDoc),
        nombre,
        nombre_encargado: nombreEncargado,
        numero_documento: numeroDocumento,
        telefono,
        direccion,
        correo,
        familias_atendidas: familiasAtendidas,
        departamento: departamentoNombre,
        municipio: municipioNombre
    };

    try {
        const res = await fetch("/parroquias/api/crear", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok || !data.success) {
            throw new Error(data.message || "Error al crear la parroquia.");
        }

        mostrarOkSwal("Éxito", "Parroquia registrada correctamente.");
        formParroquia.reset();
        // Reiniciar combos de deptos/municipios
        if (selectMunicipios) {
            selectMunicipios.innerHTML = '<option disabled selected>Municipios</option>';
            selectMunicipios.disabled = true;
        }
        await cargarParroquias();
    } catch (err) {
        console.error("Error creando parroquia:", err);
        mostrarErrorSwal("Error", err.message || "No se pudo crear la parroquia.");
    }
}

// ==============================
// EDITAR / ELIMINAR (event delegation)
// ==============================

function onClickTablaParroquias(evt) {
    const btnEditar = evt.target.closest(".btn-editar-parroquia");
    const btnEliminar = evt.target.closest(".btn-eliminar-parroquia");

    if (btnEditar) {
        const tr = btnEditar.closest("tr");
        abrirModalEditarParroquia(tr);
        return;
    }
    if (btnEliminar) {
        const tr = btnEliminar.closest("tr");
        confirmarEliminarParroquia(tr);
        return;
    }
}

function abrirModalEditarParroquia(tr) {
    if (!tr || !modalActualizar) return;

    const id = tr.dataset.idParroquia || "";
    const nombre = tr.dataset.nombre || "";
    const idTipoOrg = tr.dataset.idTipoOrganizacion || "";
    const nombreEncargado = tr.dataset.nombreEncargado || "";
    const idTipoDoc = tr.dataset.idTipoDocumento || "";
    const numeroDocumento = tr.dataset.numeroDocumento || "";
    const telefono = tr.dataset.telefono || "";
    const direccion = tr.dataset.direccion || "";
    const correo = tr.dataset.correo || "";
    const familias = tr.dataset.familiasAtendidas || "";
    const departamento = tr.dataset.departamento || "";
    const municipio = tr.dataset.municipio || "";
    const estado = tr.dataset.estado || "Activo";

    document.getElementById("idParroquiaModal").value = id;
    document.getElementById("nombreParroquiaModal").value = nombre;
    document.getElementById("nombrePadreModal").value = nombreEncargado;
    document.getElementById("numeroDocumentoModal").value = numeroDocumento;
    document.getElementById("numeroTelefonoModal").value = telefono;
    document.getElementById("direccionParroquiaModal").value = direccion;
    document.getElementById("correoParroquiaModal").value = correo;

    const familiasInput = document.getElementById("familiasAtendidasModal");
    if (familiasInput) familiasInput.value = familias;

    // Tipo organización modal
    const selTipoOrgModal = document.getElementById("categoriaParroquiaModal");
    if (selTipoOrgModal) {
        selTipoOrgModal.value = idTipoOrg || "";
    }

    // Tipo documento modal (primer <select id="tipo"> del modal)
    const selTipoDocModal = document.querySelector("#modalActualizarParroquia select[id='tipo']");
    if (selTipoDocModal) {
        selTipoDocModal.value = idTipoDoc || "";
    }

    // Si quieres guardar departamento/municipio en algún input del modal,
    // podrías agregarlos al HTML luego. Por ahora solo mostramos datos básicos.

    // Estado (si luego agregas un select de estado en el modal)
    const selEstadoModal = document.getElementById("estadoParroquiaModal");
    if (selEstadoModal) {
        selEstadoModal.value = estado;
    }

    modalActualizar.show();
}

async function confirmarEliminarParroquia(tr) {
    if (!tr) return;
    const id = tr.dataset.idParroquia;
    const nombre = tr.dataset.nombre || "";

    if (!id) return;

    const msg = `¿Seguro que deseas eliminar la parroquia "${nombre}" (ID ${id})?`;

    if (typeof swal === "function") {
        const willDelete = await swal({
            title: "Confirmar eliminación",
            text: msg,
            icon: "warning",
            buttons: ["Cancelar", "Eliminar"],
            dangerMode: true,
        });

        if (!willDelete) return;
    } else {
        if (!confirm(msg)) return;
    }

    try {
        const res = await fetch(`/parroquias/api/${id}`, {
            method: "DELETE"
        });
        const data = await res.json();
        if (!res.ok || !data.success) {
            throw new Error(data.message || "Error al eliminar la parroquia.");
        }

        mostrarOkSwal("Eliminada", "Parroquia eliminada correctamente.");
        await cargarParroquias();
    } catch (err) {
        console.error("Error eliminando parroquia:", err);
        mostrarErrorSwal("Error", err.message || "No se pudo eliminar la parroquia.");
    }
}

// ==============================
// ACTUALIZAR PARROQUIA (submit modal)
// ==============================

async function onSubmitActualizarParroquia(evt) {
    evt.preventDefault();

    const id = document.getElementById("idParroquiaModal")?.value || "";
    if (!id) {
        mostrarErrorSwal("Error", "No se encontró el ID de la parroquia.");
        return;
    }

    const nombre = document.getElementById("nombreParroquiaModal")?.value.trim() || "";
    const nombreEncargado = document.getElementById("nombrePadreModal")?.value.trim() || "";
    const numeroDocumento = document.getElementById("numeroDocumentoModal")?.value.trim() || "";
    const telefono = document.getElementById("numeroTelefonoModal")?.value.trim() || "";
    const direccion = document.getElementById("direccionParroquiaModal")?.value.trim() || "";
    const correo = document.getElementById("correoParroquiaModal")?.value.trim() || "";

    const selTipoOrgModal = document.getElementById("categoriaParroquiaModal");
    const idTipoOrg = selTipoOrgModal ? selTipoOrgModal.value : "";

    const selTipoDocModal = document.querySelector("#modalActualizarParroquia select[id='tipo']");
    const idTipoDoc = selTipoDocModal ? selTipoDocModal.value : "";

    const familiasInput = document.getElementById("familiasAtendidasModal");
    const familiasAtendidas = familiasInput ? Number(familiasInput.value || 0) : 0;

    const selEstadoModal = document.getElementById("estadoParroquiaModal");
    const estado = selEstadoModal ? selEstadoModal.value : "Activo";

    if (!nombre || !nombreEncargado || !numeroDocumento) {
        mostrarErrorSwal("Validación", "Nombre de parroquia, encargado y documento son obligatorios.");
        return;
    }
    if (!idTipoOrg || !idTipoDoc) {
        mostrarErrorSwal("Validación", "Debe seleccionar tipo de organización y tipo de documento.");
        return;
    }

    const payload = {
        id_tipo_organizacion: Number(idTipoOrg),
        tipo_doc_id: Number(idTipoDoc),
        nombre,
        nombre_encargado: nombreEncargado,
        numero_documento: numeroDocumento,
        telefono,
        direccion,
        correo,
        familias_atendidas: familiasAtendidas,
        // por ahora no editamos dpto/municipio en el modal (puedes agregar inputs si lo deseas)
        departamento: null,
        municipio: null,
        estado
    };

    try {
        const res = await fetch(`/parroquias/api/${id}`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok || !data.success) {
            throw new Error(data.message || "Error al actualizar la parroquia.");
        }

        mostrarOkSwal("Actualizada", "Parroquia actualizada correctamente.");
        if (modalActualizar) modalActualizar.hide();
        await cargarParroquias();
    } catch (err) {
        console.error("Error actualizando parroquia:", err);
        mostrarErrorSwal("Error", err.message || "No se pudo actualizar la parroquia.");
    }
}

// ==============================
// INIT
// ==============================

document.addEventListener("DOMContentLoaded", () => {
    parroquiasTableBody = document.querySelector("#tablaParroquias tbody");
    formParroquia = document.getElementById("formParroquia");
    formActualizarParroquia = document.getElementById("formActualizarParroquia");

    const modalEl = document.getElementById("modalActualizarParroquia");
    if (modalEl && window.bootstrap && bootstrap.Modal) {
        modalActualizar = new bootstrap.Modal(modalEl);
    }

    // Eventos
    if (formParroquia) {
        formParroquia.addEventListener("submit", onSubmitCrearParroquia);
    }
    if (parroquiasTableBody) {
        parroquiasTableBody.addEventListener("click", onClickTablaParroquias);
    }
    if (formActualizarParroquia) {
        formActualizarParroquia.addEventListener("submit", onSubmitActualizarParroquia);
    }

    // Cargar combos y tabla
    cargarTiposOrganizacion();
    cargarTiposDocumento();
    cargarDepartamentosColombia();
    cargarParroquias();
});
