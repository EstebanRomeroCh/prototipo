// static/js/reporte_monetarias.js

document.addEventListener("DOMContentLoaded", () => {
    const formFiltros = document.getElementById("formFiltrosMonetarias");
    const tbody = document.getElementById("tbodyMonetarias");
    const spanTotales = document.getElementById("spanTotalesMonetarias");
    const btnBuscar = document.getElementById("btnBuscarMonetarias");
    const btnExcel = document.getElementById("btnExportarExcelMonetarias");

    if (!formFiltros) return;

    const inputDesde = formFiltros.elements["desde"];
    const inputHasta = formFiltros.elements["hasta"];

    const canvasGrafica = document.getElementById("graficaMonetarias");
    const subtituloGrafica = document.getElementById("subtituloGraficaMonetarias");
    let chartMonetarias = null;

    function formatMoney(value) {
        const num = Number(value || 0);
        if (Number.isNaN(num)) return "0";
        return num.toLocaleString("es-CO", {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        });
    }

    async function cargarReporteMonetarias() {
        const params = new URLSearchParams(new FormData(formFiltros));
        const url = "/reportes/monetarias/data?" + params.toString();

        if (btnBuscar) {
            btnBuscar.disabled = true;
            btnBuscar.innerHTML = `<span class="spinner-border spinner-border-sm"></span>`;
        }

        try {
            const res = await fetch(url);
            if (!res.ok) {
                console.error("Error HTTP reporte monetarias:", res.status);
                return;
            }

            const data = await res.json();
            if (!data.success) {
                console.error("Respuesta error reporte monetarias:", data.message);
                return;
            }

            const items = data.items || [];
            const totales = data.totales || {};

            // ===== Tabla =====
            tbody.innerHTML = "";

            if (items.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="8" class="text-center">
                            No hay datos para el período seleccionado.
                        </td>
                    </tr>
                `;
            } else {
                items.forEach((item) => {
    const tr = document.createElement("tr");

    // 👀 Mira qué viene realmente desde el backend
    console.log("Fila monetaria:", item);

    // 1) Ajusta aquí el nombre del campo según tu JSON:
    //    - si tu Python hizo: COUNT(*) AS num_anexos    → usa item.num_anexos
    //    - si hizo:          COUNT(*) AS num_archivos  → usa item.num_archivos
    const cantidadAnexos = Number(
        item.num_anexos ?? item.num_archivos ?? 0
    );

    // 2) Texto por defecto (solo el número)
    let anexosHtml = cantidadAnexos.toString();

    // 3) Si hay anexos, mostramos link al comprobante
    if (cantidadAnexos > 0) {
        anexosHtml = `
            <a href="/donaciones/comprobante_monetaria/${item.id_donacion}" target="_blank">
                Ver anexos (${cantidadAnexos}) 
            </a>
        `;
    }

    tr.innerHTML = `
        <td>${item.id_donacion}</td>
        <td>${item.fecha_donacion || ""}</td>
        <td>${item.numero_documento || ""}</td>
        <td>${item.donante || "-"}</td>
        <td>${item.metodo || "-"}</td>
        <td>${formatMoney(item.monto)}</td>
        <td>${item.descripcion || ""}</td>
        <td>${anexosHtml}</td>
    `;
    tbody.appendChild(tr);
});

            }

            // ===== Totales =====
            const totalMontoStr = formatMoney(totales.total_monto);

            if (spanTotales) {
                spanTotales.textContent = `Total donado: ${totalMontoStr}`;
            }

            // ===== Gráfica =====
            actualizarGraficaMonetarias(items);

        } catch (err) {
            console.error("Error cargando reporte monetarias:", err);
        } finally {
            if (btnBuscar) {
                btnBuscar.disabled = false;
                btnBuscar.innerHTML = `<i class="bi bi-search"></i> Buscar`;
            }
        }
    }

    function actualizarGraficaMonetarias(items) {
        if (!canvasGrafica) return;

        // Agrupar por método de donación
        const mapa = new Map();

        items.forEach(it => {
            const metodo = it.metodo || "Sin método";
            const monto = Number(it.monto || 0);
            if (!mapa.has(metodo)) {
                mapa.set(metodo, 0);
            }
            mapa.set(metodo, mapa.get(metodo) + monto);
        });

        let datos = Array.from(mapa.entries()).map(([metodo, total]) => ({
            metodo,
            total
        }));

        datos.sort((a, b) => b.total - a.total);
        datos = datos.slice(0, 5); // Top 5

        const labels = datos.map(d => d.metodo);
        const values = datos.map(d => d.total);

        const desdeTxt = inputDesde.value || "inicio";
        const hastaTxt = inputHasta.value || "hoy";
        if (subtituloGrafica) {
            subtituloGrafica.textContent = `Período: ${desdeTxt} a ${hastaTxt}`;
        }

        if (labels.length === 0) {
            if (chartMonetarias) {
                chartMonetarias.destroy();
                chartMonetarias = null;
            }
            return;
        }

        if (chartMonetarias) {
            chartMonetarias.destroy();
        }

        const ctx = canvasGrafica.getContext("2d");

        chartMonetarias = new Chart(ctx, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [{
                    label: "Total donado ($)",
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
                                return "$ " + formatMoney(value);
                            }
                        }
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function (ctx) {
                                return ` $ ${formatMoney(ctx.parsed.y)}`;
                            }
                        }
                    }
                }
            }
        });
    }

    // Botón Excel
    if (btnExcel) {
        btnExcel.addEventListener("click", () => {
            const params = new URLSearchParams(new FormData(formFiltros));
            const url = "/reportes/monetarias/excel?" + params.toString();
            window.location.href = url;
        });
    }

    // Eventos
    formFiltros.addEventListener("submit", (e) => {
        e.preventDefault();
        cargarReporteMonetarias();
    });

    if (btnBuscar) {
        btnBuscar.addEventListener("click", (e) => {
            e.preventDefault();
            cargarReporteMonetarias();
        });
    }

    // Cargar al inicio
    cargarReporteMonetarias();
});
