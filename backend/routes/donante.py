from flask import Blueprint, request, jsonify, session
from db import get_db_connection
import pymysql
from utils.bitacora import registrar_bitacora
from psycopg2.extras import RealDictCursor

donantes_bp = Blueprint('donantes_bp', __name__, url_prefix='/api/donantes')

# ==============================
# OBTENER TIPOS DE DONANTE
# ==============================
# ==============================
# OBTENER TIPOS DE DONANTE
# ==============================
@donantes_bp.route('/tipos', methods=['GET'])
def obtener_tipos_donante():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT id_tipo, nombre FROM tipo_donante WHERE estado='Activo'")
        resultados = cursor.fetchall()
        # Convertir la lista de listas a una lista de diccionarios
        tipos = [{'id_tipo': fila[0], 'nombre': fila[1]} for fila in resultados]

        id_usuario = session.get("id_usuario")
        if id_usuario:
            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="DONANTES",
                accion="CONSULTAR",
                descripcion="Consultó tipos de donante.",
                tabla_afectada="tipo_donante",
                id_registro=None
            )
            conn.commit()

        return jsonify(tipos)
    except Exception as e:
        print("Error obtener_tipos_donante:", e)
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ==============================
# OBTENER TIPOS DE DOCUMENTO
# ==============================
@donantes_bp.route('/tipos_documento', methods=['GET'])
def obtener_tipos_documento():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT id_tipo_doc, nombre FROM tipo_documento WHERE estado='Activo'")
        resultados = cursor.fetchall()
        # Convertir la lista de listas a una lista de diccionarios
        tipos = [{'id_tipo_doc': fila[0], 'nombre': fila[1]} for fila in resultados]
        return jsonify(tipos)
    except Exception as e:
        print("Error obtener_tipos_documento:", e)
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ==============================
# LISTAR TODOS LOS DONANTES
# ==============================
@donantes_bp.route('/', methods=['GET'])
def listar_donantes():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT  
                d.id_donante,
                d.nombre,
                td.nombre AS tipo_documento,
                d.numero_documento,
                t.id_tipo,
                t.nombre AS tipo_nombre,
                d.correo,
                d.telefono,
                d.direccion,
                d.estado
            FROM donantes d
            LEFT JOIN tipo_documento td ON d.tipo_doc_id = td.id_tipo_doc
            LEFT JOIN tipo_donante t ON d.tipo_id = t.id_tipo
        """)
        donantes = cursor.fetchall()
        return jsonify(donantes)
    except Exception as e:
        print("Error listar_donantes:", e)
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ==============================
# CREAR NUEVO DONANTE
# ==============================
@donantes_bp.route('/', methods=['POST'])
def crear_donante():
    data = request.get_json()
    nombre = data.get('nombre')
    tipo_doc_id = data.get('tipo_doc_id')
    numero_documento = data.get('numero_documento', '')
    tipo_id = data.get('tipo_id')
    correo = data.get('correo', '')
    telefono = data.get('telefono', '')
    direccion = data.get('direccion', '')

    if not nombre or not tipo_id:
        return jsonify({'success': False, 'message': 'Nombre y tipo de donante son obligatorios'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT * FROM donantes 
            WHERE (numero_documento=%s AND numero_documento IS NOT NULL)
            OR (correo=%s AND correo IS NOT NULL)
        """, (numero_documento, correo))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'El donante ya está registrado'}), 409

        cursor.execute("""
            INSERT INTO donantes (nombre, tipo_doc_id, numero_documento, tipo_id, correo, telefono, direccion)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (nombre, tipo_doc_id, numero_documento, tipo_id, correo, telefono, direccion))
        nuevo_id = cursor.lastrowid

        id_usuario = session.get("id_usuario")
        if id_usuario:
            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="DONANTES",
                accion="CREAR",
                descripcion=f"Creó donante '{nombre}' (ID {nuevo_id}).",
                tabla_afectada="donantes",
                id_registro=nuevo_id
            )

        conn.commit()

        cursor.execute("""
            SELECT d.id_donante, d.nombre, td.nombre AS tipo_documento, 
                    d.numero_documento, t.id_tipo AS tipo_id, t.nombre AS tipo_nombre,
                    d.correo, d.telefono, d.direccion, d.estado
            FROM donantes d
            LEFT JOIN tipo_documento td ON d.tipo_doc_id = td.id_tipo_doc
            LEFT JOIN tipo_donante t ON d.tipo_id = t.id_tipo
            WHERE d.id_donante=%s
        """, (nuevo_id,))
        donante = cursor.fetchone()
        return jsonify({'success': True, 'donante': donante}), 201
    except Exception as e:
        conn.rollback()
        print("Error crear_donante:", e)
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ==============================
# ACTUALIZAR DONANTE
# ==============================
@donantes_bp.route('/<int:id_donante>', methods=['PUT'])
def actualizar_donante(id_donante):
    data = request.get_json()
    nombre = data.get('nombre')
    tipo_doc_id = data.get('tipo_doc_id')
    numero_documento = data.get('numero_documento', '')
    tipo_id = data.get('tipo_id')
    correo = data.get('correo', '')
    telefono = data.get('telefono', '')
    direccion = data.get('direccion', '')
    estado = data.get('estado', 'Activo')

    if not nombre or not tipo_id:
        return jsonify({'success': False, 'message': 'Nombre y tipo de donante son obligatorios'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            UPDATE donantes
            SET nombre=%s, tipo_doc_id=%s, numero_documento=%s, tipo_id=%s,
                correo=%s, telefono=%s, direccion=%s, estado=%s
            WHERE id_donante=%s
        """, (nombre, tipo_doc_id, numero_documento, tipo_id, correo, telefono, direccion, estado, id_donante))
        id_usuario = session.get("id_usuario")
        if id_usuario:
            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="DONANTES",
                accion="EDITAR",
                descripcion=f"Actualizó donante '{nombre}' (ID {id_donante}).",
                tabla_afectada="donantes",
                id_registro=id_donante
            )

        conn.commit()


        cursor.execute("""
            SELECT d.id_donante, d.nombre, td.nombre AS tipo_documento, 
                    d.numero_documento, t.id_tipo AS tipo_id, t.nombre AS tipo_nombre,
                    d.correo, d.telefono, d.direccion, d.estado
            FROM donantes d
            LEFT JOIN tipo_documento td ON d.tipo_doc_id = td.id_tipo_doc
            LEFT JOIN tipo_donante t ON d.tipo_id = t.id_tipo
            WHERE d.id_donante=%s
        """, (id_donante,))
        donante = cursor.fetchone()
        return jsonify({'success': True, 'donante': donante})
    except Exception as e:
        conn.rollback()
        print("Error actualizar_donante:", e)
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()




# ==============================
# OBTENER DONANTE POR ID
# ==============================
@donantes_bp.route('/<int:id_donante>', methods=['GET'])
def obtener_donante(id_donante):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT  
                d.id_donante,
                d.nombre,
                td.nombre AS tipo_documento,
                d.numero_documento,
                t.id_tipo,
                t.nombre AS tipo_nombre,
                d.correo,
                d.telefono,
                d.direccion,
                d.estado
            FROM donantes d
            LEFT JOIN tipo_documento td ON d.tipo_doc_id = td.id_tipo_doc
            LEFT JOIN tipo_donante t ON d.tipo_id = t.id_tipo
            WHERE d.id_donante = %s
        """, (id_donante,))
        donante = cursor.fetchone()

        if not donante:
            return jsonify({'success': False, 'message': 'Donante no encontrado'}), 404

        return jsonify(donante)
    except Exception as e:
        print("Error obtener_donante:", e)
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ==============================
# ELIMINAR DONANTE
# ==============================
@donantes_bp.route('/<int:id_donante>', methods=['DELETE'])
def eliminar_donante(id_donante):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("DELETE FROM donantes WHERE id_donante=%s", (id_donante,))
        id_usuario = session.get("id_usuario")
        if id_usuario:
            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="DONANTES",
                accion="ELIMINAR",
                descripcion=f"Eliminó donante ID {id_donante}.",
                tabla_afectada="donantes",
                id_registro=id_donante
            )
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        print("Error eliminar_donante:", e)
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ==============================
# BUSCAR DONANTES POR NÚMERO DE DOCUMENTO O NOMBRE
# ==============================
@donantes_bp.route('/buscar', methods=['GET'])
def buscar_donantes():
    q = request.args.get("q", "").strip()

    if not q:
        return jsonify([])

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT 
                id_donante,
                nombre,
                numero_documento
            FROM donantes
            WHERE estado='Activo'
            AND (numero_documento LIKE %s OR nombre LIKE %s)
            LIMIT 10
        """, (f"%{q}%", f"%{q}%"))
        filas = cursor.fetchall()

        # get_db_connection ya trae DictCursor, así que filas es lista de dicts
        return jsonify(filas)
    except Exception as e:
        print("Error buscar_donantes:", e)
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


