// static/js/reporte_donantes.js

document.addEventListener("DOMContentLoaded", () => {
    const formFiltros = document.getElementById("formFiltrosReporteDonantes");
    const tbody = document.getElementById("tbodyReporteDonantes");
    const spanTotales = document.getElementById("spanTotalesPeriodoDonantes");
    const btnBuscar = document.getElementById("btnBuscarReporteDonantes");
    const btnExcel = document.getElementById("btnExportarExcelDonantes");

    const inputDesde = formFiltros.elements["desde"];
    const inputHasta = formFiltros.elements["hasta"];
    const inputDonante = formFiltros.elements["donante"];

    // 📊 elementos de la gráfica
    const canvasGrafica = document.getElementById("graficaDonantes");
    const subtituloGrafica = document.getElementById("subtituloGraficaDonantes");
    let chartDonantes = null; // instancia de Chart.js

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
        // sin decimales, separador de miles con punto
        return num.toLocaleString("es-CO", {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        });
    }

    // =========================
    // Cargar reporte (tabla + totales + gráfica)
    // =========================
    async function cargarReporteDonantes() {
        const params = new URLSearchParams(new FormData(formFiltros));
        const url = "/reportes/donantes/data?" + params.toString();

        if (btnBuscar) {
            btnBuscar.disabled = true;
            btnBuscar.innerHTML = `<span class="spinner-border spinner-border-sm"></span>`;
        }

        try {
            const res = await fetch(url);
            if (!res.ok) {
                console.error("Error HTTP reporte donantes:", res.status);
                return;
            }

            const data = await res.json();
            if (!data.success) {
                console.error("Respuesta error reporte donantes:", data.message);
                return;
            }

            const items = data.items || [];
            const totales = data.totales || {};

            // ================= Tabla =================
            tbody.innerHTML = "";

            if (items.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="7" class="text-center">
                            No hay datos para el período seleccionado.
                        </td>
                    </tr>
                `;
            } else {
                items.forEach((item) => {
                    const tr = document.createElement("tr");
                    tr.innerHTML = `
                        <td>${item.id_donante}</td>
                        <td>${item.nombre}</td>
                        <td>${item.numero_documento || "-"}</td>
                        <td>${item.num_donaciones}</td>
                        <td>${formatKg(item.total_kg)} kg</td>
                        <td>${formatMoney(item.total_valor)}</td>
                        <td>${item.ultima_donacion || "-"}</td>
                    `;
                    tbody.appendChild(tr);
                });
            }

            // ================= Totales =================
            const totalKgStr = formatKg(totales.total_kg);
            const totalValorStr = formatMoney(totales.total_valor);

            if (spanTotales) {
                spanTotales.textContent = `Peso total donado: ${totalKgStr} kg | Valor total donado: ${totalValorStr}`;
            }

            // ================= Gráfica =================
            actualizarGraficaDonantes(items);

        } catch (err) {
            console.error("Error cargando reporte donantes:", err);
        } finally {
            if (btnBuscar) {
                btnBuscar.disabled = false;
                btnBuscar.innerHTML = `<i class="bi bi-search"></i>`;
            }
        }
    }

    // =========================
    // Gráfica con Chart.js
    // =========================
    function actualizarGraficaDonantes(items) {
        if (!canvasGrafica) return;

        // Tomamos solo los donantes con algo de peso
        let datos = items
            .filter(it => (it.total_kg || 0) > 0)
            .map(it => ({
                nombre: it.nombre,
                total_kg: Number(it.total_kg || 0)
            }));

        // Ordenar de mayor a menor
        datos.sort((a, b) => b.total_kg - a.total_kg);

        // Si quieres solo el top 5:
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
            if (chartDonantes) {
                chartDonantes.destroy();
                chartDonantes = null;
            }
            return;
        }

        // Destruir gráfica anterior si existe
        if (chartDonantes) {
            chartDonantes.destroy();
        }

        const ctx = canvasGrafica.getContext("2d");

        chartDonantes = new Chart(ctx, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [{
                    label: "Total donado (kg)",
                    data: values,
                    borderWidth: 1,
                    backgroundColor: "rgba(25, 135, 84, 0.6)", // verde bootstrap
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
                            // Mostramos números con 'kg'
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
            const url = "/reportes/donantes/excel?" + params.toString();
            window.location.href = url;
        });
    }

    // =========================
    // Eventos
    // =========================
    formFiltros.addEventListener("submit", (e) => {
        e.preventDefault();
        cargarReporteDonantes();
    });

    if (btnBuscar) {
        btnBuscar.addEventListener("click", (e) => {
            e.preventDefault();
            cargarReporteDonantes();
        });
    }

    // Cargar al inicio
    cargarReporteDonantes();
});
