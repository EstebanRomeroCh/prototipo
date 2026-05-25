// ==============================
// CONFIGURACIÓN INICIAL
// ==============================
let editandoCategoria = null;

const formCategoria = document.getElementById("formCategoria");
const tablaCategorias = document
  .getElementById("tablaCategorias")
  .querySelector("tbody");

// IMPORTANTE:
// tu blueprint ya tiene /api/categorias
// por eso dejamos la / al final
const API_CATEGORIAS = "/api/categorias";

// ==============================
// CARGAR TODAS LAS CATEGORÍAS
// ==============================
async function cargarCategorias() {
  try {
    const res = await fetch(API_CATEGORIAS);

    if (!res.ok) {
      throw new Error(`Error HTTP: ${res.status}`);
    }

    const categorias = await res.json();

    console.log("Categorías:", categorias);

    tablaCategorias.innerHTML = "";

    categorias.forEach((cat) => {
      agregarFilaCategoria(cat);
    });
  } catch (error) {
    console.error("Error cargando categorías:", error);
    swal("Error", "No se pudieron cargar las categorías", "error");
  }
}

// ==============================
// AGREGAR FILA A LA TABLA
// ==============================
function agregarFilaCategoria(cat) {
  const row = document.createElement("tr");

  row.innerHTML = `
        <td class="col-id">${cat.id_categoria}</td>

        <td class="col-nombre">
            ${cat.nombre}
        </td>

        <td class="col-descripcion">
            ${cat.descripcion || ""}
        </td>

        <td>
            <button class="btn btn-sm btn-success me-2"
                    onclick="editarCategoria(this)">
                <i class="bi bi-pencil-fill"></i>
            </button>

            <button class="btn btn-sm btn-danger"
                    onclick="eliminarCategoria(this)">
                <i class="bi bi-trash-fill"></i>
            </button>
        </td>
    `;

  tablaCategorias.appendChild(row);
}

// ==============================
// CREAR NUEVA CATEGORÍA
// ==============================
formCategoria.addEventListener("submit", async function (e) {
  e.preventDefault();

  const nombre = document.getElementById("nombreCategoria").value.trim();

  const descripcion = document
    .getElementById("descripcionCategoria")
    .value.trim();

  if (!nombre) {
    swal("Error", "El nombre es obligatorio", "error");
    return;
  }

  try {
    const res = await fetch(API_CATEGORIAS, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        nombre,
        descripcion,
      }),
    });

    const data = await res.json();

    console.log("Respuesta crear:", data);

    if (res.ok && data.success) {
      cargarCategorias(); // recarga todo en vez de usar objeto

      formCategoria.reset();

      swal("Éxito", "Categoría creada correctamente", "success");
    } else {
      swal("Error", data.message || "No se pudo crear la categoría", "error");
    }
  } catch (error) {
    console.error("Error creando categoría:", error);

    swal("Error", "No se pudo crear la categoría", "error");
  }
});

// ==============================
// ELIMINAR CATEGORÍA
// ==============================
async function eliminarCategoria(btn) {
  const row = btn.closest("tr");

  const id = row.querySelector(".col-id").textContent;

  const confirmacion = await swal({
    title: "¿Está seguro?",
    text: "Esta acción no se puede deshacer",
    icon: "warning",
    buttons: true,
    dangerMode: true,
  });

  if (!confirmacion) return;

  try {
    const res = await fetch(`${API_CATEGORIAS}/${id}`, {
      method: "DELETE",
    });

    const data = await res.json();

    if (res.ok && data.success) {
      row.remove();

      swal("Eliminado", data.message || "Categoría eliminada", "success");
    } else {
      swal(
        "Error",
        data.message || "No se pudo eliminar la categoría",
        "error",
      );
    }
  } catch (error) {
    console.error("Error eliminando categoría:", error);

    swal("Error", "No se pudo eliminar la categoría", "error");
  }
}

// ==============================
// EDITAR CATEGORÍA
// ==============================
function editarCategoria(btn) {
  const row = btn.closest("tr");

  const id = row.querySelector(".col-id").textContent;

  const nombre = row.querySelector(".col-nombre").textContent.trim();

  const descripcion = row.querySelector(".col-descripcion").textContent.trim();

  document.getElementById("idCategoriaModal").value = id;

  document.getElementById("nombreCategoriaModal").value = nombre;

  document.getElementById("descripcionCategoriaModal").value = descripcion;

  editandoCategoria = row;

  const modal = new bootstrap.Modal(
    document.getElementById("modalActualizarCategoria"),
  );

  modal.show();
}

// ==============================
// ACTUALIZAR CATEGORÍA
// ==============================
document
  .getElementById("formActualizarCategoria")
  .addEventListener("submit", async function (e) {
    e.preventDefault();

    const id = document.getElementById("idCategoriaModal").value;

    const nombre = document.getElementById("nombreCategoriaModal").value.trim();

    const descripcion = document
      .getElementById("descripcionCategoriaModal")
      .value.trim();

    if (!nombre) {
      swal("Error", "El nombre es obligatorio", "error");

      return;
    }

    try {
      const res = await fetch(`${API_CATEGORIAS}/${id}`, {
        method: "PUT",

        headers: {
          "Content-Type": "application/json",
        },

        body: JSON.stringify({
          nombre,
          descripcion,
          estado: "Activo",
        }),
      });

      const data = await res.json();

      console.log("Respuesta actualizar:", data);

      if (res.ok && data.success) {
        editandoCategoria.querySelector(".col-nombre").textContent =
          data.categoria.nombre;

        editandoCategoria.querySelector(".col-descripcion").textContent =
          data.categoria.descripcion || "";

        const modal = bootstrap.Modal.getInstance(
          document.getElementById("modalActualizarCategoria"),
        );

        modal.hide();

        swal("Actualizado", "Categoría actualizada correctamente", "success");

        editandoCategoria = null;
      } else {
        swal(
          "Error",
          data.message || "No se pudo actualizar la categoría",
          "error",
        );
      }
    } catch (error) {
      console.error("Error actualizando categoría:", error);

      swal("Error", "No se pudo actualizar la categoría", "error");
    }
  });

// ==============================
// INICIALIZACIÓN
// ==============================
document.addEventListener("DOMContentLoaded", cargarCategorias);
