# routes/categorias.py

from flask import Blueprint, request, jsonify, session
from db import get_db_connection
from utils.bitacora import registrar_bitacora
from psycopg2.extras import RealDictCursor



# ============================================================
# BLUEPRINT
# ============================================================

categorias_bp = Blueprint(
    'categorias_bp',
    __name__,
    url_prefix='/api/categorias'
)


# ============================================================
# LISTAR TODAS LAS CATEGORÍAS
# ============================================================

@categorias_bp.route('/', methods=['GET'])
def listar_categorias():

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT
                id_categoria,
                nombre,
                descripcion,
                estado
            FROM categorias
            ORDER BY id_categoria
        """)

        categorias = cursor.fetchall()

        return jsonify(categorias), 200

    except Exception as e:

        print("Error listar_categorias:", e)

        if conn:
            conn.rollback()

        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# ============================================================
# OBTENER CATEGORÍA POR ID
# ============================================================

@categorias_bp.route('/<int:id_categoria>', methods=['GET'])
def obtener_categoria(id_categoria):

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT
                id_categoria,
                nombre,
                descripcion,
                estado
            FROM categorias
            WHERE id_categoria = %s
        """, (id_categoria,))

        categoria = cursor.fetchone()

        if not categoria:

            return jsonify({
                'success': False,
                'message': 'Categoría no encontrada'
            }), 404

        return jsonify(categoria), 200

    except Exception as e:

        print("Error obtener_categoria:", e)

        if conn:
            conn.rollback()

        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# ============================================================
# CREAR NUEVA CATEGORÍA
# ============================================================

@categorias_bp.route('/', methods=['POST'])
def crear_categoria():

    conn = None
    cursor = None

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'message': 'No se recibieron datos'
            }), 400

        # ----------------------------------------------------
        # OBTENER DATOS
        # ----------------------------------------------------

        nombre = data.get('nombre')
        descripcion = data.get('descripcion', '')
        estado = data.get('estado', 'Activo')

        # ----------------------------------------------------
        # LIMPIAR DATOS
        # ----------------------------------------------------

        if nombre:
            nombre = nombre.strip()

        if descripcion:
            descripcion = descripcion.strip()

        if estado:
            estado = estado.strip()

        # ----------------------------------------------------
        # VALIDAR NOMBRE
        # ----------------------------------------------------

        if not nombre:

            return jsonify({
                'success': False,
                'message': 'El nombre de la categoría es obligatorio'
            }), 400

        # ----------------------------------------------------
        # CONEXIÓN
        # ----------------------------------------------------

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # ----------------------------------------------------
        # VERIFICAR SI YA EXISTE
        # ----------------------------------------------------

        cursor.execute("""
            SELECT id_categoria
            FROM categorias
            WHERE LOWER(nombre) = LOWER(%s)
        """, (nombre,))

        categoria_existente = cursor.fetchone()

        if categoria_existente:

            return jsonify({
                'success': False,
                'message': 'La categoría ya existe'
            }), 409

        # ----------------------------------------------------
        # INSERTAR
        #
        # IMPORTANTE:
        # PostgreSQL utiliza RETURNING para obtener
        # el ID generado.
        # ----------------------------------------------------

        cursor.execute("""
            INSERT INTO categorias (
                nombre,
                descripcion,
                estado
            )
            VALUES (%s, %s, %s)
            RETURNING id_categoria
        """, (
            nombre,
            descripcion,
            estado
        ))

        resultado = cursor.fetchone()

        nuevo_id = resultado['id_categoria']

        # ----------------------------------------------------
        # BITÁCORA
        # ----------------------------------------------------

        id_usuario = session.get("id_usuario")

        if id_usuario:

            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="CATEGORIAS",
                accion="CREAR",
                descripcion=(
                    f"Creó la categoría '{nombre}' "
                    f"(ID {nuevo_id}, estado={estado})."
                ),
                tabla_afectada="categorias",
                id_registro=nuevo_id
            )

        # ----------------------------------------------------
        # CONFIRMAR TRANSACCIÓN
        # ----------------------------------------------------

        conn.commit()

        # ----------------------------------------------------
        # OBTENER CATEGORÍA CREADA
        # ----------------------------------------------------

        cursor.execute("""
            SELECT
                id_categoria,
                nombre,
                descripcion,
                estado
            FROM categorias
            WHERE id_categoria = %s
        """, (nuevo_id,))

        categoria = cursor.fetchone()

        return jsonify({
            'success': True,
            'message': 'Categoría creada correctamente',
            'categoria': categoria
        }), 201

    except Exception as e:

        print("Error crear_categoria:", e)

        if conn:
            conn.rollback()

        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# ============================================================
# ACTUALIZAR CATEGORÍA
# ============================================================

@categorias_bp.route('/<int:id_categoria>', methods=['PUT'])
def actualizar_categoria(id_categoria):

    conn = None
    cursor = None

    try:

        data = request.get_json()

        if not data:

            return jsonify({
                'success': False,
                'message': 'No se recibieron datos'
            }), 400

        # ----------------------------------------------------
        # OBTENER DATOS
        # ----------------------------------------------------

        nombre = data.get('nombre')
        descripcion = data.get('descripcion', '')
        estado = data.get('estado', 'Activo')

        # ----------------------------------------------------
        # LIMPIAR DATOS
        # ----------------------------------------------------

        if nombre:
            nombre = nombre.strip()

        if descripcion:
            descripcion = descripcion.strip()

        if estado:
            estado = estado.strip()

        # ----------------------------------------------------
        # VALIDAR NOMBRE
        # ----------------------------------------------------

        if not nombre:

            return jsonify({
                'success': False,
                'message': 'El nombre de la categoría es obligatorio'
            }), 400

        # ----------------------------------------------------
        # CONEXIÓN
        # ----------------------------------------------------

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # ----------------------------------------------------
        # VERIFICAR QUE EXISTE
        # ----------------------------------------------------

        cursor.execute("""
            SELECT
                id_categoria,
                nombre,
                descripcion,
                estado
            FROM categorias
            WHERE id_categoria = %s
        """, (id_categoria,))

        categoria_existente = cursor.fetchone()

        if not categoria_existente:

            return jsonify({
                'success': False,
                'message': 'Categoría no encontrada'
            }), 404

        # ----------------------------------------------------
        # VERIFICAR NOMBRE DUPLICADO
        # ----------------------------------------------------

        cursor.execute("""
            SELECT id_categoria
            FROM categorias
            WHERE LOWER(nombre) = LOWER(%s)
            AND id_categoria <> %s
        """, (
            nombre,
            id_categoria
        ))

        nombre_existente = cursor.fetchone()

        if nombre_existente:

            return jsonify({
                'success': False,
                'message': 'Ya existe otra categoría con ese nombre'
            }), 409

        # ----------------------------------------------------
        # ACTUALIZAR
        # ----------------------------------------------------

        cursor.execute("""
            UPDATE categorias
            SET
                nombre = %s,
                descripcion = %s,
                estado = %s
            WHERE id_categoria = %s
            RETURNING
                id_categoria,
                nombre,
                descripcion,
                estado
        """, (
            nombre,
            descripcion,
            estado,
            id_categoria
        ))

        categoria_actualizada = cursor.fetchone()

        # ----------------------------------------------------
        # BITÁCORA
        # ----------------------------------------------------

        id_usuario = session.get("id_usuario")

        if id_usuario:

            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="CATEGORIAS",
                accion="EDITAR",
                descripcion=(
                    f"Actualizó la categoría "
                    f"'{nombre}' (ID {id_categoria})."
                ),
                tabla_afectada="categorias",
                id_registro=id_categoria
            )

        # ----------------------------------------------------
        # CONFIRMAR
        # ----------------------------------------------------

        conn.commit()

        return jsonify({
            'success': True,
            'message': 'Categoría actualizada correctamente',
            'categoria': categoria_actualizada
        }), 200

    except Exception as e:

        print("Error actualizar_categoria:", e)

        if conn:
            conn.rollback()

        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# ============================================================
# ELIMINAR CATEGORÍA
# ============================================================

@categorias_bp.route('/<int:id_categoria>', methods=['DELETE'])
def eliminar_categoria(id_categoria):

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # ----------------------------------------------------
        # VERIFICAR QUE LA CATEGORÍA EXISTE
        # ----------------------------------------------------

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
                'message': 'Categoría no encontrada'
            }), 404

        # ----------------------------------------------------
        # BUSCAR SUBCATEGORÍAS ASOCIADAS
        # ----------------------------------------------------

        cursor.execute("""
            SELECT id_subcategoria
            FROM subcategorias
            WHERE id_categoria = %s
        """, (id_categoria,))

        subcategorias = cursor.fetchall()

        if subcategorias:

            sub_ids = [
                sub['id_subcategoria']
                for sub in subcategorias
            ]

            # ------------------------------------------------
            # VERIFICAR PRODUCTOS ASOCIADOS
            # ------------------------------------------------

            cursor.execute("""
                SELECT id_producto
                FROM productos
                WHERE id_subcategoria = ANY(%s)
                LIMIT 1
            """, (sub_ids,))

            producto = cursor.fetchone()

            if producto:

                return jsonify({
                    'success': False,
                    'message': (
                        'No se puede eliminar la categoría '
                        'porque tiene productos asociados '
                        'a sus subcategorías'
                    )
                }), 400

            # ------------------------------------------------
            # EXISTEN SUBCATEGORÍAS PERO SIN PRODUCTOS
            # ------------------------------------------------

            return jsonify({
                'success': False,
                'message': (
                    'No se puede eliminar la categoría '
                    'porque tiene subcategorías asociadas'
                )
            }), 400

        # ----------------------------------------------------
        # ELIMINAR CATEGORÍA
        # ----------------------------------------------------

        cursor.execute("""
            DELETE FROM categorias
            WHERE id_categoria = %s
        """, (id_categoria,))

        # ----------------------------------------------------
        # BITÁCORA
        # ----------------------------------------------------

        id_usuario = session.get("id_usuario")

        if id_usuario:

            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="CATEGORIAS",
                accion="ELIMINAR",
                descripcion=(
                    f"Eliminó la categoría "
                    f"'{categoria['nombre']}' "
                    f"(ID {id_categoria})."
                ),
                tabla_afectada="categorias",
                id_registro=id_categoria
            )

        # ----------------------------------------------------
        # CONFIRMAR
        # ----------------------------------------------------

        conn.commit()

        return jsonify({
            'success': True,
            'message': 'Categoría eliminada correctamente'
        }), 200

    except Exception as e:

        print("Error eliminar_categoria:", e)

        if conn:
            conn.rollback()

        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()