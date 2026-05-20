// static/js/comprobante_salida.js

document.addEventListener("DOMContentLoaded", () => {
    const inputIdSalida = document.getElementById("idSalida");
    const mensajeCargando = document.getElementById("salida-mensaje-cargando");
    const btnImprimir = document.getElementById("btnImprimir");

    if (!inputIdSalida) {
        console.error("No se encontró el input oculto idSalida en la plantilla");
        if (mensajeCargando) {
            mensajeCargando.classList.remove("alert-info");
            mensajeCargando.classList.add("alert-danger");
            mensajeCargando.textContent = "No se encontró el ID de la salida.";
        }
        return;
    }

    const idSalida = inputIdSalida.value;

    function formatKg(value) {
        const n = Number(value || 0);
        if (Number.isNaN(n)) return "0";
        const fixed = n.toFixed(3);
        return fixed.replace(/\.?0+$/, "");
    }

    function formatFecha(fechaStr) {
        if (!fechaStr) return "";
        const d = new Date(fechaStr);
        if (isNaN(d.getTime())) return fechaStr;
        return d.toLocaleDateString("es-CO", {
            day: "2-digit",
            month: "2-digit",
            year: "numeric"
        });
    }

    async function cargarComprobanteSalida() {
        try {
            const resp = await fetch(`/salidas/api/detalle/${idSalida}`);
            if (!resp.ok) {
                throw new Error(`Error HTTP ${resp.status}`);
            }

            const data = await resp.json();
            if (!data.success) {
                throw new Error(data.message || "Error al obtener la salida.");
            }

            const salida = data.salida || {};
            const detalles = data.detalles || [];

            // Encabezado
            const numEl = document.getElementById("comp-numero");
            const tipoEl = document.getElementById("comp-tipo-salida");
            const fechaEl = document.getElementById("comp-fecha-salida");

            if (numEl) numEl.textContent = salida.id_salida || "";
            if (tipoEl) tipoEl.textContent = salida.tipo_salida || "";
            if (fechaEl) fechaEl.textContent = formatFecha(salida.fecha_salida_str);

            // Beneficiario
            const parroquiaEl = document.getElementById("comp-parroquia");
            const encargadoEl = document.getElementById("comp-encargado");
            const docEl = document.getElementById("comp-documento");
            const telEl = document.getElementById("comp-telefono");
            const dirEl = document.getElementById("comp-direccion");
            const ciudadEl = document.getElementById("comp-ciudad");

            if (parroquiaEl) parroquiaEl.textContent = salida.parroquia || "";
            if (encargadoEl) encargadoEl.textContent = salida.encargado || "";

            const docTipo = salida.tipo_documento || "";
            const docNum = salida.numero_documento || "";
            if (docEl) {
                docEl.textContent = (docTipo ? docTipo + " " : "") + (docNum || "");
            }

            if (telEl) telEl.textContent = salida.telefono || "";
            if (dirEl) dirEl.textContent = salida.direccion || "";

            const ciudadTexto =
                (salida.municipio || "") +
                (salida.departamento ? " - " + salida.departamento : "");
            if (ciudadEl) ciudadEl.textContent = ciudadTexto;

            // Observación
            const obsEl = document.getElementById("comp-observacion");
            if (obsEl) {
                obsEl.textContent = salida.observacion || "Sin observaciones.";
            }

            // Detalle
            const tbody = document.getElementById("tbody-detalle-salida");
            const totalKgEl = document.getElementById("comp-total-kg");
            let totalKg = 0;

            if (tbody) {
                tbody.innerHTML = "";

                if (!detalles.length) {
                    tbody.innerHTML = `
                        <tr>
                            <td colspan="5" class="text-center">
                                No hay detalle registrado para esta salida.
                            </td>
                        </tr>
                    `;
                } else {
                    detalles.forEach(d => {
                        const cant = Number(d.cantidad_kg || 0);
                        totalKg += cant;

                        const tr = document.createElement("tr");
                        tr.innerHTML = `
                            <td>${d.producto || ""}</td>
                            <td>${d.categoria || ""}</td>
                            <td>
                                ${d.bodega || ""}
                                ${d.bodega_texto ? " - " + d.bodega_texto : ""}
                            </td>
                            <td>${
                                d.fecha_vencimiento_str
                                    ? formatFecha(d.fecha_vencimiento_str)
                                    : "-"
                            }</td>
                            <td class="text-end">${formatKg(cant)} kg</td>
                        `;
                        tbody.appendChild(tr);
                    });
                }
            }

            if (totalKgEl) {
                totalKgEl.textContent = formatKg(totalKg);
            }

            if (mensajeCargando) {
                mensajeCargando.classList.add("d-none");
            }

        } catch (err) {
            console.error("Error cargando comprobante de salida:", err);
            if (mensajeCargando) {
                mensajeCargando.classList.remove("alert-info");
                mensajeCargando.classList.add("alert-danger");
                mensajeCargando.textContent =
                    "Error al cargar los datos de la salida. Intente nuevamente.";
            }
            if (typeof swal === "function") {
                swal("Error", err.message || "No se pudo cargar el comprobante.", "error");
            }
        }
    }

    // Botón imprimir
    if (btnImprimir) {
        btnImprimir.addEventListener("click", (e) => {
            e.preventDefault();
            window.print();
        });
    }



    // Cargar datos al inicio
    cargarComprobanteSalida();
});
