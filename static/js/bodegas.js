const API_BODEGAS = "/api/bodegas";
let bodegas = [];
let filaEditando = null;

// Cargar bodegas al iniciar
document.addEventListener("DOMContentLoaded", cargarBodegas);

// ======================
// LISTAR
// ======================
async function cargarBodegas() {
  try {
    const res = await fetch(API_BODEGAS);
    bodegas = await res.json();
    renderTabla();
  } catch (error) {
    console.error("Error cargando bodegas:", error);
  }
}

function renderTabla() {
  const tbody = document.querySelector("#tablaBodegas tbody");

  tbody.innerHTML = "";

  bodegas.forEach((b) => {
    const tr = document.createElement("tr");

    tr.innerHTML = `
      <td>${b.id_bodega}</td>
      <td>${b.nombre_bodega}</td>
      <td>${b.ubicacion || "—"}</td>
      <td>${b.capacidad ?? "—"}</td>
      <td>${b.estado || "—"}</td>
      <td>
        <button 
          class="btn btn-sm btn-success me-2"
          onclick="abrirModalActualizar(${b.id_bodega})">
          <i class="bi bi-pencil-fill"></i>
        </button>

        <button 
          class="btn btn-sm btn-danger"
          onclick="eliminarBodega(${b.id_bodega})">
          <i class="bi bi-trash-fill"></i>
        </button>
      </td>
    `;

    tbody.appendChild(tr);
  });
}

// ======================
// CREAR
// ======================
document.getElementById("formBodega").addEventListener("submit", async (e) => {
  e.preventDefault();

  const nombre_bodega = document.getElementById("nombreBodega").value.trim();
  const ubicacion = document.getElementById("direccionBodega").value.trim(); // CORREGIDO
  const descripcion = document.getElementById("descripcionBodega").value.trim();

  if (!nombre_bodega) {
    return swal("Error", "El nombre de la bodega es obligatorio", "error");
  }

  try {
    const res = await fetch(API_BODEGAS, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nombre_bodega, ubicacion, descripcion }),
    });

    const data = await res.json();
    swal("Éxito", data.message, "success");

    document.getElementById("formBodega").reset();
    cargarBodegas();
  } catch (error) {
    console.error("Error al crear bodega:", error);
    swal("Error", "No se pudo registrar la bodega", "error");
  }
});

// ======================
// ABRIR MODAL EDITAR
// ======================
function abrirModalActualizar(id) {
  const bodega = bodegas.find((b) => b.id_bodega === id);

  if (!bodega) {
    console.error("No se encontró la bodega con ID:", id);
    return;
  }

  filaEditando = id;

  document.getElementById("idBodegaModal").value = bodega.id_bodega;
  document.getElementById("nombreBodegaModal").value =
    bodega.nombre_bodega || "";

  document.getElementById("ubicacionBodegaModal").value =
    bodega.ubicacion || "";

  document.getElementById("capacidadBodegaModal").value =
    bodega.capacidad || "";

  const modal = new bootstrap.Modal(
    document.getElementById("modalActualizarBodega"),
  );

  modal.show();
}
// ======================
// ACTUALIZAR
// ======================

const formActualizarBodega = document.getElementById("formActualizarBodega");

if (formActualizarBodega) {
  formActualizarBodega.addEventListener("submit", async (e) => {
    e.preventDefault();

    const id = document.getElementById("idBodegaModal").value;

    const nombre_bodega = document
      .getElementById("nombreBodegaModal")
      .value.trim();

    const ubicacion = document
      .getElementById("ubicacionBodegaModal")
      .value.trim();

    const capacidad = document.getElementById("capacidadBodegaModal").value;

    const estado = document.getElementById("estadoBodegaModal").value;

    if (!nombre_bodega) {
      swal("Error", "El nombre de la bodega es obligatorio", "error");
      return;
    }

    if (capacidad === "") {
      swal("Error", "La capacidad es obligatoria", "error");
      return;
    }

    try {
      const res = await fetch(`${API_BODEGAS}/${id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          nombre_bodega,
          ubicacion,
          capacidad,
          estado,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detalle || data.error || "Error al actualizar");
      }

      swal("Éxito", data.message, "success");

      await cargarBodegas();

      const modalElemento = document.getElementById("modalActualizarBodega");

      const modal = bootstrap.Modal.getInstance(modalElemento);

      if (modal) {
        modal.hide();
      }
    } catch (error) {
      console.error("Error al actualizar:", error);

      swal(
        "Error",
        "No se pudo actualizar la bodega: " + error.message,
        "error",
      );
    }
  });
}
// ======================
// ELIMINAR
// ======================
async function eliminarBodega(id) {
  swal({
    title: "¿Eliminar bodega?",
    text: "Esta acción es irreversible.",
    icon: "warning",
    buttons: ["Cancelar", "Eliminar"],
    dangerMode: true,
  }).then(async (ok) => {
    if (!ok) return;

    try {
      const res = await fetch(`${API_BODEGAS}/${id}`, { method: "DELETE" });
      const data = await res.json();
      swal("Eliminada", data.message, "success");
      cargarBodegas();
    } catch (error) {
      console.error("Error al eliminar:", error);
      swal("Error", "No se pudo eliminar", "error");
    }
  });
}
