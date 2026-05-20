// ================================
// Alertas SweetAlert para Parámetros
// ================================

function mostrarExito(mensaje) {
    swal({
        title: 'Éxito',
        text: mensaje,
        icon: 'success',
        button: 'Aceptar'
    });
}

function mostrarError(mensaje) {
    swal({
        title: 'Error',
        text: mensaje,
        icon: 'error',
        button: 'Aceptar'
    });
}

function confirmarEliminacion(callback) {
    swal({
        title: '¿Está seguro?',
        text: 'El registro será desactivado y dejará de mostrarse en la lista.',
        icon: 'warning',
        buttons: ['Cancelar', 'Sí, desactivar'],
        dangerMode: true
    }).then((confirmado) => {
        if (confirmado && typeof callback === 'function') {
            callback();
        }
    });
}

function mostrarAdvertencia(mensaje) {
    swal({
        title: 'Advertencia',
        text: mensaje,
        icon: 'warning',
        button: 'Aceptar'
    });
}
