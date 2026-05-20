// static/js/reporte_donaciones.js

document.addEventListener("DOMContentLoaded", () => {
    const formFiltros = document.getElementById("formFiltrosReporte");
    const tbody = document.getElementById("tbodyReporte");
    const spanTotales = document.getElementById("spanTotalesPeriodo");
    const btnBuscar = document.getElementById("btnBuscarReporte");
    const btnExcel = document.getElementById("btnExportarExcel");

    if (!formFiltros) return;   // seguridad

    const inputDesde = formFiltros.elements["desde"];
    const inputHasta = formFiltros.elements["hasta"];
    const inputProducto = formFiltros.elements["producto"];

    // 📊 elementos de la gráfica
    const canvasGrafica = document.getElementById("graficaProductos");
    const subtituloGrafica = document.getElementById("subtituloGraficaProductos");
    let chartProductos = null; // instancia de Chart.js

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
    async function cargarReporte() {
        const params = new URLSearchParams(new FormData(formFiltros));
        const url = "/reportes/donaciones/data?" + params.toString();

        // desactivar botón mientras carga
        if (btnBuscar) {
            btnBuscar.disabled = true;
            btnBuscar.innerHTML = `<span class="spinner-border spinner-border-sm"></span>`;
        }

        try {
            const res = await fetch(url);
            if (!res.ok) {
                console.error("Error HTTP reporte:", res.status);
                return;
            }

            const data = await res.json();
            if (!data.success) {
                console.error("Respuesta error reporte:", data.message);
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
                        <td>${item.id_producto}</td>
                        <td>${item.nombre}</td>
                        <td>${item.cantidad}</td>
                        <td>${formatKg(item.total_kg)} kg</td>
                        <td>${formatMoney(item.total_valor)}</td>
                        <td>${item.primer_ingreso || "-"}</td>
                        <td>${item.ultimo_ingreso || "-"}</td>
                    `;
                    tbody.appendChild(tr);
                });
            }

            // ================= Totales =================
            const totalKgStr = formatKg(totales.total_kg);
            const totalValorStr = formatMoney(totales.total_valor);

            if (spanTotales) {
                spanTotales.textContent = `Peso total: ${totalKgStr} kg | Valor total: ${totalValorStr}`;
            }

            // ================= Gráfica =================
            actualizarGrafica(items);

        } catch (err) {
            console.error("Error cargando reporte:", err);
        } finally {
            // volver a activar el botón y restaurar el texto
            if (btnBuscar) {
                btnBuscar.disabled = false;
                btnBuscar.innerHTML = ``;
            }
        }
    }

    // =========================
    // Gráfica con Chart.js
    // =========================
    function actualizarGrafica(items) {
        if (!canvasGrafica) return;

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

        // Si no hay datos, destruir gráfica
        if (labels.length === 0) {
            if (chartProductos) {
                chartProductos.destroy();
                chartProductos = null;
            }
            return;
        }

        // Destruir gráfica anterior si existe
        if (chartProductos) {
            chartProductos.destroy();
        }

        const ctx = canvasGrafica.getContext("2d");

        chartProductos = new Chart(ctx, {
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
            const url = "/reportes/donaciones/excel?" + params.toString();
            window.location.href = url;
        });
    }

    // =========================
    // Eventos
    // =========================

    // buscar al hacer submit del formulario
    formFiltros.addEventListener("submit", (e) => {
        e.preventDefault();
        cargarReporte();
    });

    // y también al hacer click directo en el botón
    if (btnBuscar) {
        btnBuscar.addEventListener("click", (e) => {
            e.preventDefault();
            cargarReporte();
        });
    }

    // Cargar al inicio
    cargarReporte();
});
