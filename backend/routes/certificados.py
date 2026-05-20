# routes/certificados.py

from flask import Blueprint, jsonify, session, request
from db import get_db_connection
from datetime import datetime
from decimal import Decimal
from utils.bitacora import registrar_bitacora


certificados_bp = Blueprint(
    'certificados_bp',
    __name__,
    url_prefix='/api/certificados'
)


def obtener_parametros_activos(cursor):
    """
    Devuelve el último registro de parametros_certificados
    (el más reciente). Se asume que es el que está en uso.
    """
    cursor.execute("""
        SELECT *
        FROM parametros_certificados
        ORDER BY id_parametro DESC
        LIMIT 1
    """)
    return cursor.fetchone()


@certificados_bp.route('/entrada/<int:id_entrada>', methods=['GET'])
def certificado_por_entrada(id_entrada):
    # 1) Validar sesión
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'Sesión expirada'}), 401

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # 2) Obtener parámetros del certificado
        parametros = obtener_parametros_activos(cursor)
        if not parametros:
            return jsonify({
                'success': False,
                'message': 'No hay parámetros de certificados configurados.'
            }), 400

        # 3) Datos generales de la entrada / donación
        cursor.execute("""
            SELECT 
                e.id_entrada,
                e.fecha_entrada,
                e.total_peso_kg,
                e.total_valor,
                t.nombre AS tipo_entrada,
                d.nombre AS donante,
                d.numero_documento
            FROM entradas e
            JOIN tipo_entrada t ON t.id_tipo_entrada = e.id_tipo_entrada
            LEFT JOIN donantes d ON d.id_donante = e.id_donante
            WHERE e.id_entrada = %s
        """, (id_entrada,))
        entrada = cursor.fetchone()

        if not entrada:
            return jsonify({
                'success': False,
                'message': 'La entrada / donación no existe.'
            }), 404

        # Formatear fecha a string legible
        if entrada.get('fecha_entrada'):
            entrada['fecha_entrada_str'] = entrada['fecha_entrada'].strftime('%Y-%m-%d')
        else:
            entrada['fecha_entrada_str'] = None

        # 4) Detalles de productos de esa entrada
        cursor.execute("""
            SELECT 
                p.nombre AS producto,
                c.nombre AS categoria,
                ed.cantidad,
                ed.peso_total_kg,
                ed.valor_producto
            FROM entrada_detalles ed
            JOIN productos p  ON p.id_producto = ed.id_producto
            JOIN categorias c ON c.id_categoria = ed.id_categoria
            WHERE ed.id_entrada = %s
        """, (id_entrada,))
        detalles = cursor.fetchall()
        id_usuario = session.get("id_usuario")
        if id_usuario:
            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="CERTIFICADOS",
                accion="GENERAR",
                descripcion=f"Generó/consultó certificado por entrada ID {id_entrada}.",
                tabla_afectada="entradas",
                id_registro=id_entrada
            )
        conn.commit()
        # 5) Respuesta JSON para que el FRONT (JS) arme el certificado
        return jsonify({
            'success': True,
            'parametros': parametros,
            'entrada': entrada,
            'detalles': detalles
        }), 200

    except Exception as e:
        print("Error certificado_por_entrada:", e)
        return jsonify({
            'success': False,
            'message': 'Error al generar los datos del certificado'
        }), 500

    finally:
        cursor.close()
        conn.close()



@certificados_bp.route('/monetaria/<int:id_donacion>', methods=['GET'])
def certificado_monetaria(id_donacion):
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'Sesión expirada'}), 401

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # 1) Traer el último registro de parámetros
        cursor.execute("""
            SELECT *
            FROM parametros_certificados
            ORDER BY id_parametro DESC
            LIMIT 1
        """)
        parametros = cursor.fetchone()

        # 2) Traer la donación monetaria + donante + método
        cursor.execute("""
            SELECT
                dm.id_donacion,
                dm.monto,
                dm.descripcion,
                dm.fecha_donacion,
                d.nombre AS donante,
                d.numero_documento,
                m.nombre AS metodo
            FROM donaciones_monetarias dm
            JOIN donantes d        ON dm.id_donante = d.id_donante
            JOIN metodos_donacion m ON dm.id_metodo = m.id_metodo
            WHERE dm.id_donacion = %s
        """, (id_donacion,))
        donacion = cursor.fetchone()

        if not donacion:
            return jsonify({
                "success": False,
                "message": "La donación monetaria no existe"
            }), 404

        # formatear fecha a string
        fecha_str = donacion["fecha_donacion"].strftime("%Y-%m-%d") if donacion["fecha_donacion"] else None
        donacion["fecha_donacion_str"] = fecha_str

        id_usuario = session.get("id_usuario")
        if id_usuario:
            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="CERTIFICADOS",
                accion="GENERAR",
                descripcion=f"Generó/consultó certificado monetario ID {id_donacion}.",
                tabla_afectada="donaciones_monetarias",
                id_registro=id_donacion
            )
            conn.commit()

        return jsonify({
            "success": True,
            "tipo": "monetaria",
            "parametros": parametros,
            "donacion": donacion
        })

    except Exception as e:
        print("Error certificado_monetaria:", e)
        return jsonify({"success": False, "message": "Error al generar certificado monetario"}), 500
    finally:
        cursor.close()
        conn.close()


@certificados_bp.route('/donante', methods=['GET'])
def certificado_por_donante():
    """
    Genera datos para certificado por DONANTE,
    pudiendo incluir:
    - donaciones en productos
    - donaciones monetarias
    - o ambos tipos

    Parámetros por query:
    - id_donante (obligatorio)
    - tipo: 'productos' | 'monetaria' | 'ambos' (default: 'productos')
    - desde (opcional, YYYY-MM-DD)
    - hasta (opcional, YYYY-MM-DD)
    """
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'Sesión expirada'}), 401

    # -----------------------------
    # 1) Parámetros de la URL
    # -----------------------------
    id_donante_str = request.args.get('id_donante', '').strip()
    tipo = request.args.get('tipo', 'productos').strip().lower()
    desde_str = request.args.get('desde', '').strip()
    hasta_str = request.args.get('hasta', '').strip()

    if not id_donante_str:
        return jsonify({
            'success': False,
            'message': 'Debe enviar id_donante en la URL.'
        }), 400

    try:
        id_donante = int(id_donante_str)
    except ValueError:
        return jsonify({
            'success': False,
            'message': 'id_donante debe ser un número entero.'
        }), 400

    # Normalizamos tipo
    if tipo not in ('productos', 'monetaria', 'ambos'):
        tipo = 'productos'

    # Fechas opcionales
    fecha_desde = None
    fecha_hasta = None

    if desde_str:
        try:
            fecha_desde = datetime.fromisoformat(desde_str).date()
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'La fecha "desde" no tiene un formato válido (YYYY-MM-DD).'
            }), 400

    if hasta_str:
        try:
            fecha_hasta = datetime.fromisoformat(hasta_str).date()
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'La fecha "hasta" no tiene un formato válido (YYYY-MM-DD).'
            }), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # -----------------------------
        # 2) Parámetros del certificado
        # -----------------------------
        parametros = obtener_parametros_activos(cursor)
        if not parametros:
            return jsonify({
                'success': False,
                'message': 'No hay parámetros de certificados configurados.'
            }), 400

        # -----------------------------
        # 3) Datos del DONANTE
        # -----------------------------
        cursor.execute("""
            SELECT id_donante, nombre, numero_documento
            FROM donantes
            WHERE id_donante = %s
              AND estado = 'Activo'
        """, (id_donante,))
        donante = cursor.fetchone()

        if not donante:
            return jsonify({
                'success': False,
                'message': 'El donante no existe o está inactivo.'
            }), 404

        # ------------------------------------------------------
        # 4) BLOQUE PRODUCTOS (donaciones en especie)
        # ------------------------------------------------------
        productos_data = {
            'detalles': [],
            'total_kg': 0.0,
            'total_valor': 0.0
        }

        if tipo in ('productos', 'ambos'):
            filtros = [
                "e.estado = 'Activo'",
                "e.id_donante = %s",
                "(t.nombre LIKE '%donación%' OR t.nombre LIKE '%donacion%')"
            ]
            params = [id_donante]

            if fecha_desde:
                filtros.append("DATE(e.fecha_entrada) >= %s")
                params.append(fecha_desde)

            if fecha_hasta:
                filtros.append("DATE(e.fecha_entrada) <= %s")
                params.append(fecha_hasta)

            where_clause = "WHERE " + " AND ".join(filtros)

            sql_prod = f"""
                SELECT
                    p.nombre AS producto,
                    c.nombre AS categoria,
                    SUM(ed.cantidad)           AS cantidad,
                    SUM(ed.peso_total_kg)      AS peso_total_kg,
                    SUM(ed.valor_producto * ed.cantidad) AS valor_total
                FROM entradas e
                JOIN tipo_entrada t      ON t.id_tipo_entrada = e.id_tipo_entrada
                JOIN entrada_detalles ed ON ed.id_entrada = e.id_entrada
                JOIN productos p         ON p.id_producto = ed.id_producto
                JOIN categorias c        ON c.id_categoria = ed.id_categoria
                {where_clause}
                GROUP BY p.nombre, c.nombre
                ORDER BY p.nombre ASC
            """

            cursor.execute(sql_prod, params)
            rows_prod = cursor.fetchall()

            detalles = []
            total_kg = Decimal('0')
            total_valor = Decimal('0')

            for r in rows_prod:
                peso = Decimal(str(r['peso_total_kg'] or 0))
                valor = Decimal(str(r['valor_total'] or 0))
                total_kg += peso
                total_valor += valor

                detalles.append({
                    'producto': r['producto'],
                    'categoria': r['categoria'],
                    'cantidad': int(r['cantidad'] or 0),
                    'peso_total_kg': float(peso),
                    'valor_total': float(valor)
                })

            productos_data = {
                'detalles': detalles,
                'total_kg': float(total_kg),
                'total_valor': float(total_valor)
            }

        # ------------------------------------------------------
        # 5) BLOQUE MONETARIO
        # ------------------------------------------------------
        monetaria_data = {
            'total_monto': 0.0,
            'fecha_primera': None,
            'fecha_ultima': None
        }

        if tipo in ('monetaria', 'ambos'):
            filtros_m = [
                "dm.id_donante = %s",
                "dm.estado = 'Activo'"
            ]
            params_m = [id_donante]

            if fecha_desde:
                filtros_m.append("DATE(dm.fecha_donacion) >= %s")
                params_m.append(fecha_desde)

            if fecha_hasta:
                filtros_m.append("DATE(dm.fecha_donacion) <= %s")
                params_m.append(fecha_hasta)

            where_m = "WHERE " + " AND ".join(filtros_m)

            sql_mon = f"""
                SELECT
                    SUM(dm.monto)          AS total_monto,
                    MIN(dm.fecha_donacion) AS fecha_primera,
                    MAX(dm.fecha_donacion) AS fecha_ultima
                FROM donaciones_monetarias dm
                {where_m}
            """

            cursor.execute(sql_mon, params_m)
            row_m = cursor.fetchone()

            if row_m and row_m['total_monto'] is not None:
                total_monto = float(row_m['total_monto'] or 0)
                f1 = row_m['fecha_primera']
                f2 = row_m['fecha_ultima']
                monetaria_data = {
                    'total_monto': total_monto,
                    'fecha_primera': f1.strftime('%Y-%m-%d') if f1 else None,
                    'fecha_ultima': f2.strftime('%Y-%m-%d') if f2 else None
                }
        id_usuario = session.get("id_usuario")
        if id_usuario:
            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="CERTIFICADOS",
                accion="GENERAR",
                descripcion=f"Generó/consultó certificado por donante ID {id_donante} (tipo={tipo}).",
                tabla_afectada="donantes",
                id_registro=id_donante
            )
            conn.commit()
        # ------------------------------------------------------
        # 6) Respuesta final
        # ------------------------------------------------------
        return jsonify({
            'success': True,
            'parametros': parametros,
            'donante': donante,
            'productos': productos_data,
            'monetaria': monetaria_data
        }), 200

    except Exception as e:
        print("Error certificado_por_donante:", e)
        return jsonify({
            'success': False,
            'message': 'Error al generar los datos del certificado por donante'
        }), 500

    finally:
        cursor.close()
        conn.close()
