function buildParamsFromUI() {
  const desde = (document.getElementById("desde")?.value || "").trim();
  const hasta = (document.getElementById("hasta")?.value || "").trim();
  const q = (document.getElementById("q")?.value || "").trim();
  const estado = (document.getElementById("estado")?.value || "").trim();
  const id_tipo_salida = (document.getElementById("id_tipo_salida")?.value || "").trim();
  const beneficiario_tipo = (document.getElementById("beneficiario_tipo")?.value || "").trim();

  const params = new URLSearchParams();
  if (desde) params.append("desde", desde);
  if (hasta) params.append("hasta", hasta);
  if (q) params.append("q", q);
  if (estado) params.append("estado", estado);
  if (id_tipo_salida) params.append("id_tipo_salida", id_tipo_salida);
  if (beneficiario_tipo) params.append("beneficiario_tipo", beneficiario_tipo);
  return params;
}

async function cargarListado() {
  const tbody = document.getElementById("tbodySalidas");
  const totalesTxt = document.getElementById("totalesTxt");

  if (!tbody) return;

  tbody.innerHTML = `<tr><td colspan="10" class="text-center py-3">Cargando...</td></tr>`;

  try {
    const params = buildParamsFromUI();
    const res = await fetch("/reportes/salidas/listado/data?" + params.toString());
    const data = await res.json();

    if (!res.ok || !data.success) throw new Error(data.message || "Error cargando listado");

    const items = data.items || [];
    const tot = data.totales || { total_kg_str: "0", total_valor_str: "0" };
    if (totalesTxt) totalesTxt.textContent = `Total período: ${tot.total_kg_str} kg | $ ${tot.total_valor_str}`;

    if (!items.length) {
      tbody.innerHTML = `<tr><td colspan="10" class="text-center py-3">No hay salidas para mostrar.</td></tr>`;
      return;
    }

    tbody.innerHTML = items.map(x => `
      <tr>
        <td>${x.id_salida}</td>
        <td>${x.fecha_salida || ""}</td>
        <td>${x.tipo_salida || ""}</td>
        <td>${x.estado || ""}</td>
        <td>${(x.beneficiario_tipo === "N/A") ? "N/A" : (x.beneficiario_nombre || "")}</td>
        <td>${x.numero_documento || ""}</td>
        <td class="text-end">${x.total_kg_str} kg</td>
        <td class="text-end">$ ${x.total_valor_str}</td>
        <td>${x.observacion || ""}</td>
        <td class="text-nowrap">
          <button class="btn btn-sm btn-outline-success btn-detalle" data-id="${x.id_salida}">
            <i class="bi bi-list-ul"></i>
          </button>
          <a class="btn btn-sm btn-success ms-1"
             href="/salidas/comprobante/${x.id_salida}"
             target="_blank" rel="noopener">
             <i class="bi bi-receipt"></i>
          </a>
        </td>
      </tr>
    `).join("");

  } catch (err) {
    console.error(err);
    tbody.innerHTML = `<tr><td colspan="10" class="text-center text-danger py-3">Error al cargar el reporte.</td></tr>`;
    if (totalesTxt) totalesTxt.textContent = `Total período: 0 kg | $ 0`;
  }
}

async function abrirDetalleSalida(id_salida) {
  const cabDiv = document.getElementById("detalleCabecera");
  const tbodyDet = document.getElementById("tbodyDetalleSalida");
  const btnComprobante = document.getElementById("btnComprobante");

  if (!cabDiv || !tbodyDet) return;

  cabDiv.innerHTML = "Cargando...";
  tbodyDet.innerHTML = "";

  try {
    const res = await fetch(`/reportes/salidas/listado/detalle/${id_salida}`);
    const data = await res.json();
    if (!res.ok || !data.success) throw new Error(data.message || "Error cargando detalle");

    const c = data.cabecera || {};
    const detalles = data.detalles || [];

    cabDiv.innerHTML = `
      <div class="row g-2">
        <div class="col-md-3"><strong>Salida:</strong> #${c.id_salida}</div>
        <div class="col-md-3"><strong>Fecha:</strong> ${c.fecha_salida || ""}</div>
        <div class="col-md-3"><strong>Tipo:</strong> ${c.tipo_salida || ""}</div>
        <div class="col-md-3"><strong>Estado:</strong> ${c.estado || ""}</div>

        <div class="col-md-6"><strong>Beneficiario:</strong> ${c.beneficiario_nombre || "N/A"} (${c.beneficiario_tipo || "N/A"})</div>
        <div class="col-md-6"><strong>Documento:</strong> ${c.numero_documento || ""}</div>

        <div class="col-12"><strong>Observación:</strong> ${c.observacion || ""}</div>
      </div>
      <hr>
    `;

    if (!detalles.length) {
      tbodyDet.innerHTML = `<tr><td colspan="7" class="text-center">Sin detalles</td></tr>`;
    } else {
      tbodyDet.innerHTML = detalles.map(d => `
        <tr>
          <td>${d.producto || ""}</td>
          <td>${d.categoria || ""}</td>
          <td>${d.bodega || ""}</td>
          <td>${d.ubicacion || ""}</td>
          <td>${d.fecha_vencimiento || ""}</td>
          <td class="text-end">${Number(d.cantidad_kg || 0).toFixed(3).replace(/\.?0+$/, "")}</td>
          <td class="text-end">$ ${Number(d.valor_total || 0).toLocaleString("es-CO")}</td>
        </tr>
      `).join("");
    }

    if (btnComprobante) {
      btnComprobante.href = `/salidas/comprobante/${id_salida}`;
    }

    const modalEl = document.getElementById("modalDetalleSalida");
    const modal = new bootstrap.Modal(modalEl);
    modal.show();

  } catch (err) {
    console.error(err);
    cabDiv.innerHTML = `<div class="text-danger">Error: ${err.message}</div>`;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const btnBuscar = document.getElementById("btnBuscar");
  const btnLimpiar = document.getElementById("btnLimpiar");
  const btnExcel = document.getElementById("btnExcel");

  if (btnBuscar) btnBuscar.addEventListener("click", cargarListado);

  if (btnLimpiar) {
    btnLimpiar.addEventListener("click", () => {
      document.getElementById("desde").value = "";
      document.getElementById("hasta").value = "";
      document.getElementById("q").value = "";
      document.getElementById("estado").value = "";
      document.getElementById("id_tipo_salida").value = "";
      document.getElementById("beneficiario_tipo").value = "";
      cargarListado();
    });
  }

  // Export Excel con filtros actuales
  if (btnExcel) {
    btnExcel.addEventListener("click", () => {
      const params = buildParamsFromUI();
      window.location.href = "/reportes/salidas/listado/excel?" + params.toString();
    });
  }

  // Delegación: botón detalle por fila
  const tbody = document.getElementById("tbodySalidas");
  if (tbody) {
    tbody.addEventListener("click", (e) => {
      const btn = e.target.closest(".btn-detalle");
      if (!btn) return;
      const id = btn.dataset.id;
      abrirDetalleSalida(id);
    });
  }

  cargarListado();
});
