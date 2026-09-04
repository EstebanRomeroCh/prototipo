# routes/productos.py

from flask import Blueprint, request, jsonify, session
from db import get_db_connection
from decimal import Decimal, InvalidOperation
from utils.bitacora import registrar_bitacora
from psycopg2.extras import RealDictCursor


productos_bp = Blueprint(
    'productos_bp',
    __name__,
    url_prefix='/api/productos'
)


# =========================================================
# UTILIDADES
# =========================================================

def es_similar(a, b):
    """
    Considera duplicado un producto cuando el nombre es
    exactamente igual ignorando espacios y mayúsculas/minúsculas.
    """
    if not a or not b:
        return False

    return a.strip().lower() == b.strip().lower()


def normalize_decimals(obj):
    """
    Convierte Decimal a float para que Flask pueda devolver
    correctamente los valores en JSON.
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


# =========================================================
# LISTAR TODOS LOS PRODUCTOS
# =========================================================

@productos_bp.route('/', methods=['GET'])
def listar_productos():

    if 'usuario' not in session:
        return jsonify({
            'success': False,
            'message': 'Sesión expirada'
        }), 401

    conn = None
    cursor = None

    try:

        conn = get_db_connection()

        cursor = conn.cursor(
            cursor_factory=RealDictCursor
        )

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

            INNER JOIN categorias c
                ON p.id_categoria = c.id_categoria

            INNER JOIN subcategorias s
                ON p.id_subcategoria = s.id_subcategoria

            LEFT JOIN unidades_medida u
                ON p.id_unidad = u.id_unidad

            ORDER BY p.id_producto DESC
        """)

        productos = cursor.fetchall()

        productos = normalize_decimals(productos)

        return jsonify(productos), 200

    except Exception as e:

        print("Error listar_productos:", e)

        return jsonify({
            'success': False,
            'message': 'Error al listar los productos',
            'error': str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# OBTENER PRODUCTO POR ID
# =========================================================

@productos_bp.route('/<int:id_producto>', methods=['GET'])
def obtener_producto(id_producto):

    if 'usuario' not in session:
        return jsonify({
            'success': False,
            'message': 'Sesión expirada'
        }), 401

    conn = None
    cursor = None

    try:

        conn = get_db_connection()

        cursor = conn.cursor(
            cursor_factory=RealDictCursor
        )

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

            INNER JOIN categorias c
                ON p.id_categoria = c.id_categoria

            INNER JOIN subcategorias s
                ON p.id_subcategoria = s.id_subcategoria

            LEFT JOIN unidades_medida u
                ON p.id_unidad = u.id_unidad

            WHERE p.id_producto = %s
        """, (id_producto,))

        producto = cursor.fetchone()

        if not producto:

            return jsonify({
                'success': False,
                'message': 'Producto no encontrado'
            }), 404

        producto = normalize_decimals(producto)

        return jsonify(producto), 200

    except Exception as e:

        print("Error obtener_producto:", e)

        return jsonify({
            'success': False,
            'message': 'Error al obtener el producto',
            'error': str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# CREAR PRODUCTO
# =========================================================

@productos_bp.route('/', methods=['POST'])
def crear_producto():

    if 'usuario' not in session:
        return jsonify({
            'success': False,
            'message': 'Sesión expirada'
        }), 401

    data = request.get_json(silent=True) or {}

    nombre = data.get('nombre')
    stock_minimo = data.get('stock_minimo')
    id_unidad = data.get('id_unidad')
    descripcion = data.get('descripcion')
    id_categoria = data.get('id_categoria')
    id_subcategoria = data.get('id_subcategoria')
    peso_unitario = data.get('peso_unitario', 0)

    # -----------------------------------------------------
    # VALIDAR CAMPOS
    # -----------------------------------------------------

    if not nombre or not str(nombre).strip():

        return jsonify({
            'success': False,
            'message': 'El nombre del producto es obligatorio'
        }), 400

    if stock_minimo is None:

        return jsonify({
            'success': False,
            'message': 'El stock mínimo es obligatorio'
        }), 400

    if not id_unidad:

        return jsonify({
            'success': False,
            'message': 'La unidad de medida es obligatoria'
        }), 400

    if not id_categoria:

        return jsonify({
            'success': False,
            'message': 'La categoría es obligatoria'
        }), 400

    if not id_subcategoria:

        return jsonify({
            'success': False,
            'message': 'La subcategoría es obligatoria'
        }), 400

    nombre = str(nombre).strip()

    # -----------------------------------------------------
    # CONVERTIR VALORES
    # -----------------------------------------------------

    try:

        stock_minimo = Decimal(str(stock_minimo))
        peso_unitario = Decimal(str(peso_unitario))

        id_unidad = int(id_unidad)
        id_categoria = int(id_categoria)
        id_subcategoria = int(id_subcategoria)

    except (ValueError, TypeError, InvalidOperation):

        return jsonify({
            'success': False,
            'message': 'Los valores numéricos no son válidos'
        }), 400

    # -----------------------------------------------------
    # VALIDAR VALORES NEGATIVOS
    # -----------------------------------------------------

    if stock_minimo < 0:

        return jsonify({
            'success': False,
            'message': 'El stock mínimo no puede ser negativo'
        }), 400

    if peso_unitario < 0:

        return jsonify({
            'success': False,
            'message': 'El peso unitario no puede ser negativo'
        }), 400

    conn = None
    cursor = None

    try:

        conn = get_db_connection()

        cursor = conn.cursor(
            cursor_factory=RealDictCursor
        )

        # -------------------------------------------------
        # 1. VERIFICAR CATEGORÍA
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                id_categoria,
                nombre
            FROM categorias
            WHERE id_categoria = %s
        """, (id_categoria,))

        categoria = cursor.fetchone()

        if not categoria:

            return jsonify({
                'success': False,
                'message': 'La categoría seleccionada no existe'
            }), 400

        # -------------------------------------------------
        # 2. VERIFICAR SUBCATEGORÍA
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                id_subcategoria,
                nombre,
                id_categoria,
                estado
            FROM subcategorias
            WHERE id_subcategoria = %s
        """, (id_subcategoria,))

        subcategoria = cursor.fetchone()

        if not subcategoria:

            return jsonify({
                'success': False,
                'message': 'La subcategoría seleccionada no existe'
            }), 400

        # -------------------------------------------------
        # 3. VALIDAR RELACIÓN CATEGORÍA/SUBCATEGORÍA
        # -------------------------------------------------

        if subcategoria['id_categoria'] != id_categoria:

            return jsonify({
                'success': False,
                'message': (
                    'La subcategoría seleccionada no pertenece '
                    'a la categoría seleccionada'
                )
            }), 400

        # -------------------------------------------------
        # 4. VALIDAR ESTADO SUBCATEGORÍA
        # -------------------------------------------------

        if subcategoria['estado'] != 'Activo':

            return jsonify({
                'success': False,
                'message': 'La subcategoría seleccionada está inactiva'
            }), 400

        # -------------------------------------------------
        # 5. EVITAR PRODUCTOS DUPLICADOS
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                id_producto,
                nombre
            FROM productos
            WHERE id_subcategoria = %s
        """, (id_subcategoria,))

        productos_existentes = cursor.fetchall()

        for producto_existente in productos_existentes:

            if es_similar(
                nombre,
                producto_existente['nombre']
            ):

                return jsonify({
                    'success': False,
                    'message': (
                        'Ya existe un producto con el mismo '
                        'nombre en esta subcategoría: '
                        f'"{producto_existente["nombre"]}"'
                    )
                }), 400

        # -------------------------------------------------
        # 6. VERIFICAR UNIDAD DE MEDIDA
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                id_unidad,
                nombre,
                abreviatura,
                factor_kg
            FROM unidades_medida
            WHERE id_unidad = %s
        """, (id_unidad,))

        unidad = cursor.fetchone()

        if not unidad:

            return jsonify({
                'success': False,
                'message': 'La unidad de medida no existe'
            }), 400

        # -------------------------------------------------
        # 7. CALCULAR PESO KG
        # -------------------------------------------------

        factor_kg = Decimal(str(unidad['factor_kg']))

        peso_kg = peso_unitario * factor_kg

        # -------------------------------------------------
        # 8. INSERTAR PRODUCTO
        #
        # IMPORTANTE:
        # PostgreSQL utiliza RETURNING en lugar de lastrowid
        # -------------------------------------------------

        cursor.execute("""
            INSERT INTO productos
            (
                id_categoria,
                id_subcategoria,
                nombre,
                stock_minimo,
                id_unidad,
                descripcion,
                peso_unitario,
                peso_kg
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            RETURNING id_producto
        """, (
            id_categoria,
            id_subcategoria,
            nombre,
            stock_minimo,
            id_unidad,
            descripcion,
            peso_unitario,
            peso_kg
        ))

        resultado = cursor.fetchone()

        nuevo_id = resultado['id_producto']

        # -------------------------------------------------
        # 9. OBTENER PRODUCTO CREADO
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                p.*,
                c.nombre AS categoria,
                s.nombre AS subcategoria,
                u.nombre AS unidad_nombre,
                u.abreviatura AS unidad_abreviatura
            FROM productos p

            INNER JOIN categorias c
                ON p.id_categoria = c.id_categoria

            INNER JOIN subcategorias s
                ON p.id_subcategoria = s.id_subcategoria

            LEFT JOIN unidades_medida u
                ON p.id_unidad = u.id_unidad

            WHERE p.id_producto = %s
        """, (nuevo_id,))

        producto = cursor.fetchone()

        # -------------------------------------------------
        # 10. BITÁCORA
        # -------------------------------------------------

        try:

            id_usuario = session.get('id_usuario')

            if id_usuario:

                registrar_bitacora(
                    cursor,
                    id_usuario=id_usuario,
                    modulo='PRODUCTOS',
                    accion='CREAR',
                    descripcion=(
                        f'Creó producto ID {nuevo_id} - {nombre}.'
                    ),
                    tabla_afectada='productos',
                    id_registro=nuevo_id
                )

        except Exception as e:

            print(
                'Bitácora (crear_producto) error:',
                e
            )

        # -------------------------------------------------
        # 11. COMMIT FINAL
        # -------------------------------------------------

        conn.commit()

        producto = normalize_decimals(producto)

        return jsonify({
            'success': True,
            'message': 'Producto creado correctamente',
            'producto': producto
        }), 201

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            'Error crear_producto:',
            e
        )

        return jsonify({
            'success': False,
            'message': 'Error al crear el producto',
            'error': str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# ACTUALIZAR PRODUCTO
# =========================================================

@productos_bp.route('/<int:id_producto>', methods=['PUT'])
def actualizar_producto(id_producto):

    if 'usuario' not in session:
        return jsonify({
            'success': False,
            'message': 'Sesión expirada'
        }), 401

    data = request.get_json(silent=True) or {}

    nombre = data.get('nombre')
    stock_minimo = data.get('stock_minimo')
    id_unidad = data.get('id_unidad')
    descripcion = data.get('descripcion', '')
    id_categoria = data.get('id_categoria')
    id_subcategoria = data.get('id_subcategoria')
    peso_unitario = data.get('peso_unitario', 0)

    # -----------------------------------------------------
    # VALIDACIONES
    # -----------------------------------------------------

    if not nombre or not str(nombre).strip():

        return jsonify({
            'success': False,
            'message': 'El nombre del producto es obligatorio'
        }), 400

    if stock_minimo is None:

        return jsonify({
            'success': False,
            'message': 'El stock mínimo es obligatorio'
        }), 400

    if not id_unidad or not id_categoria or not id_subcategoria:

        return jsonify({
            'success': False,
            'message': 'Categoría, subcategoría y unidad son obligatorias'
        }), 400

    nombre = str(nombre).strip()

    try:

        stock_minimo = Decimal(str(stock_minimo))
        peso_unitario = Decimal(str(peso_unitario))

        id_unidad = int(id_unidad)
        id_categoria = int(id_categoria)
        id_subcategoria = int(id_subcategoria)

    except (ValueError, TypeError, InvalidOperation):

        return jsonify({
            'success': False,
            'message': 'Valores numéricos inválidos'
        }), 400

    if stock_minimo < 0:

        return jsonify({
            'success': False,
            'message': 'El stock mínimo no puede ser negativo'
        }), 400

    if peso_unitario < 0:

        return jsonify({
            'success': False,
            'message': 'El peso unitario no puede ser negativo'
        }), 400

    conn = None
    cursor = None

    try:

        conn = get_db_connection()

        cursor = conn.cursor(
            cursor_factory=RealDictCursor
        )

        # -------------------------------------------------
        # 1. VERIFICAR PRODUCTO
        # -------------------------------------------------

        cursor.execute("""
            SELECT *
            FROM productos
            WHERE id_producto = %s
        """, (id_producto,))

        producto_actual = cursor.fetchone()

        if not producto_actual:

            return jsonify({
                'success': False,
                'message': 'Producto no encontrado'
            }), 404

        # -------------------------------------------------
        # 2. VERIFICAR CATEGORÍA
        # -------------------------------------------------

        cursor.execute("""
            SELECT id_categoria
            FROM categorias
            WHERE id_categoria = %s
        """, (id_categoria,))

        if not cursor.fetchone():

            return jsonify({
                'success': False,
                'message': 'La categoría seleccionada no existe'
            }), 400

        # -------------------------------------------------
        # 3. VERIFICAR SUBCATEGORÍA
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                id_subcategoria,
                id_categoria,
                estado
            FROM subcategorias
            WHERE id_subcategoria = %s
        """, (id_subcategoria,))

        subcategoria = cursor.fetchone()

        if not subcategoria:

            return jsonify({
                'success': False,
                'message': 'La subcategoría seleccionada no existe'
            }), 400

        # -------------------------------------------------
        # 4. VALIDAR RELACIÓN
        # -------------------------------------------------

        if subcategoria['id_categoria'] != id_categoria:

            return jsonify({
                'success': False,
                'message': (
                    'La subcategoría no pertenece '
                    'a la categoría seleccionada'
                )
            }), 400

        if subcategoria['estado'] != 'Activo':

            return jsonify({
                'success': False,
                'message': 'La subcategoría seleccionada está inactiva'
            }), 400

        # -------------------------------------------------
        # 5. EVITAR NOMBRE DUPLICADO
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                id_producto,
                nombre
            FROM productos
            WHERE id_subcategoria = %s
              AND id_producto <> %s
        """, (
            id_subcategoria,
            id_producto
        ))

        productos_existentes = cursor.fetchall()

        for producto_existente in productos_existentes:

            if es_similar(
                nombre,
                producto_existente['nombre']
            ):

                return jsonify({
                    'success': False,
                    'message': (
                        'Ya existe otro producto con el mismo '
                        'nombre en esta subcategoría: '
                        f'"{producto_existente["nombre"]}"'
                    )
                }), 400

        # -------------------------------------------------
        # 6. VERIFICAR UNIDAD
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                id_unidad,
                factor_kg
            FROM unidades_medida
            WHERE id_unidad = %s
        """, (id_unidad,))

        unidad = cursor.fetchone()

        if not unidad:

            return jsonify({
                'success': False,
                'message': 'La unidad de medida no existe'
            }), 400

        # -------------------------------------------------
        # 7. CALCULAR PESO KG
        # -------------------------------------------------

        factor_kg = Decimal(str(unidad['factor_kg']))

        peso_kg = peso_unitario * factor_kg

        # -------------------------------------------------
        # 8. ACTUALIZAR
        # -------------------------------------------------

        cursor.execute("""
            UPDATE productos
            SET
                id_categoria = %s,
                id_subcategoria = %s,
                nombre = %s,
                stock_minimo = %s,
                id_unidad = %s,
                descripcion = %s,
                peso_unitario = %s,
                peso_kg = %s
            WHERE id_producto = %s
        """, (
            id_categoria,
            id_subcategoria,
            nombre,
            stock_minimo,
            id_unidad,
            descripcion,
            peso_unitario,
            peso_kg,
            id_producto
        ))

        # -------------------------------------------------
        # 9. BITÁCORA
        # -------------------------------------------------

        try:

            id_usuario = session.get('id_usuario')

            if id_usuario:

                registrar_bitacora(
                    cursor,
                    id_usuario=id_usuario,
                    modulo='PRODUCTOS',
                    accion='ACTUALIZAR',
                    descripcion=(
                        f'Actualizó producto '
                        f'ID {id_producto} - {nombre}.'
                    ),
                    tabla_afectada='productos',
                    id_registro=id_producto
                )

        except Exception as e:

            print(
                'Bitácora (actualizar_producto) error:',
                e
            )

        conn.commit()

        # -------------------------------------------------
        # 10. DEVOLVER PRODUCTO ACTUALIZADO
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                p.*,
                c.nombre AS categoria,
                s.nombre AS subcategoria,
                u.nombre AS unidad_nombre,
                u.abreviatura AS unidad_abreviatura
            FROM productos p

            INNER JOIN categorias c
                ON p.id_categoria = c.id_categoria

            INNER JOIN subcategorias s
                ON p.id_subcategoria = s.id_subcategoria

            LEFT JOIN unidades_medida u
                ON p.id_unidad = u.id_unidad

            WHERE p.id_producto = %s
        """, (id_producto,))

        producto = cursor.fetchone()

        producto = normalize_decimals(producto)

        return jsonify({
            'success': True,
            'message': 'Producto actualizado correctamente',
            'producto': producto
        }), 200

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            'Error actualizar_producto:',
            e
        )

        return jsonify({
            'success': False,
            'message': 'Error al actualizar el producto',
            'error': str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# ELIMINAR PRODUCTO
# =========================================================

@productos_bp.route('/<int:id_producto>', methods=['DELETE'])
def eliminar_producto(id_producto):

    if 'usuario' not in session:
        return jsonify({
            'success': False,
            'message': 'Sesión expirada'
        }), 401

    conn = None
    cursor = None

    try:

        conn = get_db_connection()

        cursor = conn.cursor(
            cursor_factory=RealDictCursor
        )

        # -------------------------------------------------
        # 1. VERIFICAR PRODUCTO
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                id_producto,
                nombre
            FROM productos
            WHERE id_producto = %s
        """, (id_producto,))

        producto = cursor.fetchone()

        if not producto:

            return jsonify({
                'success': False,
                'message': 'Producto no encontrado'
            }), 404

        nombre_producto = producto['nombre']

        # -------------------------------------------------
        # 2. ELIMINAR
        # -------------------------------------------------

        cursor.execute("""
            DELETE FROM productos
            WHERE id_producto = %s
        """, (id_producto,))

        # -------------------------------------------------
        # 3. BITÁCORA
        # -------------------------------------------------

        try:

            id_usuario = session.get('id_usuario')

            if id_usuario:

                registrar_bitacora(
                    cursor,
                    id_usuario=id_usuario,
                    modulo='PRODUCTOS',
                    accion='ELIMINAR',
                    descripcion=(
                        f'Eliminó producto '
                        f'ID {id_producto} - {nombre_producto}.'
                    ),
                    tabla_afectada='productos',
                    id_registro=id_producto
                )

        except Exception as e:

            print(
                'Bitácora (eliminar_producto) error:',
                e
            )

        conn.commit()

        return jsonify({
            'success': True,
            'message': 'Producto eliminado correctamente'
        }), 200

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            'Error eliminar_producto:',
            e
        )

        return jsonify({
            'success': False,
            'message': 'No se pudo eliminar el producto',
            'error': str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# AUTOCOMPLETADO / BUSCAR PRODUCTOS
# =========================================================

@productos_bp.route('/buscar', methods=['GET'])
def buscar_productos():

    q = request.args.get('q', '').strip()

    if not q:
        return jsonify([]), 200

    conn = None
    cursor = None

    try:

        conn = get_db_connection()

        cursor = conn.cursor(
            cursor_factory=RealDictCursor
        )

        cursor.execute("""
            SELECT
                p.id_producto,
                p.nombre,

                p.id_categoria,
                c.nombre AS categoria,

                p.id_subcategoria,
                s.nombre AS subcategoria,

                u.id_unidad,
                u.nombre AS unidad_medida,
                u.abreviatura,

                p.peso_unitario,
                p.peso_kg

            FROM productos p

            INNER JOIN categorias c
                ON p.id_categoria = c.id_categoria

            INNER JOIN subcategorias s
                ON p.id_subcategoria = s.id_subcategoria

            LEFT JOIN unidades_medida u
                ON p.id_unidad = u.id_unidad

            WHERE p.nombre ILIKE %s

            ORDER BY p.nombre ASC

            LIMIT 10
        """, (f"%{q}%",))

        resultados = cursor.fetchall()

        resultados = normalize_decimals(resultados)

        return jsonify(resultados), 200

    except Exception as e:

        print(
            'Error buscar_productos:',
            e
        )

        return jsonify({
            'success': False,
            'message': 'Error al buscar productos',
            'error': str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()
