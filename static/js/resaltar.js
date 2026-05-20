function resaltar() {
    // Obtener la URL actual
    const currentPage = window.location.pathname.split('/').pop();

    // Mapeo de páginas a enlaces del sidebar
    const pageMap = {
        'menu_central': 0,
        //mantiene el sidebar marcado en las paginas hijas
        'menu_de_parroquias': 1,
        'crear_organizacion': 1,
        'gestion_parroquia': 1,
        'fundaciones': 1,

        'menu_producto': 2,
        //mantiene el sidebar marcado en las paginas hijas
        'categoria': 2,
        'subcategoria': 2,
        'producto': 2,
        'bodegas': 2,
        'unidades_medida': 2,

        'menu_donante': 3,
        //mantiene el sidebar marcado en las paginas hijas
        'tipo_donante': 3,
        'donante': 3,

        'pagina_principal': 4,
        'lista_donaciones': 5,
        'tabla_producto': 6,
        'movimiento_inv': 7,
        'lista_salidas': 8,

        

        'menu_gastos': 9,
        //mantiene el sidebar marcado en las paginas hijas
        'reporte_categoria_salidas': 9,
        'reporte_salidas_beneficiarios': 9,
        'reporte_salidas_listado': 9,

        'menu_reportes': 10,
        //mantiene el sidebar marcado en las paginas hijas
        'reportes': 10,
        'reporte_monetarias': 10,
        'reporte_generales': 10,
        'reporte_donantes': 10,
        'reporte_categorias': 10,
        'reporte_donantes': 10,
        'semaforos': 10,
        'certificacion_donante': 10,
        'acta_vencimiento': 10,

        'pag_confi': 11,
        //mantiene el sidebar marcado en las paginas hijas
        'permisos_asistentes': 11,
        'parametros_certificados': 11,
        'parametros': 11,
        'bitacora': 11,
        'configuracion': 11,
        'menu_manual': 11,
        'tecnico': 11,
        'instalacion': 11,
        'manual_usuario': 11

    };

    // Encontrar el índice del enlace activo
    const activeIndex = pageMap[currentPage];

    if (activeIndex !== undefined) {
        const sidebarLinks = document.querySelectorAll('.sidebar a');
        // Remover clase active de todos los enlaces
        sidebarLinks.forEach(link => link.classList.remove('active'));
        // Agregar clase active al enlace correspondiente
        sidebarLinks[activeIndex].classList.add('active');
    }
}
document.addEventListener('DOMContentLoaded', resaltar

);




function cerrar() {
    swal({
        title: "¿Estás seguro?",
        text: "Tu sesión se cerrará y deberás iniciar nuevamente.",
        icon: "warning",
        buttons: ["Cancelar", "Sí, cerrar sesión"],
        dangerMode: true,
    }).then((cerrarSesion) => {
        if (cerrarSesion) {
            fetch('/logout')
                .then(response => {
                    if (!response.ok) throw new Error("No se pudo cerrar la sesión");

                    // Mostrar mensaje de éxito con timer y sin botones
                    return swal({
                        title: "Sesión cerrada",
                        text: "Has cerrado sesión correctamente.",
                        icon: "success",
                        timer: 2000,
                        buttons: false
                    });
                })
                .then(() => {
                    // Redirigir solo después de que desaparezca el swal
                    window.location.href = '/';
                })
                .catch(err => {
                    console.error("Error al cerrar sesión:", err);
                    swal("Error", "No se pudo cerrar la sesión.", "error");
                });
        }
    });
}
