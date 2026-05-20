// static/js/fundaciones.js

let tiposOrganizacionCache = [];
let tiposDocumentoCache = [];

let tbodyFundaciones = null;
let formFundacion = null;

let modalActualizar = null;
let formActualizar = null;

// selects Colombia (crear)
let selectDeptos = null;
let selectMunicipios = null;

// ------------------------------
// SweetAlert helpers
// ------------------------------
function mostrarErrorSwal(titulo, mensaje) {
  if (typeof swal === "function") swal(titulo || "Error", mensaje || "Ocurrió un error", "error");
  else alert((titulo ? titulo + ": " : "") + (mensaje || "Error"));
}

function mostrarOkSwal(titulo, mensaje) {
  if (typeof swal === "function") swal(titulo || "OK", mensaje || "Operación realizada correctamente.", "success");
  else alert((titulo ? titulo + ": " : "") + (mensaje || "OK"));
}

function getSelectedText(selectEl) {
  if (!selectEl) return "";
  const opt = selectEl.options[selectEl.selectedIndex];
  return opt ? opt.textContent.trim() : "";
}

// ------------------------------
// Cargar combos (Tipos)
// ------------------------------
async function cargarTiposOrganizacion() {
  try {
    const res = await fetch("/fundaciones/api/tipos_organizacion");
    const data = await res.json();
    if (!res.ok || !data.success) throw new Error(data.message || "Error tipos organización");

    tiposOrganizacionCache = data.items || [];

    const selCrear = document.getElementById("tipo_organizacion");
    const selModal = document.getElementById("tipo_organizacion_modal");

    if (selCrear) {
      selCrear.innerHTML = `<option value="">Tipo de organización</option>`;
      tiposOrganizacionCache.forEach(t => {
        const opt = document.createElement("option");
        opt.value = t.id_tipo_organizacion;
        opt.textContent = t.nombre;
        selCrear.appendChild(opt);
      });
    }

    if (selModal) {
      selModal.innerHTML = `<option value="">Tipo de organización</option>`;
      tiposOrganizacionCache.forEach(t => {
        const opt = document.createElement("option");
        opt.value = t.id_tipo_organizacion;
        opt.textContent = t.nombre;
        selModal.appendChild(opt);
      });
    }
  } catch (e) {
    console.error("cargarTiposOrganizacion:", e);
    mostrarErrorSwal("Error", "No se pudieron cargar los tipos de organización.");
  }
}

async function cargarTiposDocumento() {
  try {
    const res = await fetch("/fundaciones/api/tipos_documento");
    const data = await res.json();
    if (!res.ok || !data.success) throw new Error(data.message || "Error tipos documento");

    tiposDocumentoCache = data.items || [];

    const selCrear = document.getElementById("tipoDocumento");
    const selModal = document.getElementById("tipoDocumentoModal");

    if (selCrear) {
      selCrear.innerHTML = `<option value="">Tipo de documento</option>`;
      tiposDocumentoCache.forEach(t => {
        const opt = document.createElement("option");
        opt.value = t.id_tipo_doc;
        opt.textContent = t.nombre;
        selCrear.appendChild(opt);
      });
    }

    if (selModal) {
      selModal.innerHTML = `<option value="">Tipo de documento</option>`;
      tiposDocumentoCache.forEach(t => {
        const opt = document.createElement("option");
        opt.value = t.id_tipo_doc;
        opt.textContent = t.nombre;
        selModal.appendChild(opt);
      });
    }
  } catch (e) {
    console.error("cargarTiposDocumento:", e);
    mostrarErrorSwal("Error", "No se pudieron cargar los tipos de documento.");
  }
}

// ------------------------------
// API Colombia Departamentos/Municipios (CREAR)
// ------------------------------
async function cargarDepartamentosColombia() {
  if (!selectDeptos) return;

  try {
    const res = await fetch("https://api-colombia.com/api/v1/Department");
    const data = await res.json();

    selectDeptos.innerHTML = `<option selected disabled>Departamentos</option>`;
    data.forEach(depto => {
      const opt = document.createElement("option");
      opt.value = depto.id;
      opt.textContent = depto.name;
      selectDeptos.appendChild(opt);
    });
  } catch (e) {
    console.error("cargarDepartamentosColombia:", e);
    selectDeptos.innerHTML = `<option disabled>Error al cargar departamentos</option>`;
  }
}

async function traer() {
  if (!selectDeptos || !selectMunicipios) return;
  const id = selectDeptos.value;
  if (!id) return;

  selectMunicipios.innerHTML = `<option selected disabled>Cargando...</option>`;
  selectMunicipios.disabled = true;

  try {
    const res = await fetch(`https://api-colombia.com/api/v1/Department/${id}/cities`);
    const data = await res.json();

    selectMunicipios.innerHTML = "";
    if (!data || data.length === 0) {
      selectMunicipios.innerHTML = `<option disabled>No hay municipios</option>`;
      return;
    }

    selectMunicipios.disabled = false;

    const def = document.createElement("option");
    def.textContent = "Seleccione un municipio";
    def.disabled = true;
    def.selected = true;
    selectMunicipios.appendChild(def);

    data.forEach(city => {
      const opt = document.createElement("option");
      opt.value = city.id;
      opt.textContent = city.name;
      selectMunicipios.appendChild(opt);
    });
  } catch (e) {
    console.error("traer municipios:", e);
    selectMunicipios.innerHTML = `<option disabled>Error al cargar</option>`;
  }
}
// requerido por tu HTML: onchange="traer()"
window.traer = traer;

// ------------------------------
// LISTAR FUNDACIONES
// ------------------------------
async function cargarFundaciones() {
  if (!tbodyFundaciones) return;

  tbodyFundaciones.innerHTML = `
    <tr><td colspan="8" class="text-center">Cargando fundaciones...</td></tr>
  `;

  try {
    const res = await fetch("/fundaciones/api/listar");
    const data = await res.json();
    if (!res.ok || !data.success) throw new Error(data.message || "Error al listar");

    pintarTablaFundaciones(data.fundaciones || []);
  } catch (e) {
    console.error("cargarFundaciones:", e);
    tbodyFundaciones.innerHTML = `
      <tr><td colspan="8" class="text-center text-danger">Error al cargar fundaciones</td></tr>
    `;
  }
}

function pintarTablaFundaciones(items) {
  tbodyFundaciones.innerHTML = "";

  if (!items.length) {
    tbodyFundaciones.innerHTML = `
      <tr><td colspan="8" class="text-center">No hay fundaciones registradas.</td></tr>
    `;
    return;
  }

  items.forEach(f => {
    const tr = document.createElement("tr");

    tr.dataset.id = f.id_fundaciones;
    tr.dataset.idTipoOrganizacion = f.id_tipo_organizacion;
    tr.dataset.tipoDocId = f.tipo_doc_id;

    tr.dataset.nombre = f.nombre || "";
    tr.dataset.nombreEncargado = f.nombre_encargado || "";
    tr.dataset.numeroDocumento = f.numero_documento || "";
    tr.dataset.telefono = f.telefono || "";
    tr.dataset.direccion = f.direccion || "";
    tr.dataset.correo = f.correo || "";
    tr.dataset.familiasAtendidas = f.familias_atendidas ?? 0;
    tr.dataset.departamento = f.departamento || "";
    tr.dataset.municipio = f.municipio || "";
    tr.dataset.estado = f.estado || "Activo";

    tr.innerHTML = `
      <td>${f.id_fundaciones}</td>
      <td>${f.nombre || ""}</td>
      <td>${f.tipo_organizacion || ""}</td>
      <td>${f.nombre_encargado || ""}</td>
      <td>${(f.tipo_documento || "")} ${f.numero_documento || ""}</td>
      <td>${f.telefono || ""}</td>
      <td>${f.municipio || ""}</td>
      <td>
        <button type="button" class="btn btn-sm btn-success me-2 btn-editar">
          <i class="bi bi-pencil-fill"></i>
        </button>
        <button type="button" class="btn btn-sm btn-danger btn-eliminar">
          <i class="bi bi-trash-fill"></i>
        </button>
      </td>
    `;

    tbodyFundaciones.appendChild(tr);
  });
}

// ------------------------------
// CREAR
// ------------------------------
async function onSubmitCrear(evt) {
  evt.preventDefault();

  const nombre = document.getElementById("nombreParroquia")?.value.trim() || "";
  const idTipoOrg = document.getElementById("tipo_organizacion")?.value || "";
  const nombreEncargado = document.getElementById("nombrePadre")?.value.trim() || "";
  const tipoDocId = document.getElementById("tipoDocumento")?.value || "";
  const numeroDocumento = document.getElementById("numeroDocumento")?.value.trim() || "";

  const telefono = document.getElementById("telefono")?.value.trim() || "";
  const direccion = document.getElementById("direccion")?.value.trim() || "";
  const correo = document.getElementById("correo")?.value.trim() || "";
  const familiasAtendidas = Number(document.getElementById("familiasAtendidas")?.value || 0);

  const departamento = getSelectedText(selectDeptos);
  const municipio = getSelectedText(selectMunicipios);

  if (!nombre || !nombreEncargado || !numeroDocumento) {
    return mostrarErrorSwal("Validación", "Nombre, encargado y documento son obligatorios.");
  }
  if (!idTipoOrg || !tipoDocId) {
    return mostrarErrorSwal("Validación", "Debe seleccionar tipo de organización y tipo de documento.");
  }

  const payload = {
    id_tipo_organizacion: Number(idTipoOrg),
    tipo_doc_id: Number(tipoDocId),
    nombre,
    nombre_encargado: nombreEncargado,
    numero_documento: numeroDocumento,
    telefono,
    direccion,
    correo,
    familias_atendidas: familiasAtendidas,
    departamento,
    municipio
  };

  try {
    const res = await fetch("/fundaciones/api/crear", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok || !data.success) throw new Error(data.message || "Error al crear");

    mostrarOkSwal("Éxito", "Fundación registrada correctamente.");
    formFundacion.reset();

    if (selectMunicipios) {
      selectMunicipios.innerHTML = `<option selected disabled>Municipios</option>`;
      selectMunicipios.disabled = true;
    }

    await cargarFundaciones();
  } catch (e) {
    console.error("onSubmitCrear:", e);
    mostrarErrorSwal("Error", e.message || "No se pudo crear la fundación.");
  }
}

// ------------------------------
// EDITAR / ELIMINAR
// ------------------------------
function onClickTabla(evt) {
  const btnEditar = evt.target.closest(".btn-editar");
  const btnEliminar = evt.target.closest(".btn-eliminar");

  if (btnEditar) abrirModalEditar(btnEditar.closest("tr"));
  if (btnEliminar) confirmarEliminar(btnEliminar.closest("tr"));
}

function abrirModalEditar(tr) {
  if (!tr || !modalActualizar) return;

  document.getElementById("idFundacionModal").value = tr.dataset.id || "";
  document.getElementById("nombreFundacionModal").value = tr.dataset.nombre || "";
  document.getElementById("nombreEncargadoModal").value = tr.dataset.nombreEncargado || "";
  document.getElementById("numeroDocumentoModal").value = tr.dataset.numeroDocumento || "";
  document.getElementById("telefonoModal").value = tr.dataset.telefono || "";
  document.getElementById("direccionModal").value = tr.dataset.direccion || "";
  document.getElementById("correoModal").value = tr.dataset.correo || "";
  document.getElementById("familiasAtendidasModal").value = tr.dataset.familiasAtendidas || 0;

  document.getElementById("departamentoModal").value = tr.dataset.departamento || "";
  document.getElementById("municipioModal").value = tr.dataset.municipio || "";

  const selOrg = document.getElementById("tipo_organizacion_modal");
  if (selOrg) selOrg.value = tr.dataset.idTipoOrganizacion || "";

  const selDoc = document.getElementById("tipoDocumentoModal");
  if (selDoc) selDoc.value = tr.dataset.tipoDocId || "";

  const selEstado = document.getElementById("estadoModal");
  if (selEstado) selEstado.value = tr.dataset.estado || "Activo";

  modalActualizar.show();
}

async function onSubmitActualizar(evt) {
  evt.preventDefault();

  const id = document.getElementById("idFundacionModal")?.value || "";
  if (!id) return mostrarErrorSwal("Error", "No se encontró el ID.");

  const nombre = document.getElementById("nombreFundacionModal")?.value.trim() || "";
  const nombreEncargado = document.getElementById("nombreEncargadoModal")?.value.trim() || "";
  const tipoDocId = document.getElementById("tipoDocumentoModal")?.value || "";
  const numeroDocumento = document.getElementById("numeroDocumentoModal")?.value.trim() || "";
  const idTipoOrg = document.getElementById("tipo_organizacion_modal")?.value || "";

  const telefono = document.getElementById("telefonoModal")?.value.trim() || "";
  const direccion = document.getElementById("direccionModal")?.value.trim() || "";
  const correo = document.getElementById("correoModal")?.value.trim() || "";
  const familiasAtendidas = Number(document.getElementById("familiasAtendidasModal")?.value || 0);

  const departamento = document.getElementById("departamentoModal")?.value.trim() || null;
  const municipio = document.getElementById("municipioModal")?.value.trim() || null;
  const estado = document.getElementById("estadoModal")?.value || "Activo";

  if (!nombre || !nombreEncargado || !numeroDocumento) {
    return mostrarErrorSwal("Validación", "Nombre, encargado y documento son obligatorios.");
  }
  if (!idTipoOrg || !tipoDocId) {
    return mostrarErrorSwal("Validación", "Debe seleccionar tipo de organización y tipo de documento.");
  }

  const payload = {
    id_tipo_organizacion: Number(idTipoOrg),
    tipo_doc_id: Number(tipoDocId),
    nombre,
    nombre_encargado: nombreEncargado,
    numero_documento: numeroDocumento,
    telefono,
    direccion,
    correo,
    familias_atendidas: familiasAtendidas,
    departamento,
    municipio,
    estado
  };

  try {
    const res = await fetch(`/fundaciones/api/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok || !data.success) throw new Error(data.message || "Error al actualizar");

    mostrarOkSwal("Actualizada", "Fundación actualizada correctamente.");
    modalActualizar.hide();
    await cargarFundaciones();
  } catch (e) {
    console.error("onSubmitActualizar:", e);
    mostrarErrorSwal("Error", e.message || "No se pudo actualizar.");
  }
}

async function confirmarEliminar(tr) {
  if (!tr) return;

  const id = tr.dataset.id;
  const nombre = tr.dataset.nombre || "";
  if (!id) return;

  const msg = `¿Seguro que deseas eliminar la fundación "${nombre}" (ID ${id})?`;

  let ok = true;
  if (typeof swal === "function") {
    ok = await swal({
      title: "Confirmar eliminación",
      text: msg,
      icon: "warning",
      buttons: ["Cancelar", "Eliminar"],
      dangerMode: true
    });
  } else {
    ok = confirm(msg);
  }
  if (!ok) return;

  try {
    const res = await fetch(`/fundaciones/api/${id}`, { method: "DELETE" });
    const data = await res.json();
    if (!res.ok || !data.success) throw new Error(data.message || "Error al eliminar");

    mostrarOkSwal("Eliminada", "Fundación eliminada correctamente.");
    await cargarFundaciones();
  } catch (e) {
    console.error("confirmarEliminar:", e);
    mostrarErrorSwal("Error", e.message || "No se pudo eliminar.");
  }
}

// ------------------------------
// INIT
// ------------------------------
document.addEventListener("DOMContentLoaded", () => {
  tbodyFundaciones = document.querySelector("#tablaFundaciones tbody");
  formFundacion = document.getElementById("formFundacion");
  formActualizar = document.getElementById("formActualizarParroquia");

  selectDeptos = document.getElementById("departamentos");
  selectMunicipios = document.getElementById("municipios");

  const modalEl = document.getElementById("modalActualizarParroquia");
  if (modalEl && window.bootstrap?.Modal) {
    modalActualizar = new bootstrap.Modal(modalEl);
  }

  if (formFundacion) formFundacion.addEventListener("submit", onSubmitCrear);
  if (tbodyFundaciones) tbodyFundaciones.addEventListener("click", onClickTabla);
  if (formActualizar) formActualizar.addEventListener("submit", onSubmitActualizar);

  cargarTiposOrganizacion();
  cargarTiposDocumento();
  cargarDepartamentosColombia();
  cargarFundaciones();
});

// para tu script inline (si lo llamas)
window.cargarFundaciones = cargarFundaciones;
