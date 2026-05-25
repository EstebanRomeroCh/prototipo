# routes/productos.py
from flask import Blueprint, request, jsonify, session
from db import get_db_connection
from decimal import Decimal, InvalidOperation
from utils.bitacora import registrar_bitacora
from psycopg2.extras import RealDictCursor


productos_bp = Blueprint('productos_bp', __name__, url_prefix='/api/productos')


# ==============================
# UTILIDADES
# ==============================
def es_similar(a, b):
    """
    Regla actual: solo considerar duplicado si el nombre es
    EXACTAMENTE igual (ignorando espacios y mayúsculas).
    """
    return a.strip().lower() == b.strip().lower()


def normalize_decimals(obj):
    """
    Convierte valores Decimal en float dentro de dicts o listas,
    para que el JSON salga como número (50, 0.25) y no "50.000".
    """
    if isinstance(obj, list):
        return [normalize_decimals(o) for o in obj]
    if isinstance(obj, dict):
        nuevo = {}
        for k, v in obj.items():
            if isinstance(v, Decimal):
                nuevo[k] = float(v)
            else:
                nuevo[k] = v
        return nuevo
    return obj


# ==============================
# LISTAR TODOS LOS PRODUCTOS
# ==============================
@productos_bp.route('/', methods=['GET'])
def listar_productos():
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'Sesión expirada'}), 401

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT 
                p.id_producto,
                p.nombre,
                p.stock_minimo,
                p.id_unidad,
                p.descripcion,
                p.peso_unitario,
                p.peso_kg,
                p.id_categoria,
                p.id_subcategoria,
                c.nombre AS categoria,
                s.nombre AS subcategoria,
                u.nombre AS unidad_medida,
                u.abreviatura AS unidad_abreviatura
            FROM productos p
            JOIN categorias c ON p.id_categoria = c.id_categoria
            JOIN subcategorias s ON p.id_subcategoria = s.id_subcategoria
            LEFT JOIN unidades_medida u ON p.id_unidad = u.id_unidad
        """)
        productos = cursor.fetchall()
        productos = normalize_decimals(productos)
        return jsonify(productos)

    except Exception as e:
        print("Error listar_productos:", e)
        return jsonify({'success': False, 'message': str(e)}), 500

    finally:
        cursor.close()
        conn.close()


# ==============================
# OBTENER PRODUCTO POR ID
# ==============================
@productos_bp.route('/<int:id_producto>', methods=['GET'])
def obtener_producto(id_producto):

    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'Sesión expirada'}), 401

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute("""
            SELECT 
                p.id_producto, 
                p.nombre, 
                p.stock_minimo, 
                p.id_unidad,
                p.descripcion, 
                p.peso_unitario,
                p.peso_kg,
                p.id_categoria, 
                p.id_subcategoria,
                c.nombre AS categoria, 
                s.nombre AS subcategoria,
                u.nombre AS unidad_nombre, 
                u.abreviatura AS unidad_abreviatura
            FROM productos p
            JOIN categorias c ON p.id_categoria = c.id_categoria
            JOIN subcategorias s ON p.id_subcategoria = s.id_subcategoria
            JOIN unidades_medida u ON p.id_unidad = u.id_unidad
            WHERE p.id_producto=%s
        """, (id_producto,))

        producto = cursor.fetchone()
        if not producto:
            return jsonify({'success': False, 'message': 'Producto no encontrado'}), 404

        producto = normalize_decimals(producto)
        return jsonify(producto)

    except Exception as e:
        print("Error obtener_producto:", e)
        return jsonify({'success': False, 'message': str(e)}), 500

    finally:
        cursor.close()
        conn.close()


# ==============================
# CREAR PRODUCTO
# ==============================
@productos_bp.route('/', methods=['POST'])
def crear_producto():
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'Sesión expirada'}), 401

    data = request.get_json() or {}

    nombre = data.get('nombre')
    stock_minimo = data.get('stock_minimo')
    id_unidad = data.get('id_unidad')
    descripcion = data.get('descripcion', None)
    id_categoria = data.get('id_categoria')
    id_subcategoria = data.get('id_subcategoria')
    peso_unitario = data.get('peso_unitario', 0)

    if not nombre or stock_minimo is None or not id_unidad or not id_categoria or not id_subcategoria:
        return jsonify({'success': False, 'message': 'Todos los campos son obligatorios'}), 400

    # CAST seguro
    try:
        stock_minimo = Decimal(str(stock_minimo))
        id_unidad = int(id_unidad)
        id_categoria = int(id_categoria)
        id_subcategoria = int(id_subcategoria)
        peso_unitario = Decimal(str(peso_unitario))
    except Exception:
        return jsonify({'success': False, 'message': 'Los valores numéricos no son válidos'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # 1) Evitar productos con NOMBRE EXACTO en la misma subcategoría
        cursor.execute("SELECT nombre FROM productos WHERE id_subcategoria=%s", (id_subcategoria,))
        nombres_existentes = [row['nombre'] for row in cursor.fetchall()]

        for nombre_existente in nombres_existentes:
            if es_similar(nombre, nombre_existente):
                return jsonify({
                    'success': False,
                    'message': f'Ya existe un producto con el mismo nombre en esta subcategoría: \"{nombre_existente}\"'
                }), 400

        # 2) Obtener factor_kg de la unidad
        cursor.execute("SELECT factor_kg FROM unidades_medida WHERE id_unidad=%s", (id_unidad,))
        row_unidad = cursor.fetchone()
        if not row_unidad:
            return jsonify({'success': False, 'message': 'La unidad de medida no existe'}), 400

        factor_kg = Decimal(str(row_unidad['factor_kg']))
        peso_kg = peso_unitario * factor_kg

        # 3) Insertar producto
        cursor.execute("""
            INSERT INTO productos 
                (id_categoria, id_subcategoria, nombre, stock_minimo, id_unidad, descripcion, peso_unitario, peso_kg)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (id_categoria, id_subcategoria, nombre, stock_minimo, id_unidad, descripcion, peso_unitario, peso_kg))

        conn.commit()
        nuevo_id = cursor.lastrowid

        cursor.execute("SELECT * FROM productos WHERE id_producto=%s", (nuevo_id,))
        producto = cursor.fetchone()
        producto = normalize_decimals(producto)

        try:
            id_usuario = session.get("id_usuario")
            if id_usuario:
                registrar_bitacora(
                    cursor,
                    id_usuario=id_usuario,
                    modulo="PRODUCTOS",
                    accion="CREAR",
                    descripcion=f"Creó producto ID {nuevo_id} - {nombre}.",
                    tabla_afectada="productos",
                    id_registro=nuevo_id
                )
                conn.commit()
        except Exception as e:
            print("Bitácora (crear_producto) error:", e)

        return jsonify({'success': True, 'producto': producto}), 201

    except Exception as e:
        conn.rollback()
        print("Error crear_producto:", e)
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ==============================
# ACTUALIZAR PRODUCTO
# ==============================
@productos_bp.route('/<int:id_producto>', methods=['PUT'])
def actualizar_producto(id_producto):
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'Sesión expirada'}), 401

    data = request.get_json() or {}

    nombre = data.get('nombre')
    stock_minimo = data.get('stock_minimo')
    id_unidad = data.get('id_unidad')
    descripcion = data.get('descripcion', '')
    id_categoria = data.get('id_categoria')
    id_subcategoria = data.get('id_subcategoria')
    peso_unitario = data.get('peso_unitario', 0)

    if not nombre or stock_minimo is None or not id_unidad or not id_categoria or not id_subcategoria:
        return jsonify({'success': False, 'message': 'Todos los campos son obligatorios'}), 400

    try:
        stock_minimo = Decimal(str(stock_minimo))
        peso_unitario = Decimal(str(peso_unitario))
        id_unidad = int(id_unidad)
        id_categoria = int(id_categoria)
        id_subcategoria = int(id_subcategoria)
    except Exception:
        return jsonify({'success': False, 'message': 'Valores numéricos inválidos'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Verificar que exista
        cursor.execute("SELECT * FROM productos WHERE id_producto=%s", (id_producto,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'message': 'Producto no encontrado'}), 404

        # Obtener factor_kg
        cursor.execute("SELECT factor_kg FROM unidades_medida WHERE id_unidad=%s", (id_unidad,))
        row_unidad = cursor.fetchone()
        if not row_unidad:
            return jsonify({'success': False, 'message': 'La unidad de medida no existe'}), 400

        factor_kg = Decimal(str(row_unidad['factor_kg']))
        peso_kg = peso_unitario * factor_kg

        cursor.execute("""
            UPDATE productos
            SET id_categoria=%s, id_subcategoria=%s, nombre=%s,
                stock_minimo=%s, id_unidad=%s, descripcion=%s,
                peso_unitario=%s, peso_kg=%s
            WHERE id_producto=%s
        """, (
            id_categoria, id_subcategoria, nombre, stock_minimo,
            id_unidad, descripcion, peso_unitario, peso_kg, id_producto
        ))

        conn.commit()

        cursor.execute("SELECT * FROM productos WHERE id_producto=%s", (id_producto,))
        producto = cursor.fetchone()
        producto = normalize_decimals(producto)

        try:
            id_usuario = session.get("id_usuario")
            if id_usuario:
                registrar_bitacora(
                    cursor,
                    id_usuario=id_usuario,
                    modulo="PRODUCTOS",
                    accion="ACTUALIZAR",
                    descripcion=f"Actualizó producto ID {id_producto} - {nombre}.",
                    tabla_afectada="productos",
                    id_registro=id_producto
                )
                conn.commit()
        except Exception as e:
            print("Bitácora (actualizar_producto) error:", e)

        return jsonify({'success': True, 'producto': producto})

    except Exception as e:
        conn.rollback()
        print("Error actualizar_producto:", e)
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ==============================
# ELIMINAR PRODUCTO
# ==============================
@productos_bp.route('/<int:id_producto>', methods=['DELETE'])
def eliminar_producto(id_producto):

    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'Sesión expirada'}), 401

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute("DELETE FROM productos WHERE id_producto=%s", (id_producto,))
        conn.commit()

        try:
            id_usuario = session.get("id_usuario")
            if id_usuario:
                registrar_bitacora(
                    cursor,
                    id_usuario=id_usuario,
                    modulo="PRODUCTOS",
                    accion="ELIMINAR",
                    descripcion=f"Eliminó producto ID {id_producto}.",
                    tabla_afectada="productos",
                    id_registro=id_producto
                )
                conn.commit()
        except Exception as e:
            print("Bitácora (eliminar_producto) error:", e)
        
        return jsonify({'success': True})

    except Exception as e:
        conn.rollback()
        print("Error eliminar_producto:", e)
        return jsonify({'success': False, 'message': str(e)})

    finally:
        cursor.close()
        conn.close()


# ==============================
# AUTOCOMPLETADO
# ==============================
@productos_bp.route('/buscar', methods=['GET'])
def buscar_productos():

    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute("""
            SELECT 
                p.id_producto,
                p.nombre,
                p.id_categoria,
                c.nombre AS categoria,
                u.id_unidad,
                u.nombre AS unidad_medida,
                u.abreviatura,
                p.peso_unitario,
                p.peso_kg
            FROM productos p
            JOIN categorias c ON p.id_categoria = c.id_categoria
            JOIN unidades_medida u ON p.id_unidad = u.id_unidad
            WHERE p.nombre LIKE %s
            LIMIT 10
        """, (f"%{q}%",))

        resultados = cursor.fetchall()
        resultados = normalize_decimals(resultados)
        return jsonify(resultados)

    except Exception as e:
        print("Error buscar_productos:", e)
        return jsonify({'success': False, 'message': str(e)})

    finally:
        cursor.close()
        conn.close()
