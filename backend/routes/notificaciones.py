# routes/notificaciones.py

from flask import Blueprint, jsonify, session
from database import get_db_connection
import pymysql
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from psycopg2.extras import RealDictCursor

notificaciones_bp = Blueprint('notificaciones_bp', __name__, url_prefix='/api/notificaciones')


# ========= Helper para formatear kg =========
def format_kg(value):
    try:
        num = Decimal(str(value or 0))
    except (InvalidOperation, TypeError, ValueError):
        return "0"
    if num == num.to_integral():
        return str(int(num))
    return f"{num:.3f}".rstrip('0').rstrip('.')


@notificaciones_bp.route('/', methods=['GET'])
def obtener_notificaciones():
    """
    Devuelve una lista de notificaciones calculadas al vuelo:
    - Productos próximos a vencer
    - Productos vencidos
    - Productos con stock bajo o agotado
    """
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'Sesión expirada'}), 401

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    hoy = date.today()
    dias_alerta = 7          # rango de "próximo a vencer"
    limite_prox = hoy + timedelta(days=dias_alerta)

    notificaciones = []

    try:
        # ==============================
        # 1) PRODUCTOS PRÓXIMOS A VENCER
        #    (por producto + bodega + ubicación + fecha)
        # ==============================
        sql_prox_vencer = """
            SELECT
                p.id_producto,
                p.nombre AS producto,
                ed.fecha_vencimiento,
                SUM(ed.peso_total_kg) AS cantidad_kg,
                b.nombre_bodega AS bodega,
                ed.bodega_texto AS ubicacion
            FROM entrada_detalles ed
            JOIN entradas e   ON e.id_entrada = ed.id_entrada
            JOIN productos p  ON p.id_producto = ed.id_producto
            JOIN bodegas b    ON b.id_bodega = ed.id_bodega
            WHERE e.estado = 'Activo'
                AND ed.fecha_vencimiento IS NOT NULL
                AND ed.fecha_vencimiento >= %s
                AND ed.fecha_vencimiento <= %s
            GROUP BY
                p.id_producto,
                p.nombre,
                ed.fecha_vencimiento,
                b.nombre_bodega,
                ed.bodega_texto
            ORDER BY ed.fecha_vencimiento ASC;
        """
        cursor.execute(sql_prox_vencer, (hoy, limite_prox))
        filas = cursor.fetchall()

        for row in filas:
            fecha_venc = row["fecha_vencimiento"]
            dias_restantes = (fecha_venc - hoy).days if fecha_venc else None
            cant_str = format_kg(row["cantidad_kg"])

            mensaje = (
                f"El producto '{row['producto']}' (ID {row['id_producto']}) tiene "
                f"{cant_str} kg que vencen el {fecha_venc} "
                f"en la bodega '{row['bodega']}' (ubicación: {row['ubicacion'] or '-'})."
            )

            notificaciones.append({
                "tipo": "proximo_vencer",
                "nivel": "warning",
                "mensaje": mensaje,
                "id_producto": row["id_producto"],
                "producto": row["producto"],
                "bodega": row["bodega"],
                "ubicacion": row["ubicacion"],
                "fecha_vencimiento": fecha_venc.isoformat() if fecha_venc else None,
                "stock_kg": float(row["cantidad_kg"] or 0),
                "dias_restantes": dias_restantes,
                "fecha_notificacion": hoy.isoformat()
            })

        # ==============================
        # 2) PRODUCTOS YA VENCIDOS
        # ==============================
        sql_vencidos = """
            SELECT
                p.id_producto,
                p.nombre AS producto,
                ed.fecha_vencimiento,
                SUM(ed.peso_total_kg) AS cantidad_kg,
                b.nombre_bodega AS bodega,
                ed.bodega_texto AS ubicacion
            FROM entrada_detalles ed
            JOIN entradas e   ON e.id_entrada = ed.id_entrada
            JOIN productos p  ON p.id_producto = ed.id_producto
            JOIN bodegas b    ON b.id_bodega = ed.id_bodega
            WHERE e.estado = 'Activo'
              AND ed.fecha_vencimiento IS NOT NULL
              AND ed.fecha_vencimiento < %s
            GROUP BY
                p.id_producto,
                p.nombre,
                ed.fecha_vencimiento,
                b.nombre_bodega,
                ed.bodega_texto
            ORDER BY ed.fecha_vencimiento ASC;
        """
        cursor.execute(sql_vencidos, (hoy,))
        filas = cursor.fetchall()

        for row in filas:
            fecha_venc = row["fecha_vencimiento"]
            dias_restantes = (fecha_venc - hoy).days if fecha_venc else None
            cant_str = format_kg(row["cantidad_kg"])

            mensaje = (
                f"El producto vencido '{row['producto']}' (ID {row['id_producto']}) tiene "
                f"{cant_str} kg con fecha {fecha_venc} "
                f"en la bodega '{row['bodega']}' (ubicación: {row['ubicacion'] or '-'})."
            )

            notificaciones.append({
                "tipo": "vencido",
                "nivel": "danger",
                "mensaje": mensaje,
                "id_producto": row["id_producto"],
                "producto": row["producto"],
                "bodega": row["bodega"],
                "ubicacion": row["ubicacion"],
                "fecha_vencimiento": fecha_venc.isoformat() if fecha_venc else None,
                "stock_kg": float(row["cantidad_kg"] or 0),
                "dias_restantes": dias_restantes,
                "fecha_notificacion": hoy.isoformat()
            })

        # ==============================
        # 3) STOCK BAJO / AGOTADO
        # ==============================
        sql_stock_bajo = """
            SELECT
                p.id_producto,
                p.nombre AS producto,
                p.stock_minimo,
                inv.cantidad_total
            FROM inventario_productos inv
            JOIN productos p ON p.id_producto = inv.id_producto
            WHERE inv.cantidad_total <= p.stock_minimo
            ORDER BY inv.cantidad_total ASC;
        """
        cursor.execute(sql_stock_bajo)
        filas = cursor.fetchall()

        for row in filas:
            estado = "AGOTADO" if row["cantidad_total"] <= 0 else "BAJO"
            cant_str = format_kg(row["cantidad_total"])
            min_str = format_kg(row["stock_minimo"])

            mensaje = (
                f"Stock {estado} del producto '{row['producto']}' (ID {row['id_producto']}): "
                f"{cant_str} kg (mínimo {min_str} kg)."
            )

            notificaciones.append({
                "tipo": "stock_bajo" if estado == "BAJO" else "stock_agotado",
                "nivel": "danger" if estado == "AGOTADO" else "warning",
                "mensaje": mensaje,
                "id_producto": row["id_producto"],
                "producto": row["producto"],
                "stock_kg": float(row["cantidad_total"] or 0),
                "stock_minimo_kg": float(row["stock_minimo"] or 0),
                "fecha_notificacion": hoy.isoformat()
            })

        return jsonify({
            "success": True,
            "items": notificaciones
        })

    except Exception as e:
        print("Error obteniendo notificaciones:", e)
        return jsonify({
            "success": False,
            "message": "Error al obtener las notificaciones"
        }), 500

    finally:
        cursor.close()
        conn.close()




# =========================
# marcar leidos notificaciones
# =========================
@notificaciones_bp.route("/<int:id_notificacion>/marcar-leida", methods=["POST"])
def api_marcar_notificacion_leida(id_notificacion):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            """
            UPDATE notificaciones
            SET leida = 1
            WHERE id_notificacion = %s AND eliminada = 0
            """,
            (id_notificacion,)
        )
        conn.commit()

        if cur.rowcount == 0:
            cur.close()
            conn.close()
            return jsonify(success=False, message="Notificación no encontrada."), 404

        cur.close()
        conn.close()
        return jsonify(success=True, id=id_notificacion)

    except Exception as e:
        print("Error api_marcar_notificacion_leida:", e)
        return jsonify(success=False, message="Error al marcar la notificación como leída."), 500
  

# =========================
# eliminar notificaciones
# =========================

# 🔹 NUEVO: eliminar (marcar como eliminada)
@notificaciones_bp.route("/<int:id_notificacion>/eliminar", methods=["DELETE", "POST"])
def api_eliminar_notificacion(id_notificacion):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            """
            UPDATE notificaciones
            SET eliminada = 1
            WHERE id_notificacion = %s
            """,
            (id_notificacion,)
        )
        conn.commit()

        if cur.rowcount == 0:
            cur.close()
            conn.close()
            return jsonify(success=False, message="Notificación no encontrada."), 404

        cur.close()
        conn.close()
        return jsonify(success=True, id=id_notificacion)

    except Exception as e:
        print("Error api_eliminar_notificacion:", e)
        return jsonify(success=False, message="Error al eliminar la notificación."), 500
