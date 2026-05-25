# routes/registro_donacion.py
from flask import Blueprint, request, jsonify, session, current_app
from db import get_db_connection
from datetime import datetime, timedelta
from decimal import Decimal
from utils.bitacora import registrar_bitacora
from psycopg2.extras import RealDictCursor

import os
import json
import uuid
from werkzeug.utils import secure_filename

registro_donacion_bp = Blueprint(
    'registro_donacion_bp',
    __name__,
    url_prefix='/api/registro_donacion'
)

# =========================================
# Helpers internos
# =========================================
def obtener_nombre_tipo_entrada(cursor, id_tipo_entrada):
    """
    Devuelve el nombre del tipo de entrada (Donación, Compra, Intercambio...)
    o None si no existe / está inactivo.
    """
    cursor.execute("""
        SELECT nombre 
        FROM tipo_entrada 
        WHERE id_tipo_entrada = %s AND estado = 'Activo'
    """, (id_tipo_entrada,))
    row = cursor.fetchone()
    return row['nombre'] if row else None


def obtener_id_categoria_fruver(cursor):
    """
    Busca la categoría FRUVER por nombre, sin depender del ID.
    Devuelve id_categoria o None si no existe.
    """
    cursor.execute("""
        SELECT id_categoria 
        FROM categorias 
        WHERE LOWER(nombre) = 'fruver'
    """)
    row = cursor.fetchone()
    return row['id_categoria'] if row else None


def existe_donante(cursor, id_donante):
    """
    Verifica si existe el donante.
    """
    if not id_donante:
        return False
    cursor.execute("""
        SELECT id_donante 
        FROM donantes 
        WHERE id_donante = %s AND estado = 'Activo'
    """, (id_donante,))
    return cursor.fetchone() is not None


# =========================================
# REGISTRAR UNA ENTRADA / DONACIÓN
# =========================================
@registro_donacion_bp.route('/', methods=['POST'])
def registrar_donacion():
    # Verificar sesión
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'Sesión expirada'}), 401

    # ============================
    # 1. Obtener datos y archivos
    # ============================
    content_type = (request.content_type or "").lower()

    # Por compatibilidad: si llega JSON puro, seguimos aceptándolo
    if content_type.startswith("application/json"):
        data = request.get_json() or {}
        archivos = []
    else:
        # multipart/form-data: datos en request.form y archivos en request.files
        data = request.form.to_dict()
        archivos = request.files.getlist("anexos")

    # Campos básicos
    id_tipo_entrada = data.get('id_tipo_entrada')
    id_donante = data.get('id_donante')
    fecha_entrada_str = data.get('fecha_entrada')
    observacion = data.get('observacion', '')

    # Productos puede venir como lista (JSON) o como string JSON
    productos_raw = data.get('productos', [])

    if isinstance(productos_raw, str):
        try:
            productos = json.loads(productos_raw) if productos_raw else []
        except json.JSONDecodeError:
            return jsonify({
                'success': False,
                'message': 'El formato de productos no es válido (JSON inválido).'
            }), 400
    else:
        productos = productos_raw or []

    # -----------------------------
    # 2. Validaciones básicas
    # -----------------------------
    if not id_tipo_entrada:
        return jsonify({'success': False, 'message': 'Debe seleccionar un tipo de entrada'}), 400

    if not productos:
        return jsonify({'success': False, 'message': 'Debe agregar al menos un producto'}), 400

    # Convertir fecha_entrada
    if fecha_entrada_str:
        try:
            fecha_entrada = datetime.fromisoformat(fecha_entrada_str)
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'La fecha de entrada no tiene un formato válido'
            }), 400
    else:
        fecha_entrada = datetime.now()

    # Abrir conexión
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # -----------------------------
        # 3. Validar tipo de entrada y donante
        # -----------------------------
        nombre_tipo = obtener_nombre_tipo_entrada(cursor, id_tipo_entrada)
        if not nombre_tipo:
            return jsonify({
                'success': False,
                'message': 'El tipo de entrada no existe o está inactivo'
            }), 400

        nombre_tipo_lower = nombre_tipo.lower()

        if 'donación' in nombre_tipo_lower or 'donacion' in nombre_tipo_lower:
            if not existe_donante(cursor, id_donante):
                return jsonify({
                    'success': False,
                    'message': 'El donante no existe o está inactivo. '
                               'Por favor, regístrelo en la página de creación de donantes.'
                }), 400

        # -----------------------------
        # 4. Obtener id_categoria FRUVER
        # -----------------------------
        id_categoria_fruver = obtener_id_categoria_fruver(cursor)

        # -----------------------------
        # 5. Insertar cabecera ENTRADAS
        # -----------------------------
        cursor.execute("""
            INSERT INTO entradas (
                id_tipo_entrada, id_donante,
                fecha_entrada, observacion, total_peso_kg, total_valor
            )
            VALUES (%s, %s, %s, %s, 0, 0)
        """, (id_tipo_entrada, id_donante, fecha_entrada, observacion))

        conn.commit()
        id_entrada = cursor.lastrowid

        total_peso_kg = Decimal('0')
        total_valor = Decimal('0')

        # -----------------------------
        # 6. Insertar DETALLES
        # -----------------------------
        for p in productos:
            id_producto = p.get('id_producto')
            cantidad_raw = p.get('cantidad')
            peso_unitario_raw = p.get('peso_unitario')
            id_unidad = p.get('id_unidad')
            id_bodega = p.get('id_bodega')
            valor_producto_raw = p.get('valor_producto')
            fecha_venc_str = p.get('fecha_vencimiento')

            bodega_texto = p.get('bodega_texto') or None
            codigo_barras = p.get('codigo_barras') or None

            if not id_producto or cantidad_raw is None or peso_unitario_raw is None or not id_unidad or not id_bodega:
                conn.rollback()
                return jsonify({
                    'success': False,
                    'message': 'Datos incompletos en uno de los productos.'
                }), 400

            try:
                cantidad = Decimal(str(cantidad_raw))
                peso_unitario = Decimal(str(peso_unitario_raw))
            except Exception:
                conn.rollback()
                return jsonify({
                    'success': False,
                    'message': 'Cantidad o peso unitario inválidos en uno de los productos.'
                }), 400

            try:
                if valor_producto_raw in (None, "", "0"):
                    valor_producto = Decimal('0')
                else:
                    valor_producto = Decimal(str(valor_producto_raw))
            except Exception:
                conn.rollback()
                return jsonify({
                    'success': False,
                    'message': 'El valor del producto no es válido en uno de los productos.'
                }), 400

            peso_total_kg = cantidad * peso_unitario
            valor_total_producto = valor_producto * cantidad

            total_peso_kg += peso_total_kg
            total_valor += valor_total_producto

            cursor.execute("""
                SELECT id_categoria 
                FROM productos 
                WHERE id_producto = %s
            """, (id_producto,))
            prod_row = cursor.fetchone()
            if not prod_row:
                conn.rollback()
                return jsonify({
                    'success': False,
                    'crear_producto': True,
                    'message': f'El producto con ID {id_producto} no existe.'
                }), 400

            id_categoria_producto = prod_row['id_categoria']

            fecha_vencimiento = None
            if fecha_venc_str:
                try:
                    fecha_vencimiento = datetime.fromisoformat(fecha_venc_str).date()
                except ValueError:
                    conn.rollback()
                    return jsonify({
                        'success': False,
                        'message': 'La fecha de vencimiento no tiene un formato válido.'
                    }), 400

            if id_categoria_fruver and id_categoria_producto == id_categoria_fruver:
                if not fecha_vencimiento:
                    fecha_vencimiento = (fecha_entrada + timedelta(days=4)).date()

            cursor.execute("""
                INSERT INTO entrada_detalles (
                    id_entrada, id_producto, id_categoria,
                    cantidad, peso_unitario, peso_total_kg,
                    id_unidad, id_bodega, bodega_texto,
                    valor_producto, fecha_vencimiento, codigo_barras
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                id_entrada,
                id_producto,
                id_categoria_producto,
                cantidad,
                peso_unitario,
                peso_total_kg,
                id_unidad,
                id_bodega,
                bodega_texto,
                valor_producto,
                fecha_vencimiento,
                codigo_barras
            ))

        # -----------------------------
        # 7. Actualizar totales cabecera
        # -----------------------------
        cursor.execute("""
            UPDATE entradas
            SET total_peso_kg = %s,
                total_valor   = %s
            WHERE id_entrada = %s
        """, (total_peso_kg, total_valor, id_entrada))

        # -----------------------------
        # 8. Guardar ARCHIVOS (anexos)
        # -----------------------------
        if archivos:
            base_rel = current_app.config.get("UPLOAD_FOLDER_ENTRADAS", "uploads/entradas")
            base_abs = os.path.join(current_app.root_path, base_rel)
            os.makedirs(base_abs, exist_ok=True)

            for f in archivos:
                if not f or f.filename == "":
                    continue

                nombre_original = f.filename
                nombre_seguro = secure_filename(nombre_original)
                ext = os.path.splitext(nombre_seguro)[1]
                nombre_guardado = f"{id_entrada}_{uuid.uuid4().hex}{ext}"

                ruta_relativa = f"{base_rel}/{nombre_guardado}"
                ruta_absoluta = os.path.join(base_abs, nombre_guardado)

                f.save(ruta_absoluta)

                cursor.execute("""
                    INSERT INTO entrada_archivos (
                        id_entrada, nombre_original, nombre_guardado,
                        ruta_relativa, tipo_mime
                    )
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    id_entrada,
                    nombre_original,
                    nombre_guardado,
                    ruta_relativa,
                    f.mimetype
                ))

        # -----------------------------
        # 9. Registrar en bitácora
        # -----------------------------
        id_usuario = session.get('id_usuario')
        if id_usuario:
            descripcion = (
                f"Registró la entrada/donación ID {id_entrada} "
                f"por {total_peso_kg} kg y valor {total_valor}"
            )
            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="DONACIONES",
                accion="CREAR",
                descripcion=descripcion,
                tabla_afectada="entradas",
                id_registro=id_entrada
            )

        conn.commit()

        return jsonify({
            'success': True,
            'message': 'Donación / entrada registrada correctamente',
            'id_entrada': id_entrada
        }), 201

    except Exception as e:
        conn.rollback()
        print("Error registrar_donacion:", e)
        return jsonify({'success': False, 'message': f'Error del servidor: {str(e)}'}), 500

    finally:
        cursor.close()
        conn.close()
# Fin de archivo