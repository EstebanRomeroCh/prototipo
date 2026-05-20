// static/js/semaforo_vencimiento.js

let __chart = null;

// =========================
// Helpers
// =========================
function formatKg(value) {
  const num = Number(value || 0);
  if (Number.isNaN(num)) return "0";
  if (Number.isInteger(num)) return num.toString();
  return num.toFixed(3).replace(/\.?0+$/, "");
}

function formatFecha(fechaStr) {
  if (!fechaStr) return "-";
  const d = new Date(fechaStr);
  if (isNaN(d.getTime())) return fechaStr;
  return d.toLocaleDateString("es-CO", { day: "2-digit", month: "2-digit", year: "numeric" });
}

// días restantes = fecha_venc - hoy
function diasRestantes(fechaStr) {
  if (!fechaStr) return null;
  const hoy = new Date();
  const fv = new Date(fechaStr);
  if (isNaN(fv.getTime())) return null;

  hoy.setHours(0, 0, 0, 0);
  fv.setHours(0, 0, 0, 0);

  const ms = fv.getTime() - hoy.getTime();
  return Math.floor(ms / (1000 * 60 * 60 * 24));
}

function estiloSemaforo(dias) {
  if (dias === null) return "background-color:#6c757d; color:#ffffff;";
  if (dias < 0) return "background-color:#4b0000; color:#ffffff;";
  if (dias <= 2) return "background-color:#dc3545; color:#ffffff;";
  if (dias <= 9) return "background-color:#fd7e14; color:#ffffff;";
  if (dias <= 29) return "background-color:#ffc107; color:#000000;";
  return "background-color:#198754; color:#ffffff;";
}

function textoDias(dias) {
  if (dias === null) return "Sin fecha";
  if (dias < 0) return `Vencido (${Math.abs(dias)} d)`;
  return `${dias} d`;
}

function etiquetaSemaforo(dias) {
  if (dias === null) return "SIN FECHA";
  if (dias < 0) return "VENCIDO";
  if (dias <= 2) return "ROJO";
  if (dias <= 9) return "NARANJA";
  if (dias <= 29) return "AMARILLO";
  return "VERDE";
}

// =========================
// Cargar desde inventario
// =========================
async function cargarSemaforo(q = "") {
  const tbody = document.getElementById("tbodySemaforo");
  if (!tbody) return;

  tbody.innerHTML = `
    <tr>
      <td colspan="6" class="text-center py-3">Cargando...</td>
    </tr>
  `;

  try {
    const params = new URLSearchParams();
    if (q) params.append("q", q);

    const resp = await fetch("/inventario/api/productos?" + params.toString());
    if (!resp.ok) throw new Error("HTTP " + resp.status);

    const data = await resp.json();
    if (!data.success) throw new Error(data.message || "Error en API inventario");

    // Solo productos con stock > 0
    const productos = (data.productos || [])
      .filter(p => Number(p.cantidad_total || 0) > 0)
      .map(p => {
        const fv = p.proximo_vencimiento || null;
        const dias = diasRestantes(fv);
        return { ...p, _dias: dias };
      })
      // Orden: más urgentes primero (sin fecha al final)
      .sort((a, b) => {
        const da = (a._dias === null) ? 999999 : a._dias;
        const db = (b._dias === null) ? 999999 : b._dias;
        if (da !== db) return da - db;
        return Number(b.cantidad_total || 0) - Number(a.cantidad_total || 0);
      });

    if (!productos.length) {
      tbody.innerHTML = `
        <tr>
          <td colspan="8" class="text-center py-3">No hay productos con stock para mostrar.</td>
        </tr>
      `;
      renderChart([]); // limpia gráfico
      return;
    }

    // Pintar tabla
    let html = "";
    productos.forEach(p => {
      const dias = p._dias;
      const estilo = estiloSemaforo(dias);

      html += `
        <tr>
          <td>${p.id_producto}</td>
          <td>${p.nombre}</td>
          <td class="text-end">${formatKg(p.cantidad_total)} kg</td>
          <td>${p.proxima_bodega || "-"}</td>
          <td>${p.proxima_ubicacion || "-"}</td>
          <td style="${estilo}">${formatFecha(p.proximo_vencimiento)}</td>
          <td style="${estilo}">${textoDias(dias)}</td>
          <td style="${estilo}" class="text-center"><strong>${etiquetaSemaforo(dias)}</strong></td>
        </tr>
      `;
    });

    tbody.innerHTML = html;

    // Gráfica: Top 5 más urgentes (solo con fecha válida)
    renderChart(productos);

  } catch (err) {
    console.error("Error semáforo:", err);
    tbody.innerHTML = `
      <tr>
        <td colspan="8" class="text-center text-danger py-3">
          Error al cargar la semaforización.
        </td>
      </tr>
    `;
    renderChart([]); // limpia gráfico si falla
  }
}

// =========================
// Chart.js (Top 5) - estilo como reporte_monetarias.js
// =========================
function renderChart(productos) {
  const canvas = document.getElementById("graficoProductos");
  if (!canvas || typeof Chart === "undefined") return;

  // Top 5 más urgentes (solo con fecha válida)
  let datos = (productos || [])
    .filter(p => p && p.nombre && p._dias !== null)
    .map(p => ({
      nombre: p.nombre,
      total: Number(p.cantidad_total || 0),
      dias: p._dias
    }))
    .sort((a, b) => {
      if (a.dias !== b.dias) return a.dias - b.dias; // más urgente primero
      return b.total - a.total; // empate: más kg
    })
    .slice(0, 5);

  const labels = datos.map(d => d.nombre);
  const values = datos.map(d => d.total);

  // destruir si existe
  if (__chart) {
    __chart.destroy();
    __chart = null;
  }

  if (labels.length === 0) return;

  const ctx = canvas.getContext("2d");

  __chart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [{
        label: "Kilos en inventario (kg)",
        data: values,
        borderWidth: 1,
        backgroundColor: "rgba(25, 135, 84, 0.6)",
        borderColor: "rgba(25, 135, 84, 1)",
        barThickness: 40
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
              return formatKg(value) + " kg";
            }
          }
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: function (ctx) {
              return `${formatKg(ctx.parsed.y)} kg`;
            }
          }
        }
      }
    }
  });
}

// =========================
// Init
// =========================
document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("inputBuscarSemaforo");
  const btnBuscar = document.getElementById("btnBuscarSemaforo");
  const btnLimpiar = document.getElementById("btnLimpiarSemaforo");

  if (btnBuscar) {
    btnBuscar.addEventListener("click", () => {
      const q = (input?.value || "").trim();
      cargarSemaforo(q);
    });
  }

  if (btnLimpiar) {
    btnLimpiar.addEventListener("click", () => {
      if (input) input.value = "";
      cargarSemaforo("");
    });
  }

  // Buscar con Enter
  if (input) {
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        cargarSemaforo((input.value || "").trim());
      }
    });
  }

const btnExcelVenc = document.getElementById("btnExcelVenc");
if (btnExcelVenc) {
  btnExcelVenc.addEventListener("click", () => {
    const q = (input?.value || "").trim();
    window.location.href = "/inventario/export/vencimientos.xlsx?q=" + encodeURIComponent(q);
  });
}


  cargarSemaforo("");
});
