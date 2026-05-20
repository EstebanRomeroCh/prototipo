// static/js/parametros_certificados.js

document.addEventListener("DOMContentLoaded", () => {
    // ================================
    // 1. Referencias al DOM
    // ================================
    const formCrear = document.getElementById("formParametroCertificado");
    const tbody = document.querySelector("#tablaParametrosCertificados tbody");
    const inputBuscador = document.getElementById("buscadorParametros");

    const modalElem = document.getElementById("modalActualizarParametro");
    const modalActualizar = modalElem ? new bootstrap.Modal(modalElem) : null;

    const formActualizar = document.getElementById("formActualizarParametro");

    // Campos del modal
    const idParametroModal = document.getElementById("idParametroModal");
    const nombrePlantillaModal = document.getElementById("nombrePlantillaModal");
    const nombreOrganizacionModal = document.getElementById("nombreOrganizacionModal");
    const ciudadOrganizacionModal = document.getElementById("ciudadOrganizacionModal");
    const nombreDirectorModal = document.getElementById("nombreDirectorModal");
    const cargoDirectorModal = document.getElementById("cargoDirectorModal");
    const textoCabeceraModal = document.getElementById("textoCabeceraModal");
    const textoPieModal = document.getElementById("textoPieModal");
    const estadoParametroModal = document.getElementById("estadoParametroModal");

    // Campos del formulario principal
    const nombrePlantilla = document.getElementById("nombrePlantilla");
    const nombreOrganizacion = document.getElementById("nombreOrganizacion");
    const ciudadOrganizacion = document.getElementById("ciudadOrganizacion");
    const nombreDirector = document.getElementById("nombreDirector");
    const cargoDirector = document.getElementById("cargoDirector");
    const textoCabecera = document.getElementById("textoCabecera");
    const textoPie = document.getElementById("textoPie");
    const estadoParametro = document.getElementById("estadoParametro");

    const BASE_URL = "/api/parametros_certificados";

    // Mantendremos la lista en memoria para facilitar edición
    let listaParametros = [];

    // ================================
    // 2. Helpers
    // ================================
    function mostrarError(mensaje) {
        if (typeof swal !== "undefined") {
            swal("Error", mensaje, "error");
        } else {
            alert("Error: " + mensaje);
        }
    }

    function mostrarOk(mensaje) {
        if (typeof swal !== "undefined") {
            swal("Éxito", mensaje, "success");
        } else {
            alert(mensaje);
        }
    }

    // ================================
    // 3. Cargar lista de parámetros
    // ================================
    async function cargarParametros() {
        const q = (inputBuscador?.value || "").trim();
        const url = q
            ? `${BASE_URL}/?q=${encodeURIComponent(q)}`
            : `${BASE_URL}/`;

        try {
            const res = await fetch(url);
            if (!res.ok) {
                console.error("Error HTTP al cargar parámetros:", res.status);
                mostrarError("No se pudo cargar la lista de parámetros.");
                return;
            }

            const data = await res.json();

            if (!data.success) {
                mostrarError(data.message || "Error al cargar parámetros.");
                return;
            }

            const items = data.items || [];
            listaParametros = items;
            renderTabla(items);

        } catch (err) {
            console.error("Error cargando parámetros:", err);
            mostrarError("Error de comunicación con el servidor.");
        }
    }

    // ================================
    // 4. Render tabla
    // ================================
    function renderTabla(items) {
        tbody.innerHTML = "";

        if (!items.length) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center">
                        No hay parámetros registrados.
                    </td>
                </tr>
            `;
            return;
        }

        items.forEach((p) => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${p.id_parametro}</td>
                <td>${p.nombre_plantilla || ""}</td>
                <td>${p.nombre_organizacion || ""}</td>
                <td>${p.ciudad || ""}</td>
                <td>${p.nombre_director || "-"}</td>
                <td>
                    <span class="badge ${p.estado === "Activo" ? "bg-success" : "bg-secondary"}">
                        ${p.estado || ""}
                    </span>
                </td>
                <td>
                    <button class="btn btn-sm btn-warning me-1 btn-editar" data-id="${p.id_parametro}">
                        <i class="bi bi-pencil-square"></i>
                    </button>
                    <button class="btn btn-sm btn-danger btn-eliminar" data-id="${p.id_parametro}">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    }

    // ================================
    // 5. Crear parámetro (form principal)
    // ================================
    if (formCrear) {
        formCrear.addEventListener("submit", async (e) => {
            e.preventDefault();

            const payload = {
                nombre_plantilla: nombrePlantilla.value.trim(),
                nombre_organizacion: nombreOrganizacion.value.trim(),
                ciudad: ciudadOrganizacion.value.trim(),
                nombre_director: nombreDirector.value.trim(),
                cargo_director: cargoDirector.value.trim(),
                texto_cabecera: textoCabecera.value.trim(),
                texto_pie: textoPie.value.trim(),
                estado: estadoParametro.value || "Activo"
            };

            if (!payload.nombre_plantilla || !payload.nombre_organizacion) {
                return mostrarError("Debes diligenciar al menos plantilla y organización.");
            }

            try {
                const res = await fetch(`${BASE_URL}/`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });

                const data = await res.json();

                if (!data.success) {
                    return mostrarError(data.message || "No se pudo guardar el parámetro.");
                }

                mostrarOk("Parámetro registrado correctamente.");

                // Limpiar formulario
                formCrear.reset();
                estadoParametro.value = "Activo";

                // Recargar tabla
                cargarParametros();

            } catch (err) {
                console.error("Error creando parámetro:", err);
                mostrarError("Error de comunicación con el servidor.");
            }
        });
    }

    // ================================
    // 6. Editar (abrir modal)
    // ================================
    if (tbody) {
        tbody.addEventListener("click", (e) => {
            const btnEditar = e.target.closest(".btn-editar");
            const btnEliminar = e.target.closest(".btn-eliminar");

            if (btnEditar) {
                const id = parseInt(btnEditar.dataset.id, 10);
                abrirModalEdicion(id);
            } else if (btnEliminar) {
                const id = parseInt(btnEliminar.dataset.id, 10);
                confirmarEliminar(id);
            }
        });
    }

    function abrirModalEdicion(id) {
        const param = listaParametros.find(p => Number(p.id_parametro) === Number(id));
        if (!param) {
            mostrarError("No se encontró el parámetro en memoria.");
            return;
        }

        idParametroModal.value = param.id_parametro;
        nombrePlantillaModal.value = param.nombre_plantilla || "";
        nombreOrganizacionModal.value = param.nombre_organizacion || "";
        ciudadOrganizacionModal.value = param.ciudad || "";
        nombreDirectorModal.value = param.nombre_director || "";
        cargoDirectorModal.value = param.cargo_director || "";
        textoCabeceraModal.value = param.texto_cabecera || "";
        textoPieModal.value = param.texto_pie || "";
        estadoParametroModal.value = param.estado || "Activo";

        if (modalActualizar) {
            modalActualizar.show();
        }
    }

    // ================================
    // 7. Actualizar (submit modal)
    // ================================
    if (formActualizar) {
        formActualizar.addEventListener("submit", async (e) => {
            e.preventDefault();

            const id = idParametroModal.value;
            if (!id) {
                return mostrarError("ID de parámetro no válido.");
            }

            const payload = {
                nombre_plantilla: nombrePlantillaModal.value.trim(),
                nombre_organizacion: nombreOrganizacionModal.value.trim(),
                ciudad: ciudadOrganizacionModal.value.trim(),
                nombre_director: nombreDirectorModal.value.trim(),
                cargo_director: cargoDirectorModal.value.trim(),
                texto_cabecera: textoCabeceraModal.value.trim(),
                texto_pie: textoPieModal.value.trim(),
                estado: estadoParametroModal.value || "Activo"
            };

            if (!payload.nombre_plantilla || !payload.nombre_organizacion) {
                return mostrarError("Debes diligenciar al menos plantilla y organización.");
            }

            try {
                const res = await fetch(`${BASE_URL}/${id}`, {
                    method: "PUT",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });

                const data = await res.json();

                if (!data.success) {
                    return mostrarError(data.message || "No se pudo actualizar el parámetro.");
                }

                mostrarOk("Parámetro actualizado correctamente.");

                if (modalActualizar) {
                    modalActualizar.hide();
                }

                // Recargar lista
                cargarParametros();

            } catch (err) {
                console.error("Error actualizando parámetro:", err);
                mostrarError("Error de comunicación con el servidor.");
            }
        });
    }

    // ================================
    // 8. Eliminar parámetro
    // ================================
    function confirmarEliminar(id) {
        if (typeof swal !== "undefined") {
            swal({
                title: "¿Eliminar parámetro?",
                text: "Esta acción no se puede deshacer.",
                icon: "warning",
                buttons: true,
                dangerMode: true
            }).then((willDelete) => {
                if (willDelete) {
                    eliminarParametro(id);
                }
            });
        } else {
            const ok = confirm("¿Eliminar parámetro?");
            if (ok) eliminarParametro(id);
        }
    }

    async function eliminarParametro(id) {
        try {
            const res = await fetch(`${BASE_URL}/${id}`, {
                method: "DELETE"
            });

            const data = await res.json();

            if (!data.success) {
                return mostrarError(data.message || "No se pudo eliminar el parámetro.");
            }

            mostrarOk("Parámetro eliminado correctamente.");
            cargarParametros();

        } catch (err) {
            console.error("Error eliminando parámetro:", err);
            mostrarError("Error de comunicación con el servidor.");
        }
    }

    // ================================
    // 9. Buscador
    // ================================
    if (inputBuscador) {
        inputBuscador.addEventListener("input", () => {
            // Puedes poner un pequeño delay si quieres, pero así también funciona
            cargarParametros();
        });
    }

    // ================================
    // 10. Carga inicial
    // ================================
    cargarParametros();
});
