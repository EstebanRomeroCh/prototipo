// app.js (archivo único global)
document.addEventListener("DOMContentLoaded", () => {

    // Seleccionamos todos los links del sidebar que tengan data-role
    const links = document.querySelectorAll(".sidebar a[data-role]");

    links.forEach(link => {
        link.addEventListener("click", async (e) => {
            e.preventDefault(); // evitamos que la página se recargue

            const url = link.getAttribute("href");

            try {
                const res = await fetch(url, { method: "GET" });
                const data = await res.json();

                if (data.success === false) {
                    Swal.fire({
                        icon: 'error',
                        title: 'Oops...',
                        text: data.message,
                        confirmButtonText: 'Aceptar'
                    });
                } else {
                    // Redirige normalmente si tiene permiso
                    window.location.href = url;
                }

            } catch (error) {
                console.error(error);
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: 'No se pudo acceder a la página',
                    confirmButtonText: 'Aceptar'
                });
            }
        });
    });
});
