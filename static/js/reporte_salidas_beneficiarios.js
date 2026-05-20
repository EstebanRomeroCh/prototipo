// static/js/reporte_salidas_beneficiarios.js

let chartSalidasBenef = null;
let cacheItems = [];

function qs(sel) { return document.querySelector(sel); }

async function cargarTiposSalidaEnSelect() {
  const sel = qs("#selectTipoSalida");
  if (!sel) return;

  try {
    const resp = await fetch("/reportes/salidas/tipos-salida");
    const data = await resp.json();

    if (!data.success) {
      console.warn("No se pudieron cargar tipos de salida:", data.message);
      return;
    }

    // limpia y deja "Todos"
    sel.innerHTML = `<option value="">Todos</option>`;

    for (const t of (data.items || [])) {
      const opt = document.createElement("option");
      opt.value = t.id_tipo_salida;
      opt.textContent = t.nombre;
      sel.appendChild(opt);
    }
  } catch (err) {
    console.error("Error cargando tipos de salida:", err);
  }
}



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
  const el = qs("#subtituloGraficaSalidasBenef");
  if (!meta) { el.textContent = "Período: Todo"; return; }
  if (!meta.rango_aplicado) {
    el.textContent = "Período: Todo (desde la primera hasta la última salida)";
    return;
  }
  el.textContent = `Período: ${meta.desde} a ${meta.hasta}`;
}

function renderKPIs(kpis) {
  qs("#kpiBenefTotal").textContent = (kpis?.beneficiarios_total ?? 0);
  qs("#kpiParroquias").textContent = (kpis?.parroquias_total ?? 0);
  qs("#kpiFundaciones").textContent = (kpis?.fundaciones_total ?? 0);
}

function renderTotales(totales) {
  const el = qs("#spanTotalesSalidasBenef");
  if (!totales) { el.textContent = ""; return; }
  el.textContent = `Total período: ${totales.total_kg_str} kg | $ ${totales.total_valor_str}`;
}

function renderTabla(items) {
  cacheItems = items || [];
  const tbody = qs("#tbodySalidasBenef");
  tbody.innerHTML = "";

  if (!items || items.length === 0) {
    tbody.innerHTML = `<tr><td colspan="12" class="text-center text-muted">Sin resultados</td></tr>`;
    return;
  }

  for (const b of items) {
    const doc = (b.tipo_documento ? `${b.tipo_documento} ` : "") + (b.numero_documento || "");
    const tel = b.telefono || "-";
    const mun = [b.municipio, b.departamento].filter(Boolean).join(", ") || "-";

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${b.beneficiario_tipo || "-"}</td>
      <td>
        <div class="fw-semibold">${b.beneficiario_nombre || "-"}</div>
        <small class="text-muted">${b.direccion || ""}</small>
      </td>
      <td>${doc || "-"}</td>
      <td>${b.encargado || "-"}</td>
      <td>${tel}</td>
      <td>${mun}</td>
      <td class="text-end">${(b.familias_atendidas ?? 0)}</td>
      <td class="text-end">${(b.num_salidas ?? 0)}</td>
      <td class="text-end">${b.total_kg_str || "0"}</td>
      <td class="text-end">$ ${b.total_valor_str || "0"}</td>
      <td>${b.ultima_salida || "-"}</td>
      <td class="text-center">
        <button class="btn btn-outline-success btn-sm" data-action="ver-detalle"
          data-id="${b.id_beneficiario}" data-tipo="${b.beneficiario_tipo}">
          <i class="bi bi-list-ul"></i>
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  }

  // listeners detalle
  tbody.querySelectorAll('button[data-action="ver-detalle"]').forEach(btn => {
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-id");
      const tipo = btn.getAttribute("data-tipo");
      abrirDetalleCategorias(tipo, id);
    });
  });
}

function renderGrafica(items) {
  const top = (items || [])
    .slice()
    .sort((a, b) => (b.total_kg || 0) - (a.total_kg || 0))
    .slice(0, 10);

  const labels = top.map(x => (x.beneficiario_nombre || "").slice(0, 25));
  const data = top.map(x => x.total_kg || 0);

  const ctx = qs("#graficaSalidasBenef").getContext("2d");

  if (chartSalidasBenef) {
    chartSalidasBenef.destroy();
    chartSalidasBenef = null;
  }

  chartSalidasBenef = new Chart(ctx, {
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

function abrirDetalleCategorias(tipo, id) {
  const item = cacheItems.find(x => String(x.id_beneficiario) === String(id) && String(x.beneficiario_tipo) === String(tipo));
  if (!item) {
    swal("Aviso", "No se encontró el detalle del beneficiario.", "warning");
    return;
  }

  qs("#modalTituloBenef").textContent = `${item.beneficiario_nombre || ""} (${item.beneficiario_tipo || ""})`;
  qs("#modalTotalKg").textContent = `${item.total_kg_str || "0"} kg`;
  qs("#modalTotalValor").textContent = `$ ${item.total_valor_str || "0"}`;

  const tbody = qs("#tbodyDetalleCategorias");
  tbody.innerHTML = "";

  const cats = item.categorias || [];
  if (cats.length === 0) {
    tbody.innerHTML = `<tr><td colspan="3" class="text-center text-muted">Sin categorías</td></tr>`;
  } else {
    for (const c of cats) {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${c.categoria || "-"}</td>
        <td class="text-end">${c.total_kg_str || "0"}</td>
        <td class="text-end">$ ${c.total_valor_str || "0"}</td>
      `;
      tbody.appendChild(tr);
    }
  }

  const modalEl = qs("#modalDetalleCategorias");
  const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
  modal.show();
}

async function cargarReporte(params) {
  const url = "/reportes/salidas/beneficiarios/data?" + params.toString();
  const resp = await fetch(url);
  const data = await resp.json();

  if (!data.success) {
    swal("Error", data.message || "No se pudo cargar el reporte.", "error");
    return;
  }

  renderKPIs(data.kpis);
  setPeriodoSubtitle(data.meta);
  renderTotales(data.totales);

  renderTabla(data.items || []);
  renderGrafica(data.items || []);
}

function configurarExportExcel(form) {
  const btn = qs("#btnExportarExcelSalidasBenef");
  btn.addEventListener("click", () => {
    const params = buildQueryFromForm(form);
    const url = "/reportes/salidas/beneficiarios/excel?" + params.toString();
    window.location.href = url;
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const form = qs("#formFiltrosSalidasBenef");

  configurarExportExcel(form);

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const params = buildQueryFromForm(form);
    cargarReporte(params);
  });

  // carga inicial: sin fechas => TODO
  cargarReporte(new URLSearchParams());
    cargarTiposSalidaEnSelect();
});
