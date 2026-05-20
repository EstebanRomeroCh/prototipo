// static/js/notificacion.js

let cacheNotificaciones = [];

// =========================
// Helpers de formato
// =========================
function formatKgJS(value) {
    const n = Number(value || 0);
    if (Number.isNaN(n)) return "0";
    const fixed = n.toFixed(3);
    return fixed.replace(/\.?0+$/, ""); // quita ceros y punto
}

function formatFechaCorta(fechaStr) {
    if (!fechaStr) return "";
    const d = new Date(fechaStr);
    if (isNaN(d.getTime())) return fechaStr;
    return d.toLocaleDateString("es-CO", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric"
    });
}

function formatFechaLarga(fechaStr) {
    if (!fechaStr) return "";
    const d = new Date(fechaStr);
    if (isNaN(d.getTime())) return fechaStr;
    return d.toLocaleDateString("es-CO", {
        day: "numeric",
        month: "long",
        year: "numeric"
    });
}

// =========================
// Badge campana
// =========================
function actualizarBadgeNotificaciones(count) {
    const badge = document.getElementById("badgeNotificaciones");
    if (!badge) return;

    if (count > 0) {
        badge.classList.remove("d-none");
        const texto = count > 9 ? "9+" : String(count);
        badge.textContent = texto;
        badge.classList.remove("badge-dot");
    } else {
        badge.classList.add("d-none");
        // si prefieres puntico siempre:
        // badge.classList.remove("d-none");
        // badge.classList.add("badge-dot");
        // badge.textContent = "";
    }
}

// =========================
// Cargar desde el backend
// =========================
async function cargarNotificaciones({ soloBadge = false } = {}) {
    try {
        const res = await fetch("/api/notificaciones/");
        if (!res.ok) {
            console.error("Error HTTP al obtener notificaciones:", res.status);
            if (!soloBadge && typeof swal === "function") {
                swal("Error", "No se pudieron cargar las notificaciones.", "error");
            }
            return;
        }

        const data = await res.json();
        if (!data.success) {
            console.error("Respuesta error en notificaciones:", data.message);
            if (!soloBadge && typeof swal === "function") {
                swal("Error", data.message || "Error al obtener las notificaciones.", "error");
            }
            return;
        }

        cacheNotificaciones = data.items || [];
        actualizarBadgeNotificaciones(cacheNotificaciones.length);

        if (!soloBadge) {
            mostrarModalNotificaciones(cacheNotificaciones);
        }
    } catch (err) {
        console.error("Error JS al obtener notificaciones:", err);
        if (!soloBadge && typeof swal === "function") {
            swal("Error", "Error de conexión al consultar notificaciones.", "error");
        }
    }
}

// =========================
// Agrupar por fecha (Hoy / Ayer / Otros)
// =========================
function normalizarSoloFecha(d) {
    return new Date(d.getFullYear(), d.getMonth(), d.getDate());
}

function agruparPorFechaLegible(items) {
    const hoy = normalizarSoloFecha(new Date());
    const ayer = new Date(hoy);
    ayer.setDate(hoy.getDate() - 1);

    const grupos = {
        hoy: [],
        ayer: [],
        otros: []
    };

    items.forEach((n) => {
        const fechaStr =
            n.fecha_notificacion ||
            n.fecha ||
            n.fecha_vencimiento ||
            null;

        if (!fechaStr) {
            grupos.otros.push(n);
            return;
        }

        const d = new Date(fechaStr);
        if (isNaN(d.getTime())) {
            grupos.otros.push(n);
            return;
        }

        const dNorm = normalizarSoloFecha(d);

        if (dNorm.getTime() === hoy.getTime()) {
            grupos.hoy.push(n);
        } else if (dNorm.getTime() === ayer.getTime()) {
            grupos.ayer.push(n);
        } else {
            grupos.otros.push(n);
        }
    });

    const resultado = [];
    if (grupos.hoy.length) {
        resultado.push({ label: "Hoy", items: grupos.hoy });
    }
    if (grupos.ayer.length) {
        resultado.push({ label: "Ayer", items: grupos.ayer });
    }
    if (grupos.otros.length) {
        resultado.push({ label: "Otros días", items: grupos.otros });
    }
    return resultado;
}

// =========================
// Construir HTML bonito
// =========================
function construirHtmlNotificaciones(items) {
    const grupos = agruparPorFechaLegible(items);

    let html = `
        <div id="notificaciones-contenido" style="max-height:400px; overflow-y:auto;">
    `;

    if (!grupos.length) {
        html += `
            <div class="text-center text-muted" style="padding:10px;">
                No hay alertas en este momento. 
            </div>
        `;
        html += `</div>`;
        return html;
    }

    grupos.forEach((g) => {
        if (!g.items || !g.items.length) return;

        // 🔹 TÍTULO DEL GRUPO CON CLASE PARA USAR EN PRINT
        html += `
            <div class="grupo-title">
                ${g.label}
            </div>
        `;

        g.items.forEach((n) => {
            const notifId = n.id_notificacion || n.id || "";  // 👈 importante

            let icono = "⚠️";
            let color = "#ff9800"; // warning

            if (n.nivel === "danger") {
                icono = "🚨";
                color = "#dc3545";
            } else if (n.tipo && n.tipo.startsWith("stock")) {
                icono = "📦";
            }

            const producto = n.producto || n.nombre_producto || "";
            const bodega = n.bodega || n.nombre_bodega || "";
            const ubicacion = n.ubicacion || n.bodega_texto || "";
            const fechaVenc = n.fecha_vencimiento
                ? formatFechaCorta(n.fecha_vencimiento)
                : "";
            const fechaNotif = n.fecha_notificacion || n.fecha || "";
            const stockKg = n.stock_kg != null ? formatKgJS(n.stock_kg) : null;
            const dias = n.dias_restantes != null ? Number(n.dias_restantes) : null;

            let metaHtml = "";

            if (producto) {
                metaHtml += `<div><strong>Producto:</strong> ${producto}</div>`;
            }
            if (bodega || ubicacion) {
                metaHtml += `<div><strong>Bodega:</strong> ${bodega || "-"} &nbsp; | &nbsp; <strong>Ubicación:</strong> ${ubicacion || "-"}</div>`;
            }
            if (fechaVenc) {
                metaHtml += `<div><strong>Vence:</strong> ${fechaVenc}`;
                if (dias != null) {
                    metaHtml += ` &nbsp; (<strong>${dias} día(s)</strong> restantes)`;
                }
                metaHtml += `</div>`;
            }
            if (stockKg !== null) {
                metaHtml += `<div><strong>Cantidad:</strong> ${stockKg} kg</div>`;
            }
            if (fechaNotif) {
                metaHtml += `<div class="text-muted" style="font-size:12px;">
                    Registrado: ${formatFechaLarga(fechaNotif)}
                </div>`;
            }

            html += `
                <div class="notif-item" data-id="${notifId}" style="
                    display:flex;
                    align-items:flex-start;
                    gap:8px;
                    margin-bottom:8px;
                    padding:10px 12px;
                    border-radius:8px;
                    background:#f8f9fa;
                    border-left:4px solid ${color};
                    border-bottom:1px solid #e0e0e0;
                ">
                    <div style="font-size:20px; flex-shrink:0; line-height:1;">
                        ${icono}
                    </div>
                    <div style="font-size:14px; text-align:left; flex:1;">
                        <div style="margin-bottom:4px;">
                            ${n.mensaje || ""}
                        </div>
                        ${metaHtml}
                        
                    </div>
                </div>
            `;
        });
    });

    html += `</div>`;
    return html;
}


// =========================
// Acciones: marcar leída / eliminar
// =========================
async function marcarNotificacionLeida(id, notifEl) {
    if (!id) return;

    try {
        const res = await fetch("/api/notificaciones/marcar-leida", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ id_notificacion: id })
        });

        let data = {};
        try {
            data = await res.json();
        } catch (_) {}

        if (!res.ok || (data.success === false)) {
            throw new Error(data.message || "No se pudo marcar como leída.");
        }

        // Quitar del DOM
        if (notifEl && notifEl.parentNode) {
            notifEl.parentNode.removeChild(notifEl);
        }

        // Quitar del cache y actualizar badge
        cacheNotificaciones = cacheNotificaciones.filter(n => {
            const nid = n.id_notificacion || n.id;
            return String(nid) !== String(id);
        });
        actualizarBadgeNotificaciones(cacheNotificaciones.length);

    } catch (err) {
        console.error("Error marcarNotificacionLeida:", err);
        if (typeof swal === "function") {
            swal("Error", err.message || "No se pudo marcar la notificación.", "error");
        }
    }
}

async function eliminarNotificacion(id, notifEl) {
    if (!id) return;

    try {
        const res = await fetch("/api/notificaciones/eliminar", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ id_notificacion: id })
        });

        let data = {};
        try {
            data = await res.json();
        } catch (_) {}

        if (!res.ok || (data.success === false)) {
            throw new Error(data.message || "No se pudo eliminar la notificación.");
        }

        // Quitar del DOM
        if (notifEl && notifEl.parentNode) {
            notifEl.parentNode.removeChild(notifEl);
        }

        // Quitar del cache y actualizar badge
        cacheNotificaciones = cacheNotificaciones.filter(n => {
            const nid = n.id_notificacion || n.id;
            return String(nid) !== String(id);
        });
        actualizarBadgeNotificaciones(cacheNotificaciones.length);

    } catch (err) {
        console.error("Error eliminarNotificacion:", err);
        if (typeof swal === "function") {
            swal("Error", err.message || "No se pudo eliminar la notificación.", "error");
        }
    }
}


// =========================
// Imprimir notificaciones
// =========================
function imprimirNotificaciones(htmlContenido) {
    const win = window.open("", "_blank");
    if (!win) return;

    win.document.write(`
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Notificaciones</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    font-size: 14px;
                    margin: 20px;
                }
                h2 {
                    text-align: center;
                    margin-bottom: 20px;
                }
                .notif-item {
                    display: flex;
                    align-items: flex-start;
                    gap: 8px;
                    margin-bottom: 8px;
                    padding: 10px 12px;
                    border-radius: 8px;
                    background: #f8f9fa;
                    border-left: 4px solid #999;
                    page-break-inside: avoid;
                }
                .grupo-title {
                    margin-top: 10px;
                    margin-bottom: 4px;
                    font-weight: 600;
                    border-bottom: 1px solid #e0e0e0;
                    padding-bottom: 2px;
                }
                #notificaciones-contenido {
                    max-height: none !important;
                    overflow: visible !important;
                }
                @media print {
                    body {
                        margin: 10mm;
                    }
                }
            </style>
        </head>
        <body>
            <h2>Notificaciones del sistema</h2>
            ${htmlContenido}
        </body>
        </html>
    `);

    win.document.close();
    win.focus();
    setTimeout(() => {
        win.print();
    }, 300);
}


// =========================
// Modal con SweetAlert
// =========================
function mostrarModalNotificaciones(items) {
    if (!items || items.length === 0) {
        if (typeof swal === "function") {
            swal("Notificaciones", "No hay alertas en este momento. ", "info");
        }
        return;
    }

    const html = construirHtmlNotificaciones(items);

    if (typeof swal !== "function") {
        alert("Tienes " + items.length + " notificaciones.");
        return;
    }

    // Creamos un contenedor y le metemos el HTML
    const contenedor = document.createElement("div");
    contenedor.innerHTML = html;

    // Delegamos eventos en el contenedor
    contenedor.addEventListener("click", async (e) => {
        const btnLeida = e.target.closest(".btn-notif-leida");
        const btnEliminar = e.target.closest(".btn-notif-eliminar");

        if (btnLeida) {
            const id = btnLeida.dataset.id;
            const notifEl = btnLeida.closest(".notif-item");
            await marcarNotificacionLeida(id, notifEl);
        } else if (btnEliminar) {
            const id = btnEliminar.dataset.id;
            const notifEl = btnEliminar.closest(".notif-item");
            await eliminarNotificacion(id, notifEl);
        }
    });

    swal({
        title: "Notificaciones del sistema",
        content: contenedor,
        buttons: {
            imprimir: {
                text: "Imprimir",
                className: "bg-success",
                value: "imprimir",
            },
            cerrar: {
                text: "Cerrar",
                className: "bg-success",
                value: "cerrar",
            }
        }
    }).then((value) => {
        if (value === "imprimir") {
            imprimirNotificaciones(html);
        }
    });
}

// =========================
// API pública que usa el HTML
// =========================
async function mostrarNotificaciones() {
    await cargarNotificaciones({ soloBadge: false });
}
window.mostrarNotificaciones = mostrarNotificaciones;

// =========================
// Init: solo badge
// =========================
document.addEventListener("DOMContentLoaded", () => {
    cargarNotificaciones({ soloBadge: true });
});
