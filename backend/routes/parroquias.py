# routes/parroquias.py

from flask import Blueprint, render_template, session, redirect, url_for, jsonify, request
from database import get_db_connection
import pymysql
from utils.bitacora import registrar_bitacora

parroquias_bp = Blueprint(
    "parroquias_bp",
    __name__,
    url_prefix="/parroquias"
)

# =========================================
# VISTA HTML
# =========================================
@parroquias_bp.route("/", methods=["GET"])
def gestionar_parroquias():
    """
    Devuelve la plantilla parroquias.html.
    El JS se encargará de consumir las APIs para CRUD.
    """
    if "usuario" not in session:
        return redirect(url_for("index"))

    return render_template(
        "parroquias.html",
        usuario=session.get("usuario")
    )


# =========================================
# LISTA TIPOS DE ORGANIZACIÓN (combo)
# =========================================
@parroquias_bp.route("/api/tipos_organizacion", methods=["GET"])
def api_tipos_organizacion():
    if "usuario" not in session:
        return jsonify({"success": False, "message": "Sesión expirada"}), 401

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    try:
        cursor.execute("""
            SELECT 
                id_tipo_organizacion,
                nombre,
                descripcion
            FROM tipos_organizacion
            WHERE estado = 'Activo'
            ORDER BY nombre ASC
        """)
        rows = cursor.fetchall()

        return jsonify({
            "success": True,
            "items": rows
        })
    except Exception as e:
        print("Error api_tipos_organizacion:", e)
        return jsonify({
            "success": False,
            "message": "Error al obtener los tipos de organización"
        }), 500
    finally:
        cursor.close()
        conn.close()


# =========================================
# LISTA TIPOS DE DOCUMENTO (combo)
# =========================================
@parroquias_bp.route("/api/tipos_documento", methods=["GET"])
def api_tipos_documento():
    if "usuario" not in session:
        return jsonify({"success": False, "message": "Sesión expirada"}), 401

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    try:
        cursor.execute("""
            SELECT 
                id_tipo_doc,
                nombre,
                descripcion
            FROM tipo_documento
            WHERE estado = 'activo'
            ORDER BY nombre ASC
        """)
        rows = cursor.fetchall()

        return jsonify({
            "success": True,
            "items": rows
        })
    except Exception as e:
        print("Error api_tipos_documento:", e)
        return jsonify({
            "success": False,
            "message": "Error al obtener los tipos de documento"
        }), 500
    finally:
        cursor.close()
        conn.close()


# =========================================
# LISTAR PARROQUIAS
# =========================================
@parroquias_bp.route("/api/listar", methods=["GET"])
def api_listar_parroquias():
    """
    Lista parroquias.
    Parámetro opcional 'q' para buscar por nombre o documento.
    """
    if "usuario" not in session:
        return jsonify({"success": False, "message": "Sesión expirada"}), 401

    q = request.args.get("q", "").strip()

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

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
                p.id_parroquia,
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
                to_org.id_tipo_organizacion,
                to_org.nombre AS tipo_organizacion,
                td.id_tipo_doc,
                td.nombre AS tipo_documento
            FROM parroquias p
            JOIN tipos_organizacion to_org
                ON to_org.id_tipo_organizacion = p.id_tipo_organizacion
            JOIN tipo_documento td
                ON td.id_tipo_doc = p.tipo_doc_id
            {where_clause}
            ORDER BY p.id_parroquia DESC
        """
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        return jsonify({
            "success": True,
            "parroquias": rows
        })
    except Exception as e:
        print("Error api_listar_parroquias:", e)
        return jsonify({
            "success": False,
            "message": "Error al listar las parroquias"
        }), 500
    finally:
        cursor.close()
        conn.close()


# =========================================
# CREAR PARROQUIA
# =========================================
@parroquias_bp.route("/api/crear", methods=["POST"])
def api_crear_parroquia():
    if "usuario" not in session:
        return jsonify({"success": False, "message": "Sesión expirada"}), 401

    data = request.get_json(silent=True) or {}

    id_tipo_organizacion = data.get("id_tipo_organizacion")
    tipo_doc_id          = data.get("tipo_doc_id")
    nombre               = (data.get("nombre") or "").strip()
    nombre_encargado     = (data.get("nombre_encargado") or "").strip()
    numero_documento     = (data.get("numero_documento") or "").strip()
    telefono             = (data.get("telefono") or "").strip()
    direccion            = (data.get("direccion") or "").strip()
    correo               = (data.get("correo") or "").strip()
    familias_atendidas   = data.get("familias_atendidas") or 0
    departamento         = (data.get("departamento") or "").strip()
    municipio            = (data.get("municipio") or "").strip()

    # Validaciones mínimas
    if not nombre or not nombre_encargado or not numero_documento:
        return jsonify({
            "success": False,
            "message": "Nombre de parroquia, encargado y documento son obligatorios."
        }), 400

    if not id_tipo_organizacion or not tipo_doc_id:
        return jsonify({
            "success": False,
            "message": "Debe seleccionar tipo de organización y tipo de documento."
        }), 400

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    try:
        cursor.execute("""
            INSERT INTO parroquias (
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

        conn.commit()
        nuevo_id = cursor.lastrowid

        try:
            id_usuario = session.get("id_usuario")
            if id_usuario:
                registrar_bitacora(
                    cursor,
                    id_usuario=id_usuario,
                    modulo="PARROQUIAS",
                    accion="CREAR",
                    descripcion=f"Creó parroquia ID {nuevo_id} - {nombre}.",
                    tabla_afectada="parroquias",
                    id_registro=nuevo_id
                )
                conn.commit()
        except Exception as e:
            print("Bitácora (api_crear_parroquia) error:", e)

        return jsonify({
            "success": True,
            "message": "Parroquia creada correctamente.",
            "id_parroquia": nuevo_id
        }), 201
    except Exception as e:
        conn.rollback()
        print("Error api_crear_parroquia:", e)
        return jsonify({
            "success": False,
            "message": "Error al crear la parroquia."
        }), 500
    finally:
        cursor.close()
        conn.close()


# =========================================
# ACTUALIZAR PARROQUIA
# =========================================
@parroquias_bp.route("/api/<int:id_parroquia>", methods=["PUT"])
def api_actualizar_parroquia(id_parroquia):
    if "usuario" not in session:
        return jsonify({"success": False, "message": "Sesión expirada"}), 401

    data = request.get_json(silent=True) or {}

    id_tipo_organizacion = data.get("id_tipo_organizacion")
    tipo_doc_id          = data.get("tipo_doc_id")
    nombre               = (data.get("nombre") or "").strip()
    nombre_encargado     = (data.get("nombre_encargado") or "").strip()
    numero_documento     = (data.get("numero_documento") or "").strip()
    telefono             = (data.get("telefono") or "").strip()
    direccion            = (data.get("direccion") or "").strip()
    correo               = (data.get("correo") or "").strip()
    familias_atendidas   = data.get("familias_atendidas") or 0
    departamento         = (data.get("departamento") or "").strip()
    municipio            = (data.get("municipio") or "").strip()
    estado               = (data.get("estado") or "Activo").strip() or "Activo"

    if not nombre or not nombre_encargado or not numero_documento:
        return jsonify({
            "success": False,
            "message": "Nombre de parroquia, encargado y documento son obligatorios."
        }), 400

    if not id_tipo_organizacion or not tipo_doc_id:
        return jsonify({
            "success": False,
            "message": "Debe seleccionar tipo de organización y tipo de documento."
        }), 400

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    try:
        # Verificar que exista
        cursor.execute(
            "SELECT id_parroquia FROM parroquias WHERE id_parroquia = %s",
            (id_parroquia,)
        )
        existe = cursor.fetchone()
        if not existe:
            return jsonify({
                "success": False,
                "message": "La parroquia no existe."
            }), 404

        cursor.execute("""
            UPDATE parroquias
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
            WHERE id_parroquia       = %s
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
            id_parroquia
        ))

        conn.commit()

        try:
            id_usuario = session.get("id_usuario")
            if id_usuario:
                registrar_bitacora(
                    cursor,
                    id_usuario=id_usuario,
                    modulo="PARROQUIAS",
                    accion="ACTUALIZAR",
                    descripcion=f"Actualizó parroquia ID {id_parroquia} - {nombre}.",
                    tabla_afectada="parroquias",
                    id_registro=id_parroquia
                )
                conn.commit()
        except Exception as e:
            print("Bitácora (api_actualizar_parroquia) error:", e)

        return jsonify({
            "success": True,
            "message": "Parroquia actualizada correctamente."
        })
    except Exception as e:
        conn.rollback()
        print("Error api_actualizar_parroquia:", e)
        return jsonify({
            "success": False,
            "message": "Error al actualizar la parroquia."
        }), 500
    finally:
        cursor.close()
        conn.close()


# =========================================
# ELIMINAR (LÓGICO) PARROQUIA
# =========================================
@parroquias_bp.route("/api/<int:id_parroquia>", methods=["DELETE"])
def api_eliminar_parroquia(id_parroquia):
    """
    Eliminación lógica: estado = 'Inactivo'
    """
    if "usuario" not in session:
        return jsonify({"success": False, "message": "Sesión expirada"}), 401

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    try:
        cursor.execute(
            "SELECT id_parroquia FROM parroquias WHERE id_parroquia = %s",
            (id_parroquia,)
        )
        existe = cursor.fetchone()
        if not existe:
            return jsonify({
                "success": False,
                "message": "La parroquia no existe."
            }), 404

        cursor.execute("""
            UPDATE parroquias
            SET estado = 'Inactivo'
            WHERE id_parroquia = %s
        """, (id_parroquia,))

        conn.commit()

        try:
            id_usuario = session.get("id_usuario")
            if id_usuario:
                registrar_bitacora(
                    cursor,
                    id_usuario=id_usuario,
                    modulo="PARROQUIAS",
                    accion="ELIMINAR",
                    descripcion=f"Eliminó (lógico) parroquia ID {id_parroquia}.",
                    tabla_afectada="parroquias",
                    id_registro=id_parroquia
                )
                conn.commit()
        except Exception as e:
            print("Bitácora (api_eliminar_parroquia) error:", e)
            
        return jsonify({
            "success": True,
            "message": "Parroquia eliminada correctamente."
        })
    except Exception as e:
        conn.rollback()
        print("Error api_eliminar_parroquia:", e)
        return jsonify({
            "success": False,
            "message": "Error al eliminar la parroquia."
        }), 500
    finally:
        cursor.close()
        conn.close()
