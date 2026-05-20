// static/js/salidas_lista.js

function formatFechaLista(fechaStr) {
    if (!fechaStr) return "-";
    const d = new Date(fechaStr);
    if (isNaN(d.getTime())) return fechaStr;
    return d.toLocaleDateString("es-CO", {
        day: "2-digit",
        month: "long",
        year: "numeric"
    });
}

function formatKgLista(value) {
    const n = Number(value || 0);
    if (Number.isNaN(n)) return "0";
    const fixed = n.toFixed(3);
    return fixed.replace(/\.?0+$/, "");
}

// =====================
// Cargar tipos de salida
// =====================
async function cargarTiposSalidaFiltro() {
    const select = document.getElementById("selectFiltroTipoSalida");
    if (!select) return;

    // Mantener el "Todos los tipos..."
    select.innerHTML = `<option value="">Todos los tipos de salida</option>`;

    try {
        // ✅ tu backend real tiene: /salidas/api/tipos-salida
        // pero por compatibilidad probamos ambos
        const endpoints = ["/salidas/api/tipos-salida", "/salidas/api/tipo-salida"];
        let dataOk = null;

        for (const url of endpoints) {
            try {
                const resp = await fetch(url);
                if (!resp.ok) continue;

                const data = await resp.json();
                if (data && data.success) {
                    dataOk = data;
                    break;
                }
            } catch (e) {
                // seguimos probando el siguiente endpoint
            }
        }

        if (!dataOk) throw new Error("No se pudo cargar tipos de salida (endpoint no encontrado o error).");

        (dataOk.items || []).forEach(t => {
            const opt = document.createElement("option");
            opt.value = t.id_tipo_salida;
            opt.textContent = t.nombre;
            select.appendChild(opt);
        });

    } catch (err) {
        console.error("Error cargando tipos de salida:", err);
        if (typeof swal === "function") {
            swal("Error", "No se pudieron cargar los tipos de salida.", "error");
        }
    }
}

// =====================
// Cargar lista de salidas
// =====================
async function cargarSalidas() {
    const tbody = document.getElementById("tbodySalidas");
    const selectTipo = document.getElementById("selectFiltroTipoSalida");

    if (!tbody) return;

    // Estado según botón activo
    let estado = "";
    const btnActivas = document.getElementById("btnFiltroEstadoActivo");
    const btnAnuladas = document.getElementById("btnFiltroEstadoAnulado");
    const btnTodas = document.getElementById("btnFiltroEstadoTodas");

    if (btnActivas && btnActivas.classList.contains("active")) {
        estado = "Activo";
    } else if (btnAnuladas && btnAnuladas.classList.contains("active")) {
        estado = "Anulado";
    } else {
        estado = "";  // todas
    }

    const idTipoSalida = selectTipo ? selectTipo.value : "";

    tbody.innerHTML = `
        <tr>
            <td colspan="7" class="text-center py-3">
                Cargando salidas...
            </td>
        </tr>
    `;

    try {
        const params = new URLSearchParams();
        if (estado) params.append("estado", estado);
        if (idTipoSalida) params.append("id_tipo_salida", idTipoSalida);

        const resp = await fetch("/salidas/api/lista?" + params.toString());
        if (!resp.ok) throw new Error("HTTP " + resp.status);

        const data = await resp.json();
        if (!data.success) throw new Error(data.message || "Error en API lista de salidas");

        const items = data.items || [];
        if (!items.length) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center py-3">
                        No hay salidas registradas con esos filtros.
                    </td>
                </tr>
            `;
            return;
        }

        let html = "";
        items.forEach(s => {
            const fechaStr = formatFechaLista(s.fecha_salida);

            // ✅ soporta total_kg o total_peso_kg (según backend)
            const totalNum = (s.total_kg !== undefined && s.total_kg !== null)
                ? s.total_kg
                : (s.total_peso_kg !== undefined && s.total_peso_kg !== null)
                    ? s.total_peso_kg
                    : 0;

            const totalStr = formatKgLista(totalNum);

            // ✅ soporta parroquia/fundación
            const beneficiario = s.beneficiario || s.parroquia_nombre || "Sin registro";

            const estadoBadge = (s.estado === "Anulado")
                ? `<span class="badge bg-danger">Anulado</span>`
                : `<span class="badge bg-success">Activo</span>`;

            html += `
                <tr>
                    <td>${s.id_salida}</td>
                    <td>${beneficiario}</td>
                    <td>${s.tipo_salida || "-"}</td>
                    <td>${fechaStr}</td>
                    <td>${totalStr} kg</td>
                    <td>${estadoBadge}</td>
                    <td class="text-center">
                        <button class="btn btn-sm btn-info  me-1 btn-ver-comprobante"
                                data-id="${s.id_salida}"
                                title="Ver comprobante">
                            <i class="bi bi-eye"></i>
                        </button>
                        
                    </td>
                </tr>
            `;
        });

        tbody.innerHTML = html;

    } catch (err) {
        console.error("Error cargando salidas:", err);
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center text-danger py-3">
                    Error al cargar el listado de salidas.
                </td>
            </tr>
        `;
        if (typeof swal === "function") {
            swal("Error", "No se pudo cargar el listado de salidas.", "error");
        }
    }
}

// =====================
// Acciones tabla
// =====================
async function anularSalida(idSalida) {
    if (!idSalida) return;

    if (typeof swal === "function") {
        const conf = await swal({
            title: "Anular salida",
            text: `¿Seguro que deseas anular la salida N° ${idSalida}?`,
            icon: "warning",
            buttons: ["Cancelar", "Sí, anular"],
            dangerMode: true
        });

        if (!conf) return;
    } else {
        if (!confirm("¿Seguro que deseas anular esta salida?")) return;
    }

    try {
        const resp = await fetch(`/salidas/api/anular/${idSalida}`, {
            method: "POST"
        });
        const data = await resp.json();

        if (!resp.ok || !data.success) {
            throw new Error(data.message || "Error al anular la salida.");
        }

        if (typeof swal === "function") {
            swal("Salida anulada", "La salida se ha anulado correctamente.", "success");
        }
        cargarSalidas(); // recargar lista
    } catch (err) {
        console.error("Error anulando salida:", err);
        if (typeof swal === "function") {
            swal("Error", err.message || "No se pudo anular la salida.", "error");
        }
    }
}

// =====================
// Init
// =====================
document.addEventListener("DOMContentLoaded", () => {
    const btnActivo = document.getElementById("btnFiltroEstadoActivo");
    const btnAnulado = document.getElementById("btnFiltroEstadoAnulado");
    const btnTodas = document.getElementById("btnFiltroEstadoTodas");
    const selectTipo = document.getElementById("selectFiltroTipoSalida");
    const tbody = document.getElementById("tbodySalidas");

    // Botones de estado
    function setEstadoActivo(btn) {
        [btnActivo, btnAnulado, btnTodas].forEach(b => {
            if (!b) return;
            b.classList.remove("active");
            b.classList.remove("btn-success");
            b.classList.add("btn-outline-success");
        });
        if (btn) {
            btn.classList.add("active");
            btn.classList.remove("btn-outline-success");
            btn.classList.add("btn-success");
        }
        cargarSalidas();
    }

    if (btnActivo) btnActivo.addEventListener("click", () => setEstadoActivo(btnActivo));
    if (btnAnulado) btnAnulado.addEventListener("click", () => setEstadoActivo(btnAnulado));
    if (btnTodas) btnTodas.addEventListener("click", () => setEstadoActivo(btnTodas));

    // Cambio de tipo de salida
    if (selectTipo) selectTipo.addEventListener("change", () => cargarSalidas());

    // Acciones de la tabla
    if (tbody) {
        tbody.addEventListener("click", (e) => {
            const btnVer = e.target.closest(".btn-ver-comprobante");
            const btnAnular = e.target.closest(".btn-anular-salida");

            if (btnVer) {
                const id = btnVer.dataset.id;
                if (id) window.open(`/salidas/comprobante/${id}`, "_blank");
            } else if (btnAnular) {
                const id = btnAnular.dataset.id;
                if (id) anularSalida(id);
            }
        });
    }

    // Cargar datos iniciales
    cargarTiposSalidaFiltro().then(() => {
        setEstadoActivo(btnActivo); // por defecto "Activas"
    });
});
