const TIEMPO_INACTIVIDAD = 10 * 60 * 1000; // 10 minutos
const TIEMPO_RESPUESTA = 30 * 1000;   // 30 segundos para responder el modal

let temporizadorInactividad;
let temporizadorRespuesta;

// Función que muestra el modal de aviso
function mostrarModalInactividad() {
  Swal.fire({
    title: "¿Sigues ahí?",
    text: "Tu sesión se cerrará automáticamente si no respondes en 30 segundos.",
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: "Sí, sigo activo",
    cancelButtonText: "No, cerrar sesión",
    allowOutsideClick: false,
    allowEscapeKey: false,
    timer: TIEMPO_RESPUESTA,
    timerProgressBar: true
  }).then((result) => {
    if (result.isConfirmed) {
      reiniciarTemporizador(); // Usuario activo
    } else {
      cerrarSesion(); // Usuario no activo o no respondió
    }
  });

  // Si el usuario no responde en TIEMPO_RESPUESTA, cerrar sesión automáticamente
  temporizadorRespuesta = setTimeout(cerrarSesion, TIEMPO_RESPUESTA);
}

// Función que cierra sesión y redirige al login
function cerrarSesion() {
  clearTimeout(temporizadorInactividad);
  clearTimeout(temporizadorRespuesta);
  // Aquí puedes llamar a tu ruta logout de Flask si quieres limpiar sesión real
  fetch('/logout')
    .finally(() => {
      console.log('Sesión cerrada por inactividad.');
      window.location.href = '/'; // Redirige al login
    });
}

// Reinicia el temporizador de inactividad
function reiniciarTemporizador() {
  clearTimeout(temporizadorInactividad);
  clearTimeout(temporizadorRespuesta);
  temporizadorInactividad = setTimeout(mostrarModalInactividad, TIEMPO_INACTIVIDAD);
}

// Detectar actividad del usuario
['mousemove', 'keydown', 'click'].forEach(evento => {
  document.addEventListener(evento, reiniciarTemporizador);
});

// Iniciar temporizador al cargar la página
window.onload = reiniciarTemporizador;

// Reiniciar sesión si hay actividad
function reiniciarSesion() {
  limpiarTemporizadores();
  iniciarControlSesion();
}


document.addEventListener("DOMContentLoaded", () => {
  const sidebar = document.querySelector(".sidebar");
  const btn = document.getElementById("btnToggleSidebar");

  // Creamos overlay
  const overlay = document.createElement("div");
  overlay.className = "sidebar-overlay";
  document.body.appendChild(overlay);

  function openSidebar(){
    sidebar.classList.add("open");
    overlay.classList.add("show");
  }

  function closeSidebar(){
    sidebar.classList.remove("open");
    overlay.classList.remove("show");
  }

  function toggleSidebar(){
    if (sidebar.classList.contains("open")) closeSidebar();
    else openSidebar();
  }

  btn?.addEventListener("click", toggleSidebar);
  overlay.addEventListener("click", closeSidebar);

  // Cerrar al hacer click en un link del menú (opcional, recomendado)
  sidebar.querySelectorAll("a").forEach(a => {
    a.addEventListener("click", () => {
      if (window.innerWidth <= 768) closeSidebar();
    });
  });

  // Si se pasa a escritorio, limpiar estados
  window.addEventListener("resize", () => {
    if (window.innerWidth > 768) closeSidebar();
  });
});
