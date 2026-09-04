from flask import Blueprint, request, jsonify, session
from db import get_db_connection
from utils.bitacora import registrar_bitacora
from psycopg2.extras import RealDictCursor


subcategorias_bp = Blueprint(
    'subcategorias_bp',
    __name__,
    url_prefix='/api/subcategorias'
)


# ==========================================================
# LISTAR TODAS LAS SUBCATEGORÍAS
# ==========================================================
@subcategorias_bp.route('/', methods=['GET'])
def listar_subcategorias():

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
            ORDER BY s.id_subcategoria DESC
        """)

        subcategorias = cursor.fetchall()

        return jsonify(subcategorias), 200

    except Exception as e:

        print("Error listar_subcategorias:", e)

        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

    finally:

        cursor.close()
        conn.close()


# ==========================================================
# OBTENER SUBCATEGORÍA POR ID
# ==========================================================
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
            WHERE s.id_subcategoria = %s
        """, (id_subcategoria,))

        subcategoria = cursor.fetchone()

        if not subcategoria:

            return jsonify({
                'success': False,
                'message': 'Subcategoría no encontrada'
            }), 404

        return jsonify(subcategoria), 200

    except Exception as e:

        print("Error obtener_subcategoria:", e)

        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

    finally:

        cursor.close()
        conn.close()


# ==========================================================
# CREAR SUBCATEGORÍA
# ==========================================================
@subcategorias_bp.route('/', methods=['POST'])
def crear_subcategoria():

    data = request.get_json(silent=True)

    if not data:

        return jsonify({
            'success': False,
            'message': 'No se recibieron datos'
        }), 400

    nombre = data.get('nombre')
    descripcion = data.get('descripcion', '')
    id_categoria = data.get('id_categoria')
    estado = data.get('estado', 'Activo')

    if not nombre or not id_categoria:

        return jsonify({
            'success': False,
            'message': 'Nombre y categoría padre son obligatorios'
        }), 400

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:

        # ==================================================
        # VALIDAR QUE LA CATEGORÍA EXISTA
        # ==================================================

        cursor.execute("""
            SELECT id_categoria
            FROM categorias
            WHERE id_categoria = %s
        """, (id_categoria,))

        categoria = cursor.fetchone()

        if not categoria:

            return jsonify({
                'success': False,
                'message': 'La categoría seleccionada no existe'
            }), 400

        # ==================================================
        # VALIDAR SUBCATEGORÍA DUPLICADA
        # ==================================================

        cursor.execute("""
            SELECT id_subcategoria
            FROM subcategorias
            WHERE LOWER(TRIM(nombre)) = LOWER(TRIM(%s))
              AND id_categoria = %s
        """, (nombre, id_categoria))

        existente = cursor.fetchone()

        if existente:

            return jsonify({
                'success': False,
                'message': 'Ya existe una subcategoría con ese nombre en la misma categoría'
            }), 400

        # ==================================================
        # INSERTAR
        # ==================================================

        cursor.execute("""
            INSERT INTO subcategorias
            (
                nombre,
                descripcion,
                id_categoria,
                estado
            )
            VALUES (%s, %s, %s, %s)
            RETURNING id_subcategoria
        """, (
            nombre,
            descripcion,
            id_categoria,
            estado
        ))

        nuevo_id = cursor.fetchone()['id_subcategoria']

        # ==================================================
        # BITÁCORA
        # ==================================================

        id_usuario = session.get("id_usuario")

        if id_usuario:

            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="SUBCATEGORIAS",
                accion="CREAR",
                descripcion=(
                    f"Creó subcategoría "
                    f"id={nuevo_id} "
                    f"nombre='{nombre}' "
                    f"cat={id_categoria}"
                ),
                tabla_afectada="subcategorias",
                id_registro=nuevo_id
            )

        # ==================================================
        # OBTENER REGISTRO CREADO
        # ==================================================

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
            WHERE s.id_subcategoria = %s
        """, (nuevo_id,))

        subcategoria = cursor.fetchone()

        conn.commit()

        return jsonify({
            'success': True,
            'message': 'Subcategoría creada correctamente',
            'subcategoria': subcategoria
        }), 201

    except Exception as e:

        conn.rollback()

        print("Error crear_subcategoria:", e)

        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

    finally:

        cursor.close()
        conn.close()


# ==========================================================
# ACTUALIZAR SUBCATEGORÍA
# ==========================================================
@subcategorias_bp.route('/<int:id_subcategoria>', methods=['PUT'])
def actualizar_subcategoria(id_subcategoria):

    data = request.get_json(silent=True)

    if not data:

        return jsonify({
            'success': False,
            'message': 'No se recibieron datos'
        }), 400

    nombre = data.get('nombre')
    descripcion = data.get('descripcion', '')
    id_categoria = data.get('id_categoria')
    estado = data.get('estado', 'Activo')

    if not nombre or not id_categoria:

        return jsonify({
            'success': False,
            'message': 'Nombre y categoría son obligatorios'
        }), 400

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:

        # ==================================================
        # VALIDAR EXISTENCIA
        # ==================================================

        cursor.execute("""
            SELECT id_subcategoria
            FROM subcategorias
            WHERE id_subcategoria = %s
        """, (id_subcategoria,))

        existente = cursor.fetchone()

        if not existente:

            return jsonify({
                'success': False,
                'message': 'Subcategoría no encontrada'
            }), 404

        # ==================================================
        # VALIDAR CATEGORÍA
        # ==================================================

        cursor.execute("""
            SELECT id_categoria
            FROM categorias
            WHERE id_categoria = %s
        """, (id_categoria,))

        categoria = cursor.fetchone()

        if not categoria:

            return jsonify({
                'success': False,
                'message': 'La categoría seleccionada no existe'
            }), 400

        # ==================================================
        # VALIDAR DUPLICADO
        # ==================================================

        cursor.execute("""
            SELECT id_subcategoria
            FROM subcategorias
            WHERE LOWER(TRIM(nombre)) = LOWER(TRIM(%s))
              AND id_categoria = %s
              AND id_subcategoria <> %s
        """, (
            nombre,
            id_categoria,
            id_subcategoria
        ))

        duplicada = cursor.fetchone()

        if duplicada:

            return jsonify({
                'success': False,
                'message': 'Ya existe otra subcategoría con ese nombre en la misma categoría'
            }), 400

        # ==================================================
        # ACTUALIZAR
        # ==================================================

        cursor.execute("""
            UPDATE subcategorias
            SET
                nombre = %s,
                descripcion = %s,
                id_categoria = %s,
                estado = %s
            WHERE id_subcategoria = %s
        """, (
            nombre,
            descripcion,
            id_categoria,
            estado,
            id_subcategoria
        ))

        # ==================================================
        # BITÁCORA
        # ==================================================

        id_usuario = session.get("id_usuario")

        if id_usuario:

            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="SUBCATEGORIAS",
                accion="ACTUALIZAR",
                descripcion=(
                    f"Actualizó subcategoría "
                    f"id={id_subcategoria} "
                    f"nombre='{nombre}' "
                    f"cat={id_categoria} "
                    f"estado='{estado}'"
                ),
                tabla_afectada="subcategorias",
                id_registro=id_subcategoria
            )

        # ==================================================
        # OBTENER REGISTRO ACTUALIZADO
        # ==================================================

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
            WHERE s.id_subcategoria = %s
        """, (id_subcategoria,))

        subcategoria = cursor.fetchone()

        conn.commit()

        return jsonify({
            'success': True,
            'message': 'Subcategoría actualizada correctamente',
            'subcategoria': subcategoria
        }), 200

    except Exception as e:

        conn.rollback()

        print("Error actualizar_subcategoria:", e)

        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

    finally:

        cursor.close()
        conn.close()


# ==========================================================
# ELIMINAR SUBCATEGORÍA
# ==========================================================
@subcategorias_bp.route('/<int:id_subcategoria>', methods=['DELETE'])
def eliminar_subcategoria(id_subcategoria):

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:

        # ==================================================
        # VERIFICAR PRODUCTOS ASOCIADOS
        # ==================================================

        cursor.execute("""
            SELECT id_producto
            FROM productos
            WHERE id_subcategoria = %s
        """, (id_subcategoria,))

        productos = cursor.fetchall()

        if productos:

            return jsonify({
                'success': False,
                'message': (
                    'No se puede eliminar la subcategoría '
                    'porque tiene productos asociados'
                )
            }), 400

        # ==================================================
        # VERIFICAR EXISTENCIA
        # ==================================================

        cursor.execute("""
            SELECT id_subcategoria
            FROM subcategorias
            WHERE id_subcategoria = %s
        """, (id_subcategoria,))

        existente = cursor.fetchone()

        if not existente:

            return jsonify({
                'success': False,
                'message': 'Subcategoría no encontrada'
            }), 404

        # ==================================================
        # ELIMINAR
        # ==================================================

        cursor.execute("""
            DELETE FROM subcategorias
            WHERE id_subcategoria = %s
        """, (id_subcategoria,))

        # ==================================================
        # BITÁCORA
        # ==================================================

        id_usuario = session.get("id_usuario")

        if id_usuario:

            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="SUBCATEGORIAS",
                accion="ELIMINAR",
                descripcion=(
                    f"Eliminó subcategoría "
                    f"id={id_subcategoria}"
                ),
                tabla_afectada="subcategorias",
                id_registro=id_subcategoria
            )

        conn.commit()

        return jsonify({
            'success': True,
            'message': 'Subcategoría eliminada correctamente'
        }), 200

    except Exception as e:

        conn.rollback()

        print("Error interno al eliminar la subcategoría:", e)

        return jsonify({
            'success': False,
            'message': f'Error interno: {str(e)}'
        }), 500

    finally:

        cursor.close()
        conn.close()