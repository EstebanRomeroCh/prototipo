from flask import Blueprint, request, jsonify, session, current_app
from db import get_db_connection
from datetime import datetime
from decimal import Decimal, InvalidOperation
from utils.bitacora import registrar_bitacora
import os
import uuid
from werkzeug.utils import secure_filename
from psycopg2.extras import RealDictCursor


registro_monetaria_bp = Blueprint(
    'registro_monetaria_bp',
    __name__,
    url_prefix='/api/donacion_monetaria'
)


# =========================================================
# VERIFICAR SI EXISTE DONANTE
# =========================================================
def existe_donante(cursor, id_donante):
    cursor.execute("""
        SELECT id_donante
        FROM donantes
        WHERE id_donante = %s
          AND estado = 'Activo'
    """, (id_donante,))

    return cursor.fetchone() is not None


# =========================================================
# VERIFICAR SI EXISTE MÉTODO DE DONACIÓN
# =========================================================
def existe_metodo(cursor, id_metodo):
    cursor.execute("""
        SELECT id_metodo
        FROM metodos_donacion
        WHERE id_metodo = %s
          AND estado = 'Activo'
    """, (id_metodo,))

    return cursor.fetchone() is not None


# =========================================================
# VERIFICAR DONANTE PARA EDICIÓN
# =========================================================
def existe_donante_simple(cursor, id_donante):

    if not id_donante:
        return False

    cursor.execute("""
        SELECT id_donante
        FROM donantes
        WHERE id_donante = %s
          AND estado = 'Activo'
    """, (id_donante,))

    return cursor.fetchone() is not None


# =========================================================
# REGISTRAR DONACIÓN MONETARIA
# POST /api/donacion_monetaria/
# =========================================================
@registro_monetaria_bp.route('/', methods=['POST'])
def registrar_donacion_monetaria():

    # -----------------------------------------------------
    # VALIDAR SESIÓN
    # -----------------------------------------------------
    if 'usuario' not in session:
        return jsonify({
            'success': False,
            'message': 'Sesión expirada'
        }), 401

    # -----------------------------------------------------
    # DETECTAR JSON O FORM DATA
    # -----------------------------------------------------
    content_type = (request.content_type or "").lower()

    if content_type.startswith("application/json"):

        # JSON normal, sin archivos
        data = request.get_json() or {}
        archivos = []

    else:

        # FormData, puede contener archivos
        data = request.form.to_dict()

        # El HTML debe tener:
        # <input type="file" name="anexosMon">
        archivos = request.files.getlist("anexosMon")

    # -----------------------------------------------------
    # OBTENER DATOS
    # -----------------------------------------------------
    id_donante = data.get("id_donante")
    id_metodo = data.get("id_metodo")
    monto = data.get("monto")
    descripcion = data.get("descripcion", "")
    fecha_donacion_str = data.get("fecha_donacion")

    # -----------------------------------------------------
    # VALIDAR DONANTE
    # -----------------------------------------------------
    if not id_donante:

        return jsonify({
            'success': False,
            'message': 'Debe seleccionar un donante válido'
        }), 400

    # -----------------------------------------------------
    # VALIDAR MONTO
    # -----------------------------------------------------
    if monto is None or str(monto).strip() == "":

        return jsonify({
            'success': False,
            'message': 'Debe indicar un monto'
        }), 400

    try:

        monto_decimal = Decimal(str(monto))

        if monto_decimal <= 0:

            return jsonify({
                'success': False,
                'message': 'El monto debe ser mayor que cero'
            }), 400

    except (InvalidOperation, ValueError, TypeError):

        return jsonify({
            'success': False,
            'message': 'El monto no es válido'
        }), 400

    # -----------------------------------------------------
    # VALIDAR MÉTODO
    # -----------------------------------------------------
    if not id_metodo:

        return jsonify({
            'success': False,
            'message': 'Debe seleccionar un método de donación'
        }), 400

    # -----------------------------------------------------
    # CONVERTIR FECHA
    # -----------------------------------------------------
    if fecha_donacion_str:

        try:

            # Si viene solamente YYYY-MM-DD
            if len(fecha_donacion_str) == 10:

                fecha_donacion = datetime.strptime(
                    fecha_donacion_str,
                    "%Y-%m-%d"
                )

            else:

                fecha_donacion = datetime.fromisoformat(
                    fecha_donacion_str
                )

        except Exception:

            return jsonify({
                'success': False,
                'message': 'Fecha inválida'
            }), 400

    else:

        fecha_donacion = datetime.now()

    # -----------------------------------------------------
    # CONEXIÓN
    # -----------------------------------------------------
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:

        # =================================================
        # VALIDAR DONANTE
        # =================================================
        if not existe_donante(cursor, id_donante):

            return jsonify({
                'success': False,
                'message': (
                    'El donante no existe o está inactivo. '
                    'Debe crearlo primero.'
                )
            }), 400

        # =================================================
        # VALIDAR MÉTODO
        # =================================================
        if not existe_metodo(cursor, id_metodo):

            return jsonify({
                'success': False,
                'message': 'El método de donación no es válido.'
            }), 400

        # =================================================
        # INSERTAR DONACIÓN MONETARIA
        #
        # IMPORTANTE:
        # PostgreSQL utiliza RETURNING en lugar de lastrowid
        # =================================================
        cursor.execute("""
            INSERT INTO donaciones_monetarias (
                id_donante,
                id_metodo,
                monto,
                descripcion,
                fecha_donacion
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id_donacion
        """, (
            id_donante,
            id_metodo,
            monto_decimal,
            descripcion,
            fecha_donacion
        ))

        fila = cursor.fetchone()

        if not fila:

            raise Exception(
                "No fue posible obtener el ID de la donación monetaria."
            )

        id_donacion = fila["id_donacion"]

        # =================================================
        # BITÁCORA
        # =================================================
        try:

            id_usuario = session.get("id_usuario")

            if id_usuario:

                descripcion_bit = (
                    f"Registró donación monetaria ID {id_donacion} "
                    f"(Donante ID {id_donante}, "
                    f"Método ID {id_metodo}, "
                    f"Monto {monto_decimal})"
                )

                registrar_bitacora(
                    cursor,
                    id_usuario=id_usuario,
                    modulo="DONACIONES_MONETARIAS",
                    accion="CREAR",
                    descripcion=descripcion_bit,
                    tabla_afectada="donaciones_monetarias",
                    id_registro=id_donacion
                )

        except Exception as e:

            print(
                "Advertencia bitácora donación monetaria:",
                e
            )

        # =================================================
        # GUARDAR ANEXOS
        # =================================================
        if archivos:

            base_rel = current_app.config.get(
                "UPLOAD_FOLDER_MONETARIAS",
                "uploads/monetarias"
            )

            base_abs = os.path.join(
                current_app.root_path,
                base_rel
            )

            os.makedirs(
                base_abs,
                exist_ok=True
            )

            for archivo in archivos:

                # Ignorar archivos vacíos
                if not archivo:
                    continue

                if not archivo.filename:
                    continue

                # -----------------------------------------
                # NOMBRE ORIGINAL
                # -----------------------------------------
                nombre_original = archivo.filename

                # -----------------------------------------
                # NOMBRE SEGURO
                # -----------------------------------------
                nombre_seguro = secure_filename(
                    nombre_original
                )

                # Si secure_filename devuelve vacío
                if not nombre_seguro:

                    continue

                # -----------------------------------------
                # EXTENSIÓN
                # -----------------------------------------
                ext = os.path.splitext(
                    nombre_seguro
                )[1]

                # -----------------------------------------
                # NOMBRE ÚNICO
                # -----------------------------------------
                nombre_guardado = (
                    f"{id_donacion}_"
                    f"{uuid.uuid4().hex}"
                    f"{ext}"
                )

                # -----------------------------------------
                # RUTA RELATIVA
                # -----------------------------------------
                ruta_relativa = (
                    f"{base_rel}/{nombre_guardado}"
                )

                # -----------------------------------------
                # RUTA ABSOLUTA
                # -----------------------------------------
                ruta_absoluta = os.path.join(
                    base_abs,
                    nombre_guardado
                )

                # -----------------------------------------
                # GUARDAR ARCHIVO
                # -----------------------------------------
                archivo.save(
                    ruta_absoluta
                )

                # -----------------------------------------
                # REGISTRAR EN BD
                # -----------------------------------------
                cursor.execute("""
                    INSERT INTO donacion_monetaria_archivos (
                        id_donacion,
                        nombre_original,
                        nombre_guardado,
                        ruta_relativa,
                        tipo_mime
                    )
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    id_donacion,
                    nombre_original,
                    nombre_guardado,
                    ruta_relativa,
                    archivo.mimetype
                ))

        # =================================================
        # CONFIRMAR TRANSACCIÓN
        # =================================================
        conn.commit()

        # =================================================
        # RESPUESTA
        # =================================================
        return jsonify({
            'success': True,
            'message': 'Donación monetaria registrada con éxito',
            'id_donacion': id_donacion
        }), 201

    except Exception as e:

        # -----------------------------------------------
        # DESHACER TRANSACCIÓN
        # -----------------------------------------------
        conn.rollback()

        print(
            "ERROR donación monetaria:",
            e
        )

        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

    finally:

        cursor.close()
        conn.close()


# =========================================================
# EDITAR DONACIÓN MONETARIA
# PUT /api/donacion_monetaria/<id_donacion>
# =========================================================
@registro_monetaria_bp.route(
    '/<int:id_donacion>',
    methods=['PUT']
)
def editar_donacion_monetaria(id_donacion):

    # -----------------------------------------------------
    # VALIDAR SESIÓN
    # -----------------------------------------------------
    if 'usuario' not in session:

        return jsonify({
            'success': False,
            'message': 'Sesión expirada'
        }), 401

    # -----------------------------------------------------
    # OBTENER JSON
    # -----------------------------------------------------
    data = request.get_json() or {}

    id_donante = data.get('id_donante')
    id_metodo = data.get('id_metodo')
    monto = data.get('monto')
    descripcion = data.get('descripcion', '')
    fecha_str = data.get('fecha_donacion')

    # -----------------------------------------------------
    # VALIDAR DONANTE
    # -----------------------------------------------------
    if not id_donante:

        return jsonify({
            'success': False,
            'message': 'Debe seleccionar un donante'
        }), 400

    # -----------------------------------------------------
    # VALIDAR MÉTODO
    # -----------------------------------------------------
    if not id_metodo:

        return jsonify({
            'success': False,
            'message': 'Debe seleccionar un método de donación'
        }), 400

    # -----------------------------------------------------
    # VALIDAR MONTO
    # -----------------------------------------------------
    try:

        monto_decimal = Decimal(str(monto))

        if monto_decimal <= 0:

            return jsonify({
                'success': False,
                'message': 'El monto debe ser mayor que cero'
            }), 400

    except (InvalidOperation, ValueError, TypeError):

        return jsonify({
            'success': False,
            'message': 'Monto inválido'
        }), 400

    # -----------------------------------------------------
    # CONEXIÓN
    # -----------------------------------------------------
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:

        # =================================================
        # BUSCAR DONACIÓN
        # =================================================
        cursor.execute("""
            SELECT *
            FROM donaciones_monetarias
            WHERE id_donacion = %s
              AND estado = 'Activo'
        """, (id_donacion,))

        row = cursor.fetchone()

        if not row:

            return jsonify({
                'success': False,
                'message': (
                    'La donación monetaria no existe '
                    'o está anulada'
                )
            }), 404

        # =================================================
        # VALIDAR DONANTE
        # =================================================
        if not existe_donante_simple(
            cursor,
            id_donante
        ):

            return jsonify({
                'success': False,
                'message': (
                    'El donante no existe o está inactivo'
                )
            }), 400

        # =================================================
        # VALIDAR MÉTODO
        # =================================================
        if not existe_metodo(
            cursor,
            id_metodo
        ):

            return jsonify({
                'success': False,
                'message': (
                    'El método de donación no es válido'
                )
            }), 400

        # =================================================
        # CONVERTIR FECHA
        # =================================================
        if fecha_str:

            try:

                if len(fecha_str) == 10:

                    fecha_donacion = datetime.strptime(
                        fecha_str,
                        "%Y-%m-%d"
                    )

                else:

                    fecha_donacion = datetime.fromisoformat(
                        fecha_str
                    )

            except Exception:

                return jsonify({
                    'success': False,
                    'message': 'Fecha inválida'
                }), 400

        else:

            fecha_donacion = datetime.now()

        # =================================================
        # ACTUALIZAR DONACIÓN
        # =================================================
        cursor.execute("""
            UPDATE donaciones_monetarias
            SET
                id_donante = %s,
                id_metodo = %s,
                monto = %s,
                descripcion = %s,
                fecha_donacion = %s
            WHERE id_donacion = %s
        """, (
            id_donante,
            id_metodo,
            monto_decimal,
            descripcion,
            fecha_donacion,
            id_donacion
        ))

        # =================================================
        # BITÁCORA
        # =================================================
        try:

            id_usuario = session.get(
                "id_usuario"
            )

            if id_usuario:

                descripcion_bit = (
                    f"Editó donación monetaria "
                    f"ID {id_donacion} "
                    f"(Donante ID {id_donante}, "
                    f"Método ID {id_metodo}, "
                    f"Monto {monto_decimal})"
                )

                registrar_bitacora(
                    cursor,
                    id_usuario=id_usuario,
                    modulo="DONACIONES_MONETARIAS",
                    accion="EDITAR",
                    descripcion=descripcion_bit,
                    tabla_afectada="donaciones_monetarias",
                    id_registro=id_donacion
                )

        except Exception as e:

            print(
                "Advertencia bitácora edición monetaria:",
                e
            )

        # =================================================
        # CONFIRMAR
        # =================================================
        conn.commit()

        return jsonify({
            'success': True,
            'message': (
                'Donación monetaria actualizada correctamente'
            )
        })

    except Exception as e:

        conn.rollback()

        print(
            "ERROR editando donación monetaria:",
            e
        )

        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

    finally:

        cursor.close()
        conn.close()