from flask import Blueprint, request, jsonify, session
from db import get_db_connection
from utils.bitacora import registrar_bitacora
from psycopg2.extras import RealDictCursor

subcategorias_bp = Blueprint('subcategorias_bp', __name__, url_prefix='/api/subcategorias')

# ==============================
# LISTAR TODAS LAS SUBCATEGORÍAS
# ==============================
@subcategorias_bp.route('/', methods=['GET'])
def listar_subcategorias():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)  # <- sin DictCursor
    try:
        cursor.execute("""
        SELECT
            s.id_subcategoria,
            s.nombre,
            s.descripcion,
            s.id_categoria,
            c.nombre AS categoria_nombre,
            s.estado
        FROM subcategorias s
        INNER JOIN categorias c
            ON s.id_categoria = c.id_categoria
    """)
        
        subcategorias = cursor.fetchall()  # Esto devuelve tuplas
        return jsonify(subcategorias)
    except Exception as e:
        print("Error listar_subcategorias:", e)
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ==============================
# OBTENER SUBCATEGORÍA POR ID
# ==============================
@subcategorias_bp.route('/<int:id_subcategoria>', methods=['GET'])
def obtener_subcategoria(id_subcategoria):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
        SELECT
            s.id_subcategoria,
            s.nombre,
            s.descripcion,
            s.id_categoria,
            c.nombre AS categoria_nombre,
            s.estado
        FROM subcategorias s
        INNER JOIN categorias c
            ON s.id_categoria = c.id_categoria
        WHERE s.id_subcategoria=%s
    """, (id_subcategoria,))
        
        subcategoria = cursor.fetchone()
        if not subcategoria:
            return jsonify({'success': False, 'message': 'Subcategoría no encontrada'}), 404
        return jsonify(subcategoria)  # Devuelve tupla
    except Exception as e:
        print("Error obtener_subcategoria:", e)
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ==============================
# CREAR SUBCATEGORÍA
# ==============================
@subcategorias_bp.route('/', methods=['POST'])
def crear_subcategoria():
    data = request.get_json()
    nombre = data.get('nombre')
    descripcion = data.get('descripcion', '')
    id_categoria = data.get('id_categoria')
    estado = data.get('estado', 'Activo')

    if not nombre or not id_categoria:
        return jsonify({'success': False, 'message': 'Nombre y categoría padre son obligatorios'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Validar duplicados exactos ignorando mayúsculas/minúsculas
        
        cursor.execute("SELECT nombre FROM subcategorias")
        
        nombres_existentes = [row['nombre'].lower() for row in cursor.fetchall()]
        
        if nombre.lower() in nombres_existentes:
            return jsonify({'success': False, 'message': f'Ya existe una subcategoría con ese nombre'}), 400
            
            cursor.execute("""
            INSERT INTO subcategorias (nombre, descripcion, id_categoria, estado)
            VALUES (%s, %s, %s, %s)
            RETURNING id_subcategoria
        """, (nombre, descripcion, id_categoria, estado))
        nuevo_id = cursor.fetchone()['id_subcategoria']
        conn.commit()


        id_usuario = session.get("id_usuario")
        if id_usuario:
            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="SUBCATEGORIAS",
                accion="CREAR",
                descripcion=f"Creó subcategoría id={nuevo_id} nombre='{nombre}' cat={id_categoria}",
                tabla_afectada="subcategorias",
                id_registro=nuevo_id
            )
            conn.commit()

            cursor.execute("""
    SELECT
        s.id_subcategoria,
        s.nombre,
        s.descripcion,
        s.id_categoria,
        c.nombre AS categoria_nombre,
        s.estado
    FROM subcategorias s
    INNER JOIN categorias c
        ON s.id_categoria = c.id_categoria
    WHERE s.id_subcategoria=%s
""", (nuevo_id,))

        subcategoria = cursor.fetchone()

        return jsonify({'success': True, 'subcategoria': subcategoria}), 201
    except Exception as e:
        conn.rollback()
        print("Error crear_subcategoria:", e)
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ==============================
# ACTUALIZAR SUBCATEGORÍA
# ==============================
@subcategorias_bp.route('/<int:id_subcategoria>', methods=['PUT'])
def actualizar_subcategoria(id_subcategoria):
    data = request.get_json()
    nombre = data.get('nombre')
    descripcion = data.get('descripcion')
    id_categoria = data.get('id_categoria')
    estado = data.get('estado', 'Activo')

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT id_subcategoria FROM subcategorias WHERE id_subcategoria=%s", (id_subcategoria,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'message': 'Subcategoría no encontrada'}), 404

        cursor.execute("SELECT nombre FROM subcategorias WHERE id_subcategoria != %s", (id_subcategoria,))
        nombres_existentes = [row['nombre'].lower() for row in cursor.fetchall()]
        if nombre.lower() in nombres_existentes:
            return jsonify({'success': False, 'message': 'Ya existe otra subcategoría con ese nombre'}), 400

        cursor.execute("""
    UPDATE subcategorias
    SET nombre=%s, descripcion=%s, id_categoria=%s, estado=%s
    WHERE id_subcategoria=%s
""", (nombre, descripcion, id_categoria, estado, id_subcategoria))
        
        
        conn.commit()
         # Bitácora
        id_usuario = session.get("id_usuario")
        if id_usuario:
            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="SUBCATEGORIAS",
                accion="ACTUALIZAR",
                descripcion=f"Actualizó subcategoría id={id_subcategoria} nombre='{nombre}' cat={id_categoria} estado='{estado}'",
                tabla_afectada="subcategorias",
                id_registro=id_subcategoria
            )
            conn.commit()

        cursor.execute("""
    SELECT
        s.id_subcategoria,
        s.nombre,
        s.descripcion,
        s.id_categoria,
        c.nombre AS categoria_nombre,
        s.estado
    FROM subcategorias s
    INNER JOIN categorias c
        ON s.id_categoria = c.id_categoria
    WHERE s.id_subcategoria=%s
""", (id_subcategoria,))
        
        subcategoria = cursor.fetchone()
        return jsonify({'success': True, 'subcategoria': subcategoria})
    except Exception as e:
        conn.rollback()
        print("Error actualizar_subcategoria:", e)
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ==============================
# ELIMINAR SUBCATEGORÍA
# ==============================
@subcategorias_bp.route('/<int:id_subcategoria>', methods=['DELETE'])
def eliminar_subcategoria(id_subcategoria):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT id_producto FROM productos WHERE id_subcategoria=%s", (id_subcategoria,))
        productos = cursor.fetchall()
        if productos:
            return jsonify({'success': False, 'message': 'No se puede eliminar la subcategoría porque tiene productos asociados'}), 400

        cursor.execute("DELETE FROM subcategorias WHERE id_subcategoria=%s", (id_subcategoria,))
        conn.commit()

        # Bitácora
        id_usuario = session.get("id_usuario")
        if id_usuario:
            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="SUBCATEGORIAS",
                accion="ELIMINAR",
                descripcion=f"Eliminó subcategoría id={id_subcategoria}",
                tabla_afectada="subcategorias",
                id_registro=id_subcategoria
            )
            conn.commit()
            
        return jsonify({'success': True, 'message': 'Subcategoría eliminada correctamente'})
    except Exception as e:
        conn.rollback()
        print("Error interno al eliminar la subcategoría:", e)
        return jsonify({'success': False, 'message': f'Error interno: {str(e)}'}), 500
    finally:
        cursor.close()
        conn.close()
