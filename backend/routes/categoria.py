# routes/categorias.py
from flask import Blueprint, request, jsonify, session
from db import get_db_connection
import pymysql
from utils.bitacora import registrar_bitacora
categorias_bp = Blueprint('categorias_bp', __name__, url_prefix='/api/categorias')

# ==============================
# LISTAR TODAS LAS CATEGORIAS
# ==============================
@categorias_bp.route('/', methods=['GET'])
def listar_categorias():
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("SELECT * FROM categorias")
        categorias = cursor.fetchall()
        return jsonify(categorias)
    except Exception as e:
        print("Error listar_categorias:", e)
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ==============================
# OBTENER CATEGORIA POR ID
# ==============================
@categorias_bp.route('/<int:id_categoria>', methods=['GET'])
def obtener_categoria(id_categoria):
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("SELECT * FROM categorias WHERE id_categoria=%s", (id_categoria,))
        categoria = cursor.fetchone()
        if not categoria:
            return jsonify({'success': False, 'message': 'Categoría no encontrada'}), 404
        return jsonify(categoria)
    except Exception as e:
        print("Error obtener_categoria:", e)
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ==============================
# CREAR NUEVA CATEGORIA
# ==============================
# CREAR NUEVA CATEGORIA
@categorias_bp.route('/', methods=['POST'])
def crear_categoria():
    data = request.get_json()
    nombre = data.get('nombre')
    descripcion = data.get('descripcion', '')
    estado = data.get('estado', 'Activo')

    if not nombre:
        return jsonify({'success': False, 'message': 'El nombre es obligatorio'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)  # <-- DictCursor
    try:
        # Validar si ya existe
        cursor.execute("SELECT * FROM categorias WHERE nombre=%s", (nombre,))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'La categoría ya existe'}), 409

        cursor.execute(
            "INSERT INTO categorias (nombre, descripcion, estado) VALUES (%s, %s, %s)",
            (nombre, descripcion, estado)
        )
        id_usuario = session.get("id_usuario")
        if id_usuario:
            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="CATEGORIAS",
                accion="CREAR",
                descripcion=f"Creó la categoría '{nombre}' (estado={estado}).",
                tabla_afectada="categorias",
                id_registro=getattr(cursor, "lastrowid", None)
            )
        conn.commit()
        nuevo_id = cursor.lastrowid

        cursor.execute("SELECT * FROM categorias WHERE id_categoria=%s", (nuevo_id,))
        categoria = cursor.fetchone()  # Ahora sí es un dict
        return jsonify({'success': True, 'categoria': categoria}), 201
    except Exception as e:
        conn.rollback()
        print("Error crear_categoria:", e)
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ACTUALIZAR CATEGORIA
@categorias_bp.route('/<int:id_categoria>', methods=['PUT'])
def actualizar_categoria(id_categoria):
    data = request.get_json()
    nombre = data.get('nombre')
    descripcion = data.get('descripcion')
    estado = data.get('estado', 'Activo')

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)  # <-- DictCursor
    try:
        cursor.execute("SELECT * FROM categorias WHERE id_categoria=%s", (id_categoria,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'message': 'Categoría no encontrada'}), 404

        cursor.execute("""
            UPDATE categorias
            SET nombre=%s, descripcion=%s, estado=%s
            WHERE id_categoria=%s
        """, (nombre, descripcion, estado, id_categoria))
        id_usuario = session.get("id_usuario")
        if id_usuario:
            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="CATEGORIAS",
                accion="EDITAR",
                descripcion=f"Actualizó la categoría ID {id_categoria} (nombre='{nombre}', estado={estado}).",
                tabla_afectada="categorias",
                id_registro=id_categoria
            )
        conn.commit()

        cursor.execute("SELECT * FROM categorias WHERE id_categoria=%s", (id_categoria,))
        categoria = cursor.fetchone()  # <-- dict
        return jsonify({'success': True, 'categoria': categoria})
    except Exception as e:
        conn.rollback()
        print("Error actualizar_categoria:", e)
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ==============================
# ELIMINAR CATEGORIA
# ==============================
# ==============================
# ELIMINAR CATEGORIA
# ==============================
@categorias_bp.route('/<int:id_categoria>', methods=['DELETE'])
def eliminar_categoria(id_categoria):
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)  # <-- DictCursor
    try:
        # Revisar subcategorías asociadas
        cursor.execute("SELECT id_subcategoria FROM subcategorias WHERE id_categoria=%s", (id_categoria,))
        subcategorias = cursor.fetchall()
        if subcategorias:
            # Revisar si esas subcategorías tienen productos
            sub_ids = tuple([sub['id_subcategoria'] for sub in subcategorias])
            if sub_ids:  # prevenir error si hay solo una
                cursor.execute("""
                    SELECT id_producto FROM productos
                    WHERE id_subcategoria IN %s
                """, (sub_ids,))
                productos = cursor.fetchall()
                if productos:
                    return jsonify({
                        'success': False,
                        'message': 'No se puede eliminar la categoría porque tiene productos asociados a sus subcategorías'
                    }), 400

            return jsonify({
                'success': False,
                'message': 'No se puede eliminar la categoría porque tiene subcategorías asociadas'
            }), 400

        # Si no tiene dependencias, eliminar
        cursor.execute("DELETE FROM categorias WHERE id_categoria=%s", (id_categoria,))
        id_usuario = session.get("id_usuario")
        if id_usuario:
            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="CATEGORIAS",
                accion="ELIMINAR",
                descripcion=f"Eliminó la categoría ID {id_categoria}.",
                tabla_afectada="categorias",
                id_registro=id_categoria
            )
        conn.commit()
        return jsonify({'success': True, 'message': 'Categoría eliminada correctamente'})

    except Exception as e:
        conn.rollback()
        print("Error interno al eliminar la categoría:", e)
        return jsonify({'success': False, 'message': f'Error interno: {str(e)}'}), 500
    finally:
        cursor.close()
        conn.close()

