// =========================================
// VARIABLES GLOBALES
// =========================================
let idDonanteSeleccionado = null;
let idDonanteSeleccionadoMon = null;
let productoSeleccionado = null;
let listaProductos = [];

// =========================================
// SELECCIÓN DE CAMPOS DEL FORMULARIO
// =========================================
const tipoEntradaSelect = document.getElementById("tipoEntradaSelect");
const docDonante = document.getElementById("docDonante");
const nombreDonante = document.getElementById("nombreDonante");

const tipoBodegaSelect = document.getElementById("tipoBodegaSelect");

// Campos donación monetaria
const docDonanteMon = document.getElementById("docDonanteMon");
const nombreDonanteMon = document.getElementById("nombreDonanteMon");

const contDonante = document.getElementById("contenedorDonante");
// contenedorResponsable puede ya no estar

// Botones y formularios
const btnProducto = document.getElementById("btnProducto");
const btnMonetaria = document.getElementById("btnMonetaria");
const formProducto = document.getElementById("formProducto");
const formMonetaria = document.getElementById("formMonetaria");

// Campos de fechas
const ingresoProducto = document.getElementById("ingresoProducto");
const prodVencimiento = document.getElementById("prod_vencimiento");

// Campos producto
const prodNombre = document.getElementById("prod_nombre");
const prodUnidad = document.getElementById("prod_unidad");
const prodPeso = document.getElementById("prod_peso");
const prodCategoria = document.getElementById("prod_categoria");
const prodUbicacion = document.getElementById("ubicacionProducto");
const inputAnexos = document.getElementById("anexos");
const inputAnexosMon = document.getElementById("anexosMon");

// Totales (opcional, si existen en el HTML)
const totalPesoDonacionEl = document.getElementById("totalPesoDonacion");
const totalValorDonacionEl = document.getElementById("totalValorDonacion");

// =========================
// FORMATEADORES NUMÉRICOS
// =========================
function formatKg(value) {
    const num = Number(value || 0);
    if (Number.isNaN(num)) return "0";
    if (Number.isInteger(num)) {
        return num.toString();
    }
    return num.toFixed(3).replace(/\.?0+$/, "");
}

function formatMoney(value) {
    const num = Number(value || 0);
    if (Number.isNaN(num)) return "0";
    return num
        .toFixed(0)
        .replace(/\B(?=(\d{3})+(?!\d))/g, ".");
}

// =========================================
// CAMBIO ENTRE FORMULARIOS (CON ESTILOS)
// =========================================
btnProducto.addEventListener("click", () => {
    formProducto.classList.remove("d-none");
    formMonetaria.classList.add("d-none");

    btnProducto.classList.add("boton-activo");
    btnProducto.classList.remove("boton-inactivo");

    btnMonetaria.classList.remove("boton-activo");
    btnMonetaria.classList.add("boton-inactivo");
});

btnMonetaria.addEventListener("click", () => {
    formMonetaria.classList.remove("d-none");
    formProducto.classList.add("d-none");

    btnMonetaria.classList.add("boton-activo");
    btnMonetaria.classList.remove("boton-inactivo");

    btnProducto.classList.remove("boton-activo");
    btnProducto.classList.add("boton-inactivo");
});

// =========================================
// FECHAS AUTOMÁTICAS
// =========================================
const hoy = new Date();
const hoyStr = hoy.toISOString().split("T")[0];

ingresoProducto.value = hoyStr;
ingresoProducto.max = hoyStr;



// =========================================
// CARGAR TIPOS DE ENTRADA
// =========================================
async function cargarTiposEntrada() {
    try {
        const res = await fetch("/api/tipo_entrada/activas");
        const tipos = await res.json();

        tipoEntradaSelect.innerHTML = `<option value="">Seleccione...</option>`;

        tipos.forEach(t => {
            tipoEntradaSelect.innerHTML += `
                <option value="${t.id_tipo_entrada}">
                    ${t.nombre}
                </option>`;
        });

    } catch (err) {
        console.error(" Error cargando tipos entrada:", err);
    }
}

// =========================================
// CARGAR BODEGAS (incluyendo ubicación)
// =========================================
async function cargarBodegas() {
    try {
        const res = await fetch("/api/bodegas/listar");
        const bodegas = await res.json();

        tipoBodegaSelect.innerHTML = `<option value="">Seleccione la bodega...</option>`;

        bodegas.forEach(b => {
            tipoBodegaSelect.innerHTML += `
                <option value="${b.id_bodega}" data-ubicacion="${b.ubicacion || ''}">
                    ${b.nombre_bodega}
                </option>`;
        });

    } catch (err) {
        console.error("Error cargando bodegas:", err);
    }
}

// =========================================
// CARGAR MÉTODOS DE DONACIÓN (MONETARIA)
// =========================================
async function cargarMetodosDonacion() {
    try {
        const res = await fetch("/api/metodos_donacion/activos");
        const metodos = await res.json();

        const select = document.getElementById("metodoDonacionMon");

        select.innerHTML = `<option value="">Seleccione un método...</option>`;

        metodos.forEach(m => {
            select.innerHTML += `
                <option value="${m.id_metodo}">${m.nombre}</option>
            `;
        });

    } catch (err) {
        console.error("Error cargando métodos de donación:", err);
    }
}



// =========================================
// AUTOCOMPLETAR DONANTE (PRODUCTOS)
// =========================================
docDonante.addEventListener("input", () => {
    buscarDonantes(docDonante, nombreDonante, (id) => idDonanteSeleccionado = id);
});

// =========================================
// AUTOCOMPLETAR DONANTE (MONETARIA)
// =========================================
docDonanteMon.addEventListener("input", () => {
    buscarDonantes(docDonanteMon, nombreDonanteMon, (id) => idDonanteSeleccionadoMon = id);
});

// =========================================
// AUTOCOMPLETAR PRODUCTO
// =========================================
prodNombre.addEventListener("input", async () => {
    const q = prodNombre.value.trim();
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

        mostrarSugerencias(prodNombre, productos, (item) => {
            productoSeleccionado = item;

            prodNombre.value = item.nombre;
            prodUnidad.value = item.unidad_medida;
            prodPeso.value = item.peso_unitario;
            prodCategoria.value = item.categoria;

            productoSeleccionado.id_categoria = item.id_categoria;
            productoSeleccionado.peso_kg = item.peso_kg;
            productoSeleccionado.unidad = item.unidad_medida;
        });

    } catch (err) {
        console.error("Error buscar productos:", err);
    }
});

// =========================================
// AUTOCOMPLETE VISUAL
// =========================================
function mostrarSugerencias(input, datos, onSelect) {
    eliminarSugerencias();
    if (!Array.isArray(datos) || datos.length === 0) return;

    const rect = input.getBoundingClientRect();
    const cont = document.createElement("div");

    cont.classList.add("autocomplete-list");
    cont.style.position = "absolute";
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
        div.textContent = Object.values(item).join(" | ");
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

// =========================================
// FUNCIÓN GENÉRICA PARA BUSCAR DONANTES
// =========================================
async function buscarDonantes(inputDocumento, inputNombre, setID) {
    const q = inputDocumento.value.trim();
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

        mostrarSugerencias(inputDocumento, donantes, (item) => {
            setID(item.id_donante);
            inputDocumento.value = item.numero_documento;
            inputNombre.value = item.nombre;
        });

    } catch (err) {
        console.error("Error en buscarDonantes:", err);
    }
}

// =========================================
// AGREGAR PRODUCTO A LA LISTA
// =========================================
function agregarProducto() {
    if (!productoSeleccionado) {
        return Swal.fire("Atención", "Seleccione un producto válido", "warning");
    }

    if (!tipoBodegaSelect.value) {
        return Swal.fire("Atención", "Debe seleccionar una bodega para este producto", "warning");
    }

    const optBodega = tipoBodegaSelect.options[tipoBodegaSelect.selectedIndex];
    const nombreBodega = optBodega.text;

    let ubicacionBodega = (prodUbicacion.value || "").trim();
    if (!ubicacionBodega) {
        ubicacionBodega = optBodega.dataset.ubicacion || "";
    }

    const cantidad = document.getElementById("prod_cantidad").value;
    const valorUnitario = document.getElementById("prod_valor").value;
    const codigoBarras = document.getElementById("prod_codigo").value;

    listaProductos.push({
        id_producto: productoSeleccionado.id_producto,
        id_categoria: productoSeleccionado.id_categoria,
        nombre: productoSeleccionado.nombre,
        categoria: productoSeleccionado.categoria,
        cantidad: cantidad,
        peso_unitario: prodPeso.value,
        peso_kg: productoSeleccionado.peso_kg,
        id_unidad: productoSeleccionado.id_unidad,
        unidad: productoSeleccionado.unidad,
        id_bodega: tipoBodegaSelect.value,
        nombre_bodega: nombreBodega,
        bodega_texto: ubicacionBodega,
        valor_producto: valorUnitario,
        fecha_vencimiento: document.getElementById("prod_vencimiento").value,
        codigo_barras: codigoBarras
    });

    renderTablaProductos();

    // limpiar campos
    prodNombre.value = "";
    prodUnidad.value = "";
    prodPeso.value = "";
    prodCategoria.value = "";
    document.getElementById("prod_cantidad").value = 1;
    tipoBodegaSelect.value = "";
    document.getElementById("prod_valor").value = "";
    document.getElementById("prod_codigo").value = "";
    prodUbicacion.value = "";

    productoSeleccionado = null;
}

// =========================================
// RENDER TABLA DE PRODUCTOS
// =========================================
function renderTablaProductos() {
    const tbody = document.querySelector("#tablaProductos tbody");
    tbody.innerHTML = "";

    let totalPeso = 0;
    let totalValor = 0;

    listaProductos.forEach((p, i) => {
        const cantidadNum = Number(p.cantidad) || 0;
        const pesoKgNum = Number(p.peso_kg) || 0;
        const valorUnitarioNum = Number(p.valor_producto) || 0;

        const pesoTotal = cantidadNum * pesoKgNum;
        const valorTotal = cantidadNum * valorUnitarioNum;

        totalPeso += pesoTotal;
        totalValor += valorTotal;

        tbody.innerHTML += `
            <tr>
                <td>${i + 1}</td>
                <td>${p.nombre}</td>
                <td>${cantidadNum}</td>
                <td>${p.unidad || p.id_unidad}</td>
                <td>${pesoTotal ? formatKg(pesoTotal) + " kg" : "-"}</td>
                <td>${p.categoria}</td>
                <td>${p.nombre_bodega}</td>
                <td>${p.bodega_texto || "-"}</td>
                <td>${valorTotal ? formatMoney(valorTotal) : "-"}</td>
                <td>${p.fecha_vencimiento || "-"}</td>
                <td>
                    <button class="btn btn-danger btn-sm" onclick="eliminarProducto(${i})">X</button>
                </td>
            </tr>`;
    });

    if (totalPesoDonacionEl) {
        totalPesoDonacionEl.textContent = formatKg(totalPeso) + " kg";
    }
    if (totalValorDonacionEl) {
        totalValorDonacionEl.textContent = formatMoney(totalValor);
    }
}

function eliminarProducto(i) {
    listaProductos.splice(i, 1);
    renderTablaProductos();
}

// =========================================
// ENVIAR REGISTRO DE DONACIÓN DE PRODUCTOS
// =========================================
// =========================================
// ENVIAR REGISTRO DE DONACIÓN DE PRODUCTOS
// =========================================
formProducto.addEventListener("submit", async (e) => {
    e.preventDefault();

    const selectedText = tipoEntradaSelect.options[tipoEntradaSelect.selectedIndex].text.toLowerCase();

    if (!tipoEntradaSelect.value) {
        return Swal.fire("Atención", "Debe seleccionar un tipo de entrada", "warning");
    }

    if (listaProductos.length === 0) {
        return Swal.fire("Atención", "Debe agregar al menos un producto", "warning");
    }

    // ✅ Si es DONACIÓN, exigimos donante
    if (selectedText.includes("donación") || selectedText.includes("donacion")) {
        if (!idDonanteSeleccionado) {
            return Swal.fire("Atención", "Debe seleccionar un donante válido", "warning");
        }
    }

    // ==============================
    // Construir FormData (multipart)
    // ==============================
    const formData = new FormData();

    formData.append("id_tipo_entrada", tipoEntradaSelect.value);
    if (idDonanteSeleccionado) {
        formData.append("id_donante", idDonanteSeleccionado);
    }
    formData.append("fecha_entrada", ingresoProducto.value);
    formData.append("observacion", document.getElementById("descripcionEntrada").value || "");

    // Lista de productos en JSON
    formData.append("productos", JSON.stringify(listaProductos));

    // Archivos (anexos)
    if (inputAnexos && inputAnexos.files && inputAnexos.files.length > 0) {
        Array.from(inputAnexos.files).forEach(file => {
            formData.append("anexos", file);
        });
    }

    try {
        const res = await fetch("/api/registro_donacion/", {
            method: "POST",
            // ❌ NO poner Content-Type, fetch lo arma solo para multipart
            body: formData
        });

        const data = await res.json();

        if (!data.success) {
            return Swal.fire("Error", data.message, "error");
        }

        Swal.fire({
            icon: "success",
            title: "Entrada registrada",
            text: "¿Desea ver el comprobante?",
            showCancelButton: true,
            confirmButtonText: "Ver comprobante",
            cancelButtonText: "Cerrar"
        }).then(r => {
            if (r.isConfirmed) {
                window.open(`/donaciones/comprobante/${data.id_entrada}`, "_blank");
            }
        });

        // LIMPIEZA
        listaProductos = [];
        renderTablaProductos();
        docDonante.value = "";
        nombreDonante.value = "";
        tipoEntradaSelect.value = "";
        document.getElementById("descripcionEntrada").value = "";
        idDonanteSeleccionado = null;

        // limpiar input de anexos
        if (inputAnexos) {
            inputAnexos.value = "";
        }

    } catch (err) {
        console.error(err);
        Swal.fire("Error", "Fallo en comunicación con el servidor", "error");
    }
});


// =========================================
// ENVIAR REGISTRO DE DONACIÓN MONETARIA
// =========================================
// =========================================
// ENVIAR REGISTRO DE DONACIÓN MONETARIA
// =========================================
formMonetaria.addEventListener("submit", async (e) => {
    e.preventDefault();

    if (!idDonanteSeleccionadoMon) {
        return Swal.fire("Atención", "Seleccione un donante válido", "warning");
    }

    const monto = document.getElementById("montoMon").value;
    const id_metodo = document.getElementById("metodoDonacionMon").value;
    const descripcion = document.getElementById("descripcionMon").value;
    const fecha = document.getElementById("fechaDonacionMon").value;

    if (!id_metodo) {
        return Swal.fire("Atención", "Debe seleccionar un método de donación", "warning");
    }

    if (!monto || monto <= 0) {
        return Swal.fire("Atención", "El monto debe ser mayor que cero", "warning");
    }

    // ==============================
    // Construir FormData (multipart)
    // ==============================
    const formData = new FormData();
    formData.append("id_donante", idDonanteSeleccionadoMon);
    formData.append("id_metodo", id_metodo);
    formData.append("monto", monto);
    formData.append("descripcion", descripcion || "");
    formData.append("fecha_donacion", fecha || "");

    // Archivos de comprobante monetario
    if (inputAnexosMon && inputAnexosMon.files && inputAnexosMon.files.length > 0) {
        Array.from(inputAnexosMon.files).forEach(file => {
            formData.append("anexosMon", file);
        });
    }

    try {
        const res = await fetch("/api/donacion_monetaria/", {
            method: "POST",
            // ❌ No pongas Content-Type; fetch lo arma solo para FormData
            body: formData
        });

        const data = await res.json();

        if (!data.success) {
            return Swal.fire("Error", data.message, "error");
        }

        Swal.fire({
            icon: "success",
            title: "Donación monetaria registrada",
            text: "¿Desea ver el comprobante?",
            showCancelButton: true,
            confirmButtonText: "Ver comprobante",
            cancelButtonText: "Cerrar"
        }).then(r => {
            if (r.isConfirmed) {
                window.open(`/donaciones/comprobante_monetaria/${data.id_donacion}`, "_blank");
            }
        });

        // Limpiar formulario monetario
        docDonanteMon.value = "";
        nombreDonanteMon.value = "";
        document.getElementById("montoMon").value = "";
        document.getElementById("descripcionMon").value = "";
        document.getElementById("metodoDonacionMon").value = "";
        document.getElementById("fechaDonacionMon").value = "";
        idDonanteSeleccionadoMon = null;

        // limpiar input de anexos monetarios
        if (inputAnexosMon) {
            inputAnexosMon.value = "";
        }

    } catch (error) {
        console.error(error);
        Swal.fire("Error", "Fallo en comunicación con el servidor", "error");
    }
});


// =========================================
// INICIO
// =========================================
cargarTiposEntrada();
cargarBodegas();
cargarMetodosDonacion();
document.addEventListener("click", eliminarSugerencias);