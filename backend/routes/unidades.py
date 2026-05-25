from flask import Blueprint, jsonify, session
from db import get_db_connection
from mysql.connector import Error
from utils.bitacora import registrar_bitacora
from psycopg2.extras import RealDictCursor

unidades_bp = Blueprint('unidades_bp', __name__, url_prefix='/api/unidades')

# ================================
# LISTAR TODAS LAS UNIDADES
# ================================
@unidades_bp.route('/', methods=['GET'])
def listar_unidades():
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'Sesión expirada'}), 401

    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT id_unidad, nombre, abreviatura, factor_kg, estado
            FROM unidades_medida
            ORDER BY id_unidad ASC
        """)

        unidades = cursor.fetchall()
        return jsonify(unidades)

    except Error as e:
        print("Error listar_unidades:", e)
        return jsonify({'success': False, 'message': str(e)}), 500

    finally:
        cursor.close()
        conn.close()


# ================================
# LISTAR SOLO ACTIVAS (para productos)
# ================================
@unidades_bp.route('/activas', methods=['GET'])
def listar_unidades_activas():
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'Sesión expirada'}), 401

    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT id_unidad, nombre, abreviatura, factor_kg
            FROM unidades_medida
            WHERE estado = 'Activo'
            ORDER BY nombre ASC
        """)

        unidades = cursor.fetchall()

        # -----------------------------
        # Bitácora (consulta)
        # -----------------------------
        id_usuario = session.get("id_usuario")
        if id_usuario:
            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="UNIDADES",
                accion="CONSULTAR",
                descripcion=f"Consultó unidades activas (total={len(unidades)})",
                tabla_afectada="unidades_medida",
                id_registro=None
            )
            conn.commit()

        return jsonify(unidades)

    except Error as e:
        print("Error listar_unidades_activas:", e)
        return jsonify({'success': False, 'message': str(e)}), 500

    finally:
        cursor.close()
        conn.close()


# ================================
# DESACTIVAR UNIDAD
# ================================
@unidades_bp.route('/desactivar/<int:id_unidad>', methods=['PUT'])
def desactivar_unidad(id_unidad):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            UPDATE unidades_medida
            SET estado='Inactivo'
            WHERE id_unidad = %s
        """, (id_unidad,))

        conn.commit()

        id_usuario = session.get("id_usuario")
        if id_usuario:
            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="UNIDADES",
                accion="ACTUALIZAR",
                descripcion=f"Desactivó unidad de medida id={id_unidad}",
                tabla_afectada="unidades_medida",
                id_registro=id_unidad
            )
            conn.commit()

        return jsonify({"success": True, "message": "Unidad desactivada correctamente"})

    except Error as e:
        print("Error desactivar_unidad:", e)
        return jsonify({"success": False, "message": str(e)})

    finally:
        cursor.close()
        conn.close()


# ================================
# ACTIVAR UNIDAD
# ================================
@unidades_bp.route('/activar/<int:id_unidad>', methods=['PUT'])
def activar_unidad(id_unidad):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            UPDATE unidades_medida
            SET estado='Activo'
            WHERE id_unidad = %s
        """, (id_unidad,))

        conn.commit()

        id_usuario = session.get("id_usuario")
        if id_usuario:
            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="UNIDADES",
                accion="ACTUALIZAR",
                descripcion=f"Activó unidad de medida id={id_unidad}",
                tabla_afectada="unidades_medida",
                id_registro=id_unidad
            )
            conn.commit()

        return jsonify({"success": True, "message": "Unidad activada correctamente"})

    except Error as e:
        print("Error activar_unidad:", e)
        return jsonify({"success": False, "message": str(e)})

    finally:
        cursor.close()
        conn.close()
