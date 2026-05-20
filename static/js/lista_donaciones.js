// =========================================
// VARIABLES GLOBALES
// =========================================
let idEdicion = null;
let productosEdicion = [];

let idEdicionMon = null;
let productoSeleccionadoEdicion = null;


// =========================================
// BOTONES Y SECCIONES
// =========================================
const btnProducto = document.getElementById('btnProducto');
const btnMonetaria = document.getElementById('btnMonetaria');
const tablaProducto = document.getElementById('tablaProducto');
const tablaMonetaria = document.getElementById('tablaMonetaria');

// =========================================
// CAMBIO ENTRE TABLAS
// =========================================
btnProducto.addEventListener('click', () => {
    btnProducto.classList.add('btn-success', 'active');
    btnProducto.classList.remove('btn-outline-success');
    btnMonetaria.classList.remove('btn-success', 'active');
    btnMonetaria.classList.add('btn-outline-success');

    tablaProducto.classList.remove('d-none');
    tablaMonetaria.classList.add('d-none');
});

btnMonetaria.addEventListener('click', () => {
    btnMonetaria.classList.add('btn-success', 'active');
    btnMonetaria.classList.remove('btn-outline-success');
    btnProducto.classList.remove('btn-success', 'active');
    btnProducto.classList.add('btn-outline-success');

    tablaMonetaria.classList.remove('d-none');
    tablaProducto.classList.add('d-none');
});

// =========================================
// CARGAR AMBAS TABLAS
// =========================================
function configurarMinimoVencimientoEditar() {
    const hoy = new Date();
    hoy.setDate(hoy.getDate() + 1); // mañana
    const min = hoy.toISOString().split("T")[0];

    document.getElementById("editProd_vencimiento").min = min;
}


async function cargarTablas() {
    await cargarTablaProductos();
    await cargarTablaMonetaria();
}

function formatearFecha(fechaISO) {
    if (!fechaISO) return "-";
    const fecha = new Date(fechaISO);
    return fecha.toLocaleDateString("es-ES", {
        year: "numeric",
        month: "long",
        day: "numeric"
    });
}


async function cargarBodegasEditar() {
    try {
        const res = await fetch("/api/bodegas/listar");
        const bodegas = await res.json();

        const select = document.getElementById("editProd_bodegaSelect");
        if (!select) return;

        select.innerHTML = `<option value="">Seleccione la bodega...</option>`;

        bodegas.forEach(b => {
            select.innerHTML += `
                <option value="${b.id_bodega}">${b.nombre_bodega}</option>
            `;
        });

    } catch (err) {
        console.error("Error cargando bodegas (modal edición):", err);
    }
}

async function cargarTiposEntradaFiltro() {
    const select = document.getElementById("filtroTipoEntrada");

    try {
        const res = await fetch("/api/donaciones/tipos_entrada");
        const tipos = await res.json();

        tipos.forEach(t => {
            select.innerHTML += `
                <option value="${t.nombre}">${t.nombre}</option>
            `;
        });

    } catch (err) {
        console.error("Error cargando tipos de entrada:", err);
    }
}


// =========================================
// LISTAR DONACIONES DE PRODUCTO
// =========================================
async function cargarTablaProductos() {
    try {
        const res = await fetch("/api/donaciones/productos");
        const datos = await res.json();

        const tbody = document.getElementById("tbodyProductos");
        tbody.innerHTML = "";

        datos.forEach(d => {
            tbody.innerHTML += `
                <tr>
                    <td>${d.id}</td>
                    <td>${d.nombre}</td>          <!-- viene de COALESCE -->
                    <td>${d.tipo}</td>            <!-- viene de t.nombre AS tipo -->
                    <td>${formatearFecha(d.fecha)}</td>
                    <td>
                        

                        <button class="btn btn-sm btn-info me-1" onclick="verProducto(${d.id})">
                            <i class="bi bi-eye-fill"></i>
                        </button>

                        
                    </td>
                </tr>
            `;
        });

    } catch (error) {
        console.error("Error cargando donaciones de productos:", error);
    }
}


// =========================================
// LISTAR DONACIONES MONETARIAS
// =========================================
async function cargarTablaMonetaria() {
    try {
        const res = await fetch("/api/donaciones/monetaria");
        const datos = await res.json();

        const tbody = document.getElementById("tbodyMonetaria");
        tbody.innerHTML = "";

        datos.forEach(d => {
            tbody.innerHTML += `
                <tr>
                    <td>${d.id}</td>
                    <td>${d.donante}</td>
                    <td>$${Number(d.monto).toLocaleString()}</td>
                    <td>${formatearFecha(d.fecha)}</td>
                    <td>
                        
                        <button class="btn btn-sm btn-info me-1" onclick="verMonetaria(${d.id})">
                            <i class="bi bi-eye-fill"></i>
                        </button>
                        
                    </td>
                </tr>
            `;
        });

    } catch (error) {
        console.error("Error cargando donaciones monetarias:", error);
    }
}

// =========================================
// ACCIONES (VER COMPROBANTES)
// =========================================
function verProducto(id) {
    window.open(`/donaciones/comprobante/${id}`, "_blank");
}

function verMonetaria(id) {
    window.open(`/donaciones/comprobante_monetaria/${id}`, "_blank");
}

// =========================================
// CARGAR LISTAS (TIPOS ENTRADA / MÉTODOS)
// =========================================
async function cargarTiposEntradaFiltro() {
    const select = document.getElementById("filtroTipoEntrada");

    try {
        const res = await fetch("/api/donaciones/tipos_entrada");
        const tipos = await res.json();

        // Dejamos el "Todos" que ya tienes en el HTML:
        // <option value="">Todos</option>

        tipos.forEach(t => {
            select.innerHTML += `
                <option value="${t.id_tipo_entrada}">${t.nombre}</option>
            `;
        });

    } catch (err) {
        console.error("Error cargando tipos de entrada:", err);
    }
}



async function cargarMetodosDonacionEditar() {
    try {
        const res = await fetch("/api/metodos_donacion/activos");
        const metodos = await res.json();

        const select = document.getElementById("editMon_metodo");
        select.innerHTML = `<option value="">Seleccione un método...</option>`;

        metodos.forEach(m => {
            select.innerHTML += `<option value="${m.id_metodo}">${m.nombre}</option>`;
        });

    } catch (err) {
        console.error("Error cargando métodos de donación:", err);
    }
}

// =========================================
// AUTOCOMPLETE DONANTES (MODALES)
// =========================================
async function buscarDonantesModal(inputDoc, inputNombre, hiddenId) {
    const q = inputDoc.value.trim();
    if (q.length < 2) return;

    try {
        const res = await fetch(`/api/donantes/buscar?q=${encodeURIComponent(q)}`);
        const donantes = await res.json();

        if (!donantes || donantes.length === 0) {
            return Swal.fire({
                icon: "warning",
                title: "Donante no encontrado",
                text: "¿Desea crearlo ahora?",
                showCancelButton: true,
                confirmButtonText: "Sí, crear",
                cancelButtonText: "No"
            }).then(r => {
                if (r.isConfirmed) window.location.href = "/donante";
            });
        }

        mostrarSugerencias(inputDoc, donantes, (item) => {
            document.getElementById(hiddenId).value = item.id_donante;
            inputDoc.value = item.numero_documento;
            inputNombre.value = item.nombre;
        });

    } catch (err) {
        console.error("Error buscar donantes (modal):", err);
    }
}

function mostrarSugerencias(input, datos, onSelect) {
    eliminarSugerencias();
    if (!Array.isArray(datos) || datos.length === 0) return;

    const rect = input.getBoundingClientRect();
    const cont = document.createElement("div");

    cont.classList.add("autocomplete-list");
    cont.style.position = "fixed";
    cont.style.left = `${rect.left}px`;
    cont.style.top = `${rect.bottom}px`;
    cont.style.width = `${rect.width}px`;
    cont.style.background = "white";
    cont.style.border = "1px solid #ccc";
    cont.style.zIndex = "9999";
    cont.style.maxHeight = "200px";
    cont.style.overflowY = "auto";

    datos.forEach(item => {
        const div = document.createElement("div");
        div.classList.add("autocomplete-item");
        div.style.padding = "4px 6px";
        div.style.cursor = "pointer";
        div.textContent = `${item.numero_documento} | ${item.nombre}`;
        div.addEventListener("click", () => {
            onSelect(item);
            eliminarSugerencias();
        });
        cont.appendChild(div);
    });

    document.body.appendChild(cont);
}

function eliminarSugerencias() {
    document.querySelectorAll(".autocomplete-list").forEach(el => el.remove());
}

// Eventos input en los campos del modal
document.addEventListener("DOMContentLoaded", () => {
    const docDonanteEdit = document.getElementById("edit_docDonante");
    const nombreDonanteEdit = document.getElementById("edit_nombreDonante");

    if (docDonanteEdit) {
        docDonanteEdit.addEventListener("input", () => {
            buscarDonantesModal(docDonanteEdit, nombreDonanteEdit, "edit_idDonante");
        });
    }

    const docDonMon = document.getElementById("editMon_docDonante");
    const nomDonMon = document.getElementById("editMon_nombreDonante");

    if (docDonMon) {
        docDonMon.addEventListener("input", () => {
            buscarDonantesModal(docDonMon, nomDonMon, "editMon_idDonante");
        });
    }

    // 🔹 NUEVO: autocomplete de producto en el modal
    const editProdNombre = document.getElementById("editProd_nombre");
    if (editProdNombre) {
        editProdNombre.addEventListener("input", () => {
            buscarProductosModal(editProdNombre);
        });
    }
});


// =========================================
// AUTOCOMPLETE PRODUCTO (MODAL EDICIÓN)
// =========================================
async function buscarProductosModal(inputNombre) {
    const q = inputNombre.value.trim();
    if (q.length < 2) return;

    try {
        const res = await fetch(`/api/productos/buscar?q=${encodeURIComponent(q)}`);
        const productos = await res.json();

        if (!productos || productos.length === 0) {
            return Swal.fire({
                icon: "warning",
                title: "Producto no encontrado",
                text: "¿Desea crearlo ahora?",
                showCancelButton: true,
                confirmButtonText: "Sí, crear",
                cancelButtonText: "No"
            }).then(r => {
                if (r.isConfirmed) {
                    window.location.href = "/producto";
                }
            });
        }

        mostrarSugerencias(inputNombre, productos, (item) => {
            productoSeleccionadoEdicion = {
                id_producto: item.id_producto,
                nombre: item.nombre,
                categoria: item.categoria,
                id_unidad: item.id_unidad,
                unidad: item.unidad_medida,
                peso_unitario: item.peso_unitario
            };

            document.getElementById("editProd_nombre").value = item.nombre;
            document.getElementById("editProd_categoria").value = item.categoria;
            document.getElementById("editProd_unidad").value = item.unidad_medida;
            document.getElementById("editProd_peso").value = item.peso_unitario;
        });

    } catch (err) {
        console.error("Error buscando productos (modal edición):", err);
    }
}


// =========================================
// EDITAR PRODUCTO
// =========================================
async function editarProducto(id) {
    idEdicion = id;
configurarMinimoVencimientoEditar();

    try {
        // Cargar tipos de entrada antes
        await cargarTiposEntradaEditar();
        await cargarBodegasEditar(); 

        const res = await fetch(`/api/donaciones/producto/${id}`);
        const data = await res.json();

        if (!data.success) {
            return Swal.fire("Error", data.message, "error");
        }

        // Rellenar cabecera
        document.getElementById("edit_idDonante").value = data.id_donante || "";
        document.getElementById("edit_docDonante").value = data.donante_documento || "";
        document.getElementById("edit_nombreDonante").value = data.donante_nombre || "";
        document.getElementById("edit_fechaEntrada").value = data.fecha_entrada.split("T")[0];
        document.getElementById("edit_observacion").value = data.observacion || "";
        document.getElementById("edit_tipoEntradaSelect").value = data.id_tipo_entrada || "";

        // Cambiar visibilidad de responsable según tipo de entrada
        const tipoSelect = document.getElementById("edit_tipoEntradaSelect");
        manejarResponsablePorTipo(tipoSelect);

        tipoSelect.addEventListener("change", () => manejarResponsablePorTipo(tipoSelect));

        // Productos
        productosEdicion = data.productos || [];
        renderTablaEdicion();

        new bootstrap.Modal(document.getElementById("modalEditarDonacion")).show();

    } catch (err) {
        console.error("Error editando donación:", err);
        Swal.fire("Error", "No fue posible cargar la donación", "error");
    }
    const inputFechaIngreso = document.getElementById("edit_fechaEntrada");

const hoy = new Date();
const hoyStr = hoy.toISOString().split("T")[0];

// Bloquear futuras
inputFechaIngreso.max = hoyStr;

// Opcional, si quieres bloquear hacia atrás también:
// inputFechaIngreso.min = "2020-01-01";   // O una fecha específica

// Si la fecha guardada es futura (dato sucio), la corrige
if (inputFechaIngreso.value > hoyStr) {
    inputFechaIngreso.value = hoyStr;
}

}

// =========================================
// AGREGAR PRODUCTO NUEVO EN MODAL EDICIÓN
// =========================================
function agregarProductoEdicion() {
    if (!productoSeleccionadoEdicion) {
        return Swal.fire("Atención", "Debe seleccionar un producto válido", "warning");
    }

    const cantidad = document.getElementById("editProd_cantidad").value;
    const peso = document.getElementById("editProd_peso").value || productoSeleccionadoEdicion.peso_unitario;
    const valor = document.getElementById("editProd_valor").value;
    const fecha_venc = document.getElementById("editProd_vencimiento").value;
    const bodegaSelect = document.getElementById("editProd_bodegaSelect");

    if (!cantidad || Number(cantidad) <= 0) {
        return Swal.fire("Atención", "La cantidad debe ser mayor que cero", "warning");
    }

    if (!bodegaSelect.value) {
        return Swal.fire("Atención", "Debe seleccionar una bodega", "warning");
    }

    const nombreBodega = bodegaSelect.options[bodegaSelect.selectedIndex].text;

    productosEdicion.push({
        id_producto: productoSeleccionadoEdicion.id_producto,
        nombre: productoSeleccionadoEdicion.nombre,
        cantidad: cantidad,
        peso_unitario: peso,
        id_unidad: productoSeleccionadoEdicion.id_unidad,
        unidad: productoSeleccionadoEdicion.unidad,
        id_bodega: bodegaSelect.value,
        bodega: nombreBodega,
        valor_producto: valor || null,
        fecha_vencimiento: fecha_venc || null
    });

    // Limpiar campos del mini-formulario
    document.getElementById("editProd_nombre").value = "";
    document.getElementById("editProd_categoria").value = "";
    document.getElementById("editProd_cantidad").value = 1;
    document.getElementById("editProd_unidad").value = "";
    document.getElementById("editProd_peso").value = "";
    document.getElementById("editProd_valor").value = "";
    document.getElementById("editProd_vencimiento").value = "";
    bodegaSelect.value = "";

    productoSeleccionadoEdicion = null;

    renderTablaEdicion();
}




// =========================================
// RENDER TABLA DE EDICIÓN
// =========================================
function renderTablaEdicion() {
    const tbody = document.getElementById("tbodyEditarProductos");
    tbody.innerHTML = "";

    productosEdicion.forEach((p, i) => {
        const fechaVenc = p.fecha_vencimiento ? p.fecha_vencimiento.split("T")[0] : "";

        tbody.innerHTML += `
            <tr>
                <td>${i + 1}</td>
                <td>${p.nombre}</td>
                <td>
                    <input type="number" min="1" class="form-control"
                        value="${p.cantidad}"
                        onchange="actualizarCantidadEdicion(${i}, this.value)">
                </td>
                <td>${p.peso_unitario} ${p.unidad || ""}</td>
                <td>${p.bodega || "-"}</td>
                <td>
                    <input type="number" min="0" class="form-control"
                        value="${p.valor_producto || 0}"
                        onchange="actualizarValorEdicion(${i}, this.value)">
                </td>
                <td>
                    <input type="date" class="form-control"
                        value="${fechaVenc}"
                        onchange="actualizarFechaVencEdicion(${i}, this.value)">
                </td>
                <td>
                    <button class="btn btn-danger btn-sm" onclick="eliminarProductoEdicion(${i})">
                        <i class="bi bi-x-circle"></i>
                    </button>
                </td>
            </tr>
        `;
    });
}

function actualizarCantidadEdicion(i, v) {
    productosEdicion[i].cantidad = v;
}

function actualizarValorEdicion(i, v) {
    productosEdicion[i].valor_producto = v;
}

function actualizarFechaVencEdicion(i, v) {
    productosEdicion[i].fecha_vencimiento = v;
}

function eliminarProductoEdicion(i) {
    productosEdicion.splice(i, 1);
    renderTablaEdicion();
}



async function cargarTablaFiltrada() {
    const tipo = document.getElementById("filtroTipoEntrada").value;

    let url = "/api/donaciones/filtrar?";
    if (tipo) url += `tipo=${encodeURIComponent(tipo)}`;

    try {
        const res = await fetch(url);
        const datos = await res.json();

        const tbody = document.getElementById("tbodyProductos");
        tbody.innerHTML = "";

        datos.forEach(d => {
            tbody.innerHTML += `
                <tr>
                    <td>${d.id}</td>
                    <td>${d.nombre}</td>
                    <td>${d.tipo}</td>
                    <td>${formatearFecha(d.fecha)}</td>
                    <td>
                        <button class="btn btn-warning btn-sm" onclick="editarProducto(${d.id})"><i class="bi bi-pencil"></i></button>
                        <button class="btn btn-info btn-sm" onclick="verProducto(${d.id})"><i class="bi bi-eye"></i></button>
                        <button class="btn btn-danger btn-sm" onclick="anularProducto(${d.id})"><i class="bi bi-x-circle"></i></button>
                    </td>
                </tr>
            `;
        });

    } catch (err) {
        console.error("Error cargando filtrados:", err);
    }
}

document.getElementById("filtroTipoEntrada").addEventListener("change", cargarTablaFiltrada);







// =========================================
// INICIO
// =========================================
cargarTablas();
console.log("Cargando tipos entrada...");
cargarTiposEntradaFiltro();

