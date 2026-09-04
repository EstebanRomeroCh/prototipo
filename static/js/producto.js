// ============================================================
// CONFIGURACIÓN INICIAL
// ============================================================

let productos = [];
let categorias = [];
let subcategorias = [];
let unidades = [];
let editandoProducto = null;

const formProducto = document.getElementById("formProducto");

const tablaElement = document.getElementById("tablaProductos");
const tablaProductos = tablaElement
  ? tablaElement.querySelector("tbody")
  : null;

const buscadorProductos = document.getElementById("buscadorProductos");

const API_PRODUCTOS = "/api/productos";
const API_CATEGORIAS = "/api/categorias";
const API_SUBCATEGORIAS = "/api/subcategorias";
const API_UNIDADES = "/api/unidades";

// ============================================================
// ALERTAS - SWEETALERT2
// ============================================================

function mostrarAlerta(titulo, mensaje, icono = "info") {
  // SweetAlert2
  if (typeof Swal !== "undefined") {
    return Swal.fire({
      title: titulo,
      text: mensaje,
      icon: icono,
      confirmButtonText: "Aceptar",
    });
  }

  // Fallback por si SweetAlert2 no está cargado
  alert(`${titulo}\n\n${mensaje}`);
}

// ============================================================
// FUNCIÓN DE SIMILITUD
// ============================================================

function es_similar(a, b) {
  if (a === null || a === undefined) {
    return false;
  }

  if (b === null || b === undefined) {
    return false;
  }

  return String(a).trim().toLowerCase() === String(b).trim().toLowerCase();
}

// ============================================================
// FORMATEO DE NÚMEROS
// ============================================================

function formatNumber(value) {
  if (value === null || value === undefined || value === "") {
    return "";
  }

  const num = Number(value);

  if (Number.isNaN(num)) {
    return value;
  }

  // Entero
  if (Number.isInteger(num)) {
    return num.toString();
  }

  // Máximo 3 decimales
  return num.toFixed(3).replace(/\.?0+$/, "");
}

// ============================================================
// OBTENER MENSAJE DE ERROR DEL BACKEND
// ============================================================

async function obtenerMensajeError(res) {
  try {
    const data = await res.json();

    return data.message || data.error || `Error HTTP ${res.status}`;
  } catch (error) {
    return `Error HTTP ${res.status}`;
  }
}

// ============================================================
// CARGAR CATEGORÍAS Y SUBCATEGORÍAS
// ============================================================

async function cargarCategoriasYSubcategorias() {
  try {
    // --------------------------------------------------------
    // CARGAR CATEGORÍAS
    // --------------------------------------------------------

    const resCat = await fetch(API_CATEGORIAS);

    if (!resCat.ok) {
      throw new Error(`Error cargando categorías: ${resCat.status}`);
    }

    categorias = await resCat.json();

    const selectCrear = document.getElementById("categoriaSelect");

    const selectModalCat = document.getElementById("categoriaProductoModal");

    // Limpiar selects
    if (selectCrear) {
      selectCrear.innerHTML =
        '<option value="">Selecciona una categoría</option>';
    }

    if (selectModalCat) {
      selectModalCat.innerHTML =
        '<option value="">Selecciona una categoría</option>';
    }

    // --------------------------------------------------------
    // INSERTAR CATEGORÍAS
    // --------------------------------------------------------

    categorias.forEach((cat) => {
      if (selectCrear) {
        const option = document.createElement("option");

        option.value = cat.id_categoria;
        option.textContent = cat.nombre;

        selectCrear.appendChild(option);
      }

      if (selectModalCat) {
        const option = document.createElement("option");

        option.value = cat.id_categoria;
        option.textContent = cat.nombre;

        selectModalCat.appendChild(option);
      }
    });

    // ========================================================
    // CARGAR TODAS LAS SUBCATEGORÍAS UNA SOLA VEZ
    // ========================================================

    const resSub = await fetch(API_SUBCATEGORIAS);

    if (!resSub.ok) {
      throw new Error(`Error cargando subcategorías: ${resSub.status}`);
    }

    subcategorias = await resSub.json();

    // ========================================================
    // EVENTO CATEGORÍA - CREAR PRODUCTO
    // ========================================================

    if (selectCrear) {
      selectCrear.onchange = function () {
        const id_categoria = this.value;

        const selectSub = document.getElementById("subcategoriaSelect");

        if (!selectSub) {
          return;
        }

        selectSub.innerHTML = "";

        if (!id_categoria) {
          selectSub.innerHTML =
            '<option value="">Selecciona una categoría primero</option>';

          selectSub.disabled = true;

          return;
        }

        // Filtrar subcategorías pertenecientes
        // a la categoría seleccionada
        const subRelacionadas = subcategorias.filter(
          (sub) => String(sub.id_categoria) === String(id_categoria),
        );

        // ------------------------------------------------
        // EXISTEN SUBCATEGORÍAS
        // ------------------------------------------------

        if (subRelacionadas.length > 0) {
          selectSub.innerHTML =
            '<option value="">Selecciona una subcategoría</option>';

          subRelacionadas.forEach((sub) => {
            const option = document.createElement("option");

            // IMPORTANTE:
            // Aquí estaba el error.
            // Debe ser id_subcategoria.
            option.value = sub.id_subcategoria;

            option.textContent = sub.nombre;

            selectSub.appendChild(option);
          });

          selectSub.disabled = false;
        } else {
          // ------------------------------------------------
          // NO EXISTEN SUBCATEGORÍAS
          // ------------------------------------------------

          selectSub.innerHTML =
            '<option value="">No hay subcategorías</option>';

          selectSub.disabled = true;
        }
      };
    }

    // ========================================================
    // EVENTO CATEGORÍA - MODAL EDITAR
    // ========================================================

    if (selectModalCat) {
      selectModalCat.onchange = function () {
        const id_categoria = this.value;

        const selectSubModal = document.getElementById(
          "subcategoriaProductoModal",
        );

        if (!selectSubModal) {
          return;
        }

        selectSubModal.innerHTML = "";

        if (!id_categoria) {
          selectSubModal.innerHTML =
            '<option value="">Selecciona una categoría primero</option>';

          selectSubModal.disabled = true;

          return;
        }

        const subRelacionadas = subcategorias.filter(
          (sub) => String(sub.id_categoria) === String(id_categoria),
        );

        if (subRelacionadas.length > 0) {
          selectSubModal.innerHTML =
            '<option value="">Selecciona una subcategoría</option>';

          subRelacionadas.forEach((sub) => {
            const option = document.createElement("option");

            // IMPORTANTE:
            // Debe ser id_subcategoria
            option.value = sub.id_subcategoria;

            option.textContent = sub.nombre;

            selectSubModal.appendChild(option);
          });

          selectSubModal.disabled = false;
        } else {
          selectSubModal.innerHTML =
            '<option value="">No hay subcategorías</option>';

          selectSubModal.disabled = true;
        }
      };
    }
  } catch (error) {
    console.error("Error cargando categorías y subcategorías:", error);

    mostrarAlerta(
      "Error",
      "No se pudieron cargar las categorías y subcategorías.",
      "error",
    );
  }
}

// ============================================================
// CARGAR UNIDADES
// ============================================================

async function cargarUnidades() {
  try {
    const res = await fetch("/api/unidades/activas");

    if (!res.ok) {
      throw new Error(`Error cargando unidades: ${res.status}`);
    }

    unidades = await res.json();

    // ========================================================
    // SELECT CREAR
    // ========================================================

    const select = document.getElementById("selectUnidad");

    if (select) {
      select.innerHTML = '<option value="">Seleccione...</option>';

      unidades.forEach((u) => {
        const opt = document.createElement("option");

        opt.value = u.id_unidad;
        opt.textContent = u.nombre;

        select.appendChild(opt);
      });
    }

    // ========================================================
    // SELECT MODAL
    // ========================================================

    const selectModal = document.getElementById("selectUnidadModal");

    if (selectModal) {
      selectModal.innerHTML = '<option value="">Seleccione...</option>';

      unidades.forEach((u) => {
        const opt = document.createElement("option");

        opt.value = u.id_unidad;
        opt.textContent = u.nombre;

        selectModal.appendChild(opt);
      });
    }
  } catch (error) {
    console.error("Error cargarUnidades:", error);

    mostrarAlerta("Error", "No se pudieron cargar las unidades.", "error");
  }
}

// ============================================================
// CARGAR PRODUCTOS
// ============================================================

async function cargarProductos() {
  try {
    const res = await fetch(API_PRODUCTOS);

    if (!res.ok) {
      throw new Error(`Error HTTP ${res.status}`);
    }

    const data = await res.json();

    productos = data.map((p) => {
      const stock = Number(p.stock_minimo);

      const pesoUnit = Number(p.peso_unitario);

      const pesoKg = Number(p.peso_kg);

      return {
        id_producto: p.id_producto,

        nombre: p.nombre,

        stock_minimo: Number.isNaN(stock) ? p.stock_minimo : stock,

        peso_unitario: Number.isNaN(pesoUnit) ? p.peso_unitario : pesoUnit,

        peso_kg: Number.isNaN(pesoKg) ? p.peso_kg : pesoKg,

        id_unidad: p.id_unidad,

        descripcion: p.descripcion || "",

        id_categoria: p.id_categoria,

        id_subcategoria: p.id_subcategoria,

        categoria: p.categoria,

        subcategoria: p.subcategoria,

        unidad_medida: p.unidad_medida || "Sin unidad",
      };
    });

    // ========================================================
    // LIMPIAR TABLA
    // ========================================================

    if (!tablaProductos) {
      return;
    }

    tablaProductos.innerHTML = "";

    // ========================================================
    // INSERTAR PRODUCTOS
    // ========================================================

    productos.forEach((prod) => {
      const fila = document.createElement("tr");

      fila.dataset.id = prod.id_producto;

      fila.innerHTML = `

                <td>
                    ${prod.id_producto}
                </td>

                <td class="col-nombre">
                    ${prod.nombre}
                </td>

                <td>
                    ${formatNumber(prod.stock_minimo)}
                </td>

                <td>
                    ${formatNumber(prod.peso_unitario)}
                    (${formatNumber(prod.peso_kg)} kg)
                </td>

                <td>
                    ${prod.unidad_medida}
                </td>

                <td>
                    ${prod.descripcion}
                </td>

                <td>

                    <button
                        type="button"
                        class="btn btn-sm btn-success me-2"
                        onclick="abrirModalEditarProducto(${prod.id_producto})"
                        title="Editar"
                    >
                        <i class="bi bi-pencil-fill"></i>
                    </button>

                    <button
                        type="button"
                        class="btn btn-sm btn-danger"
                        onclick="eliminarProducto(${prod.id_producto})"
                        title="Eliminar"
                    >
                        <i class="bi bi-trash-fill"></i>
                    </button>

                </td>
            `;

      tablaProductos.appendChild(fila);
    });
  } catch (error) {
    console.error("Error cargando productos:", error);

    mostrarAlerta("Error", "No se pudieron cargar los productos.", "error");
  }
}

// ============================================================
// BUSCADOR DE PRODUCTOS
// ============================================================

if (buscadorProductos && tablaProductos) {
  buscadorProductos.addEventListener("input", () => {
    const texto = buscadorProductos.value.toLowerCase().trim();

    Array.from(tablaProductos.rows).forEach((row) => {
      const nombre =
        row.querySelector(".col-nombre")?.textContent.toLowerCase() || "";

      const descripcion = row.children[5]?.textContent.toLowerCase() || "";

      const peso = row.children[3]?.textContent.toLowerCase() || "";

      const unidad = row.children[4]?.textContent.toLowerCase() || "";

      const coincide =
        nombre.includes(texto) ||
        descripcion.includes(texto) ||
        peso.includes(texto) ||
        unidad.includes(texto);

      row.style.display = coincide ? "" : "none";
    });
  });
}

// ============================================================
// CREAR PRODUCTO
// ============================================================

if (formProducto) {
  formProducto.addEventListener("submit", async function (e) {
    e.preventDefault();

    // ----------------------------------------------------
    // OBTENER CAMPOS
    // ----------------------------------------------------

    const nombre =
      document.getElementById("productoSelect")?.value.trim() || "";

    const id_categoria =
      document.getElementById("categoriaSelect")?.value || "";

    const id_subcategoria =
      document.getElementById("subcategoriaSelect")?.value || "";

    const stock_minimo =
      document.getElementById("cantidadProducto")?.value || "";

    const peso_unitario =
      document.getElementById("pesoUnitarioInput")?.value || "";

    const id_unidad = document.getElementById("selectUnidad")?.value || "";

    const descripcion =
      document.getElementById("descripcionProducto")?.value.trim() || "";

    // ----------------------------------------------------
    // VALIDAR CAMPOS OBLIGATORIOS
    // ----------------------------------------------------

    if (
      !nombre ||
      !id_categoria ||
      !id_subcategoria ||
      !stock_minimo ||
      !peso_unitario ||
      !id_unidad
    ) {
      mostrarAlerta(
        "Error",
        "Todos los campos obligatorios deben estar completos.",
        "error",
      );

      return;
    }

    // ----------------------------------------------------
    // CONVERTIR NÚMEROS
    // ----------------------------------------------------

    const stockNumero = Number(stock_minimo);

    const pesoNumero = Number(peso_unitario);

    if (!Number.isFinite(stockNumero) || stockNumero < 0) {
      mostrarAlerta(
        "Error",
        "El stock mínimo debe ser un número válido mayor o igual a 0.",
        "error",
      );

      return;
    }

    if (!Number.isFinite(pesoNumero) || pesoNumero < 0) {
      mostrarAlerta(
        "Error",
        "El peso unitario debe ser un número válido mayor o igual a 0.",
        "error",
      );

      return;
    }

    // ----------------------------------------------------
    // VALIDAR DUPLICADO
    // ----------------------------------------------------

    if (productos.some((p) => es_similar(p.nombre, nombre))) {
      mostrarAlerta(
        "Producto duplicado",
        "Ya existe un producto con ese nombre.",
        "warning",
      );

      return;
    }

    // ----------------------------------------------------
    // VALIDAR RELACIÓN CATEGORÍA / SUBCATEGORÍA
    // ----------------------------------------------------

    const subcategoriaSeleccionada = subcategorias.find(
      (sub) => String(sub.id_subcategoria) === String(id_subcategoria),
    );

    if (!subcategoriaSeleccionada) {
      mostrarAlerta(
        "Error",
        "La subcategoría seleccionada no es válida.",
        "error",
      );

      return;
    }

    if (
      String(subcategoriaSeleccionada.id_categoria) !== String(id_categoria)
    ) {
      mostrarAlerta(
        "Error",
        "La subcategoría no pertenece a la categoría seleccionada.",
        "error",
      );

      return;
    }

    // ----------------------------------------------------
    // DATOS A ENVIAR
    // ----------------------------------------------------

    const datosProducto = {
      nombre: nombre,

      id_categoria: Number(id_categoria),

      id_subcategoria: Number(id_subcategoria),

      stock_minimo: stockNumero,

      peso_unitario: pesoNumero,

      id_unidad: Number(id_unidad),

      descripcion: descripcion,
    };

    // Mostrar en consola para depuración
    console.log("DATOS QUE SE ENVIARÁN:", datosProducto);

    // ----------------------------------------------------
    // ENVIAR AL BACKEND
    // ----------------------------------------------------

    try {
      const res = await fetch(API_PRODUCTOS, {
        method: "POST",

        headers: {
          "Content-Type": "application/json",
        },

        body: JSON.stringify(datosProducto),
      });

      // ------------------------------------------------
      // RESPUESTA
      // ------------------------------------------------

      let data = {};

      try {
        data = await res.json();
      } catch (jsonError) {
        console.error("La respuesta no es JSON:", jsonError);
      }

      console.log("RESPUESTA DEL SERVIDOR:", data);

      // ------------------------------------------------
      // PRODUCTO CREADO
      // ------------------------------------------------

      if (res.ok && data.success) {
        await cargarProductos();

        formProducto.reset();

        // Reiniciar select de subcategoría
        const selectSub = document.getElementById("subcategoriaSelect");

        if (selectSub) {
          selectSub.innerHTML =
            '<option value="">Selecciona una categoría primero</option>';

          selectSub.disabled = true;
        }

        mostrarAlerta("Éxito", "Producto creado correctamente.", "success");

        return;
      }

      // ------------------------------------------------
      // ERROR DEL BACKEND
      // ------------------------------------------------

      mostrarAlerta(
        `Error ${res.status}`,
        data.message || data.error || "No se pudo crear el producto.",
        "error",
      );
    } catch (error) {
      console.error("Error creando producto:", error);

      mostrarAlerta(
        "Error de conexión",
        "No se pudo conectar con el servidor.",
        "error",
      );
    }
  });
}

// ============================================================
// MODAL EDITAR PRODUCTO
// ============================================================

async function abrirModalEditarProducto(id) {
  try {
    const producto = productos.find(
      (p) => String(p.id_producto) === String(id),
    );

    if (!producto) {
      mostrarAlerta("Error", "Producto no encontrado en memoria.", "error");

      return;
    }

    // --------------------------------------------------------
    // ID
    // --------------------------------------------------------

    document.getElementById("idProductoModal").value = producto.id_producto;

    // --------------------------------------------------------
    // NOMBRE
    // --------------------------------------------------------

    document.getElementById("nombreProductoModal").value = producto.nombre;

    // --------------------------------------------------------
    // STOCK
    // --------------------------------------------------------

    document.getElementById("nombreStockModal").value = producto.stock_minimo;

    // --------------------------------------------------------
    // PESO
    // --------------------------------------------------------

    document.getElementById("pesoUnitarioModal").value = producto.peso_unitario;

    // --------------------------------------------------------
    // DESCRIPCIÓN
    // --------------------------------------------------------

    document.getElementById("descripcionProductoModal").value =
      producto.descripcion || "";

    // --------------------------------------------------------
    // CATEGORÍA
    // --------------------------------------------------------

    const categoriaModal = document.getElementById("categoriaProductoModal");

    const subcategoriaModal = document.getElementById(
      "subcategoriaProductoModal",
    );

    if (categoriaModal) {
      categoriaModal.value = producto.id_categoria;
    }

    // --------------------------------------------------------
    // CARGAR SUBCATEGORÍAS
    // --------------------------------------------------------

    if (categoriaModal && subcategoriaModal) {
      subcategoriaModal.innerHTML =
        '<option value="">Selecciona una subcategoría</option>';

      const subRelacionadas = subcategorias.filter(
        (sub) => String(sub.id_categoria) === String(producto.id_categoria),
      );

      subRelacionadas.forEach((sub) => {
        const option = document.createElement("option");

        option.value = sub.id_subcategoria;

        option.textContent = sub.nombre;

        subcategoriaModal.appendChild(option);
      });

      subcategoriaModal.disabled = subRelacionadas.length === 0;

      subcategoriaModal.value = producto.id_subcategoria;
    }

    // --------------------------------------------------------
    // UNIDADES
    // --------------------------------------------------------

    const selectUnidadModal = document.getElementById("selectUnidadModal");

    if (selectUnidadModal) {
      if (unidades.length === 0) {
        await cargarUnidades();
      }

      selectUnidadModal.value = producto.id_unidad;
    }

    // --------------------------------------------------------
    // FILA QUE ESTAMOS EDITANDO
    // --------------------------------------------------------

    editandoProducto = document.querySelector(`tr[data-id="${id}"]`);

    // --------------------------------------------------------
    // ABRIR MODAL
    // --------------------------------------------------------

    const modalElement = document.getElementById("modalActualizarProducto");

    if (!modalElement) {
      mostrarAlerta(
        "Error",
        "No se encontró el modal de actualización.",
        "error",
      );

      return;
    }

    const modal = bootstrap.Modal.getOrCreateInstance(modalElement);

    modal.show();
  } catch (error) {
    console.error("Error cargando producto:", error);

    mostrarAlerta("Error", "No se pudo cargar el producto.", "error");
  }
}

// ============================================================
// ACTUALIZAR PRODUCTO
// ============================================================

const formActualizar = document.getElementById("formActualizarProducto");

if (formActualizar) {
  formActualizar.addEventListener("submit", async function (e) {
    e.preventDefault();

    // ----------------------------------------------------
    // OBTENER DATOS
    // ----------------------------------------------------

    const id = document.getElementById("idProductoModal")?.value || "";

    const nombre =
      document.getElementById("nombreProductoModal")?.value.trim() || "";

    const id_categoria =
      document.getElementById("categoriaProductoModal")?.value || "";

    const id_subcategoria =
      document.getElementById("subcategoriaProductoModal")?.value || "";

    const stock_minimo =
      document.getElementById("nombreStockModal")?.value || "";

    const peso_unitario =
      document.getElementById("pesoUnitarioModal")?.value || "";

    const descripcion =
      document.getElementById("descripcionProductoModal")?.value.trim() || "";

    const id_unidad = document.getElementById("selectUnidadModal")?.value || "";

    // ----------------------------------------------------
    // VALIDACIÓN
    // ----------------------------------------------------

    if (
      !id ||
      !nombre ||
      !id_categoria ||
      !id_subcategoria ||
      !stock_minimo ||
      !peso_unitario ||
      !id_unidad
    ) {
      mostrarAlerta(
        "Error",
        "Todos los campos obligatorios deben estar completos.",
        "error",
      );

      return;
    }

    // ----------------------------------------------------
    // CONVERTIR NÚMEROS
    // ----------------------------------------------------

    const stockNumero = Number(stock_minimo);

    const pesoNumero = Number(peso_unitario);

    if (!Number.isFinite(stockNumero) || stockNumero < 0) {
      mostrarAlerta("Error", "El stock mínimo no es válido.", "error");

      return;
    }

    if (!Number.isFinite(pesoNumero) || pesoNumero < 0) {
      mostrarAlerta("Error", "El peso unitario no es válido.", "error");

      return;
    }

    // ----------------------------------------------------
    // VALIDAR DUPLICADO
    // ----------------------------------------------------

    if (
      productos.some(
        (p) =>
          String(p.id_producto) !== String(id) && es_similar(p.nombre, nombre),
      )
    ) {
      mostrarAlerta(
        "Producto duplicado",
        "Ya existe otro producto con ese nombre.",
        "warning",
      );

      return;
    }

    // ----------------------------------------------------
    // VALIDAR SUBCATEGORÍA
    // ----------------------------------------------------

    const subcategoriaSeleccionada = subcategorias.find(
      (sub) => String(sub.id_subcategoria) === String(id_subcategoria),
    );

    if (!subcategoriaSeleccionada) {
      mostrarAlerta(
        "Error",
        "La subcategoría seleccionada no es válida.",
        "error",
      );

      return;
    }

    if (
      String(subcategoriaSeleccionada.id_categoria) !== String(id_categoria)
    ) {
      mostrarAlerta(
        "Error",
        "La subcategoría no pertenece a la categoría seleccionada.",
        "error",
      );

      return;
    }

    // ----------------------------------------------------
    // DATOS
    // ----------------------------------------------------

    const datosProducto = {
      nombre: nombre,

      id_categoria: Number(id_categoria),

      id_subcategoria: Number(id_subcategoria),

      stock_minimo: stockNumero,

      peso_unitario: pesoNumero,

      id_unidad: Number(id_unidad),

      descripcion: descripcion,
    };

    console.log("DATOS ACTUALIZACIÓN:", datosProducto);

    // ----------------------------------------------------
    // PETICIÓN PUT
    // ----------------------------------------------------

    try {
      const res = await fetch(`${API_PRODUCTOS}/${id}`, {
        method: "PUT",

        headers: {
          "Content-Type": "application/json",
        },

        body: JSON.stringify(datosProducto),
      });

      let data = {};

      try {
        data = await res.json();
      } catch (jsonError) {
        console.error("Error leyendo JSON:", jsonError);
      }

      console.log("RESPUESTA ACTUALIZACIÓN:", data);

      // ------------------------------------------------
      // ÉXITO
      // ------------------------------------------------

      if (res.ok) {
        await cargarProductos();

        // Cerrar modal
        const modalElement = document.getElementById("modalActualizarProducto");

        if (modalElement) {
          const modal = bootstrap.Modal.getInstance(modalElement);

          if (modal) {
            modal.hide();
          }
        }

        mostrarAlerta(
          "Éxito",
          "Producto actualizado correctamente.",
          "success",
        );

        editandoProducto = null;

        return;
      }

      // ------------------------------------------------
      // ERROR
      // ------------------------------------------------

      mostrarAlerta(
        `Error ${res.status}`,
        data.message || data.error || "No se pudo actualizar el producto.",
        "error",
      );
    } catch (error) {
      console.error("Error actualizando producto:", error);

      mostrarAlerta(
        "Error de conexión",
        "No se pudo conectar con el servidor.",
        "error",
      );
    }
  });
}

// ============================================================
// ELIMINAR PRODUCTO
// ============================================================

async function eliminarProducto(id) {
  try {
    let confirmar = false;

    // --------------------------------------------------------
    // SWEETALERT2
    // --------------------------------------------------------

    if (typeof Swal !== "undefined") {
      const resultado = await Swal.fire({
        title: "¿Estás seguro?",

        text: "Una vez eliminado, no podrás recuperarlo.",

        icon: "warning",

        showCancelButton: true,

        confirmButtonText: "Sí, eliminar",

        cancelButtonText: "Cancelar",

        reverseButtons: true,
      });

      confirmar = resultado.isConfirmed;
    } else {
      confirmar = confirm("¿Estás seguro de eliminar este producto?");
    }

    if (!confirmar) {
      return;
    }

    // --------------------------------------------------------
    // DELETE
    // --------------------------------------------------------

    const res = await fetch(`${API_PRODUCTOS}/${id}`, {
      method: "DELETE",
    });

    let data = {};

    try {
      data = await res.json();
    } catch (jsonError) {
      console.error("Error leyendo respuesta DELETE:", jsonError);
    }

    console.log("RESPUESTA ELIMINAR:", data);

    // --------------------------------------------------------
    // ÉXITO
    // --------------------------------------------------------

    if (res.ok && data.success) {
      productos = productos.filter((p) => String(p.id_producto) !== String(id));

      await cargarProductos();

      mostrarAlerta("Éxito", "Producto eliminado correctamente.", "success");

      return;
    }

    // --------------------------------------------------------
    // ERROR
    // --------------------------------------------------------

    mostrarAlerta(
      `Error ${res.status}`,
      data.message || data.error || "No se pudo eliminar el producto.",
      "error",
    );
  } catch (error) {
    console.error("Error eliminando producto:", error);

    mostrarAlerta(
      "Error de conexión",
      "No se pudo conectar con el servidor.",
      "error",
    );
  }
}

// ============================================================
// HACER FUNCIONES DISPONIBLES GLOBALMENTE
// ============================================================

window.abrirModalEditarProducto = abrirModalEditarProducto;

window.eliminarProducto = eliminarProducto;

// ============================================================
// INICIALIZACIÓN
// ============================================================

document.addEventListener("DOMContentLoaded", async () => {
  console.log("Inicializando módulo de productos...");

  await cargarCategoriasYSubcategorias();

  await cargarUnidades();

  await cargarProductos();

  console.log("Módulo de productos inicializado correctamente.");
});
