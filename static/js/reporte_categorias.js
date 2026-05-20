// static/js/reporte_categorias.js

document.addEventListener("DOMContentLoaded", () => {
    const formFiltros = document.getElementById("formFiltrosCategorias");
    const tbody = document.getElementById("tbodyCategorias");
    const spanTotales = document.getElementById("spanTotalesCategorias");
    const btnBuscar = document.getElementById("btnBuscarCategorias");
    const btnExcel = document.getElementById("btnExportarExcelCategorias");

    const inputDesde = formFiltros.elements["desde"];
    const inputHasta = formFiltros.elements["hasta"];

    // Elementos para la gráfica
    const canvasGrafica = document.getElementById("graficaCategorias");
    const subtituloGrafica = document.getElementById("subtituloGraficaCategorias");
    let chartCategorias = null; // instancia de Chart.js

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
    async function cargarReporteCategorias() {
        const params = new URLSearchParams(new FormData(formFiltros));
        const url = "/reportes/categorias/data?" + params.toString();

        if (btnBuscar) {
            btnBuscar.disabled = true;
            btnBuscar.innerHTML = `<span class="spinner-border spinner-border-sm"></span>`;
        }

        try {
            const res = await fetch(url);
            if (!res.ok) {
                console.error("Error HTTP reporte categorías:", res.status);
                return;
            }

            const data = await res.json();
            if (!data.success) {
                console.error("Respuesta error reporte categorías:", data.message);
                return;
            }

            const items = data.items || [];
            const totales = data.totales || {};

            // ----- Tabla -----
            tbody.innerHTML = "";

            if (items.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="9" class="text-center">
                            No hay datos para el período seleccionado.
                        </td>
                    </tr>
                `;
            } else {
                items.forEach((item) => {

                    // 👇👈 AQUI SACAMOS EL NOMBRE DE LA CATEGORÍA
                    const nombreCat =
                        item.nombre ||
                        item.nombre_categoria ||
                        item.categoria ||
                        "Sin nombre";

                    const tr = document.createElement("tr");
                    tr.innerHTML = `
                        <td>${item.id_categoria}</td>
                        <td>${nombreCat}</td>
                        <td>${item.num_productos}</td>
                        <td>${item.num_donaciones}</td>
                        <td>${item.cantidad_unidades}</td>
                        <td>${formatKg(item.total_kg)} kg</td>
                        <td>${formatMoney(item.total_valor)}</td>
                        <td>${item.primera_donacion || "-"}</td>
                        <td>${item.ultima_donacion || "-"}</td>
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
            actualizarGraficaCategorias(items);

        } catch (err) {
            console.error("Error cargando reporte categorías:", err);
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
    function actualizarGraficaCategorias(items) {
        if (!canvasGrafica) return;

        let datos = items
            .filter(it => (it.total_kg || 0) > 0)
            .map(it => {
                // 👇👈 MISMO TRUCO PARA LA GRÁFICA
                const nombreCat =
                    it.nombre ||
                    it.nombre_categoria ||
                    it.categoria ||
                    "Sin nombre";

                return {
                    nombre: nombreCat,
                    total_kg: Number(it.total_kg || 0)
                };
            });

        // Ordenar de mayor a menor
        datos.sort((a, b) => b.total_kg - a.total_kg);
        datos = datos.slice(0, 5);

        const labels = datos.map(d => d.nombre);
        const values = datos.map(d => d.total_kg);

        // Subtítulo con rango de fechas
        const desdeTxt = inputDesde.value || "inicio";
        const hastaTxt = inputHasta.value || "hoy";
        if (subtituloGrafica) {
            subtituloGrafica.textContent = `Período: ${desdeTxt} a ${hastaTxt}`;
        }

        // Si no hay datos, destruimos la gráfica anterior
        if (labels.length === 0) {
            if (chartCategorias) {
                chartCategorias.destroy();
                chartCategorias = null;
            }
            return;
        }

        // Destruir gráfica anterior si existe
        if (chartCategorias) {
            chartCategorias.destroy();
        }

        const ctx = canvasGrafica.getContext("2d");

        chartCategorias = new Chart(ctx, {
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
            const url = "/reportes/categorias/excel?" + params.toString();
            window.location.href = url;
        });
    }

    // =========================
    // Eventos de búsqueda
    // =========================
    formFiltros.addEventListener("submit", (e) => {
        e.preventDefault();
        cargarReporteCategorias();
    });

    if (btnBuscar) {
        btnBuscar.addEventListener("click", (e) => {
            e.preventDefault();
            cargarReporteCategorias();
        });
    }

    // Cargar reporte inicial al abrir la página
    cargarReporteCategorias();
});
