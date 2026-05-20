from flask import Blueprint, jsonify, request, session
from database import get_db_connection
from datetime import datetime, timedelta
from utils.bitacora import registrar_bitacora

reportes_cat_bp = Blueprint('reportes_cat_bp', __name__)

@reportes_cat_bp.route('/reportes/categorias/data', methods=['GET'])
def data_reporte_categorias():
    fecha_desde_str = request.args.get('desde', '').strip()
    fecha_hasta_str = request.args.get('hasta', '').strip()
    filtro_categoria = request.args.get('categoria', '').strip()

    hoy = datetime.today().date()

    if not fecha_hasta_str:
        fecha_hasta = hoy
    else:
        fecha_hasta = datetime.fromisoformat(fecha_hasta_str).date()

    if not fecha_desde_str:
        fecha_desde = fecha_hasta - timedelta(days=30)
    else:
        fecha_desde = datetime.fromisoformat(fecha_desde_str).date()

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        sql = """
            SELECT
                c.id_categoria,
                c.nombre AS categoria,
                COUNT(DISTINCT ed.id_producto) AS num_productos,
                COUNT(DISTINCT e.id_entrada) AS num_donaciones,
                SUM(ed.cantidad) AS cantidad_unidades,
                SUM(ed.peso_total_kg) AS total_kg,
                SUM(ed.valor_producto * ed.cantidad) AS total_valor
            FROM entradas e
            JOIN entrada_detalles ed ON ed.id_entrada = e.id_entrada
            JOIN categorias c ON c.id_categoria = ed.id_categoria
            WHERE DATE(e.fecha_entrada) BETWEEN %s AND %s
        """
        params = [fecha_desde, fecha_hasta]

        if filtro_categoria:
            sql += " AND c.nombre LIKE %s"
            params.append(f"%{filtro_categoria}%")

        sql += " GROUP BY c.id_categoria ORDER BY total_kg DESC"

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        items = []
        for r in rows:
            items.append({
                "id_categoria": r["id_categoria"],
                "categoria": r["categoria"],
                "num_donaciones": r["num_donaciones"],
                "total_kg": r["total_kg"],
                "total_valor": r["total_valor"]
            })

        # -----------------------------
        # Bitácora (consulta de reporte)
        # -----------------------------
        id_usuario = session.get("id_usuario")
        if id_usuario:
            descripcion_bit = (
                f"Consultó reporte por categorías "
                f"(desde {fecha_desde} hasta {fecha_hasta}"
                f"{', filtro categoria: ' + filtro_categoria if filtro_categoria else ''})"
            )

            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="REPORTES",
                accion="CONSULTAR",
                descripcion=descripcion_bit,
                tabla_afectada="categorias",
                id_registro=None
            )
            conn.commit()

        return jsonify({
            "success": True,
            "items": items,
            "totales": {
                "total_kg": sum(item["total_kg"] for item in items),
                "total_valor": sum(item["total_valor"] for item in items)
            }
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
