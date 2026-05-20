document.addEventListener("DOMContentLoaded", () => {
    cargarRoles();
    cargarUsuarios();

    document.getElementById("formUsuario").addEventListener("submit", crearUsuario);
});

// ================================
// MOSTRAR / OCULTAR CONTRASEÑA
// ================================
document.addEventListener("click", function (e) {
    if (e.target.classList.contains("toggle-pass")) {
        const inputID = e.target.getAttribute("data-target");
        const input = document.getElementById(inputID);

        if (input.type === "password") {
            input.type = "text";
            e.target.classList.remove("fa-eye");
            e.target.classList.add("fa-eye-slash");
        } else {
            input.type = "password";
            e.target.classList.remove("fa-eye-slash");
            e.target.classList.add("fa-eye");
        }
    }
});

// ================================
// CARGAR ROLES
// ================================
function cargarRoles() {
    fetch("/api/usuarios/roles")
        .then(res => res.json())
        .then(data => {
            const select = document.getElementById("rol");
            select.innerHTML = "";

            if (data.length === 0) {
                select.innerHTML = "<option value=''>No hay roles disponibles</option>";
                return;
            }

            data.forEach(rol => {
                const option = document.createElement("option");
                option.value = rol.id_rol;
                option.textContent = rol.nombre;
                select.appendChild(option);
            });
        })
        .catch(err => console.error("Error cargando roles:", err));
}

// ================================
// VALIDACIONES
// ================================
function validarCorreo(correo) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(correo);
}

function validarPassword(pass) {
    const mayus = /[A-Z]/;
    const minus = /[a-z]/;
    const numero = /[0-9]/;
    const especial = /[@$!%*?&#]/;

    return pass.length >= 8 && mayus.test(pass) && minus.test(pass) && numero.test(pass) && especial.test(pass);
}

// ================================
// CREAR USUARIO
// ================================
function crearUsuario(e) {
    e.preventDefault();

    const nombre = document.getElementById("nombreUsuario").value.trim();
    const correo = document.getElementById("correo").value.trim();
    const password = document.getElementById("password").value;
    const pass2 = document.getElementById("confirmPassword").value;
    const rol = document.getElementById("rol").value;

    if (!validarCorreo(correo)) return swal("Correo inválido", "Introduce un correo electrónico válido.", "error");
    if (!validarPassword(password)) return swal("Contraseña débil", "Debe contener mínimo 8 caracteres, mayúscula, minúscula, número y un símbolo especial.", "warning");
    if (password !== pass2) return swal("Las contraseñas no coinciden", "Verifica los campos.", "error");

    fetch("/api/usuarios/crear", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            nombre_completo: nombre,
            correo: correo,
            contrasena: password,
            telefono: "",
            rol_id: rol
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) return swal("Error", data.error, "error");
        swal("Éxito", "Usuario creado correctamente.", "success");
        document.getElementById("formUsuario").reset();
        setTimeout(cargarUsuarios, 200);

        cargarUsuarios();

    })
    .catch(err => console.error("Error al crear usuario:", err));
}

// ================================
// CARGAR USUARIOS
// ================================
function cargarUsuarios() {
    fetch("/api/usuarios/")
        .then(res => res.json())
        .then(data => {
            const cont = document.getElementById("listaUsuarios");
            cont.innerHTML = "";

            data.forEach(u => {
                const card = document.createElement("div");
                card.classList.add("col-md-4");

                const estadoActivo = u.estado === "Activo";

                card.innerHTML = `
                    <div class="card shadow-sm mb-3">
                        <div class="card-body">
                            <h5>${u.nombre_completo}</h5>
                            <p><strong>Correo:</strong> ${u.correo}</p>
                            <p><strong>Rol:</strong> ${u.rol}</p>
                            <p><strong>Estado:</strong> 
                                <span class="badge ${estadoActivo ? "bg-success" : "bg-danger"}">
                                    ${estadoActivo ? "Activo" : "Inactivo"}
                                </span>
                            </p>
                            <button class="btn ${estadoActivo ? "btn-danger" : "btn-success"} w-100"
                                onclick="cambiarEstado(${u.id_usuario}, '${u.estado}')">
                                ${estadoActivo ? "Desactivar" : "Activar"}
                            </button>
                            <button class="btn btn-success w-100 mt-2"
                                onclick="abrirModalEditar(${u.id_usuario})">
                                Editar
                            </button>
                        </div>
                    </div>
                `;

                cont.appendChild(card);
            });
        })
        .catch(err => console.error("Error cargando usuarios:", err));
}

// ================================
// CAMBIAR ESTADO DE USUARIO
// ================================
function cambiarEstado(id, estadoActual) {
    const nuevoEstado = estadoActual === "Activo" ? "Inactivo" : "Activo";

    fetch(`/api/usuarios/estado/${id}/${nuevoEstado}`, { method: "PUT" })
        .then(res => res.json())
        .then(data => cargarUsuarios())
        .catch(err => console.error(err));
}

// ================================
// ABRIR MODAL EDITAR USUARIO
// ================================
function abrirModalEditar(id) {
    fetch("/api/usuarios/roles")
        .then(res => res.json())
        .then(roles => {
            const selectRol = document.getElementById("editarRol");
            selectRol.innerHTML = "";
            roles.forEach(r => {
                const option = document.createElement("option");
                option.value = r.id_rol;
                option.textContent = r.nombre;
                selectRol.appendChild(option);
            });
            return fetch("/api/usuarios/");
        })
        .then(res => res.json())
        .then(data => {
            const usuario = data.find(u => u.id_usuario === id);
            if (!usuario) return;

            document.getElementById("editarIdUsuario").value = usuario.id_usuario;
            document.getElementById("editarNombreUsuario").value = usuario.nombre_completo;
            document.getElementById("editarTelefono").value = usuario.telefono || "";
            document.getElementById("editarCorreo").value = usuario.correo;
            document.getElementById("editarPassword").value = "";
            document.getElementById("editarConfirmPassword").value = "";
            document.getElementById("editarRol").value = usuario.rol_id;

            new bootstrap.Modal(document.getElementById("modalEditarUsuario")).show();
        })
        .catch(err => console.error(err));
}

// ================================
// SUBMIT DEL FORM DEL MODAL EDITAR
// ================================
document.getElementById("formEditarUsuario").addEventListener("submit", function(e) {
    e.preventDefault();

    const id = document.getElementById("editarIdUsuario").value;
    const nombre = document.getElementById("editarNombreUsuario").value.trim();
    const telefono = document.getElementById("editarTelefono").value.trim();
    const correo = document.getElementById("editarCorreo").value.trim();
    const password = document.getElementById("editarPassword").value;
    const pass2 = document.getElementById("editarConfirmPassword").value;
    const rol = document.getElementById("editarRol").value;

    if (!validarCorreo(correo)) return swal("Correo inválido", "Introduce un correo electrónico válido.", "error");
    if (password && !validarPassword(password)) return swal("Contraseña débil", "Debe contener mínimo 8 caracteres, mayúscula, minúscula, número y símbolo especial.", "warning");
    if (password && password !== pass2) return swal("Las contraseñas no coinciden", "Verifica los campos.", "error");

    fetch(`/api/usuarios/actualizar/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nombre_completo: nombre, correo, contrasena: password, telefono, rol_id: rol })
    })
    .then(res => res.json())
    .then(data => {
        if (!data.success) return swal("Error", data.message, "error");
        swal("Éxito", "Usuario actualizado correctamente.", "success");

        bootstrap.Modal.getInstance(document.getElementById("modalEditarUsuario")).hide();
        cargarUsuarios();
    })
    .catch(err => console.error(err));
});
