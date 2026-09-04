
from flask import Blueprint, jsonify, request, session
from database import get_db_connection
from utils.bitacora import registrar_bitacora
import pymysql
from psycopg2.extras import RealDictCursor

tipo_documento_bp = Blueprint('tipo_documento_bp', __name__, url_prefix='/api/tipo_documento')


def _norm(s: str) -> str:
    return (s or "").strip().lower()


# ------------------ OBTENER TODOS LOS TIPOS ------------------
@tipo_documento_bp.route('/', methods=['GET'])
def obtener_tipos_documento():
    if 'usuario' not in session:
        return jsonify({"success": False, "message": "Sesión expirada"}), 401

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT id_tipo_doc, nombre, descripcion, estado
            FROM tipo_documento
            WHERE estado= 'activo'
            ORDER BY nombre DESC
        """)
        tipos = cursor.fetchall() or []

        # Bitácora
        id_usuario = session.get("id_usuario")
        if id_usuario:
            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="TIPO_DOCUMENTO",
                accion="CONSULTAR",
                descripcion=f"Listó tipos de documento (total={len(tipos)})",
                tabla_afectada="tipo_documento",
                id_registro=None
            )
            conn.commit()

        return jsonify({"success": True, "items": tipos})

    except Exception as e:
        print("Error obtener_tipos_documento:", e)
        return jsonify({"success": False, "message": "Error al listar tipos de documento"}), 500

    finally:
        cursor.close()
        conn.close()


# ------------------ CREAR NUEVO TIPO ------------------
@tipo_documento_bp.route('/', methods=['POST'])
def agregar_tipo_documento():
    if 'usuario' not in session:
        return jsonify({"success": False, "message": "Sesión expirada"}), 401

    data = request.get_json(silent=True) or {}
    nombre = (data.get('nombre') or "").strip()
    descripcion = (data.get('descripcion') or "").strip()

    if not nombre:
        return jsonify({"success": False, "message": "El campo 'nombre' es obligatorio"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Duplicado exacto por nombre (ignorando mayúsculas/espacios)
        cursor.execute("""
            SELECT id_tipo_doc
            FROM tipo_documento
            WHERE LOWER(TRIM(nombre)) = %s
            LIMIT 1
        """, (_norm(nombre),))
        if cursor.fetchone():
            return jsonify({"success": False, "message": "Ya existe un tipo de documento con ese nombre"}), 400

        cursor.execute("""
            INSERT INTO tipo_documento (nombre, descripcion, estado)
            VALUES (%s, %s, 'activo')
        """, (nombre, descripcion))
        conn.commit()

        nuevo_id = cursor.lastrowid

        # Bitácora
        id_usuario = session.get("id_usuario")
        if id_usuario:
            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="TIPO_DOCUMENTO",
                accion="CREAR",
                descripcion=f"Creó tipo_documento id={nuevo_id} nombre='{nombre}'",
                tabla_afectada="tipo_documento",
                id_registro=nuevo_id
            )
            conn.commit()

        return jsonify({"success": True, "message": "Tipo de documento creado correctamente", "id_tipo_doc": nuevo_id}), 201

    except Exception as e:
        conn.rollback()
        print("Error agregar_tipo_documento:", e)
        return jsonify({"success": False, "message": "Error al crear el tipo de documento"}), 500

    finally:
        cursor.close()
        conn.close()


# ------------------ ACTUALIZAR TIPO ------------------
@tipo_documento_bp.route('/<int:id_tipo_doc>', methods=['PUT'])
def actualizar_tipo_documento(id_tipo_doc):
    if 'usuario' not in session:
        return jsonify({"success": False, "message": "Sesión expirada"}), 401

    data = request.get_json(silent=True) or {}
    nombre = (data.get('nombre') or "").strip()
    descripcion = (data.get('descripcion') or "").strip()
    estado = (data.get('estado') or "activo").strip() or "activo"  # opcional

    if not nombre:
        return jsonify({"success": False, "message": "El campo 'nombre' es obligatorio"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Existe?
        cursor.execute("SELECT id_tipo_doc FROM tipo_documento WHERE id_tipo_doc=%s", (id_tipo_doc,))
        if not cursor.fetchone():
            return jsonify({"success": False, "message": "Tipo de documento no encontrado"}), 404

        # Duplicado (otro registro)
        cursor.execute("""
            SELECT id_tipo_doc
            FROM tipo_documento
            WHERE LOWER(TRIM(nombre)) = %s
              AND id_tipo_doc <> %s
            LIMIT 1
        """, (_norm(nombre), id_tipo_doc))
        if cursor.fetchone():
            return jsonify({"success": False, "message": "Ya existe otro tipo de documento con ese nombre"}), 400

        cursor.execute("""
            UPDATE tipo_documento
            SET nombre=%s, descripcion=%s, estado=%s
            WHERE id_tipo_doc=%s
        """, (nombre, descripcion, estado, id_tipo_doc))
        conn.commit()

        # Bitácora
        id_usuario = session.get("id_usuario")
        if id_usuario:
            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="TIPO_DOCUMENTO",
                accion="ACTUALIZAR",
                descripcion=f"Actualizó tipo_documento id={id_tipo_doc} nombre='{nombre}' estado='{estado}'",
                tabla_afectada="tipo_documento",
                id_registro=id_tipo_doc
            )
            conn.commit()

        return jsonify({"success": True, "message": "Tipo de documento actualizado correctamente"})

    except Exception as e:
        conn.rollback()
        print("Error actualizar_tipo_documento:", e)
        return jsonify({"success": False, "message": "Error al actualizar el tipo de documento"}), 500

    finally:
        cursor.close()
        conn.close()


# ------------------ ELIMINAR TIPO (LÓGICO) ------------------
@tipo_documento_bp.route('/<int:id_tipo_doc>', methods=['DELETE'])
def eliminar_tipo_documento(id_tipo_doc):
    if 'usuario' not in session:
        return jsonify({"success": False, "message": "Sesión expirada"}), 401

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Existe?
        # En uso? (parroquias y fundaciones)
        cursor.execute(
            "SELECT 1 FROM parroquias WHERE tipo_doc_id=%s LIMIT 1",
            (id_tipo_doc,)
        )
        if cursor.fetchone():
            return jsonify({
                "success": False,
                "message": "No se puede inactivar: está asociado a parroquias"
            }), 400

        cursor.execute(
            "SELECT 1 FROM fundaciones WHERE tipo_doc_id=%s LIMIT 1",
            (id_tipo_doc,)
        )
        if cursor.fetchone():
            return jsonify({
                "success": False,
                "message": "No se puede inactivar: está asociado a fundaciones"
            }), 400

        # Eliminación lógica
        cursor.execute("""
            UPDATE tipo_documento
            SET estado='inactivo'
            WHERE id_tipo_doc=%s
        """, (id_tipo_doc,))
        conn.commit()

        # Bitácora
        id_usuario = session.get("id_usuario")
        if id_usuario:
            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="TIPO_DOCUMENTO",
                accion="ELIMINAR",
                descripcion=f"Inactivó tipo_documento id={id_tipo_doc}",
                tabla_afectada="tipo_documento",
                id_registro=id_tipo_doc
            )
            conn.commit()

        return jsonify({"success": True, "message": "Tipo de documento inactivado correctamente"})

    except Exception as e:
        conn.rollback()
        print("Error eliminar_tipo_documento:", e)
        return jsonify({"success": False, "message": "Error al eliminar/inactivar el tipo de documento"}), 500

    finally:
        cursor.close()
        conn.close()
