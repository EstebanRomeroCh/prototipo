from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash
from db import get_db_connection
import re
from utils.bitacora import registrar_bitacora

usuarios_bp = Blueprint('usuarios_bp', __name__, url_prefix='/api/usuarios')

# ====================================
# VALIDACIONES
# ====================================
def validar_correo(correo):
    patron = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(patron, correo) is not None

def validar_contrasena(contra):
    patron = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$'
    return re.match(patron, contra) is not None


# ====================================
# OBTENER ROLES
# ====================================
@usuarios_bp.route('/roles', methods=['GET'])
def obtener_roles():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id_rol, nombre FROM roles")
    roles = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(roles), 200


# ====================================
# CREAR USUARIO
# ====================================
@usuarios_bp.route('/crear', methods=['POST'])
def crear_usuario():
    data = request.json

    nombre_completo = data.get("nombre_completo")
    correo = data.get("correo")
    contrasena = data.get("contrasena")
    telefono = data.get("telefono")
    rol_id = data.get("rol_id")

    # Validaciones
    if not nombre_completo or not correo or not contrasena or not rol_id:
        return jsonify({"success": False, "message": "Todos los campos obligatorios deben completarse"}), 400

    if not validar_correo(correo):
        return jsonify({"success": False, "message": "Correo inválido"}), 400

    if not validar_contrasena(contrasena):
        return jsonify({
            "success": False,
            "message": "La contraseña debe tener mínimo 8 caracteres, incluyendo mayúscula, minúscula, número y símbolo."
        }), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Verificar si el correo ya existe
    cursor.execute("SELECT id_usuario FROM usuarios WHERE correo = %s", (correo,))
    if cursor.fetchone():
        return jsonify({"success": False, "message": "El correo ya está registrado"}), 409

    # Hashear contraseña
    hash_contra = generate_password_hash(contrasena)

    try:
        cursor.execute("""
            INSERT INTO usuarios (nombre_completo, correo, contrasena, telefono, rol_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (nombre_completo, correo, hash_contra, telefono, rol_id))

        nuevo_id = cursor.lastrowid
        conn.commit()

        # Bitácora
        id_usuario = session.get("id_usuario")
        if id_usuario:
            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="USUARIOS",
                accion="CREAR",
                descripcion=f"Creó usuario id={nuevo_id} correo={correo}",
                tabla_afectada="usuarios",
                id_registro=nuevo_id
            )
            conn.commit()

        return jsonify({"success": True, "message": "Usuario creado correctamente"}), 201

    except Exception as e:
        print("Error creando usuario:", e)
        return jsonify({"success": False, "message": "Error en el servidor"}), 500

    finally:
        cursor.close()
        conn.close()


# ====================================
# LISTAR USUARIOS
# ====================================
@usuarios_bp.route('/', methods=['GET'])
def listar_usuarios():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            u.id_usuario, u.nombre_completo, u.correo, u.telefono,
            u.estado, r.nombre AS rol, u.fecha_registro
        FROM usuarios u
        INNER JOIN roles r ON u.rol_id = r.id_rol
    """)

    usuarios = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(usuarios), 200



@usuarios_bp.route('/actualizar/<int:id>', methods=['PUT'])
def actualizar_usuario(id):
    data = request.json

    nombre_completo = data.get("nombre_completo")
    correo = data.get("correo")
    contrasena = data.get("contrasena")  # opcional, si no se cambia, dejar igual
    telefono = data.get("telefono")
    rol_id = data.get("rol_id")

    if not nombre_completo or not correo or not rol_id:
        return jsonify({"success": False, "message": "Campos obligatorios incompletos"}), 400

    if not validar_correo(correo):
        return jsonify({"success": False, "message": "Correo inválido"}), 400

    if contrasena and not validar_contrasena(contrasena):
        return jsonify({"success": False, "message": "Contraseña débil"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Verificar si el correo ya está registrado por otro usuario
    cursor.execute("SELECT id_usuario FROM usuarios WHERE correo = %s AND id_usuario != %s", (correo, id))
    if cursor.fetchone():
        return jsonify({"success": False, "message": "El correo ya está registrado por otro usuario"}), 409

    # Si hay contraseña nueva, hashearla
    hash_contra = generate_password_hash(contrasena) if contrasena else None

    try:
        if hash_contra:
            cursor.execute("""
                UPDATE usuarios
                SET nombre_completo=%s, correo=%s, contrasena=%s, telefono=%s, rol_id=%s
                WHERE id_usuario=%s
            """, (nombre_completo, correo, hash_contra, telefono, rol_id, id))
        else:
            cursor.execute("""
                UPDATE usuarios
                SET nombre_completo=%s, correo=%s, telefono=%s, rol_id=%s
                WHERE id_usuario=%s
            """, (nombre_completo, correo, telefono, rol_id, id))

        conn.commit()

        id_usuario = session.get("id_usuario")
        if id_usuario:
            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="USUARIOS",
                accion="ACTUALIZAR",
                descripcion=f"Actualizó usuario id={id} correo={correo}",
                tabla_afectada="usuarios",
                id_registro=id
            )
            conn.commit()


        return jsonify({"success": True, "message": "Usuario actualizado correctamente"}), 200

    except Exception as e:
        print("Error actualizando usuario:", e)
        return jsonify({"success": False, "message": "Error en el servidor"}), 500

    finally:
        cursor.close()
        conn.close()

# ====================================
# ACTIVAR / DESACTIVAR USUARIO
# ====================================
@usuarios_bp.route('/estado/<int:id>/<string:nuevo_estado>', methods=['PUT'])
def cambiar_estado_usuario(id, nuevo_estado):

    if nuevo_estado not in ["Activo", "Inactivo"]:
        return jsonify({"success": False, "message": "Estado inválido"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE usuarios SET estado = %s WHERE id_usuario = %s", 
                   (nuevo_estado, id))
    conn.commit()

    id_usuario = session.get("id_usuario")
    if id_usuario:
            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="USUARIOS",
                accion="ACTUALIZAR",
                descripcion=f"Cambió estado de usuario id={id} a {nuevo_estado}",
                tabla_afectada="usuarios",
                id_registro=id
            )
            conn.commit()

    cursor.close()
    conn.close()

    return jsonify({"success": True, "message": "Estado actualizado correctamente"})
