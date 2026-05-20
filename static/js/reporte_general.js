// static/js/reporte_general.js

document.addEventListener("DOMContentLoaded", () => {
    const formFiltros = document.getElementById("formFiltrosGeneral");
    const tbody = document.getElementById("tbodyGeneral");
    const spanTotales = document.getElementById("spanTotalesGeneral");
    const btnBuscar = document.getElementById("btnBuscarGeneral");
    const btnExcel = document.getElementById("btnExportarExcelGeneral");

    const inputDesde = formFiltros.elements["desde"];
    const inputHasta = formFiltros.elements["hasta"];

    // Gráfica
    const canvasGrafica = document.getElementById("graficaGeneral");
    const subtituloGrafica = document.getElementById("subtituloGraficaGeneral");
    let chartGeneral = null;

    // =========================
    // Helpers de formato
    // =========================
    function formatKg(value) {
        const num = Number(value || 0);
        if (Number.isNaN(num)) return "0";
        if (Number.isInteger(num)) return num.toString();
        return num.toFixed(3).replace(/0+$/, "").replace(/\.$/, "");
    }

    function formatMoney(value) {
        const num = Number(value || 0);
        if (Number.isNaN(num)) return "0";
        return num.toLocaleString("es-CO", {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        });
    }

    // =========================
    // Cargar reporte (tabla + totales + gráfica)
    // =========================
    async function cargarReporteGeneral() {
        const params = new URLSearchParams(new FormData(formFiltros));
        const url = "/reportes/general/data?" + params.toString();

        if (btnBuscar) {
            btnBuscar.disabled = true;
            btnBuscar.innerHTML = `<span class="spinner-border spinner-border-sm"></span>`;
        }

        try {
            const res = await fetch(url);
            if (!res.ok) {
                console.error("Error HTTP reporte general:", res.status);
                return;
            }

            const data = await res.json();
            if (!data.success) {
                console.error("Respuesta error reporte general:", data.message);
                return;
            }

            const items = data.items || [];
            const totales = data.totales || {};

            // ----- Tabla -----
            tbody.innerHTML = "";

            if (items.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="16" class="text-center">
                            No hay datos para el período seleccionado.
                        </td>
                    </tr>
                `;
            } else {
                items.forEach((item) => {
    const tr = document.createElement("tr");

    // 👇 Si tiene anexos, mostramos link al comprobante
    const anexosHtml = item.num_archivos && item.num_archivos > 0
        ? `<a href="/donaciones/comprobante/${item.id_entrada}" target="_blank">
               Ver anexos (${item.num_archivos})
           </a>`
        : "0";

    tr.innerHTML = `
        <td>${item.id_entrada}</td>
        <td>${item.fecha_entrada || ""}</td>
        <td>${item.tipo_entrada || ""}</td>
        <td>${item.numero_documento || ""}</td>
        <td>${item.donante || "-"}</td>
        <td>${item.producto || ""}</td>
        <td>${item.categoria || ""}</td>
        <td>${item.cantidad || 0}</td>
        <td>${formatKg(item.peso_total_kg)} kg</td>
        <td>${formatMoney(item.valor_total)}</td>
        <td>${item.bodega || "-"}</td>
        <td>${item.ubicacion || "-"}</td>
        <td>${item.fecha_vencimiento || "-"}</td>
        <td>${anexosHtml}</td>   <!-- 👈 aquí ahora va el link -->
    `;
    tbody.appendChild(tr);
});

            }

            // ----- Totales -----
            const totalKgStr = formatKg(totales.total_kg);
            const totalValorStr = formatMoney(totales.total_valor);

            if (spanTotales) {
                spanTotales.textContent =
                    `Peso total: ${totalKgStr} kg | Valor total: ${totalValorStr}`;
            }

            // ----- Gráfica -----
            actualizarGraficaGeneral(items);

        } catch (err) {
            console.error("Error cargando reporte general:", err);
        } finally {
            if (btnBuscar) {
                btnBuscar.disabled = false;
                btnBuscar.innerHTML = `<i class="bi bi-search"></i> Buscar`;
            }
        }
    }

    // =========================
    // Gráfica con Chart.js
    // =========================
    function actualizarGraficaGeneral(items) {
        if (!canvasGrafica) return;

        // Agrupar por producto: suma de peso_total_kg
        const mapa = new Map();

        items.forEach(it => {
            const nombre = it.producto || "Sin nombre";
            const peso = Number(it.peso_total_kg || 0);
            if (!mapa.has(nombre)) {
                mapa.set(nombre, 0);
            }
            mapa.set(nombre, mapa.get(nombre) + peso);
        });

        let datos = Array.from(mapa.entries()).map(([nombre, total_kg]) => ({
            nombre,
            total_kg
        }));

        // Ordenar por mayor peso
        datos.sort((a, b) => b.total_kg - a.total_kg);

        // Si quieres limitar, por ejemplo top 5:
        datos = datos.slice(0, 5);

        const labels = datos.map(d => d.nombre);
        const values = datos.map(d => d.total_kg);

        // Subtítulo con rango de fechas
        const desdeTxt = inputDesde.value || "inicio";
        const hastaTxt = inputHasta.value || "hoy";
        if (subtituloGrafica) {
            subtituloGrafica.textContent = `Período: ${desdeTxt} a ${hastaTxt}`;
        }

        // Si no hay datos, destruimos gráfica y salimos
        if (labels.length === 0) {
            if (chartGeneral) {
                chartGeneral.destroy();
                chartGeneral = null;
            }
            return;
        }

        // Destruir gráfica anterior
        if (chartGeneral) {
            chartGeneral.destroy();
        }

        const ctx = canvasGrafica.getContext("2d");

        chartGeneral = new Chart(ctx, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [{
                    label: "Total donado (kg)",
                    data: values,
                    borderWidth: 1,
                    backgroundColor: "rgba(25, 135, 84, 0.6)",
                    borderColor: "rgba(25, 135, 84, 1)"
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function (value) {
                                return value + " kg";
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function (ctx) {
                                return ` ${formatKg(ctx.parsed.y)} kg`;
                            }
                        }
                    }
                }
            }
        });
    }

    // =========================
    // Botón Excel
    // =========================
    if (btnExcel) {
        btnExcel.addEventListener("click", () => {
            const params = new URLSearchParams(new FormData(formFiltros));
            const url = "/reportes/general/excel?" + params.toString();
            window.location.href = url;
        });
    }

    // =========================
    // Eventos de búsqueda
    // =========================
    formFiltros.addEventListener("submit", (e) => {
        e.preventDefault();
        cargarReporteGeneral();
    });

    if (btnBuscar) {
        btnBuscar.addEventListener("click", (e) => {
            e.preventDefault();
            cargarReporteGeneral();
        });
    }

    // Cargar al inicio
    cargarReporteGeneral();
});
