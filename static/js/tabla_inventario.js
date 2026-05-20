// static/js/tabla_inventario.js

// =========================
// Helpers
// =========================
function formatKg(value) {
    const num = Number(value || 0);
    if (Number.isNaN(num)) return "0";
    if (Number.isInteger(num)) {
        return num.toString();
    }
    return num.toFixed(3).replace(/\.?0+$/, "");
}

// días restantes = fecha_venc - hoy
function diasRestantes(fechaStr) {
    if (!fechaStr) return null;
    const hoy = new Date();
    const fv = new Date(fechaStr);
    if (isNaN(fv.getTime())) return null;
    const ms = fv.getTime() - hoy.getTime();
    return Math.floor(ms / (1000 * 60 * 60 * 24));
}

// Devuelve estilo inline según días restantes
function getEstiloFila(dias) {
    // Vencido
    if (dias === null) {
        return 'background-color:#6c757d; color:#ffffff;'; // sin fecha → gris
    }
    if (dias < 0) {
        // vencido
        return 'background-color:#4b0000; color:#ffffff;'; // muy oscuro / alarmante
    }
    if (dias <= 2) {
        // rojo fuerte
        return 'background-color:#dc3545; color:#ffffff;';
    }
    if (dias <= 9) {
        // naranja
        return 'background-color:#fd7e14; color:#ffffff;';
    }
    if (dias <= 29) {
        // amarillo
        return 'background-color:#ffc107;';
    }
    // verde (> 30 días)
    return 'background-color:#198754; color:#ffffff;';
}

// =========================
// Construye las filas de la tabla a partir del JSON
// =========================
//const productos = (data.productos || []).filter(p => Number(p.cantidad_total || 0) > 0);
//pintarTabla(productos);

function pintarTabla(productos) {
    const tbody = document.getElementById("tbodyProductos");
    tbody.innerHTML = "";

    if (!productos || productos.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center">
                    No hay productos en el inventario.
                </td>
            </tr>
        `;
        return;
    }

    productos.forEach(p => {
        // Fila principal
        const trMain = document.createElement("tr");
        trMain.innerHTML = `
            <td>${p.id_producto}</td>
            <td>${p.nombre}</td>
            <td>${formatKg(p.cantidad_total)} (kg)</td>
            <td>${p.proximo_vencimiento || '-'}</td>
            <td class="text-center">
                <button type="button"
                        class="btn btn-sm btn-success btn-toggle-detalle"
                        data-product-id="${p.id_producto}">
                    VER SUBLISTA
                </button>
            </td>
        `;
        tbody.appendChild(trMain);

        // Fila de detalle (oculta)
        const trDetalle = document.createElement("tr");
        trDetalle.classList.add("fila-detalle", "d-none");
        trDetalle.dataset.productId = p.id_producto;

        let detalleHTML = `
            <td colspan="5">
                <strong>Detalle de vencimientos para ${p.nombre}:</strong>
                <div class="table-responsive mt-2">
                    <table class="table table-sm table-bordered mb-0">
                        <thead class="table-light">
                            <tr>
                                <th>Fecha de vencimiento</th>
                                <th>Cantidad (kg)</th>
                                <th>Bodega</th>
                                <th>Ubicación</th>
                            </tr>
                        </thead>
                        <tbody>
        `;

        if (p.detalles && p.detalles.length > 0) {
            // Ordenar por días restantes (más urgente primero)
            const detallesOrdenados = p.detalles
                .map(d => ({
                    ...d,
                    dias: diasRestantes(d.fecha_vencimiento)
                }))
                .sort((a, b) => {
                    const da = a.dias === null ? 999999 : a.dias;
                    const db = b.dias === null ? 999999 : b.dias;
                    return da - db;
                })
                .slice(0, 4); // 👈 mostrar solo top 4 más urgentes

            detallesOrdenados.forEach(d => {
                const estilo = getEstiloFila(d.dias);
                detalleHTML += `
                    <tr>
            <td style="${estilo}">${d.fecha_vencimiento || '-'}</td>
            <td style="${estilo}">${formatKg(d.stock_kg)} (kg)</td>
            <td style="${estilo}">${d.nombre_bodega || '-'}</td>
            <td style="${estilo}">${d.bodega_texto || '-'}</td>
        </tr>
                `;
            });
        } else {
            detalleHTML += `
                <tr>
                    <td colspan="4" class="text-center">
                        No hay detalle de vencimientos para este producto.
                    </td>
                </tr>
            `;
        }

        detalleHTML += `
                        </tbody>
                    </table>
                </div>
            </td>
        `;

        trDetalle.innerHTML = detalleHTML;
        tbody.appendChild(trDetalle);
    });
}

// =========================
// Llama a la API y carga los productos (con o sin búsqueda)
// =========================
async function cargarInventario(q = "") {
    const tbody = document.getElementById("tbodyProductos");
    tbody.innerHTML = `
        <tr>
            <td colspan="5" class="text-center">Cargando productos...</td>
        </tr>
    `;

    try {
        const params = new URLSearchParams();
        if (q) params.append("q", q);

        const url = `/inventario/api/productos?` + params.toString();

        const resp = await fetch(url);
        if (!resp.ok) throw new Error("Error de red");

        const data = await resp.json();
        if (!data.success) throw new Error(data.message || "Error en la API");

        pintarTabla(data.productos || []);
    } catch (err) {
        console.error(err);
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center text-danger">
                    Error al cargar el inventario.
                </td>
            </tr>
        `;
    }
}

// =========================
// Lógica para abrir/cerrar sublista
// =========================
function inicializarToggleSublista() {
    document.addEventListener("click", function (e) {
        const btn = e.target.closest(".btn-toggle-detalle");
        if (!btn) return;

        const productId = btn.dataset.productId;
        if (!productId) return;

        const filaDetalle = document.querySelector(
            'tr.fila-detalle[data-product-id="' + productId + '"]'
        );
        if (!filaDetalle) return;

        const estaOculta = filaDetalle.classList.contains("d-none");

        if (estaOculta) {
            filaDetalle.classList.remove("d-none");
            btn.textContent = "OCULTAR";
            btn.classList.remove("btn-success");
            btn.classList.add("btn-secondary");
        } else {
            filaDetalle.classList.add("d-none");
            btn.textContent = "VER SUBLISTA";
            btn.classList.remove("btn-secondary");
            btn.classList.add("btn-success");
        }
    });
}

// =========================
// Inicio
// =========================
document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("form[role='search']");
    if (form) {
        form.addEventListener("submit", (e) => {
            e.preventDefault();
            const q = form.q ? form.q.value.trim() : "";
            cargarInventario(q);
        });
    }

    inicializarToggleSublista();
    cargarInventario(); // carga inicial sin filtro
});
