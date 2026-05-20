from functools import wraps
from flask import session, request, jsonify, redirect, url_for, flash

# Permisos por rol (AJUSTA nombres exactamente como los guardas en session['rol_nombre'])
ROLE_ACTIONS = {
    "Administrador": {"create", "read", "update", "delete"},
    "Asistente": {"create", "read", "update"},     
    "Auxiliar de Bodega": {"create", "read"},    
}

def has_permission(action: str) -> bool:
    rol = session.get("rol_nombre")
    return action in ROLE_ACTIONS.get(rol, set())

def _deny(message="No tienes permisos para esta acción"):
    # Si es API o se espera JSON, responde JSON; si es página, redirige con flash.
    wants_json = request.path.startswith("/api/") or request.is_json or \
                 "application/json" in (request.headers.get("Accept") or "")

    if wants_json:
        return jsonify({"success": False, "message": message}), 403

    flash(message, "danger")
    return redirect(url_for("rutas_dp.pagina_principal"))

def permission_required(action: str):
    """
    action: 'create' | 'read' | 'update' | 'delete'
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Debe estar logueado
            if not session.get("id_usuario") or not session.get("rol_nombre"):
                wants_json = request.path.startswith("/api/") or request.is_json or \
                             "application/json" in (request.headers.get("Accept") or "")
                if wants_json:
                    return jsonify({"success": False, "message": "Debes iniciar sesión"}), 401
                return redirect(url_for("rutas_dp.index"))

            # Debe tener permiso
            if not has_permission(action):
                return _deny("No tienes permisos para esta acción")

            return f(*args, **kwargs)
        return wrapper
    return decorator
