// static/js/salidas_nueva.js

// ===============================
// Helpers de formato
// ===============================
function formatKg(value) {
  const n = Number(value || 0);
  if (Number.isNaN(n)) return "0";
  const fixed = n.toFixed(3);
  return fixed.replace(/\.?0+$/, "");
}

function formatFecha(fechaStr) {
  if (!fechaStr) return "";
  const d = new Date(fechaStr);
  if (isNaN(d.getTime())) return fechaStr;
  return d.toLocaleDateString("es-CO", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

// ===============================
// Config
// ===============================
const URL_MENU_BENEFICIARIOS = "/menu_de_parroquias";

// ===============================
// Estado en memoria
// ===============================

// Beneficiario seleccionado (por compatibilidad)
let parroquiaSeleccionada = null;
// parroquiaSeleccionada ahora podrá guardar:
// { id_parroquia, nombre, encargado, telefono, municipio, tipo_beneficiario }  // tipo_beneficiario: "Parroquia"|"Fundacion"

// Detalle de la salida (array de lotes)
let detalleSalida = [];

// ===============================
// Debounce (para no saturar el server)
// ===============================
function debounce(fn, wait = 300) {
  let t = null;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), wait);
  };
}

// ===============================
// Autocomplete visual (igual a tu patrón)
// ===============================
function mostrarSugerencias(input, datos, onSelect) {
  eliminarSugerencias();
  if (!Array.isArray(datos) || datos.length === 0) return;

  const rect = input.getBoundingClientRect();
  const cont = document.createElement("div");

  cont.classList.add("autocomplete-list");
  cont.style.position = "absolute";
  cont.style.left = `${rect.left + window.scrollX}px`;
  cont.style.top = `${rect.bottom + window.scrollY}px`;
  cont.style.width = `${rect.width}px`;
  cont.style.background = "white";
  cont.style.border = "1px solid #ccc";
  cont.style.zIndex = "9999";
  cont.style.maxHeight = "220px";
  cont.style.overflowY = "auto";

  datos.forEach((item) => {
    const div = document.createElement("div");
    div.classList.add("autocomplete-item");

    // Mostrar en una línea útil
    const tipo = item.tipo || "Parroquia";
    const id = item.id_beneficiario ?? item.id_parroquia ?? "";
    const nombre = item.nombre || "";
    const doc = item.numero_documento || "";
    const muni = item.municipio || "";

    div.textContent = `${tipo} | ${id} | ${nombre}${doc ? " | " + doc : ""}${muni ? " | " + muni : ""}`;

    div.style.padding = "8px 10px";
    div.style.cursor = "pointer";
    div.addEventListener("mouseover", () => (div.style.background = "#f3f3f3"));
    div.addEventListener("mouseout", () => (div.style.background = "white"));

    div.addEventListener("click", () => {
      onSelect(item);
      eliminarSugerencias();
    });
    cont.appendChild(div);
  });

  document.body.appendChild(cont);
}

function eliminarSugerencias() {
  document.querySelectorAll(".autocomplete-list").forEach((el) => el.remove());
}

// ===============================
// Modal "no encontrado" -> redirige a menu_de_parroquias.html
// ===============================
function modalNoEncontradoRedirigir(q) {
  const nombre = (q || "").trim();
  if (nombre.length < 2) return;

  // Evitar disparos repetidos con el mismo texto
  if (window.__ultimoNoEncontrado === nombre) return;
  window.__ultimoNoEncontrado = nombre;

  // SweetAlert2
  if (window.Swal && typeof Swal.fire === "function") {
    return Swal.fire({
      icon: "warning",
      title: "Beneficiario no encontrado",
      text: `No existe "${nombre}". ¿Desea crearlo ahora?`,
      showCancelButton: true,
      confirmButtonText: "Sí, ir a crear",
      cancelButtonText: "No",
      confirmButtonColor: "#198754", // verde Bootstrap
      cancelButtonColor: "#6c757d", // gris Bootstrap
    }).then((r) => {
      if (r.isConfirmed) {
        // Puedes mandar el texto como querystring para prellenar en el menú si quieres
        window.location.href = `${URL_MENU_BENEFICIARIOS}?q=${encodeURIComponent(nombre)}`;
      }
    });
  }

  // SweetAlert v1
  if (typeof swal === "function") {
    return swal({
      title: "Beneficiario no encontrado",
      text: `No existe "${nombre}". ¿Desea crearlo ahora?`,
      icon: "warning",
      buttons: {
        cancel: {
          text: "No",
          value: false,
          visible: true,
          className: "btn btn-secondary",
          closeModal: true,
        },
        confirm: {
          text: "Sí, ir a crear",
          value: true,
          visible: true,
          className: "btn btn-success",
          closeModal: true,
        },
      },
    }).then((ok) => {
      if (ok) {
        window.location.href = `${URL_MENU_BENEFICIARIOS}?q=${encodeURIComponent(nombre)}`;
      }
    });
  }

  // Fallback
  if (confirm(`No existe "${nombre}". ¿Desea crearlo ahora?`)) {
    window.location.href = `${URL_MENU_BENEFICIARIOS}?q=${encodeURIComponent(nombre)}`;
  }
}

// ===============================
// Parroquias (beneficiario)
// ===============================

// - dispararModalSiNoExiste: si true -> muestra modal cuando no hay resultados
async function buscarParroquias(
  dispararModalSiNoExiste = false,
  mostrarAutocomplete = false,
) {
  const input = document.getElementById("inputBuscarParroquia");
  const tbody = document.getElementById("tbodyParroquias");
  if (!input || !tbody) return;

  const q = (input.value || "").trim();

  tbody.innerHTML = `
        <tr>
            <td colspan="5" class="text-center">Buscando parroquias / fundaciones...</td>
        </tr>
    `;

  try {
    // -----------------------------------------
    // 1) Intento NUEVO: beneficiarios (Parroquias + Fundaciones)
    // -----------------------------------------
    const params = new URLSearchParams();
    if (q) params.append("q", q);

    let resp = await fetch(`/salidas/api/beneficiarios?${params.toString()}`);

    if (resp.ok) {
      const data = await resp.json();
      if (data.success) {
        const items = data.items || [];

        // ✅ autocomplete debajo del input
        if (mostrarAutocomplete && q.length >= 2) {
          // solo mostramos los primeros 12 para no saturar
          mostrarSugerencias(input, items.slice(0, 12), (item) => {
            // al seleccionar, usamos el mismo flujo de selección
            seleccionarBeneficiarioDesdeAutocomplete(item);
          });
        } else {
          eliminarSugerencias();
        }

        if (!items.length) {
          tbody.innerHTML = `
                        <tr>
                            <td colspan="5" class="text-center">
                                No se encontraron parroquias / fundaciones con ese criterio.
                            </td>
                        </tr>
                    `;

          if (dispararModalSiNoExiste && q.length >= 2) {
            modalNoEncontradoRedirigir(q);
          }
          return;
        }

        // Mantenemos 5 columnas (como tu HTML actual): id, nombre, encargado, telefono, acción.
        let html = "";
        items.forEach((b) => {
          const tipo = b.tipo || "Parroquia";
          const id = b.id_beneficiario;

          html += `
                        <tr>
                            <td>${id}</td>
                            <td>${tipo}: ${b.nombre}</td>
                            <td>${b.encargado || ""}</td>
                            <td>${b.telefono || ""}</td>
                            <td>
                                <button type="button"
                                        class="btn btn-sm btn-success btn-elegir-parroquia"
                                        data-id="${id}"
                                        data-nombre="${b.nombre}"
                                        data-encargado="${b.encargado || ""}"
                                        data-telefono="${b.telefono || ""}"
                                        data-municipio="${b.municipio || ""}"
                                        data-tipo="${tipo}">
                                    Elegir
                                </button>
                            </td>
                        </tr>
                    `;
        });

        tbody.innerHTML = html;
        return;
      }
    }

    // -----------------------------------------
    // 2) Fallback VIEJO: solo parroquias
    // -----------------------------------------
    resp = await fetch(`/salidas/api/parroquias?${params.toString()}`);
    if (!resp.ok) throw new Error("Error HTTP " + resp.status);

    const data = await resp.json();
    if (!data.success)
      throw new Error(data.message || "Error en la búsqueda de parroquias");

    const items = data.items || [];

    if (mostrarAutocomplete && q.length >= 2) {
      mostrarSugerencias(input, items.slice(0, 12), (item) => {
        // item viene con forma de parroquia
        seleccionarBeneficiarioDesdeAutocomplete({
          tipo: "Parroquia",
          id_beneficiario: item.id_parroquia,
          nombre: item.nombre,
          encargado: item.encargado,
          telefono: item.telefono,
          municipio: item.municipio,
        });
      });
    } else {
      eliminarSugerencias();
    }

    if (!items.length) {
      tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center">
                        No se encontraron parroquias con ese criterio.
                    </td>
                </tr>
            `;
      if (dispararModalSiNoExiste && q.length >= 2) {
        modalNoEncontradoRedirigir(q);
      }
      return;
    }

    let html = "";
    items.forEach((p) => {
      html += `
                <tr>
                    <td>${p.id_parroquia}</td>
                    <td>${p.nombre}</td>
                    <td>${p.encargado || ""}</td>
                    <td>${p.telefono || ""}</td>
                    <td>
                        <button type="button"
                                class="btn btn-sm btn-success btn-elegir-parroquia"
                                data-id="${p.id_parroquia}"
                                data-nombre="${p.nombre}"
                                data-encargado="${p.encargado || ""}"
                                data-telefono="${p.telefono || ""}"
                                data-municipio="${p.municipio || ""}"
                                data-tipo="Parroquia">
                            Elegir
                        </button>
                    </td>
                </tr>
            `;
    });

    tbody.innerHTML = html;
  } catch (err) {
    console.error("Error buscando beneficiarios:", err);
    eliminarSugerencias();
    tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center text-danger">
                    Error al buscar parroquias / fundaciones.
                </td>
            </tr>
        `;
    if (typeof swal === "function") {
      swal("Error", "No se pudieron cargar los beneficiarios.", "error");
    } else if (window.Swal && typeof Swal.fire === "function") {
      Swal.fire("Error", "No se pudieron cargar los beneficiarios.", "error");
    }
  }
}

function seleccionarBeneficiarioDesdeAutocomplete(item) {
  const tipo = item.tipo || "Parroquia";
  const id = item.id_beneficiario ?? item.id_parroquia ?? item.id_fundaciones;

  parroquiaSeleccionada = {
    id_parroquia: String(id),
    nombre: item.nombre || "",
    encargado: item.encargado || "",
    telefono: item.telefono || "",
    municipio: item.municipio || "",
    tipo_beneficiario: tipo,
  };

  // Poner el texto en el input (queda bonito)
  const input = document.getElementById("inputBuscarParroquia");
  if (input) input.value = `${parroquiaSeleccionada.nombre}`;

  // Hidden viejo (si existe)
  const inputHidden = document.getElementById("idParroquiaSeleccionada");
  if (inputHidden) inputHidden.value = parroquiaSeleccionada.id_parroquia;

  // Hidden nuevo (si existe)
  const inputTipoHidden = document.getElementById(
    "tipoBeneficiarioSeleccionado",
  );
  if (inputTipoHidden)
    inputTipoHidden.value = parroquiaSeleccionada.tipo_beneficiario;

  // resumen
  const resumen = document.getElementById("resumenParroquiaSeleccionada");
  if (resumen) {
    let text = `[${parroquiaSeleccionada.tipo_beneficiario}] ${parroquiaSeleccionada.nombre}`;
    if (parroquiaSeleccionada.municipio)
      text += ` - ${parroquiaSeleccionada.municipio}`;
    if (parroquiaSeleccionada.encargado)
      text += ` (Encargado: ${parroquiaSeleccionada.encargado})`;
    resumen.textContent = text;
  }

  // Opcional: refrescar tabla con el texto ya seleccionado
  buscarParroquias(false, false);

  // Modal de confirmación
  if (window.Swal && typeof Swal.fire === "function") {
    Swal.fire({
      icon: "success",
      title: "Beneficiario seleccionado",
      text: `${parroquiaSeleccionada.nombre} (${parroquiaSeleccionada.tipo_beneficiario})`,
      timer: 1200,
      showConfirmButton: false,
    });
  } else if (typeof swal === "function") {
    swal("Beneficiario seleccionado", parroquiaSeleccionada.nombre, "success");
  }
}

// ===============================
// Tipos de salida (select)
// ===============================
async function cargarTipoSalida() {
  const select = document.getElementById("selectTipoSalida");
  if (!select) return;

  select.innerHTML = `<option value="">Seleccione tipo de salida</option>`;

  try {
    const resp = await fetch("/salidas/api/tipos-salida");

    if (!resp.ok) {
      throw new Error("Error HTTP " + resp.status);
    }

    const data = await resp.json();

    if (!data.success) {
      throw new Error(data.message || "Error al cargar tipos de salida.");
    }

    const items = data.items || [];

    items.forEach((t) => {
      const opt = document.createElement("option");
      opt.value = t.id_tipo_salida;
      opt.textContent = t.nombre;
      select.appendChild(opt);
    });
  } catch (err) {
    console.error("Error cargando tipos de salida:", err);

    if (window.Swal && typeof Swal.fire === "function") {
      Swal.fire("Error", "No se pudieron cargar los tipos de salida.", "error");
    } else if (typeof swal === "function") {
      swal("Error", "No se pudieron cargar los tipos de salida.", "error");
    }
  }
}
function manejarClickElegirParroquia(e) {
  const btn = e.target.closest(".btn-elegir-parroquia");
  if (!btn) return;

  // Guardamos tipo (Parroquia/Fundacion) sin romper lo anterior
  const tipo = btn.dataset.tipo || "Parroquia";

  parroquiaSeleccionada = {
    id_parroquia: btn.dataset.id,
    nombre: btn.dataset.nombre,
    encargado: btn.dataset.encargado || "",
    telefono: btn.dataset.telefono || "",
    municipio: btn.dataset.municipio || "",
    tipo_beneficiario: tipo,
  };

  const resumen = document.getElementById("resumenParroquiaSeleccionada");

  // Hidden viejo (si existe)
  const inputHidden = document.getElementById("idParroquiaSeleccionada");
  if (inputHidden) inputHidden.value = parroquiaSeleccionada.id_parroquia;

  // Hidden nuevo (si existe)
  const inputTipoHidden = document.getElementById(
    "tipoBeneficiarioSeleccionado",
  );
  if (inputTipoHidden)
    inputTipoHidden.value = parroquiaSeleccionada.tipo_beneficiario;

  if (resumen) {
    let text = `[${parroquiaSeleccionada.tipo_beneficiario}] ${parroquiaSeleccionada.nombre}`;
    if (parroquiaSeleccionada.municipio)
      text += ` - ${parroquiaSeleccionada.municipio}`;
    if (parroquiaSeleccionada.encargado)
      text += ` (Encargado: ${parroquiaSeleccionada.encargado})`;
    resumen.textContent = text;
  }

  if (window.Swal && typeof Swal.fire === "function") {
    Swal.fire({
      icon: "success",
      title: "Beneficiario seleccionado",
      text: parroquiaSeleccionada.nombre,
      timer: 1200,
      showConfirmButton: false,
    });
  } else if (typeof swal === "function") {
    swal("Beneficiario seleccionado", parroquiaSeleccionada.nombre, "success");
  }
}

// ===============================
// Lotes disponibles (productos)
// ===============================
async function buscarLotes() {
  const input = document.getElementById("inputBuscarProducto");
  const tbody = document.getElementById("tbodyLotesDisponibles");
  if (!input || !tbody) return;

  const q = (input.value || "").trim();

  tbody.innerHTML = `
        <tr>
            <td colspan="6" class="text-center">Buscando productos en inventario...</td>
        </tr>
    `;

  try {
    const params = new URLSearchParams();
    if (q) params.append("q", q);

    const resp = await fetch(
      `/salidas/api/lotes-disponibles?${params.toString()}`,
    );
    if (!resp.ok) throw new Error("Error HTTP " + resp.status);

    const data = await resp.json();
    if (!data.success)
      throw new Error(data.message || "Error en la consulta de lotes");

    const items = data.items || [];
    if (!items.length) {
      tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center">
                        No hay lotes disponibles con ese filtro.
                    </td>
                </tr>
            `;
      return;
    }

    let html = "";
    items.forEach((lote) => {
      html += `
                <tr>
                    <td>${lote.id_producto}</td>
                    <td>${lote.producto}</td>
                    <td>
                        ${lote.bodega || ""}
                        ${lote.bodega_texto ? " - " + lote.bodega_texto : ""}
                    </td>
                    <td>${lote.fecha_vencimiento ? formatFecha(lote.fecha_vencimiento) : "-"}</td>
                    <td class="text-end">${formatKg(lote.stock_disponible_kg)} kg</td>
                    <td class="text-center">
                        <button type="button"
                                class="btn btn-sm btn-success btn-agregar-lote"
                                data-id-entrada-detalle="${lote.id_entrada_detalle}"
                                data-id-producto="${lote.id_producto}"
                                data-producto="${lote.producto}"
                                data-valor-producto="${lote.valor_producto || 0}"
                                data-valor-unitario="${lote.valor_unitario || 0}"
                                data-id-categoria="${lote.id_categoria}"
                                data-categoria="${lote.categoria}"
                                data-id-bodega="${lote.id_bodega}"
                                data-bodega="${lote.bodega}"
                                data-bodega-texto="${lote.bodega_texto || ""}"
                                data-fecha-vencimiento="${lote.fecha_vencimiento || ""}"
                                data-stock="${lote.stock_disponible_kg}">
                            Agregar
                        </button>
                    </td>
                </tr>
            `;
    });

    tbody.innerHTML = html;
  } catch (err) {
    console.error("Error buscando lotes:", err);
    tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-danger">
                    Error al cargar el inventario disponible.
                </td>
            </tr>
        `;
    if (window.Swal && typeof Swal.fire === "function") {
      Swal.fire(
        "Error",
        "No se pudieron cargar los productos disponibles.",
        "error",
      );
    } else if (typeof swal === "function") {
      swal(
        "Error",
        "No se pudieron cargar los productos disponibles.",
        "error",
      );
    }
  }
}

function agregarLoteDesdeBoton(e) {
  const btn = e.target.closest(".btn-agregar-lote");
  if (!btn) return;

  const idEntradaDetalle = Number(btn.dataset.idEntradaDetalle);
  const idProducto = Number(btn.dataset.idProducto);
  const producto = btn.dataset.producto || "";

  const idCategoria = Number(btn.dataset.idCategoria);
  const categoria = btn.dataset.categoria || "";
  const idBodega = Number(btn.dataset.idBodega);
  const bodega = btn.dataset.bodega || "";
  const bodegaTexto = btn.dataset.bodegaTexto || "";
  const fechaVenc = btn.dataset.fechaVencimiento || "";
  const stock = Number(btn.dataset.stock || 0);
  const valorProducto = Number(btn.dataset.valorProducto || 0);

  if (!idEntradaDetalle || stock <= 0) {
    if (window.Swal && typeof Swal.fire === "function") {
      Swal.fire("Aviso", "Este lote no tiene stock disponible.", "warning");
    } else if (typeof swal === "function") {
      swal("Aviso", "Este lote no tiene stock disponible.", "warning");
    }
    return;
  }

  const yaExiste = detalleSalida.some(
    (d) => d.id_entrada_detalle === idEntradaDetalle,
  );
  if (yaExiste) {
    if (window.Swal && typeof Swal.fire === "function") {
      Swal.fire("Aviso", "Este lote ya está agregado en el detalle.", "info");
    } else if (typeof swal === "function") {
      swal("Aviso", "Este lote ya está agregado en el detalle.", "info");
    }
    return;
  }

  const item = {
    id_entrada_detalle: idEntradaDetalle,
    id_producto: idProducto,
    producto,
    id_categoria: idCategoria,
    categoria,
    id_bodega: idBodega,
    bodega,
    bodega_texto: bodegaTexto,
    fecha_vencimiento: fechaVenc,
    stock_disponible_kg: stock,
    cantidad_kg: stock,
    valor_unitario: valorProducto,
  };

  detalleSalida.push(item);
  pintarDetalleSalida();
}

function pintarDetalleSalida() {
  const tbody = document.getElementById("tbodyDetalleSalida");
  const totalKgEl = document.getElementById("totalKgSalida");

  if (!tbody) return;
  tbody.innerHTML = "";

  if (!detalleSalida.length) {
    tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center">
                    No hay productos agregados a esta salida.
                </td>
            </tr>
        `;
    if (totalKgEl) totalKgEl.textContent = "0";
    return;
  }

  let totalKg = 0;

  detalleSalida.forEach((item) => {
    totalKg += Number(item.cantidad_kg || 0);

    const tr = document.createElement("tr");
    tr.dataset.idEntradaDetalle = item.id_entrada_detalle;

    tr.innerHTML = `
            <td>${item.id_producto}</td>
            <td>${item.producto}</td>
            <td>
                ${item.bodega || ""}
                ${item.bodega_texto ? " - " + item.bodega_texto : ""}
            </td>
            <td>${item.fecha_vencimiento ? formatFecha(item.fecha_vencimiento) : "-"}</td>
            <td class="text-end">${formatKg(item.stock_disponible_kg)} kg</td>
            <td class="text-end">
                <input type="number"
                       class="form-control form-control-sm input-cantidad-salida"
                       style="max-width:120px; display:inline-block;"
                       min="0.001"
                       step="0.001"
                       max="${item.stock_disponible_kg}"
                       value="${item.cantidad_kg}">
            </td>
            <td class="text-center">
                <button type="button" class="btn btn-sm btn-danger btn-quitar-detalle">
                    Quitar
                </button>
            </td>
        `;
    tbody.appendChild(tr);
  });

  if (totalKgEl) totalKgEl.textContent = formatKg(totalKg);
}

function manejarCambioCantidad(e) {
  const input = e.target.closest(".input-cantidad-salida");
  if (!input) return;

  const tr = input.closest("tr");
  if (!tr) return;

  const idEntradaDetalle = Number(tr.dataset.idEntradaDetalle);
  const item = detalleSalida.find(
    (d) => d.id_entrada_detalle === idEntradaDetalle,
  );
  if (!item) return;

  let val = Number(input.value || 0);
  if (Number.isNaN(val) || val <= 0) val = 0;

  const max = Number(input.getAttribute("max") || item.stock_disponible_kg);
  if (val > max) {
    val = max;
    input.value = val;
    if (window.Swal && typeof Swal.fire === "function") {
      Swal.fire(
        "Aviso",
        "La cantidad no puede superar el stock disponible.",
        "warning",
      );
    } else if (typeof swal === "function") {
      swal(
        "Aviso",
        "La cantidad no puede superar el stock disponible.",
        "warning",
      );
    }
  }

  item.cantidad_kg = val;

  const totalKgEl = document.getElementById("totalKgSalida");
  if (totalKgEl) {
    const total = detalleSalida.reduce(
      (acc, d) => acc + Number(d.cantidad_kg || 0),
      0,
    );
    totalKgEl.textContent = formatKg(total);
  }
}

function manejarQuitarDetalle(e) {
  const btn = e.target.closest(".btn-quitar-detalle");
  if (!btn) return;

  const tr = btn.closest("tr");
  if (!tr) return;

  const idEntradaDetalle = Number(tr.dataset.idEntradaDetalle);
  detalleSalida = detalleSalida.filter(
    (d) => d.id_entrada_detalle !== idEntradaDetalle,
  );

  pintarDetalleSalida();
}

// ===============================
// Guardar salida
// ===============================
async function guardarSalida() {
  const idParroquiaInput = document.getElementById("idParroquiaSeleccionada");
  const selectTipoSalida = document.getElementById("selectTipoSalida");
  const inputFechaSalida = document.getElementById("fechaSalida");
  const inputObs = document.getElementById("observacionSalida");

  const idSeleccionado = idParroquiaInput ? idParroquiaInput.value || "" : "";
  const idTipoSalida = selectTipoSalida ? selectTipoSalida.value || "" : "";
  const fechaSalida = inputFechaSalida ? inputFechaSalida.value || "" : "";
  const observacion = inputObs ? inputObs.value.trim() || "" : "";

  if (!idSeleccionado) {
    if (window.Swal && typeof Swal.fire === "function") {
      Swal.fire(
        "Falta beneficiario",
        "Seleccione primero una parroquia o fundación.",
        "warning",
      );
    } else if (typeof swal === "function") {
      swal(
        "Falta beneficiario",
        "Seleccione primero una parroquia o fundación.",
        "warning",
      );
    }
    return;
  }

  if (!idTipoSalida) {
    if (window.Swal && typeof Swal.fire === "function") {
      Swal.fire(
        "Falta tipo de salida",
        "Seleccione el tipo de salida.",
        "warning",
      );
    } else if (typeof swal === "function") {
      swal("Falta tipo de salida", "Seleccione el tipo de salida.", "warning");
    }
    return;
  }

  if (!detalleSalida.length) {
    if (window.Swal && typeof Swal.fire === "function") {
      Swal.fire(
        "Sin productos",
        "Agregue al menos un producto a la salida.",
        "warning",
      );
    } else if (typeof swal === "function") {
      swal(
        "Sin productos",
        "Agregue al menos un producto a la salida.",
        "warning",
      );
    }
    return;
  }

  const detallesParaEnviar = detalleSalida
    .filter((d) => Number(d.cantidad_kg || 0) > 0)
    .map((d) => ({
      id_entrada_detalle: d.id_entrada_detalle,
      cantidad_kg: Number(d.cantidad_kg),
      valor_unitario: Number(d.valor_unitario || 0),
    }));

  if (!detallesParaEnviar.length) {
    if (window.Swal && typeof Swal.fire === "function") {
      Swal.fire(
        "Sin cantidades",
        "Todas las cantidades están en 0. Ajuste antes de guardar.",
        "warning",
      );
    } else if (typeof swal === "function") {
      swal(
        "Sin cantidades",
        "Todas las cantidades están en 0. Ajuste antes de guardar.",
        "warning",
      );
    }
    return;
  }

  // Validar que realmente se eligió beneficiario desde el botón "Elegir" o autocomplete
  const tipoBenef = parroquiaSeleccionada?.tipo_beneficiario;
  const idBenef = parroquiaSeleccionada?.id_parroquia || idSeleccionado;

  if (!tipoBenef || !idBenef) {
    if (window.Swal && typeof Swal.fire === "function") {
      Swal.fire(
        "Falta beneficiario",
        "Seleccione una parroquia o fundación con el botón Elegir.",
        "warning",
      );
    } else if (typeof swal === "function") {
      swal(
        "Falta beneficiario",
        "Seleccione una parroquia o fundación con el botón Elegir.",
        "warning",
      );
    }
    return;
  }

  const payload = {
    tipo_beneficiario: tipoBenef, // "Parroquia" | "Fundacion"
    id_beneficiario: Number(idBenef), // id de parroquia o fundación
    id_tipo_salida: Number(idTipoSalida),
    fecha_salida: fechaSalida || null,
    observacion,
    detalles: detallesParaEnviar,
  };

  try {
    const resp = await fetch("/salidas/api/crear", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await resp.json();
    if (!resp.ok || !data.success)
      throw new Error(data.message || "Error al registrar la salida.");

    const idSalidaCreada = data.id_salida;

    // SweetAlert2
    if (window.Swal && typeof Swal.fire === "function") {
      Swal.fire({
        icon: "success",
        title: "Salida creada",
        text: "¿Deseas ver el comprobante de salida?",
        showCancelButton: true,
        confirmButtonText: "Ver comprobante",
        cancelButtonText: "Cerrar",
      }).then((r) => {
        if (r.isConfirmed && idSalidaCreada) {
          window.open(`/salidas/comprobante/${idSalidaCreada}`, "_blank");
        } else {
          detalleSalida = [];
          pintarDetalleSalida();
          if (inputObs) inputObs.value = "";
          if (inputFechaSalida) inputFechaSalida.value = "";
        }
      });
    } else if (typeof swal === "function") {
      swal({
        title: "Salida creada",
        text: "¿Deseas ver el comprobante de salida?",
        icon: "success",
        buttons: {
          cancelar: {
            text: "Cerrar",
            value: "no",
            visible: true,
            closeModal: true,
          },
          ver: {
            text: "Ver comprobante",
            value: "si",
            visible: true,
            closeModal: true,
          },
        },
      }).then((value) => {
        if (value === "si" && idSalidaCreada) {
          window.open(`/salidas/comprobante/${idSalidaCreada}`, "_blank");
        } else {
          detalleSalida = [];
          pintarDetalleSalida();
          if (inputObs) inputObs.value = "";
          if (inputFechaSalida) inputFechaSalida.value = "";
        }
      });
    } else {
      alert("Salida creada correctamente.");
    }
  } catch (err) {
    console.error("Error guardando salida:", err);
    if (window.Swal && typeof Swal.fire === "function") {
      Swal.fire(
        "Error",
        err.message || "No se pudo registrar la salida.",
        "error",
      );
    } else if (typeof swal === "function") {
      swal("Error", err.message || "No se pudo registrar la salida.", "error");
    } else {
      alert("Error: " + (err.message || "No se pudo registrar la salida."));
    }
  }
}

// ===============================
// Init
// ===============================
document.addEventListener("DOMContentLoaded", () => {
  const inputFechaSalida = document.getElementById("fechaSalida");
  if (inputFechaSalida) {
    const hoy = new Date().toISOString().split("T")[0];
    inputFechaSalida.setAttribute("max", hoy);
  }

  // ✅ AUTOCOMPLETE + TABLA mientras escribe (SIN modal)
  const inputBuscar = document.getElementById("inputBuscarParroquia");
  if (inputBuscar) {
    const live = debounce(() => buscarParroquias(false, true), 300);
    inputBuscar.addEventListener("input", live);

    // ✅ Enter: busca y si no existe dispara modal para ir a crear
    inputBuscar.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        buscarParroquias(true, true);
      }
    });
  }

  // Botón buscar: busca y si no existe dispara modal
  const btnBuscarParroquia = document.getElementById("btnBuscarParroquia");
  if (btnBuscarParroquia) {
    btnBuscarParroquia.addEventListener("click", (e) => {
      e.preventDefault();
      buscarParroquias(true, true);
    });
  }

  // Click en resultados de parroquias (tabla)
  const tbodyParroquias = document.getElementById("tbodyParroquias");
  if (tbodyParroquias) {
    tbodyParroquias.addEventListener("click", manejarClickElegirParroquia);
  }

  // Buscar lotes/prod disponibles
  const btnBuscarProducto = document.getElementById("btnBuscarProducto");
  if (btnBuscarProducto) {
    btnBuscarProducto.addEventListener("click", (e) => {
      e.preventDefault();
      buscarLotes();
    });
  }

  // Click en "Agregar" lote
  const tbodyLotes = document.getElementById("tbodyLotesDisponibles");
  if (tbodyLotes) {
    tbodyLotes.addEventListener("click", agregarLoteDesdeBoton);
  }

  // Eventos en detalle (cambio cantidad, quitar)
  const tbodyDetalle = document.getElementById("tbodyDetalleSalida");
  if (tbodyDetalle) {
    tbodyDetalle.addEventListener("input", manejarCambioCantidad);
    tbodyDetalle.addEventListener("click", manejarQuitarDetalle);
  }

  // Guardar salida
  const btnGuardar = document.getElementById("btnGuardarSalida");
  if (btnGuardar) {
    btnGuardar.addEventListener("click", (e) => {
      e.preventDefault();
      guardarSalida();
    });
  }

  // Tipos de salida
  cargarTipoSalida();

  // Cerrar autocomplete al click afuera
  document.addEventListener("click", (e) => {
    const input = document.getElementById("inputBuscarParroquia");
    const list = document.querySelector(".autocomplete-list");
    if (!list) return;
    if (input && (e.target === input || list.contains(e.target))) return;
    eliminarSugerencias();
  });
});
