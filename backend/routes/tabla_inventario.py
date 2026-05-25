# routes/tabla_inventario.py

from flask import Blueprint, render_template, session, jsonify, request
from database import get_db_connection
import pymysql  
from flask import send_file
from io import BytesIO
from datetime import date
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter
from psycopg2.extras import RealDictCursor


tabla_inventario = Blueprint('tabla_inventario', __name__)

# Vista que solo devuelve el HTML (la tabla vacía)
@tabla_inventario.route('/tabla-producto', methods=['GET'])
def tabla_producto():
    if "usuario" not in session:
        return render_template("index.html"), 401 
    return render_template("tabla_producto.html", usuario=session.get("usuario"))

def _obtener_productos_inventario(q: str):
    q = (q or "").strip()

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    filtros = ["p.estado = 'Activo'", "COALESCE(inv.cantidad_total, 0) > 0"]
    params = []

    if q:
        if q.isdigit():
            filtros.append("(p.id_producto = %s OR p.nombre LIKE %s)")
            params.extend([int(q), f"%{q}%"])
        else:
            filtros.append("p.nombre LIKE %s")
            params.append(f"%{q}%")

    where_clause = "WHERE " + " AND ".join(filtros)

    sql_productos = f"""
    SELECT
        p.id_producto,
        p.nombre,
        inv.cantidad_total,
        (
            SELECT x.fecha_vencimiento
            FROM (
                SELECT
                    ed2.fecha_vencimiento,
                    (
                        SUM(ed2.peso_total_kg)
                        - COALESCE(SUM(
                            CASE WHEN s2.estado = 'Activo' THEN sd2.cantidad_kg ELSE 0 END
                        ), 0)
                    ) AS stock_kg
                FROM entrada_detalles ed2
                JOIN entradas e2
                    ON e2.id_entrada = ed2.id_entrada
                    AND e2.estado = 'Activo'
                LEFT JOIN salida_detalles sd2
                    ON sd2.id_entrada_detalle = ed2.id_detalle
                LEFT JOIN salidas s2
                    ON s2.id_salida = sd2.id_salida
                WHERE ed2.id_producto = p.id_producto
                GROUP BY ed2.fecha_vencimiento
                HAVING stock_kg > 0
                ORDER BY ed2.fecha_vencimiento ASC
                LIMIT 1
            ) x
        ) AS proximo_vencimiento,
        (
            SELECT y.nombre_bodega
            FROM (
                SELECT
                    ed3.fecha_vencimiento,
                    b3.nombre_bodega,
                    ed3.bodega_texto,
                    (
                        SUM(ed3.peso_total_kg)
                        - COALESCE(SUM(
                            CASE WHEN s3.estado = 'Activo' THEN sd3.cantidad_kg ELSE 0 END
                        ), 0)
                    ) AS stock_kg
                FROM entrada_detalles ed3
                JOIN entradas e3
                    ON e3.id_entrada = ed3.id_entrada
                    AND e3.estado = 'Activo'
                JOIN bodegas b3
                    ON b3.id_bodega = ed3.id_bodega
                LEFT JOIN salida_detalles sd3
                    ON sd3.id_entrada_detalle = ed3.id_detalle
                LEFT JOIN salidas s3
                    ON s3.id_salida = sd3.id_salida
                WHERE ed3.id_producto = p.id_producto
                GROUP BY ed3.fecha_vencimiento, b3.id_bodega, ed3.bodega_texto
                HAVING stock_kg > 0
                ORDER BY ed3.fecha_vencimiento ASC
                LIMIT 1
            ) y
        ) AS proxima_bodega,
        (
            SELECT z.bodega_texto
            FROM (
                SELECT
                    ed4.fecha_vencimiento,
                    ed4.bodega_texto,
                    (
                        SUM(ed4.peso_total_kg)
                        - COALESCE(SUM(
                            CASE WHEN s4.estado = 'Activo' THEN sd4.cantidad_kg ELSE 0 END
                        ), 0)
                    ) AS stock_kg
                FROM entrada_detalles ed4
                JOIN entradas e4
                    ON e4.id_entrada = ed4.id_entrada
                    AND e4.estado = 'Activo'
                LEFT JOIN salida_detalles sd4
                    ON sd4.id_entrada_detalle = ed4.id_detalle
                LEFT JOIN salidas s4
                    ON s4.id_salida = sd4.id_salida
                WHERE ed4.id_producto = p.id_producto
                GROUP BY ed4.fecha_vencimiento, ed4.bodega_texto
                HAVING stock_kg > 0
                ORDER BY ed4.fecha_vencimiento ASC
                LIMIT 1
            ) z
        ) AS proxima_ubicacion
    FROM inventario_productos inv
    JOIN productos p
        ON p.id_producto = inv.id_producto
    {where_clause}
    ORDER BY p.id_producto ASC;
    """

    cursor.execute(sql_productos, params)
    filas_productos = cursor.fetchall()

    sql_detalles = """
    SELECT
        ed.id_producto,
        ed.fecha_vencimiento,
        (
            SUM(ed.peso_total_kg)
            - COALESCE(SUM(
                CASE WHEN s.estado = 'Activo' THEN sd.cantidad_kg ELSE 0 END
            ), 0)
        ) AS stock_kg,
        b.nombre_bodega,
        ed.bodega_texto
    FROM entrada_detalles ed
    JOIN entradas e
        ON e.id_entrada = ed.id_entrada
        AND e.estado = 'Activo'
    JOIN bodegas b
        ON b.id_bodega = ed.id_bodega
    LEFT JOIN salida_detalles sd
        ON sd.id_entrada_detalle = ed.id_detalle
    LEFT JOIN salidas s
        ON s.id_salida = sd.id_salida
    GROUP BY
        ed.id_producto,
        ed.fecha_vencimiento,
        b.id_bodega,
        ed.bodega_texto
    HAVING stock_kg > 0
    ORDER BY ed.id_producto, ed.fecha_vencimiento;
    """

    cursor.execute(sql_detalles)
    filas_detalle = cursor.fetchall()

    cursor.close()
    conn.close()

    detalles_map = {}
    for d in filas_detalle:
        pid = d["id_producto"]
        detalles_map.setdefault(pid, []).append({
            "fecha_vencimiento": d["fecha_vencimiento"],  # date o None
            "stock_kg": float(d["stock_kg"] or 0),
            "nombre_bodega": d.get("nombre_bodega"),
            "bodega_texto": d.get("bodega_texto"),
        })

    productos = []
    for p in filas_productos:
        pid = p["id_producto"]
        productos.append({
            "id_producto": pid,
            "nombre": p["nombre"],
            "cantidad_total": float(p["cantidad_total"] or 0),
            "proximo_vencimiento": p["proximo_vencimiento"],  # date o None
            "proxima_bodega": p.get("proxima_bodega"),
            "proxima_ubicacion": p.get("proxima_ubicacion"),
            "detalles": detalles_map.get(pid, [])
        })

    return productos

#  API que devuelve los productos del inventario en JSON
@tabla_inventario.route('/api/productos', methods=['GET'])
def api_productos_inventario():
    q = request.args.get('q', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # --------- FILTROS ----------
    filtros = ["p.estado = 'Activo'", "COALESCE(inv.cantidad_total, 0) > 0"]
    params = []

    if q:
        if q.isdigit():
            filtros.append("(p.id_producto = %s OR p.nombre LIKE %s)")
            params.extend([int(q), f"%{q}%"])
        else:
            filtros.append("p.nombre LIKE %s")
            params.append(f"%{q}%")

    where_clause = "WHERE " + " AND ".join(filtros)

    # --------- 1) LISTA PRINCIPAL DESDE inventario_productos ----------
    sql_productos = f"""
    SELECT
        p.id_producto,
        p.nombre,
        inv.cantidad_total,

        -- Próximo vencimiento REAL (solo lotes con stock > 0)
        (
            SELECT x.fecha_vencimiento
            FROM (
                SELECT
                    ed2.fecha_vencimiento,
                    (
                        SUM(ed2.peso_total_kg)
                        - COALESCE(SUM(
                            CASE WHEN s2.estado = 'Activo' THEN sd2.cantidad_kg ELSE 0 END
                        ), 0)
                    ) AS stock_kg
                FROM entrada_detalles ed2
                JOIN entradas e2
                    ON e2.id_entrada = ed2.id_entrada
                    AND e2.estado = 'Activo'
                LEFT JOIN salida_detalles sd2
                    ON sd2.id_entrada_detalle = ed2.id_detalle
                LEFT JOIN salidas s2
                    ON s2.id_salida = sd2.id_salida
                WHERE ed2.id_producto = p.id_producto
                GROUP BY ed2.fecha_vencimiento
                HAVING stock_kg > 0
                ORDER BY ed2.fecha_vencimiento ASC
                LIMIT 1
            ) x
        ) AS proximo_vencimiento,

        -- Bodega del lote próximo
        (
            SELECT y.nombre_bodega
            FROM (
                SELECT
                    ed3.fecha_vencimiento,
                    b3.nombre_bodega,
                    ed3.bodega_texto,
                    (
                        SUM(ed3.peso_total_kg)
                        - COALESCE(SUM(
                            CASE WHEN s3.estado = 'Activo' THEN sd3.cantidad_kg ELSE 0 END
                        ), 0)
                    ) AS stock_kg
                FROM entrada_detalles ed3
                JOIN entradas e3
                    ON e3.id_entrada = ed3.id_entrada
                    AND e3.estado = 'Activo'
                JOIN bodegas b3
                    ON b3.id_bodega = ed3.id_bodega
                LEFT JOIN salida_detalles sd3
                    ON sd3.id_entrada_detalle = ed3.id_detalle
                LEFT JOIN salidas s3
                    ON s3.id_salida = sd3.id_salida
                WHERE ed3.id_producto = p.id_producto
                GROUP BY ed3.fecha_vencimiento, b3.id_bodega, ed3.bodega_texto
                HAVING stock_kg > 0
                ORDER BY ed3.fecha_vencimiento ASC
                LIMIT 1
            ) y
        ) AS proxima_bodega,

        -- Ubicación del lote próximo
        (
            SELECT z.bodega_texto
            FROM (
                SELECT
                    ed4.fecha_vencimiento,
                    ed4.bodega_texto,
                    (
                        SUM(ed4.peso_total_kg)
                        - COALESCE(SUM(
                            CASE WHEN s4.estado = 'Activo' THEN sd4.cantidad_kg ELSE 0 END
                        ), 0)
                    ) AS stock_kg
                FROM entrada_detalles ed4
                JOIN entradas e4
                    ON e4.id_entrada = ed4.id_entrada
                    AND e4.estado = 'Activo'
                LEFT JOIN salida_detalles sd4
                    ON sd4.id_entrada_detalle = ed4.id_detalle
                LEFT JOIN salidas s4
                    ON s4.id_salida = sd4.id_salida
                WHERE ed4.id_producto = p.id_producto
                GROUP BY ed4.fecha_vencimiento, ed4.bodega_texto
                HAVING stock_kg > 0
                ORDER BY ed4.fecha_vencimiento ASC
                LIMIT 1
            ) z
        ) AS proxima_ubicacion

    FROM inventario_productos inv
    JOIN productos p
        ON p.id_producto = inv.id_producto
    {where_clause}
    ORDER BY p.id_producto ASC;
"""

    cursor.execute(sql_productos, params)
    filas_productos = cursor.fetchall()

    # --------- 2) DETALLE POR PRODUCTO + FECHA VENCIMIENTO + BODEGA ----------
    sql_detalles = """
    SELECT
        ed.id_producto,
        ed.fecha_vencimiento,
        (
            SUM(ed.peso_total_kg)
            - COALESCE(SUM(
                CASE WHEN s.estado = 'Activo' THEN sd.cantidad_kg ELSE 0 END
            ), 0)
        ) AS stock_kg,
        b.nombre_bodega,
        ed.bodega_texto
    FROM entrada_detalles ed
    JOIN entradas e
        ON e.id_entrada = ed.id_entrada
        AND e.estado = 'Activo'
    JOIN bodegas b
        ON b.id_bodega = ed.id_bodega

    -- salidas asociadas al lote
    LEFT JOIN salida_detalles sd
        ON sd.id_entrada_detalle = ed.id_detalle
    LEFT JOIN salidas s
        ON s.id_salida = sd.id_salida

    GROUP BY
        ed.id_producto,
        ed.fecha_vencimiento,
        b.id_bodega,
        ed.bodega_texto

    HAVING stock_kg > 0
    ORDER BY ed.id_producto, ed.fecha_vencimiento;
"""

    cursor.execute(sql_detalles)
    filas_detalle = cursor.fetchall()

    cursor.close()
    conn.close()

    # --------- 3) Armar mapa de detalles por producto ----------
    detalles_map = {}
    for d in filas_detalle:
        pid = d["id_producto"]
        detalles_map.setdefault(pid, []).append({
            "fecha_vencimiento": d["fecha_vencimiento"].isoformat() if d["fecha_vencimiento"] else None,
            "stock_kg": float(d["stock_kg"] or 0),
            "nombre_bodega": d.get("nombre_bodega"),
            "bodega_texto": d.get("bodega_texto"),
        })

    # --------- 4) Armar respuesta JSON ----------
    productos = []
    for p in filas_productos:
        pid = p["id_producto"]
        productos.append({
            "id_producto": pid,
            "nombre": p["nombre"],
            "cantidad_total": float(p["cantidad_total"] or 0),
            "proximo_vencimiento": p["proximo_vencimiento"].isoformat() if p["proximo_vencimiento"] else None,
            "proxima_bodega": p.get("proxima_bodega"),
            "proxima_ubicacion": p.get("proxima_ubicacion"),
            
            "detalles": detalles_map.get(pid, [])
        })

    

    return jsonify({"success": True, "productos": productos})


@tabla_inventario.route('/export/vencimientos.xlsx', methods=['GET'])
def export_vencimientos_excel():
    if "usuario" not in session:
        return render_template("index.html"), 401

    q = request.args.get('q', '').strip()
    productos = _obtener_productos_inventario(q)

    filas = []
    for p in productos:
        for d in (p.get("detalles") or []):
            filas.append([
                p.get("id_producto"),
                p.get("nombre"),
                d.get("fecha_vencimiento"),          # date (Excel real)
                float(d.get("stock_kg") or 0),
                d.get("nombre_bodega") or "-",
                d.get("bodega_texto") or "-"
            ])

    # Orden por fecha asc (None al final)
    filas.sort(key=lambda r: (r[2] is None, r[2] or date.max, r[1] or ""))

    wb = Workbook()
    ws = wb.active
    ws.title = "Vencimientos"

    headers = ["ID", "Producto", "Fecha vencimiento", "Stock lote (kg)", "Bodega", "Ubicación"]
    ws.append(headers)

    bold = Font(bold=True)
    for c in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=c)
        cell.font = bold
        cell.alignment = Alignment(horizontal="center")

    for row in filas:
        ws.append(row)

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:F{ws.max_row}"

    # Formatos
    for cell in ws["C"][1:]:
        cell.number_format = "dd/mm/yyyy"
    for cell in ws["D"][1:]:
        cell.number_format = "0.000"

    # Auto ancho
    for col in range(1, ws.max_column + 1):
        max_len = 0
        for cell in ws[get_column_letter(col)]:
            v = "" if cell.value is None else str(cell.value)
            max_len = max(max_len, len(v))
        ws.column_dimensions[get_column_letter(col)].width = min(max_len + 2, 45)

    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)

    return send_file(
        bio,
        as_attachment=True,
        download_name="vencimientos_inventario.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
