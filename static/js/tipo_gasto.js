const formGasto = document.getElementById("formGasto");
const tablaGastos = document.querySelector("#tablaGastos tbody");
const API_TIPOS_GASTO = '/api/tipos_gasto';
// Cargar lista al iniciar
document.addEventListener("DOMContentLoaded", cargarTiposGasto);

// LISTAR
async function cargarTiposGasto() {
    const res = await fetch(API_TIPOS_GASTO);
    const datos = await res.json();
    tablaGastos.innerHTML = "";

    datos.forEach(g => {
        tablaGastos.innerHTML += `
      <tr>
        <td>${g.id_tipo_gasto}</td>
        <td>${g.nombre}</td>
        <td>${g.descripcion}</td>
        <td>
            <button class="btn btn-sm btn-success me-2" onclick="abrirModalActualizar(${g.id_tipo_gasto})">
              <i class="bi bi-pencil-fill"></i>
            </button>
            <button class="btn btn-sm btn-danger" onclick="eliminarTipoGasto(${g.id_tipo_gasto})">
              <i class="bi bi-trash-fill"></i>
            </button>
        </td>
      </tr>
    `;
    });
}

// CREAR
formGasto.addEventListener("submit", async (e) => {
    e.preventDefault();
    const data = {
        nombre: document.getElementById("nombreGasto").value.trim(),
        descripcion: document.getElementById("descripcionGasto").value.trim()
    };

    const res = await fetch("/api/tipos_gasto", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    });

    if (!res.ok) {
        const error = await res.json();
        return swal("Error", error.error, "warning");
    }

    swal("Tipo de gasto registrado", "", "success");
    formGasto.reset();
    cargarTiposGasto();
});



// ABRIR MODAL EDITAR
async function abrirModalActualizar(id) {
    const res = await fetch(`${API_TIPOS_GASTO}/${id}`);
    const gasto = await res.json();

    if(gasto.error){
        return swal("Error", "No se encontró el registro", "error");
    }

    document.getElementById("idTipoGastoModal").value = gasto.id_tipo_gasto;
    document.getElementById("nombreTipoGastoModal").value = gasto.nombre;
    document.getElementById("descripcionTipoGastoModal").value = gasto.descripcion;

    const modal = new bootstrap.Modal(document.getElementById("modalActualizarTipoGasto"));
    modal.show();
}



// ACTUALIZAR
document.getElementById("formActualizarTipoGasto").addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = document.getElementById("idTipoGastoModal").value;

    const data = {
        nombre: document.getElementById("nombreTipoGastoModal").value.trim(),
        descripcion: document.getElementById("descripcionTipoGastoModal").value.trim()
    };

    const res = await fetch(`/api/tipos_gasto/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    });

    if (!res.ok) {
        const error = await res.json();
        return swal("Error", error.error, "warning");
    }

    swal("Actualizado correctamente", "", "success");

    const modal = bootstrap.Modal.getInstance(document.getElementById("modalActualizarTipoGasto"));
modal.hide();
    cargarTiposGasto();
});

// ELIMINAR
async function eliminarTipoGasto(id) {
    const confirmacion = await swal({
        title: "¿Eliminar?",
        text: "Esta acción no se puede deshacer.",
        icon: "warning",
        buttons: ["Cancelar", "Eliminar"],
        dangerMode: true,
    });

    if (!confirmacion) return;

    try {
        const res = await fetch(`${API_TIPOS_GASTO}/${id}`, {
            method: "DELETE"
        });

        const data = await res.json();

        // ❌ Si el backend envía error (por relación con gastos)
        if (!res.ok) {
            return swal("No se puede eliminar", data.error, "error");
        }

        // ✔ Eliminación exitosa
        swal("Eliminado", "", "success");
        cargarTiposGasto();

    } catch (error) {
        console.error(error);
        swal("Error", "Error al intentar eliminar", "error");
    }
}



