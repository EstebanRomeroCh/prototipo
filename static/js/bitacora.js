// static/js/bitacora.js

document.addEventListener("DOMContentLoaded", () => {
    console.log("bitacora.js cargado ✅");

    const formFiltros = document.getElementById("formFiltrosBitacora");
    const tbody = document.getElementById("tbodyBitacora");

    if (!formFiltros || !tbody) {
        console.error("No se encontró formFiltrosBitacora o tbodyBitacora en el DOM");
        return;
    }

    async function cargarBitacora() {
        const params = new URLSearchParams(new FormData(formFiltros));
        const url = "/bitacora/data?" + params.toString();

        console.log("Consultando bitácora en:", url);

        try {
            const res = await fetch(url);
            console.log("Status bitácora:", res.status);

            if (!res.ok) {
                console.error("Error HTTP al cargar bitácora:", res.status);
                tbody.innerHTML = `
                    <tr>
                        <td colspan="8" class="text-center text-danger">
                            Error cargando bitácora (HTTP ${res.status})
                        </td>
                    </tr>
                `;
                return;
            }

            const data = await res.json();
            console.log("Respuesta bitácora:", data);

            if (!data.success) {
                console.error("Respuesta error en bitácora:", data.message);
                tbody.innerHTML = `
                    <tr>
                        <td colspan="8" class="text-center text-danger">
                            ${data.message || 'Error al cargar bitácora'}
                        </td>
                    </tr>
                `;
                return;
            }

            tbody.innerHTML = "";

            if (!data.items || data.items.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="8" class="text-center">
                            No hay registros en la bitácora para los filtros seleccionados.
                        </td>
                    </tr>
                `;
                return;
            }

            data.items.forEach(reg => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td>${reg.fecha || ""}</td>
                    <td>${reg.usuario || ""}</td>
                    <td>${reg.modulo || ""}</td>
                    <td>${reg.accion || ""}</td>
                    <td class="text-start">${reg.descripcion || ""}</td>
                    <td>${reg.tabla_afectada || "-"}</td>
                    <td>${reg.id_registro != null ? reg.id_registro : "-"}</td>
                    <td>${reg.ip_origen || "-"}</td>
                `;
                tbody.appendChild(tr);
            });

        } catch (err) {
            console.error("Error cargando bitácora:", err);
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center text-danger">
                        Error de conexión al cargar bitácora
                    </td>
                </tr>
            `;
        }
    }

    // Cargar al inicio
    cargarBitacora();

    // Re-cargar cuando se usen los filtros
    formFiltros.addEventListener("submit", (e) => {
        e.preventDefault();
        cargarBitacora();
    });
});
