# routes/fundaciones.py

from flask import Blueprint, render_template, session, redirect, url_for, jsonify, request
from database import get_db_connection
import pymysql
from utils.bitacora import registrar_bitacora
from psycopg2.extras import RealDictCursor

fundaciones_bp = Blueprint(
    "fundaciones_bp",
    __name__,
    url_prefix="/fundaciones"
)

# =========================================
# VISTA HTML
# =========================================
@fundaciones_bp.route("/", methods=["GET"])
def gestionar_fundaciones():
    if "usuario" not in session:
        return redirect(url_for("index"))

    return render_template(
        "fundaciones.html",  # <-- corrige tu plantilla
        usuario=session.get("usuario")
    )


# =========================================
# LISTA TIPOS DE ORGANIZACIÓN (combo)
# =========================================
@fundaciones_bp.route("/api/tipos_organizacion", methods=["GET"])
def api_tipos_organizacion():
    if "usuario" not in session:
        return jsonify({"success": False, "message": "Sesión expirada"}), 401

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute("""
            SELECT 
                id_tipo_organizacion,
                nombre,
                descripcion
            FROM tipos_organizacion
            WHERE LOWER(estado) = 'activo'
            ORDER BY nombre ASC
        """)
        return jsonify({"success": True, "items": cursor.fetchall()})
    except Exception as e:
        print("Error api_tipos_organizacion:", e)
        return jsonify({"success": False, "message": "Error al obtener los tipos de organización"}), 500
    finally:
        cursor.close()
        conn.close()


# =========================================
# LISTA TIPOS DE DOCUMENTO (combo)
# =========================================
@fundaciones_bp.route("/api/tipos_documento", methods=["GET"])
def api_tipos_documento():
    if "usuario" not in session:
        return jsonify({"success": False, "message": "Sesión expirada"}), 401

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute("""
            SELECT 
                id_tipo_doc,
                nombre,
                descripcion
            FROM tipo_documento
            WHERE LOWER(estado) = 'activo'
            ORDER BY nombre ASC
        """)
        return jsonify({"success": True, "items": cursor.fetchall()})
    except Exception as e:
        print("Error api_tipos_documento:", e)
        return jsonify({"success": False, "message": "Error al obtener los tipos de documento"}), 500
    finally:
        cursor.close()
        conn.close()


# =========================================
# LISTAR FUNDACIONES
# =========================================
@fundaciones_bp.route("/api/listar", methods=["GET"])
def api_listar_fundaciones():
    if "usuario" not in session:
        return jsonify({"success": False, "message": "Sesión expirada"}), 401

    q = (request.args.get("q") or "").strip()

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        filtros = ["p.estado = 'Activo'"]
        params = []

        if q:
            filtros.append("(p.nombre LIKE %s OR p.numero_documento LIKE %s)")
            like = f"%{q}%"
            params.extend([like, like])

        where_clause = "WHERE " + " AND ".join(filtros)

        sql = f"""
            SELECT
                p.id_fundaciones,
                p.id_tipo_organizacion,
                to_org.nombre AS tipo_organizacion,

                p.tipo_doc_id,
                td.nombre AS tipo_documento,

                p.nombre,
                p.nombre_encargado,
                p.numero_documento,
                p.telefono,
                p.direccion,
                p.correo,
                p.familias_atendidas,
                p.departamento,
                p.municipio,
                p.estado,
                p.fecha_registro
            FROM fundaciones p
            JOIN tipos_organizacion to_org
                ON to_org.id_tipo_organizacion = p.id_tipo_organizacion
            JOIN tipo_documento td
                ON td.id_tipo_doc = p.tipo_doc_id
            {where_clause}
            ORDER BY p.id_fundaciones DESC
        """
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        return jsonify({"success": True, "fundaciones": rows})
    except Exception as e:
        print("Error api_listar_fundaciones:", e)
        return jsonify({"success": False, "message": "Error al listar las fundaciones"}), 500
    finally:
        cursor.close()
        conn.close()


# =========================================
# OBTENER 1 FUNDACIÓN (OPCIONAL, útil para editar)
# =========================================
@fundaciones_bp.route("/api/<int:id_fundaciones>", methods=["GET"])
def api_obtener_fundacion(id_fundaciones):
    if "usuario" not in session:
        return jsonify({"success": False, "message": "Sesión expirada"}), 401

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute("""
            SELECT
                p.id_fundaciones,
                p.id_tipo_organizacion,
                p.tipo_doc_id,
                p.nombre,
                p.nombre_encargado,
                p.numero_documento,
                p.telefono,
                p.direccion,
                p.correo,
                p.familias_atendidas,
                p.departamento,
                p.municipio,
                p.estado,
                p.fecha_registro
            FROM fundaciones p
            WHERE p.id_fundaciones = %s
            LIMIT 1
        """, (id_fundaciones,))
        row = cursor.fetchone()

        if not row:
            return jsonify({"success": False, "message": "La fundación no existe."}), 404

        return jsonify({"success": True, "fundacion": row})
    except Exception as e:
        print("Error api_obtener_fundacion:", e)
        return jsonify({"success": False, "message": "Error al obtener la fundación"}), 500
    finally:
        cursor.close()
        conn.close()


# =========================================
# CREAR FUNDACIÓN
# =========================================
@fundaciones_bp.route("/api/crear", methods=["POST"])
def api_crear_fundacion():
    if "usuario" not in session:
        return jsonify({"success": False, "message": "Sesión expirada"}), 401

    data = request.get_json(silent=True) or {}

    id_tipo_organizacion = data.get("id_tipo_organizacion")
    tipo_doc_id          = data.get("tipo_doc_id")
    nombre               = (data.get("nombre") or "").strip()
    nombre_encargado     = (data.get("nombre_encargado") or "").strip()
    numero_documento     = (data.get("numero_documento") or "").strip()
    telefono             = (data.get("telefono") or "").strip() or None
    direccion            = (data.get("direccion") or "").strip() or None
    correo               = (data.get("correo") or "").strip() or None
    familias_atendidas   = data.get("familias_atendidas") or 0
    departamento         = (data.get("departamento") or "").strip() or None
    municipio            = (data.get("municipio") or "").strip() or None

    if not nombre or not nombre_encargado or not numero_documento:
        return jsonify({"success": False, "message": "Nombre, encargado y número de documento son obligatorios."}), 400

    if not id_tipo_organizacion or not tipo_doc_id:
        return jsonify({"success": False, "message": "Debe seleccionar tipo de organización y tipo de documento."}), 400

    try:
        familias_atendidas = int(familias_atendidas)
        if familias_atendidas < 0:
            raise ValueError()
    except Exception:
        return jsonify({"success": False, "message": "Familias atendidas debe ser un número válido (>= 0)."}), 400

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute("""
            INSERT INTO fundaciones(
                id_tipo_organizacion,
                tipo_doc_id,
                nombre,
                nombre_encargado,
                numero_documento,
                telefono,
                direccion,
                correo,
                familias_atendidas,
                departamento,
                municipio,
                estado
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Activo')
        """, (
            id_tipo_organizacion,
            tipo_doc_id,
            nombre,
            nombre_encargado,
            numero_documento,
            telefono,
            direccion,
            correo,
            familias_atendidas,
            departamento,
            municipio
        ))
        nuevo_id = cursor.lastrowid

        # BITÁCORA (crear)
        id_usuario = session.get("id_usuario")
        if id_usuario:
            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="FUNDACIONES",
                accion="CREAR",
                descripcion=f"Creó fundación '{nombre}' (ID {nuevo_id}).",
                tabla_afectada="fundaciones",
                id_registro=nuevo_id
            )
        conn.commit()
        return jsonify({
            "success": True,
            "message": "Fundación creada correctamente.",
            "id_fundaciones": cursor.lastrowid
        }), 201
    except Exception as e:
        conn.rollback()
        print("Error api_crear_fundacion:", e)
        return jsonify({"success": False, "message": "Error al crear la fundación."}), 500
    finally:
        cursor.close()
        conn.close()


# =========================================
# ACTUALIZAR FUNDACIÓN
# =========================================
@fundaciones_bp.route("/api/<int:id_fundaciones>", methods=["PUT"])
def api_actualizar_fundacion(id_fundaciones):
    if "usuario" not in session:
        return jsonify({"success": False, "message": "Sesión expirada"}), 401

    data = request.get_json(silent=True) or {}

    id_tipo_organizacion = data.get("id_tipo_organizacion")
    tipo_doc_id          = data.get("tipo_doc_id")
    nombre               = (data.get("nombre") or "").strip()
    nombre_encargado     = (data.get("nombre_encargado") or "").strip()
    numero_documento     = (data.get("numero_documento") or "").strip()
    telefono             = (data.get("telefono") or "").strip() or None
    direccion            = (data.get("direccion") or "").strip() or None
    correo               = (data.get("correo") or "").strip() or None
    familias_atendidas   = data.get("familias_atendidas") or 0
    departamento         = (data.get("departamento") or "").strip() or None
    municipio            = (data.get("municipio") or "").strip() or None
    estado               = (data.get("estado") or "Activo").strip() or "Activo"

    if estado not in ("Activo", "Inactivo"):
        estado = "Activo"

    if not nombre or not nombre_encargado or not numero_documento:
        return jsonify({"success": False, "message": "Nombre, encargado y número de documento son obligatorios."}), 400

    if not id_tipo_organizacion or not tipo_doc_id:
        return jsonify({"success": False, "message": "Debe seleccionar tipo de organización y tipo de documento."}), 400

    try:
        familias_atendidas = int(familias_atendidas)
        if familias_atendidas < 0:
            raise ValueError()
    except Exception:
        return jsonify({"success": False, "message": "Familias atendidas debe ser un número válido (>= 0)."}), 400

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute(
            "SELECT id_fundaciones FROM fundaciones WHERE id_fundaciones = %s",
            (id_fundaciones,)
        )
        if not cursor.fetchone():
            return jsonify({"success": False, "message": "La fundación no existe."}), 404

        cursor.execute("""
            UPDATE fundaciones
            SET id_tipo_organizacion = %s,
                tipo_doc_id          = %s,
                nombre               = %s,
                nombre_encargado     = %s,
                numero_documento     = %s,
                telefono             = %s,
                direccion            = %s,
                correo               = %s,
                familias_atendidas   = %s,
                departamento         = %s,
                municipio            = %s,
                estado               = %s
            WHERE id_fundaciones     = %s
        """, (
            id_tipo_organizacion,
            tipo_doc_id,
            nombre,
            nombre_encargado,
            numero_documento,
            telefono,
            direccion,
            correo,
            familias_atendidas,
            departamento,
            municipio,
            estado,
            id_fundaciones
        ))
        id_usuario = session.get("id_usuario")
        if id_usuario:
            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="FUNDACIONES",
                accion="EDITAR",
                descripcion=f"Actualizó fundación '{nombre}' (ID {id_fundaciones}).",
                tabla_afectada="fundaciones",
                id_registro=id_fundaciones
            )

        conn.commit()
        return jsonify({"success": True, "message": "Fundación actualizada correctamente."})
    except Exception as e:
        conn.rollback()
        print("Error api_actualizar_fundacion:", e)
        return jsonify({"success": False, "message": "Error al actualizar la fundación."}), 500
    finally:
        cursor.close()
        conn.close()


# =========================================
# ELIMINAR (LÓGICO) FUNDACIÓN
# =========================================
@fundaciones_bp.route("/api/<int:id_fundaciones>", methods=["DELETE"])
def api_eliminar_fundacion(id_fundaciones):
    if "usuario" not in session:
        return jsonify({"success": False, "message": "Sesión expirada"}), 401

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute(
            "SELECT id_fundaciones FROM fundaciones WHERE id_fundaciones = %s",
            (id_fundaciones,)
        )
        if not cursor.fetchone():
            return jsonify({"success": False, "message": "La fundación no existe."}), 404

        cursor.execute("""
            UPDATE fundaciones
            SET estado = 'Inactivo'
            WHERE id_fundaciones = %s
        """, (id_fundaciones,))
        id_usuario = session.get("id_usuario")
        if id_usuario:
            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="FUNDACIONES",
                accion="ANULAR",
                descripcion=f"Marcó como inactiva la fundación ID {id_fundaciones}.",
                tabla_afectada="fundaciones",
                id_registro=id_fundaciones
            )
        conn.commit()
        return jsonify({"success": True, "message": "Fundación eliminada correctamente."})
    except Exception as e:
        conn.rollback()
        print("Error api_eliminar_fundacion:", e)
        return jsonify({"success": False, "message": "Error al eliminar la fundación."}), 500
    finally:
        cursor.close()
        conn.close()
