// =============================
// CONFIGURACIÓN BASE
// =============================
const API_DONANTES = `${window.location.origin}/api/donantes`;

const formDonante = document.getElementById('formDonante');
const tablaDonantes = document.getElementById('tablaDonantes').querySelector('tbody');
const selectTipoDonante = document.getElementById('tipoDonante');
const selectTipoDocumento = document.getElementById('tipoDocumento');
let editandoId = null;

// =============================
// CARGAR TIPOS DE DONANTE
// =============================
async function cargarTiposDonante() {
    try {
        const res = await fetch(`${API_DONANTES}/tipos`);
        if (!res.ok) throw new Error('No se pudo obtener los tipos de donante');

        const tipos = await res.json();
        console.log("Tipos de donante:", tipos); // <- Para depuración

        selectTipoDonante.innerHTML = '<option value="">Seleccione un tipo...</option>';
        tipos.forEach(tipo => {
            const option = document.createElement('option');
            option.value = tipo.id_tipo;
            option.textContent = tipo.nombre;
            selectTipoDonante.appendChild(option);
        });
    } catch (error) {
        console.error("Error cargarTiposDonante:", error);
        Swal.fire('Error', 'No se pudieron cargar los tipos de donante', 'error');
    }
}

// =============================
// CARGAR TIPOS DE DOCUMENTO
// =============================
async function cargarTiposDocumento() {
    try {
        const res = await fetch(`${API_DONANTES}/tipos_documento`);
        if (!res.ok) throw new Error('No se pudo obtener los tipos de documento');

        const tipos = await res.json();
        console.log("Tipos de documento:", tipos); // <- Para depuración

        selectTipoDocumento.innerHTML = '<option value="">Seleccione un tipo de documento...</option>';
        tipos.forEach(tipo => {
            const option = document.createElement('option');
            option.value = tipo.id_tipo_doc;
            option.textContent = tipo.nombre;
            selectTipoDocumento.appendChild(option);
        });
    } catch (error) {
        console.error("Error cargarTiposDocumento:", error);
        Swal.fire('Error', 'No se pudieron cargar los tipos de documento', 'error');
    }
}

// =============================
// CARGAR LISTA DE DONANTES
// =============================
async function cargarDonantes() {
    try {
        const res = await fetch(`${API_DONANTES}/`);
        if (!res.ok) throw new Error('No se pudieron cargar los donantes');

        const donantes = await res.json();
        tablaDonantes.innerHTML = '';

        donantes.forEach(d => {
    // Si es un array, conviértelo en objeto
    const donante = Array.isArray(d)
        ? {
            id_donante: d[0],
            nombre: d[1],
            tipo_documento: d[2],
            numero_documento: d[3],
            tipo_id: d[4],
            tipo_nombre: d[5],
            correo: d[6],
            telefono: d[7],
            direccion: d[8],
            estado: d[9]
        }
        : d;

    const row = document.createElement('tr');
    row.innerHTML = `
        <td>${donante.id_donante}</td>
        <td>${donante.nombre || ''}</td>
        <td>${donante.tipo_documento || 'Sin tipo'}</td>
        <td>${donante.numero_documento || ''}</td>
        <td>${donante.tipo_nombre || 'Sin tipo'}</td>
        <td>${donante.telefono || ''}</td>
        <td>${donante.correo || ''}</td>
        <td>${donante.direccion || ''}</td>
        <td>
            <button class="btn btn-sm btn-success me-2" onclick="abrirModalEditarDonante(${donante.id_donante})">
                <i class="bi bi-pencil-fill"></i>
            </button>
            <button class="btn btn-sm btn-danger" onclick="eliminarDonante(${donante.id_donante})">
                <i class="bi bi-trash-fill"></i>
            </button>
        </td>
    `;
    tablaDonantes.appendChild(row);
});
    } catch (error) {
        console.error(error);
        Swal.fire('Error', 'No se pudieron cargar los donantes', 'error');
    }
}

// =============================
// REGISTRAR NUEVO DONANTE
// =============================
formDonante.addEventListener('submit', async (e) => {
    e.preventDefault();

    const nombre = document.getElementById('nombreDonante').value.trim();
    const tipo_id = selectTipoDonante.value;
    const tipo_doc_id = selectTipoDocumento.value || null;
    const numero_documento = document.getElementById('numeroDocumento').value.trim() || null;
    const correo = document.getElementById('correo').value.trim() || null;
    const telefono = document.getElementById('telefono').value.trim() || null;
    const direccion = document.getElementById('direccion').value.trim() || null;

    if (!nombre || !tipo_id) {
        return Swal.fire('Error', 'Por favor complete los campos obligatorios', 'warning');
    }

    const data = { nombre, tipo_id, tipo_doc_id, numero_documento, correo, telefono, direccion };

    try {
        const url = `${API_DONANTES}/`;
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await res.json();
        if (res.ok) {
            Swal.fire({ icon: 'success', title: 'Donante registrado', timer: 1500, showConfirmButton: false });
            formDonante.reset();
            await cargarDonantes();
        } else {
            Swal.fire('Error', result.message || 'No se pudo guardar el donante', 'error');
        }
    } catch (error) {
        console.error(error);
        Swal.fire('Error', 'No se pudo guardar el donante', 'error');
    }
});

// =============================
// ABRIR MODAL PARA EDITAR DONANTE
// =============================
// =============================
// ABRIR MODAL PARA EDITAR DONANTE
// =============================
async function abrirModalEditarDonante(id) {
    try {
        const res = await fetch(`${API_DONANTES}/${id}`);
        if (!res.ok) throw new Error('No se pudo obtener el donante');
        let d = await res.json();

        // Si viene como array, convertirlo a objeto
        if (Array.isArray(d)) {
            d = {
                id_donante: d[0],
                nombre: d[1],
                tipo_documento: d[2],
                numero_documento: d[3],
                tipo_id: d[4],
                tipo_nombre: d[5],
                correo: d[6],
                telefono: d[7],
                direccion: d[8],
                estado: d[9]
            };
        }

        // Asignar valores a los inputs del modal
        document.getElementById('editandoIdModal').value = d.id_donante;
        document.getElementById('nombreDonanteModal').value = d.nombre || '';
        document.getElementById('numeroDocumentoModal').value = d.numero_documento || '';
        document.getElementById('telefonoModal').value = d.telefono || '';
        document.getElementById('correoModal').value = d.correo || '';
        document.getElementById('direccionModal').value = d.direccion || '';

        // Cargar tipos de documento
        const tiposDocRes = await fetch(`${API_DONANTES}/tipos_documento`);
        const tiposDocumento = await tiposDocRes.json();
        const tipoDocumentoModal = document.getElementById('tipoDocumentoModal');
        tipoDocumentoModal.innerHTML = '<option value="">Seleccione un tipo de documento...</option>';
        tiposDocumento.forEach(td => {
            const option = document.createElement('option');
            option.value = td.id_tipo_doc;
            option.textContent = td.nombre;
            tipoDocumentoModal.appendChild(option);
        });
        tipoDocumentoModal.value = d.tipo_doc_id || '';

        // Cargar tipos de donante
        const tiposRes = await fetch(`${API_DONANTES}/tipos`);
        const tipos = await tiposRes.json();
        const tipoDonanteModal = document.getElementById('tipoDonanteModal');
        tipoDonanteModal.innerHTML = '<option value="">Seleccione un tipo de donante...</option>';
        tipos.forEach(t => {
            const option = document.createElement('option');
            option.value = t.id_tipo;
            option.textContent = t.nombre;
            tipoDonanteModal.appendChild(option);
        });
        tipoDonanteModal.value = d.tipo_id || '';

        // Mostrar el modal (asegúrate de tenerlo en tu HTML con el id correcto)
        const modalElement = document.getElementById('modalActualizarDonante');
        const modal = new bootstrap.Modal(modalElement);
        modal.show();

    } catch (error) {
        console.error("Error abrirModalEditarDonante:", error);
        Swal.fire('Error', 'No se pudo cargar el donante', 'error');
    }
}


// =============================
// ACTUALIZAR DONANTE DESDE MODAL
// =============================
document.getElementById('formActualizarDonante').addEventListener('submit', async (e) => {
    e.preventDefault();

    const id = document.getElementById('editandoIdModal').value;
    const data = {
        nombre: document.getElementById('nombreDonanteModal').value.trim(),
        tipo_id: document.getElementById('tipoDonanteModal').value,
        tipo_doc_id: document.getElementById('tipoDocumentoModal').value || null,
        numero_documento: document.getElementById('numeroDocumentoModal').value.trim() || null,
        correo: document.getElementById('correoModal').value.trim() || null,
        telefono: document.getElementById('telefonoModal').value.trim() || null,
        direccion: document.getElementById('direccionModal').value.trim() || null
    };

    try {
        const res = await fetch(`${API_DONANTES}/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await res.json();
        if (res.ok) {
            Swal.fire({ icon: 'success', title: 'Donante actualizado', timer: 1500, showConfirmButton: false });
            bootstrap.Modal.getInstance(document.getElementById('modalActualizarDonante')).hide();
            await cargarDonantes();
        } else {
            Swal.fire('Error', result.message || 'No se pudo actualizar', 'error');
        }
    } catch (error) {
        console.error(error);
        Swal.fire('Error', 'No se pudo actualizar el donante', 'error');
    }
});

// =============================
// ELIMINAR DONANTE
// =============================
async function eliminarDonante(id) {
    Swal.fire({
        title: '¿Eliminar donante?',
        text: 'Esta acción no se puede deshacer.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    }).then(async (result) => {
        if (result.isConfirmed) {
            try {
                const res = await fetch(`${API_DONANTES}/${id}`, { method: 'DELETE' });
                if (res.ok) {
                    Swal.fire('Eliminado', 'El donante ha sido eliminado.', 'success');
                    await cargarDonantes();
                } else {
                    Swal.fire('Error', 'No se pudo eliminar el donante', 'error');
                }
            } catch (error) {
                console.error(error);
            }
        }
    });
}


fetch(API_DONANTES)
  .then(res => res.json())
  .then(data => {
    console.log('Datos recibidos del backend:', data);
  })
  .catch(err => console.error(err));

// =============================
// BUSCADOR DE DONANTES
// =============================
const buscador = document.getElementById('buscadorDonantes');
const tabla = document.getElementById('tablaDonantes').getElementsByTagName('tbody')[0];

buscador.addEventListener('keyup', function () {
  const texto = this.value.toLowerCase().trim();
  const filas = tabla.getElementsByTagName('tr');

  for (let fila of filas) {
    const contenidoFila = fila.textContent.toLowerCase();
    fila.style.display = contenidoFila.includes(texto) ? '' : 'none';
  }
});



document.addEventListener('DOMContentLoaded', async () => {
    await cargarTiposDonante();
    await cargarTiposDocumento();
    await cargarDonantes();
});
