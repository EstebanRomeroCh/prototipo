// gastos.js
const formGasto = document.getElementById("formGasto");
const tablaGastos = document.querySelector("#tablaGastos tbody");
const formActualizarGasto = document.getElementById("formActualizarGasto");
const modalActualizarGasto = new bootstrap.Modal(document.getElementById("modalActualizarGasto"));

const API_TIPOS_GASTO = "/api/gastos/tipos";
const API_GASTOS = "/api/gastos";

// ==============================
// CARGAR DATOS AL INICIAR
// ==============================
document.addEventListener("DOMContentLoaded", () => {
    cargarTiposGasto();
    listarGastos();

    // ====== BLOQUEAR FECHAS FUTURAS ======
    const hoy = new Date().toISOString().split("T")[0];

    const fechaNueva = document.getElementById("fecha");
    const fechaModal = document.getElementById("fecha_modal");

    if (fechaNueva) fechaNueva.setAttribute("max", hoy);
    if (fechaModal) fechaModal.setAttribute("max", hoy);
});

// ==============================
// CARGAR TIPOS DE GASTO EN SELECTS
// ==============================


async function cargarTiposGasto() {
    try {
        const res = await fetch("/api/gastos/tipos");
        if (!res.ok) throw new Error("No se pudieron cargar los tipos de gasto");
        const tipos = await res.json();

        const selectNuevo = document.getElementById("id_tipo_gasto");
        const selectModal = document.getElementById("id_tipo_gasto_modal");

        selectNuevo.innerHTML = '<option value="">Seleccione tipo de gasto</option>';
        selectModal.innerHTML = '<option value="">Seleccione tipo de gasto</option>';

        tipos.forEach(t => {
            selectNuevo.innerHTML += `<option value="${t.id_tipo_gasto}">${t.nombre}</option>`;
            selectModal.innerHTML += `<option value="${t.id_tipo_gasto}">${t.nombre}</option>`;
        });

    } catch (err) {
        console.error(err);
        swal("Error", "No se pudieron cargar los tipos de gasto", "error");
    }
}


// ==============================
// LISTAR GASTOS
// ==============================
async function listarGastos() {
    try {
        const res = await fetch(API_GASTOS);
        if (!res.ok) throw new Error("No se pudieron cargar los gastos");
        const gastos = await res.json();

        tablaGastos.innerHTML = ""; // limpiar tabla

        gastos.forEach(g => {
            const fila = document.createElement("tr");

            fila.innerHTML = `
                <td>${g.id_gasto}</td>
                <td>${g.tipo_nombre || ""}</td>
                <td>${g.descripcion}</td>
                <td>${g.monto}</td>
                <td>${g.fecha}</td>
                <td>
                    <button class="btn btn-sm btn-success me-2" onclick="abrirModalActualizarGasto(${g.id_gasto})">
                        <i class="bi bi-pencil-fill"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="eliminarGasto(${g.id_gasto})">
                        <i class="bi bi-trash-fill"></i>
                    </button>
                </td>
            `;

            tablaGastos.appendChild(fila); // ← AÑADE AL FINAL EN ORDEN REAL
        });

    } catch (error) {
        console.error(error);
        swal("Error", "No se pudieron cargar los gastos", "error");
    }
}



fetch("/api/gastos/tipos")
  .then(r => r.json())
  .then(data => console.log(data))
  .catch(err => console.error(err));


// ==============================
// CREAR GASTO
// ==============================
formGasto.addEventListener("submit", async (e) => {
    e.preventDefault();

    const data = {
        id_tipo_gasto: document.getElementById("id_tipo_gasto").value,
        descripcion: document.getElementById("descripcion").value.trim(),
        monto: document.getElementById("monto").value,
        fecha: document.getElementById("fecha").value
    };

    try {
        const res = await fetch(API_GASTOS, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });

        const result = await res.json();
        if (!res.ok) throw new Error(result.message || "Error creando gasto");

        swal("Gasto registrado", "", "success");
        formGasto.reset();
        listarGastos();
    } catch (error) {
        console.error(error);
        swal("Error", error.message, "error");
    }
});

// ==============================
// ABRIR MODAL ACTUALIZAR
// ==============================
async function abrirModalActualizarGasto(id_gasto) {
    try {
        const res = await fetch(`${API_GASTOS}/${id_gasto}`);
        const gasto = await res.json();

        if (!res.ok) throw new Error(gasto.message || "No se encontró el gasto");

        document.getElementById("id_gasto_modal").value = gasto.id_gasto;
        document.getElementById("id_tipo_gasto_modal").value = gasto.id_tipo_gasto;
        document.getElementById("descripcion_modal").value = gasto.descripcion;
        document.getElementById("monto_modal").value = gasto.monto;
        document.getElementById("fecha_modal").value = gasto.fecha;

        modalActualizarGasto.show();
    } catch (error) {
        console.error(error);
        swal("Error", error.message || "No se pudo abrir el gasto", "error");
    }
}

// ==============================
// ACTUALIZAR GASTO
// ==============================
formActualizarGasto.addEventListener("submit", async (e) => {
    e.preventDefault();

    const id_gasto = document.getElementById("id_gasto_modal").value;
    const data = {
        id_tipo_gasto: document.getElementById("id_tipo_gasto_modal").value,
        descripcion: document.getElementById("descripcion_modal").value.trim(),
        monto: document.getElementById("monto_modal").value,
        fecha: document.getElementById("fecha_modal").value
    };

    try {
        const res = await fetch(`${API_GASTOS}/${id_gasto}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });

        const result = await res.json();
        if (!res.ok) throw new Error(result.message || "Error actualizando gasto");

        swal("Actualizado correctamente", "", "success");
        modalActualizarGasto.hide();
        listarGastos();
    } catch (error) {
        console.error(error);
        swal("Error", error.message, "error");
    }
});

// ==============================
// ELIMINAR GASTO
// ==============================
async function eliminarGasto(id_gasto) {
    const confirmacion = await swal({
        title: "¿Eliminar?",
        text: "Esta acción no se puede deshacer.",
        icon: "warning",
        buttons: ["Cancelar", "Eliminar"],
        dangerMode: true
    });

    if (!confirmacion) return;

    try {
        const res = await fetch(`${API_GASTOS}/${id_gasto}`, { method: "DELETE" });
        const result = await res.json();
        if (!res.ok) throw new Error(result.message || "Error eliminando gasto");

        swal("Eliminado", "", "success");
        listarGastos();
    } catch (error) {
        console.error(error);
        swal("Error", error.message, "error");
    }
}
