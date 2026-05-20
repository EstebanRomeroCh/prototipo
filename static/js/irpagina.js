document.addEventListener("DOMContentLoaded", () => {
    // Obtenemos el nombre de la página desde un atributo data-page en <body>
    const pagina = document.body.dataset.page;

    if (!pagina) return; // si no hay página definida, no hacemos nada

    fetch(`/api/verificar_rol/${pagina}`)
        .then(res => res.json())
        .then(data => {
            if (!data.success) {
                Swal.fire({
                    icon: 'error',
                    title: 'Acceso denegado',
                    text: data.message,
                    confirmButtonText: 'Aceptar',
                    allowOutsideClick: false
                }).then(() => {
                    // Redirige a la página principal si no tiene acceso
                    window.location.href = '/pagina_principal';
                });
            }
            // Si success == true, no hace nada y la página se muestra normalmente
        })
        .catch(err => {
            console.error("Error al verificar rol:", err);
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: 'No se pudo verificar el rol del usuario.',
                confirmButtonText: 'Aceptar'
            });
        });
});
