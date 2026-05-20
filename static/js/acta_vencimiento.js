// static/js/acta_vencimiento.js

document.addEventListener("DOMContentLoaded", () => {
  const selectSalida = document.getElementById("selectSalida");
  const btnRecargarSalidas = document.getElementById("btnRecargarSalidas");

  const bloqueSalida = document.getElementById("bloqueSalida");
  const salidaNumero = document.getElementById("salidaNumero");
  const salidaFecha = document.getElementById("salidaFecha");
  const salidaTotalKg = document.getElementById("salidaTotalKg");
  const salidaObs = document.getElementById("salidaObs");
  const tbodySalidaDetalle = document.getElementById("tbodySalidaDetalle");

  const fechaActa = document.getElementById("fechaActa");
  const motivoActa = document.getElementById("motivoActa");

  const form = document.getElementById("formActaVencimiento");
  const btnGuardarActa = document.getElementById("btnGuardarActa");
  const btnImprimirActa = document.getElementById("btnImprimirActa");
  const btnVerActa = document.getElementById("btnVerActa");

  const vistaActa = document.getElementById("vistaActa");

  let cacheSalidas = [];
  let salidaActual = null;
  let idActaCreada = null;

  // ---------------------------
  // Helpers
  // ---------------------------
  function hoyISO() {
    const d = new Date();
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    return `${d.getFullYear()}-${mm}-${dd}`;
  }

  function formatKg(v) {
    const n = Number(v || 0);
    if (Number.isNaN(n)) return "0";
    return n.toFixed(3).replace(/\.?0+$/, "");
  }

  function formatFecha(fechaStr) {
    if (!fechaStr) return "-";
    const d = new Date(fechaStr);
    if (isNaN(d.getTime())) return fechaStr;
    return d.toLocaleDateString("es-CO", { day: "2-digit", month: "2-digit", year: "numeric" });
  }

  function escapeHtml(str) {
    return String(str || "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  // ---------------------------
  // Cargar salidas elegibles
  // ---------------------------
  async function cargarSalidasElegibles() {
    try {
      selectSalida.innerHTML = `<option value="" disabled selected>Cargando...</option>`;
      const res = await fetch("/actas-vencimiento/api/salidas-elegibles");
      const data = await res.json();

      if (!res.ok || data.success === false) {
        throw new Error(data.message || "No se pudieron cargar las salidas.");
      }

      cacheSalidas = data.items || [];

      if (!cacheSalidas.length) {
        selectSalida.innerHTML = `<option value="" disabled selected>No hay salidas elegibles</option>`;
        bloqueSalida.classList.add("d-none");
        return;
      }

      const options = cacheSalidas.map(s => {
        const label = `Salida #${s.id_salida} | ${formatFecha(s.fecha_salida)} | ${formatKg(s.total_peso_kg)} kg`;
        return `<option value="${s.id_salida}">${escapeHtml(label)}</option>`;
      });

      selectSalida.innerHTML = `<option value="" disabled selected>Seleccione una salida...</option>` + options.join("");

    } catch (err) {
      console.error("cargarSalidasElegibles:", err);
      selectSalida.innerHTML = `<option value="" disabled selected>Error al cargar</option>`;
      if (typeof swal === "function") swal("Error", err.message, "error");
    }
  }

  // ---------------------------
  // Cargar detalle de salida seleccionada
  // ---------------------------
  async function cargarDetalleSalida(idSalida) {
    if (!idSalida) return;

    try {
      const res = await fetch(`/actas-vencimiento/api/salida/${idSalida}`);
      const data = await res.json();

      if (!res.ok || data.success === false) {
        throw new Error(data.message || "No se pudo cargar el detalle de la salida.");
      }

      salidaActual = data.salida || null;
      const detalles = data.detalles || [];

      // pintar
      bloqueSalida.classList.remove("d-none");
      salidaNumero.textContent = salidaActual.id_salida || "";
      salidaFecha.textContent = formatFecha(salidaActual.fecha_salida);
      salidaTotalKg.textContent = formatKg(salidaActual.total_peso_kg || 0);
      salidaObs.textContent = salidaActual.observacion || "Sin observaciones.";

      tbodySalidaDetalle.innerHTML = "";
      if (!detalles.length) {
        tbodySalidaDetalle.innerHTML = `
          <tr><td colspan="5" class="text-center text-muted">Sin detalle.</td></tr>
        `;
      } else {
        detalles.forEach(d => {
          tbodySalidaDetalle.innerHTML += `
            <tr>
              <td>${escapeHtml(d.producto || "")}</td>
              <td>${escapeHtml(d.bodega || "")}</td>
              <td>${escapeHtml(d.bodega_texto || "")}</td>
              <td>${escapeHtml(formatFecha(d.fecha_vencimiento))}</td>
              <td class="text-end">${escapeHtml(formatKg(d.cantidad_kg))}</td>
            </tr>
          `;
        });
      }

      // reset de acta previa
      idActaCreada = null;
      vistaActa.classList.add("d-none");
      vistaActa.innerHTML = "";
      btnImprimirActa.classList.add("d-none");
      btnVerActa.classList.add("d-none");

    } catch (err) {
      console.error("cargarDetalleSalida:", err);
      bloqueSalida.classList.add("d-none");
      if (typeof swal === "function") swal("Error", err.message, "error");
    }
  }

  // ---------------------------
  // Render acta (preview imprimible)
  // ---------------------------
  async function cargarDetalleActa(idActa) {
    const res = await fetch(`/actas-vencimiento/api/detalle/${idActa}`);
    const data = await res.json();
    if (!res.ok || data.success === false) {
      throw new Error(data.message || "No se pudo cargar el acta.");
    }

    const acta = data.acta || {};
    const detalles = data.detalles || [];

    let filas = "";
    detalles.forEach(d => {
      filas += `
        <tr>
          <td>${escapeHtml(d.nombre_producto)}</td>
          <td>${escapeHtml(d.nombre_bodega || "")}</td>
          <td>${escapeHtml(d.bodega_texto || "")}</td>
          <td>${escapeHtml(formatFecha(d.fecha_vencimiento))}</td>
          <td class="text-end">${escapeHtml(formatKg(d.cantidad_kg))}</td>
        </tr>
      `;
    });

    vistaActa.innerHTML = `
      <div class="bg-white p-4 rounded border">
        <h2 class="h5 text-center mb-3">ACTA DE VENCIMIENTO</h2>

        <div class="d-flex justify-content-between">
          <div><strong>Acta N°:</strong> ${escapeHtml(acta.id_acta)}</div>
          <div><strong>Fecha:</strong> ${escapeHtml(formatFecha(acta.fecha_acta))}</div>
        </div>

        <div class="mt-2">
          <strong>Salida relacionada:</strong> #${escapeHtml(acta.id_salida)}
        </div>

        <hr>

        <div class="mb-3">
          <strong>Motivo:</strong>
          <div style="white-space:pre-wrap;">${escapeHtml(acta.motivo || "")}</div>
        </div>

        <h6 class="mt-3">Detalle de productos (salida por vencimiento)</h6>
        <div class="table-responsive">
          <table class="table table-sm table-bordered align-middle">
            <thead class="table-light">
              <tr>
                <th>Producto</th>
                <th>Bodega</th>
                <th>Ubicación</th>
                <th>Vence</th>
                <th class="text-end">Cantidad (kg)</th>
              </tr>
            </thead>
            <tbody>
              ${filas || `<tr><td colspan="5" class="text-center text-muted">Sin detalle</td></tr>`}
            </tbody>
          </table>
        </div>

        <div class="row mt-5 text-center">
          <div class="col-md-6">
            <div style="border-top:1px solid #000; padding-top:6px;">
              <strong>Elaboró:</strong> ${escapeHtml(acta.creado_por || "")}
            </div>
          </div>
          <div class="col-md-6 mt-4 mt-md-0">
            <div style="border-top:1px solid #000; padding-top:6px;">
              <strong>Responsable:</strong> __________________________
            </div>
          </div>
        </div>
      </div>
    `;

    vistaActa.classList.remove("d-none");
  }

  // ---------------------------
  // Guardar acta
  // ---------------------------
  async function guardarActa() {
    const idSalida = selectSalida.value;
    const fecha = fechaActa.value;
    const motivo = (motivoActa.value || "").trim();

    if (!idSalida) {
      if (typeof swal === "function") swal("Atención", "Seleccione una salida.", "warning");
      return;
    }
    if (!fecha) {
      if (typeof swal === "function") swal("Atención", "Seleccione la fecha del acta.", "warning");
      return;
    }
    if (!motivo || motivo.length < 5) {
      if (typeof swal === "function") swal("Atención", "Escriba un motivo (mínimo 5 caracteres).", "warning");
      return;
    }

    btnGuardarActa.disabled = true;

    try {
      const res = await fetch("/actas-vencimiento/api/crear", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id_salida: Number(idSalida),
          fecha_acta: fecha,
          motivo: motivo
        })
      });

      const data = await res.json();
      if (!res.ok || data.success === false) {
        throw new Error(data.message || "No se pudo crear el acta.");
      }

      idActaCreada = data.id_acta;

      if (typeof swal === "function") {
        swal("Listo", `Acta creada correctamente. N° ${idActaCreada}`, "success");
      }

      await cargarDetalleActa(idActaCreada);

      // mostrar botones
      btnImprimirActa.classList.remove("d-none");
      btnVerActa.classList.remove("d-none");

      // refrescar salidas elegibles (la usada debe desaparecer)
      await cargarSalidasElegibles();

    } catch (err) {
      console.error("guardarActa:", err);
      if (typeof swal === "function") swal("Error", err.message, "error");
    } finally {
      btnGuardarActa.disabled = false;
    }
  }

  // ---------------------------
  // Eventos
  // ---------------------------
  if (fechaActa) fechaActa.value = hoyISO();

  if (btnRecargarSalidas) {
    btnRecargarSalidas.addEventListener("click", async () => {
      await cargarSalidasElegibles();
    });
  }

  if (selectSalida) {
    selectSalida.addEventListener("change", async () => {
      const idSalida = selectSalida.value;
      await cargarDetalleSalida(idSalida);
    });
  }

  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      await guardarActa();
    });
  }

  if (btnVerActa) {
    btnVerActa.addEventListener("click", () => {
      if (!idActaCreada) return;
      // si tienes la vista HTML /actas-vencimiento/ver/<id_acta>, úsala:
      window.open(`/actas-vencimiento/ver/${idActaCreada}`, "_blank");
    });
  }

  if (btnImprimirActa) {
    btnImprimirActa.addEventListener("click", () => {
      if (!idActaCreada) return;
      window.print();
    });
  }

  // Init
  cargarSalidasElegibles();
});
