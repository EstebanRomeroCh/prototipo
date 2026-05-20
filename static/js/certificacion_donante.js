// static/js/certificacion_donante.js

document.addEventListener("DOMContentLoaded", () => {
    // =========================
    // Referencias al DOM
    // =========================
    const inputDocDonante = document.getElementById("docDonanteCert");
    const inputNomDonante = document.getElementById("nombreDonanteCert");
    const inputIdDonante = document.getElementById("idDonanteCert");

    const inputDesde = document.getElementById("desdeCert");
    const inputHasta = document.getElementById("hastaCert");

    const btnGenerar = document.getElementById("btnGenerarCert");
    const btnImprimir = document.getElementById("btnImprimirCertificado");

    const mensajeCargando = document.getElementById("cert-mensaje-cargando");
    const vistaCertificado = document.getElementById("vista-certificado");

    const bloqueProductos = document.getElementById("bloque-productos");
    const bloqueMonetaria = document.getElementById("bloque-monetaria");

    const tbodyDetalles = document.getElementById("tbody-detalles-cert");
    const totalKgEl = document.getElementById("cert-total-kg");
    const wrapperTotalValor = document.getElementById("wrapper-total-valor");
    const totalValorEl = document.getElementById("cert-total-valor");

    const totalMonetarioEl = document.getElementById("cert-total-monetario");
    const primerMonetariaEl = document.getElementById("cert-primer-monetaria");
    const ultimaMonetariaEl = document.getElementById("cert-ultima-monetaria");

    // Encabezado / parámetros
    const nombreOrgEl = document.getElementById("cert-nombre-organizacion");
    const ciudadEl = document.getElementById("cert-ciudad");
    const direccionEl = document.getElementById("cert-direccion");
    const telefonoEl = document.getElementById("cert-telefono");
    const nitEl = document.getElementById("cert-nit");
    const logoEl = document.getElementById("cert-logo");

    const textoEncabezadoEl = document.getElementById("cert-texto-encabezado");
    const parrafoIntroEl = document.getElementById("cert-parrafo-intro");
    const textoDespedidaEl = document.getElementById("cert-texto-despedida");
    const lugarFechaEl = document.getElementById("cert-lugar-fecha");
    const firmaEl = document.getElementById("cert-firma-responsable");
    const cargoEl = document.getElementById("cert-cargo-responsable");

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

    function formatFechaLarga(fechaStr) {
        if (!fechaStr) return "";
        const d = new Date(fechaStr);
        if (isNaN(d.getTime())) return fechaStr;
        return d.toLocaleDateString("es-CO", {
            day: "numeric",
            month: "long",
            year: "numeric"
        });
    }

    // =========================
    // Autocomplete donantes
    // =========================
    function eliminarSugerencias() {
        document.querySelectorAll(".autocomplete-list").forEach(el => el.remove());
    }

    function mostrarSugerencias(input, datos, onSelect) {
        eliminarSugerencias();
        if (!Array.isArray(datos) || datos.length === 0) return;

        const rect = input.getBoundingClientRect();
        const cont = document.createElement("div");

        cont.classList.add("autocomplete-list");
        cont.style.position = "absolute";
        cont.style.left = `${rect.left}px`;
        cont.style.top = `${rect.bottom}px`;
        cont.style.width = `${rect.width}px`;
        cont.style.background = "white";
        cont.style.border = "1px solid #ccc";
        cont.style.zIndex = "9999";
        cont.style.maxHeight = "200px";
        cont.style.overflowY = "auto";

        datos.forEach(item => {
            const div = document.createElement("div");
            div.classList.add("autocomplete-item");
            div.style.padding = "4px 8px";
            div.style.cursor = "pointer";

            div.textContent = `${item.numero_documento || ""} | ${item.nombre || ""}`;
            div.addEventListener("click", () => {
                onSelect(item);
                eliminarSugerencias();
            });
            cont.appendChild(div);
        });

        document.body.appendChild(cont);
    }

    async function buscarDonantesCert() {
        const q = (inputDocDonante.value || "").trim();
        if (q.length < 2) return;

        try {
            const res = await fetch(`/api/donantes/buscar?q=${encodeURIComponent(q)}`);
            const donantes = await res.json();

            if (!donantes || donantes.length === 0) {
                if (typeof Swal !== "undefined") {
                    Swal.fire({
                        icon: "warning",
                        title: "Donante no encontrado",
                        text: "¿Desea crearlo ahora?",
                        showCancelButton: true,
                        confirmButtonText: "Sí, crear",
                        cancelButtonText: "No"
                    }).then(r => {
                        if (r.isConfirmed) window.location.href = "/donante";
                    });
                }
                return;
            }

            mostrarSugerencias(inputDocDonante, donantes, (item) => {
                inputIdDonante.value = item.id_donante;
                inputDocDonante.value = item.numero_documento || "";
                inputNomDonante.value = item.nombre || "";
            });

        } catch (err) {
            console.error("Error buscando donantes para certificado:", err);
        }
    }

    if (inputDocDonante) {
        inputDocDonante.addEventListener("input", buscarDonantesCert);
        document.addEventListener("click", eliminarSugerencias);
    }

    // =========================
    // Render del certificado
    // =========================
    function renderCertificado(data, tipoSeleccionado) {
        const parametros = data.parametros || {};
        const donante = data.donante || {};
        const prodData = data.productos || {};
        const monData = data.monetaria || {};

        // ---- Encabezado organización ----
        if (nombreOrgEl) nombreOrgEl.textContent = parametros.nombre_organizacion || "Nombre de la organización";
        if (ciudadEl) ciudadEl.textContent = parametros.ciudad || "";
        if (direccionEl) direccionEl.textContent = parametros.direccion_organizacion || "";
        if (telefonoEl) {
            telefonoEl.textContent = parametros.telefono_organizacion
                ? `Teléfono: ${parametros.telefono_organizacion}`
                : "";
        }
        if (nitEl) {
            nitEl.textContent = parametros.nit_organizacion
                ? `NIT: ${parametros.nit_organizacion}`
                : "";
        }

        if (logoEl && parametros.ruta_logo) {
            const ruta = parametros.ruta_logo.trim();
            if (ruta.startsWith("http://") || ruta.startsWith("https://")) {
                logoEl.src = ruta;
            } else if (ruta.startsWith("/")) {
                logoEl.src = ruta;
            } else {
                logoEl.src = `/static/${ruta}`;
            }
        }
        const firmaContadora = document.getElementById("firma-contadora");
        const firmasWrap = document.querySelector(".firmas");

        // Mostrar contadora solo si es monetaria o ambos
        const requiereContadora = (tipoSeleccionado === "monetaria" || tipoSeleccionado === "ambos");

        if (firmaContadora) {
            if (requiereContadora) firmaContadora.classList.remove("d-none");
            else firmaContadora.classList.add("d-none");
        }

        // Ajustar grid 2 o 3 columnas
        if (firmasWrap) {
            if (requiereContadora) firmasWrap.classList.remove("firmas-2");
            else firmasWrap.classList.add("firmas-2");
        }


        // ---- Título / texto encabezado ----
        if (textoEncabezadoEl) {
            textoEncabezadoEl.textContent =
                parametros.texto_encabezado && parametros.texto_encabezado.trim() !== ""
                    ? parametros.texto_encabezado
                    : "CERTIFICADO DE DONACIÓN";
        }

        // ---- Párrafo intro ----
        if (parrafoIntroEl) {
            const nombreDonante = donante.nombre || "el(la) donante";
            const doc = donante.numero_documento || "N/A";

            // Rango de fechas para texto
            const desdeTxt = inputDesde.value ? formatFechaLarga(inputDesde.value) : "";
            const hastaTxt = inputHasta.value ? formatFechaLarga(inputHasta.value) : "";

            let rangoTexto = "";
            if (desdeTxt && hastaTxt) {
                rangoTexto = `en el período comprendido entre ${desdeTxt} y ${hastaTxt}`;
            } else if (desdeTxt) {
                rangoTexto = `desde el ${desdeTxt}`;
            } else if (hastaTxt) {
                rangoTexto = `hasta el ${hastaTxt}`;
            } else {
                rangoTexto = "en el período consultado";
            }

            let textoBase = parametros.texto_cuerpo_base || "";
            const fraseDonante =
                `Se certifica que el(la) señor(a) ${nombreDonante}, identificado(a) ` +
                `con documento No. ${doc}, ha realizado donaciones ${rangoTexto}.`;

            if (textoBase.trim() !== "") {
                parrafoIntroEl.textContent = `${textoBase} ${fraseDonante}`;
            } else {
                parrafoIntroEl.textContent = fraseDonante;
            }
        }

        // =========================
        // Bloque productos
        // =========================
        if (bloqueProductos && tbodyDetalles && totalKgEl && wrapperTotalValor && totalValorEl) {
            // Mostrar u ocultar bloque según tipo seleccionado / datos
            const tieneProductos = Array.isArray(prodData.detalles) && prodData.detalles.length > 0;

            if ((tipoSeleccionado === "productos" || tipoSeleccionado === "ambos") && tieneProductos) {
                bloqueProductos.classList.remove("d-none");

                tbodyDetalles.innerHTML = "";
                let totalKg = 0;
                let totalValor = 0;

                prodData.detalles.forEach(det => {
                    const peso = Number(det.peso_total_kg || 0);
                    const valor = Number(det.valor_total || 0);
                    totalKg += peso;
                    totalValor += valor;

                    const tr = document.createElement("tr");
                    tr.innerHTML = `
                        <td>${det.producto || ""}</td>
                        <td>${det.categoria || ""}</td>
                        <td class="text-end">${det.cantidad || 0}</td>
                        <td class="text-end">${formatKg(peso)}</td>
                        <td class="text-end">${formatMoney(valor)}</td>
                    `;
                    tbodyDetalles.appendChild(tr);
                });

                totalKgEl.textContent = formatKg(prodData.total_kg || totalKg);

                const mostrarValor = (parametros.mostrar_valor_monetario || "").toLowerCase();
                const debeMostrar = mostrarValor === "si" || mostrarValor === "sí" || mostrarValor === "sí";

                if (debeMostrar) {
                    wrapperTotalValor.classList.remove("d-none");
                    const val = prodData.total_valor || totalValor;
                    totalValorEl.textContent = formatMoney(val);
                } else {
                    wrapperTotalValor.classList.add("d-none");
                }
            } else {
                bloqueProductos.classList.add("d-none");
                tbodyDetalles.innerHTML = "";
            }
        }

        // =========================
        // Bloque monetaria
        // =========================
        if (bloqueMonetaria && totalMonetarioEl && primerMonetariaEl && ultimaMonetariaEl) {
            const totalMonto = Number(monData.total_monto || 0);
            const fecha1 = monData.fecha_primera || null;
            const fecha2 = monData.fecha_ultima || null;
            const hayMonetaria = totalMonto > 0 || fecha1 || fecha2;

            if ((tipoSeleccionado === "monetaria" || tipoSeleccionado === "ambos") && hayMonetaria) {
                bloqueMonetaria.classList.remove("d-none");
                totalMonetarioEl.textContent = formatMoney(totalMonto);
                primerMonetariaEl.textContent = fecha1 ? formatFechaLarga(fecha1) : "-";
                ultimaMonetariaEl.textContent = fecha2 ? formatFechaLarga(fecha2) : "-";
            } else {
                bloqueMonetaria.classList.add("d-none");
                totalMonetarioEl.textContent = "0";
                primerMonetariaEl.textContent = "-";
                ultimaMonetariaEl.textContent = "-";
            }
        }

        // ---- Despedida ----
        if (textoDespedidaEl) {
            textoDespedidaEl.textContent =
                parametros.texto_despedida && parametros.texto_despedida.trim() !== ""
                    ? parametros.texto_despedida
                    : "Agradecemos profundamente su valioso aporte y solidaridad.";
        }

        // ---- Lugar y fecha de emisión ----
        if (lugarFechaEl) {
            const lugar = parametros.lugar_emision || parametros.ciudad || "";
            const hoy = new Date();
            const fechaHoy = hoy.toLocaleDateString("es-CO", {
                day: "numeric",
                month: "long",
                year: "numeric"
            });
            lugarFechaEl.textContent = lugar ? `${lugar}, ${fechaHoy}` : fechaHoy;
        }

        // ---- Firma ----
        if (firmaEl) {
            firmaEl.textContent = parametros.firma_responsable || "Responsable del Banco de Alimentos";
        }
        if (cargoEl) {
            cargoEl.textContent = parametros.cargo_responsable || "Cargo";
        }

        // Mostrar certificado y botón imprimir
        if (vistaCertificado) vistaCertificado.classList.remove("d-none");
        if (btnImprimir) btnImprimir.classList.remove("d-none");
    }

    // =========================
    // Llamar API / Generar
    // =========================
    async function generarCertificado() {
        const idDonante = inputIdDonante.value || "";
        if (!idDonante) {
            if (typeof Swal !== "undefined") {
                Swal.fire("Atención", "Debe seleccionar un donante válido.", "warning");
            }
            return;
        }

        const radioSeleccionado = document.querySelector('input[name="tipoCert"]:checked');
        const tipoSeleccionado = radioSeleccionado ? radioSeleccionado.value : "productos";

        const params = new URLSearchParams();
        params.append("id_donante", idDonante);
        params.append("tipo", tipoSeleccionado);

        if (inputDesde.value) params.append("desde", inputDesde.value);
        if (inputHasta.value) params.append("hasta", inputHasta.value);

        const url = `/api/certificados/donante?${params.toString()}`;

        if (mensajeCargando) {
            mensajeCargando.classList.remove("d-none");
            mensajeCargando.classList.remove("alert-danger");
            mensajeCargando.classList.add("alert-info");
            mensajeCargando.textContent = "Cargando información del certificado...";
        }

        try {
            const res = await fetch(url);
            if (!res.ok) {
                throw new Error(`Error HTTP ${res.status}`);
            }
            const data = await res.json();
            if (!data.success) {
                throw new Error(data.message || "No se pudo generar el certificado.");
            }

            renderCertificado(data, tipoSeleccionado);

            if (mensajeCargando) {
                mensajeCargando.classList.add("d-none");
            }

        } catch (err) {
            console.error("Error cargando certificado:", err);
            if (mensajeCargando) {
                mensajeCargando.classList.remove("d-none");
                mensajeCargando.classList.remove("alert-info");
                mensajeCargando.classList.add("alert-danger");
                mensajeCargando.textContent =
                    "Error al cargar los datos del certificado. Intente nuevamente.";
            }
            if (typeof Swal !== "undefined") {
                Swal.fire("Error", "No se pudo generar el certificado. Revise la consola.", "error");
            }
        }
    }

    // =========================
    // Eventos
    // =========================
    if (btnGenerar) {
        btnGenerar.addEventListener("click", (e) => {
            e.preventDefault();
            generarCertificado();
        });
    }

    if (btnImprimir) {
        btnImprimir.addEventListener("click", (e) => {
            e.preventDefault();
            window.print();
        });
    }
});
