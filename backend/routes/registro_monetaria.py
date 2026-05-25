from flask import Blueprint, request, jsonify, session, current_app
from db import get_db_connection
from datetime import datetime
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


# ================================
# 🔹 Verificar si existe donante
# ================================
def existe_donante(cursor, id_donante):
    cursor.execute("""
        SELECT id_donante 
        FROM donantes 
        WHERE id_donante = %s AND estado = 'Activo'
    """, (id_donante,))
    return cursor.fetchone() is not None


# ================================
# 🔹 Verificar si método existe
# ================================
def existe_metodo(cursor, id_metodo):
    cursor.execute("""
        SELECT id_metodo 
        FROM metodos_donacion
        WHERE id_metodo = %s AND estado = 'Activo'
    """, (id_metodo,))
    return cursor.fetchone() is not None


# ================================
# ✅ REGISTRAR DONACIÓN MONETARIA
#    (ahora con ANEXOS)
# ================================
@registro_monetaria_bp.route('/', methods=['POST'])
def registrar_donacion_monetaria():

    # Validar sesión
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'Sesión expirada'}), 401

    # Detectar si viene JSON o multipart/form-data
    content_type = (request.content_type or "").lower()

    if content_type.startswith("application/json"):
        # Modo antiguo: JSON puro (sin archivos)
        data = request.get_json() or {}
        archivos = []
    else:
        # Nuevo: FormData con posibles archivos
        data = request.form.to_dict()
        # Muy importante: el name del input file en el HTML debe ser "anexosMon"
        archivos = request.files.getlist("anexosMon")

    id_donante = data.get("id_donante")
    id_metodo = data.get("id_metodo")
    monto = data.get("monto")
    descripcion = data.get("descripcion", "")
    fecha_donacion_str = data.get("fecha_donacion")

    # -----------------------------
    # Validaciones
    # -----------------------------
    if not id_donante:
        return jsonify({'success': False, 'message': 'Debe seleccionar un donante válido'}), 400

    if not monto:
        return jsonify({'success': False, 'message': 'Debe indicar un monto'}), 400

    try:
        monto_float = float(monto)
        if monto_float <= 0:
            return jsonify({'success': False, 'message': 'El monto debe ser mayor que cero'}), 400
    except ValueError:
        return jsonify({'success': False, 'message': 'El monto no es numérico'}), 400

    if not id_metodo:
        return jsonify({'success': False, 'message': 'Debe seleccionar un método de donación'}), 400

    # Convertir fecha
    if fecha_donacion_str:
        try:
            fecha_donacion = datetime.fromisoformat(fecha_donacion_str).date()
        except Exception:
            return jsonify({'success': False, 'message': 'Fecha inválida'}), 400
    else:
        fecha_donacion = datetime.now().date()

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Validar donante
        if not existe_donante(cursor, id_donante):
            return jsonify({
                'success': False,
                'message': 'El donante no existe o está inactivo. Debe crearlo primero.'
            }), 400

        # Validar método
        if not existe_metodo(cursor, id_metodo):
            return jsonify({
                'success': False,
                'message': 'El método de donación no es válido.'
            }), 400

        # Insertar la donación monetaria
        cursor.execute("""
            INSERT INTO donaciones_monetarias (
                id_donante, id_metodo, monto, descripcion, fecha_donacion
            )
            VALUES (%s, %s, %s, %s, %s)
        """, (id_donante, id_metodo, monto_float, descripcion, fecha_donacion))

        id_donacion = cursor.lastrowid

                # -----------------------------
        # 9) Registrar en bitácora
        # -----------------------------
        id_usuario = session.get("id_usuario")
        if id_usuario:
            descripcion_bit = (
                f"Registró donación monetaria ID {id_donacion} "
                f"(Donante ID {id_donante}, Método ID {id_metodo}, Monto {monto_float})"
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


        # ============================
        # Guardar ANEXOS (si los hay)
        # ============================
        if archivos:
            # Carpeta relativa para comprobantes de monetaria
            base_rel = current_app.config.get(
                "UPLOAD_FOLDER_MONETARIAS",
                "uploads/monetarias"          # por defecto
            )
            base_abs = os.path.join(current_app.root_path, base_rel)
            os.makedirs(base_abs, exist_ok=True)

            for f in archivos:
                if not f or f.filename == "":
                    continue

                nombre_original = f.filename
                nombre_seguro = secure_filename(nombre_original)
                ext = os.path.splitext(nombre_seguro)[1]
                nombre_guardado = f"{id_donacion}_{uuid.uuid4().hex}{ext}"

                ruta_relativa = f"{base_rel}/{nombre_guardado}"
                ruta_absoluta = os.path.join(base_abs, nombre_guardado)

                # Guardar archivo en disco
                f.save(ruta_absoluta)

                # Registrar en la tabla donacion_monetaria_archivos
                cursor.execute("""
                    INSERT INTO donacion_monetaria_archivos (
                        id_donacion, nombre_original, nombre_guardado,
                        ruta_relativa, tipo_mime
                    )
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    id_donacion,
                    nombre_original,
                    nombre_guardado,
                    ruta_relativa,
                    f.mimetype
                ))

        conn.commit()

        return jsonify({
            'success': True,
            'message': 'Donación monetaria registrada con éxito',
            'id_donacion': id_donacion
        }), 201

    except Exception as e:
        conn.rollback()
        print("Error donación monetaria:", e)
        return jsonify({'success': False, 'message': str(e)}), 500

    finally:
        cursor.close()
        conn.close()


# ================================
# 🔹 Helper para edición
# ================================
def existe_donante_simple(cursor, id_donante):
    if not id_donante:
        return False
    cursor.execute(
        "SELECT id_donante FROM donantes WHERE id_donante=%s AND estado='Activo'",
        (id_donante,))
    return cursor.fetchone() is not None


# ================================
# ✅ EDITAR DONACIÓN MONETARIA
#   (esta sigue con JSON simple)
# ================================
@registro_monetaria_bp.route('/<int:id_donacion>', methods=['PUT'])
def editar_donacion_monetaria(id_donacion):

    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'Sesión expirada'}), 401

    data = request.get_json() or {}

    id_donante = data.get('id_donante')
    id_metodo = data.get('id_metodo')
    monto = data.get('monto')
    descripcion = data.get('descripcion', '')
    fecha_str = data.get('fecha_donacion')

    if not id_metodo:
        return jsonify({'success': False, 'message': 'Debe seleccionar un método de donación'}), 400

    try:
        monto = float(monto)
        if monto <= 0:
            return jsonify({'success': False, 'message': 'El monto debe ser mayor que cero'}), 400
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Monto inválido'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute("""
            SELECT * FROM donaciones_monetarias
            WHERE id_donacion=%s AND estado='Activo'
        """, (id_donacion,))
        row = cursor.fetchone()

        if not row:
            return jsonify({
                'success': False,
                'message': 'La donación monetaria no existe o está anulada'
            }), 404

        if not existe_donante_simple(cursor, id_donante):
            return jsonify({
                'success': False,
                'message': 'El donante no existe o está inactivo'
            }), 400

        fecha_donacion = datetime.fromisoformat(fecha_str) if fecha_str else datetime.now()

        cursor.execute("""
            UPDATE donaciones_monetarias
            SET id_donante=%s,
                id_metodo=%s,
                monto=%s,
                descripcion=%s,
                fecha_donacion=%s
            WHERE id_donacion=%s
        """, (id_donante, id_metodo, monto, descripcion, fecha_donacion, id_donacion))
                # -----------------------------
        # Bitácora
        # -----------------------------
        id_usuario = session.get("id_usuario")
        if id_usuario:
            descripcion_bit = (
                f"Editó donación monetaria ID {id_donacion} "
                f"(Donante ID {id_donante}, Método ID {id_metodo}, Monto {monto})"
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

        conn.commit()
        return jsonify({'success': True, 'message': 'Donación monetaria actualizada correctamente'})

    except Exception as e:
        conn.rollback()
        print("ERROR editando donación monetaria:", e)
        return jsonify({'success': False, 'message': str(e)}), 500

    finally:
        cursor.close()
        conn.close()
