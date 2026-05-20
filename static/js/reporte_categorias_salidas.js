let chartCategorias = null;
let cacheItemsCategorias = [];

function qs(sel) { return document.querySelector(sel); }

function buildQueryFromForm(form) {
    const fd = new FormData(form);
    const params = new URLSearchParams();

    for (const [k, v] of fd.entries()) {
        if (v !== null && String(v).trim() !== "") {
            params.append(k, String(v).trim());
        }
    }
    return params;
}

function setPeriodoSubtitle(meta) {
    const el = qs("#subtituloGraficaCategorias");
    if (!meta) { el.textContent = "Período: Todo"; return; }
    if (!meta.rango_aplicado) {
        el.textContent = "Período: Todo (desde la primera hasta la última donación)";
        return;
    }
    el.textContent = `Período: ${meta.desde} a ${meta.hasta}`;
}

function renderTotales(totales) {
    const el = qs("#spanTotalesPeriodoCategorias");
    if (!totales) { el.textContent = ""; return; }
    el.textContent = `Total período: ${totales.total_kg_str} kg | $ ${totales.total_valor_str}`;
}

function renderTabla(items) {
    cacheItemsCategorias = items || [];
    const tbody = qs("#tbodyReporteCategorias");
    tbody.innerHTML = "";

    if (!items || items.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted">Sin resultados</td></tr>`;
        return;
    }

    for (const c of items) {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${c.id_categoria || "-"}</td>
            <td>${c.categoria || "-"}</td>
            <td class="text-end">${(c.num_donaciones ?? 0)}</td>
            <td class="text-end">${(c.total_kg_str || "0")}</td>
            <td class="text-end">$ ${c.total_valor_str || "0"}</td>
        `;
        tbody.appendChild(tr);
    }
}

function renderGrafica(items) {
    const top = (items || [])
        .slice()
        .sort((a, b) => (b.total_kg || 0) - (a.total_kg || 0))
        .slice(0, 10);

    const labels = top.map(x => (x.categoria || "").slice(0, 25));
    const data = top.map(x => x.total_kg || 0);

    const ctx = qs("#graficaCategorias").getContext("2d");

    if (chartCategorias) {
        chartCategorias.destroy();
        chartCategorias = null;
    }

    chartCategorias = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Kg entregados",
                data: data
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: true }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

async function cargarReporte(params) {
    const url = "/reportes/categorias/data?" + params.toString();
    const resp = await fetch(url);
    const data = await resp.json();

    if (!data.success) {
        swal("Error", data.message || "No se pudo cargar el reporte.", "error");
        return;
    }

    setPeriodoSubtitle(data.meta);
    renderTotales(data.totales);

    renderTabla(data.items || []);
    renderGrafica(data.items || []);
}

function configurarExportExcel(form) {
    const btn = qs("#btnExportarExcelCategorias");
    btn.addEventListener("click", () => {
        const params = buildQueryFromForm(form);
        const url = "/reportes/categorias/excel?" + params.toString();
        window.location.href = url;
    });
}

document.addEventListener("DOMContentLoaded", () => {
    const form = qs("#formFiltrosReporteCategorias");

    configurarExportExcel(form);

    form.addEventListener("submit", (e) => {
        e.preventDefault();
        const params = buildQueryFromForm(form);
        cargarReporte(params);
    });

    // carga inicial: sin fechas => TODO
    cargarReporte(new URLSearchParams());
});
