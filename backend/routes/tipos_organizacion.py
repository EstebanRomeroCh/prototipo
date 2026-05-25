from flask import Blueprint, request, jsonify, session
from database import get_db_connection
import pymysql
from utils.bitacora import registrar_bitacora
from psycopg2.extras import RealDictCursor


tipos_organizacion_bp = Blueprint(
    "tipos_organizacion_bp",
    __name__,
    url_prefix="/api/tipos_organizacion"
)

# =========================
# Helpers
# =========================
def fila_por_id(cursor, id_tipo):
    cursor.execute(
        """
        SELECT id_tipo_organizacion, nombre, descripcion, estado
        FROM tipos_organizacion
        WHERE id_tipo_organizacion = %s
        """,
        (id_tipo,)
    )
    return cursor.fetchone()

def existe_nombre(cursor, nombre, excluir_id=None):
    sql = """
        SELECT id_tipo_organizacion
        FROM tipos_organizacion
        WHERE LOWER(TRIM(nombre)) = LOWER(TRIM(%s))
    """
    params = [nombre]
    if excluir_id:
        sql += " AND id_tipo_organizacion <> %s"
        params.append(excluir_id)
    sql += " LIMIT 1"
    cursor.execute(sql, params)
    return cursor.fetchone() is not None


# =========================
# LISTAR (GET /api/tipos_organizacion/)
# =========================
@tipos_organizacion_bp.route("/", methods=["GET"])
def listar_tipos_organizacion():
    if "usuario" not in session:
        return jsonify({"success": False, "message": "Sesión expirada"}), 401

    estado = (request.args.get("estado", "Activo") or "").strip()

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        sql = """
            SELECT id_tipo_organizacion, nombre, descripcion, estado
            FROM tipos_organizacion
        """
        params = []
        if estado:
            sql += " WHERE estado = %s"
            params.append(estado)

        sql += " ORDER BY id_tipo_organizacion DESC"

        cursor.execute(sql, params)
        filas = cursor.fetchall() or []

        # -----------------------------
        # Bitácora (consulta)
        # -----------------------------
        id_usuario = session.get("id_usuario")
        if id_usuario:
            desc = f"Consultó tipos_organizacion (estado='{estado or 'TODOS'}', total={len(filas)})"
            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="TIPOS_ORGANIZACION",
                accion="CONSULTAR",
                descripcion=desc,
                tabla_afectada="tipos_organizacion",
                id_registro=None
            )
            conn.commit()

        return jsonify({"success": True, "items": filas})

    except Exception as e:
        print("Error listar_tipos_organizacion:", e)
        return jsonify({"success": False, "message": "Error al listar tipos de organización"}), 500

    finally:
        cursor.close()
        conn.close()


# =========================
# CREAR (POST /api/tipos_organizacion/)
# =========================
@tipos_organizacion_bp.route("/", methods=["POST"])
def crear_tipo_organizacion():
    if "usuario" not in session:
        return jsonify({"success": False, "message": "Sesión expirada"}), 401

    data = request.get_json(silent=True) or {}
    nombre = (data.get("nombre") or "").strip()
    descripcion = (data.get("descripcion") or "").strip()

    if not nombre:
        return jsonify({"success": False, "message": "El nombre del tipo de organización es obligatorio."}), 400

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Duplicado por nombre (ignora mayúsculas/espacios)
        if existe_nombre(cursor, nombre):
            return jsonify({"success": False, "message": "Ya existe un tipo de organización con ese nombre."}), 400

        cursor.execute(
            """
            INSERT INTO tipos_organizacion (nombre, descripcion, estado)
            VALUES (%s, %s, 'Activo')
            """,
            (nombre, descripcion)
        )
        conn.commit()
        nuevo_id = cursor.lastrowid

        # -----------------------------
        # Bitácora (crear)
        # -----------------------------
        id_usuario = session.get("id_usuario")
        if id_usuario:
            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="TIPOS_ORGANIZACION",
                accion="CREAR",
                descripcion=f"Creó tipo_organizacion id={nuevo_id} nombre='{nombre}'",
                tabla_afectada="tipos_organizacion",
                id_registro=nuevo_id
            )
            conn.commit()

        return jsonify({
            "success": True,
            "message": "Tipo de organización creado correctamente.",
            "id_tipo_organizacion": nuevo_id
        }), 201

    except Exception as e:
        conn.rollback()
        print("Error crear_tipo_organizacion:", e)
        return jsonify({"success": False, "message": "Error al crear el tipo de organización."}), 500

    finally:
        cursor.close()
        conn.close()


# =========================
# ACTUALIZAR (PUT /api/tipos_organizacion/<id>)
# =========================
@tipos_organizacion_bp.route("/<int:id_tipo>", methods=["PUT"])
def actualizar_tipo_organizacion(id_tipo):
    if "usuario" not in session:
        return jsonify({"success": False, "message": "Sesión expirada"}), 401

    data = request.get_json(silent=True) or {}
    nombre = (data.get("nombre") or "").strip()
    descripcion = (data.get("descripcion") or "").strip()

    if not nombre:
        return jsonify({"success": False, "message": "El nombre del tipo de organización es obligatorio."}), 400

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        fila = fila_por_id(cursor, id_tipo)
        if not fila:
            return jsonify({"success": False, "message": "El tipo de organización no existe."}), 404

        # Duplicado (excluyendo el mismo id)
        if existe_nombre(cursor, nombre, excluir_id=id_tipo):
            return jsonify({"success": False, "message": "Ya existe otro tipo de organización con ese nombre."}), 400

        cursor.execute(
            """
            UPDATE tipos_organizacion
            SET nombre = %s,
                descripcion = %s
            WHERE id_tipo_organizacion = %s
            """,
            (nombre, descripcion, id_tipo)
        )
        conn.commit()

        # -----------------------------
        # Bitácora (actualizar)
        # -----------------------------
        id_usuario = session.get("id_usuario")
        if id_usuario:
            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="TIPOS_ORGANIZACION",
                accion="ACTUALIZAR",
                descripcion=f"Actualizó tipo_organizacion id={id_tipo} nombre='{nombre}'",
                tabla_afectada="tipos_organizacion",
                id_registro=id_tipo
            )
            conn.commit()

        return jsonify({"success": True, "message": "Tipo de organización actualizado correctamente."})

    except Exception as e:
        conn.rollback()
        print("Error actualizar_tipo_organizacion:", e)
        return jsonify({"success": False, "message": "Error al actualizar el tipo de organización."}), 500

    finally:
        cursor.close()
        conn.close()


# =========================
# ELIMINAR (DELETE /api/tipos_organizacion/<id>)
#   -> marcamos como Inactivo
# =========================
@tipos_organizacion_bp.route("/<int:id_tipo>", methods=["DELETE"])
def eliminar_tipo_organizacion(id_tipo):
    if "usuario" not in session:
        return jsonify({"success": False, "message": "Sesión expirada"}), 401

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        fila = fila_por_id(cursor, id_tipo)
        if not fila:
            return jsonify({"success": False, "message": "El tipo de organización no existe."}), 404

        cursor.execute(
            """
            UPDATE tipos_organizacion
            SET estado = 'Inactivo'
            WHERE id_tipo_organizacion = %s
            """,
            (id_tipo,)
        )
        conn.commit()

        # -----------------------------
        # Bitácora (eliminar/inactivar)
        # -----------------------------
        id_usuario = session.get("id_usuario")
        if id_usuario:
            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="TIPOS_ORGANIZACION",
                accion="ELIMINAR",
                descripcion=f"Inactivó tipo_organizacion id={id_tipo} (antes estado='{fila.get('estado')}')",
                tabla_afectada="tipos_organizacion",
                id_registro=id_tipo
            )
            conn.commit()

        return jsonify({"success": True, "message": "Tipo de organización eliminado (marcado como Inactivo)."})

    except Exception as e:
        conn.rollback()
        print("Error eliminar_tipo_organizacion:", e)
        return jsonify({"success": False, "message": "Error al eliminar el tipo de organización."}), 500

    finally:
        cursor.close()
        conn.close()
