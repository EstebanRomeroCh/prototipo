# routes/reportes_donaciones.py

from flask import Blueprint, render_template, send_file, session, redirect, url_for, jsonify, request
from database import get_db_connection
import pymysql
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from io import BytesIO
from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.chart.label import DataLabelList
from utils.bitacora import registrar_bitacora
from psycopg2.extras import RealDictCursor
# pip install openpyxl

reportes_bp = Blueprint('reportes_bp', __name__)

# ===== Helpers de formato =====
def format_kg(value):
    try:
        num = Decimal(str(value or 0))
    except (InvalidOperation, TypeError, ValueError):
        return "0"
    if num == num.to_integral():
        return str(int(num))
    return f"{num:.3f}".rstrip('0').rstrip('.')


def format_money(value):
    try:
        num = Decimal(str(value or 0))
    except (InvalidOperation, TypeError, ValueError):
        return "0"
    text = f"{num:,.0f}"
    return text.replace(",", ".")


# ===== VISTA HTML =====
@reportes_bp.route('/reportes/donaciones', methods=['GET'])
def vista_reporte_donaciones():
    if 'usuario' not in session:
        return redirect(url_for('index'))

    return render_template(
        'reporte_donaciones.html',
        usuario=session.get('usuario'),
        rol_nombre=session.get('rol_nombre')
    )


# ===== ENDPOINT JSON PARA JS =====
@reportes_bp.route('/reportes/donaciones/data', methods=['GET'])
def data_reporte_donaciones():
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'Sesión expirada'}), 401

    # Filtros
    fecha_desde_str = request.args.get('desde', '').strip()
    fecha_hasta_str = request.args.get('hasta', '').strip()
    filtro_nombre = request.args.get('producto', '').strip()

    hoy = datetime.today().date()

    # Si no envían fechas, usamos últimos 30 días
    if not fecha_hasta_str:
        fecha_hasta = hoy
    else:
        fecha_hasta = datetime.fromisoformat(fecha_hasta_str).date()

    if not fecha_desde_str:
        fecha_desde = fecha_hasta - timedelta(days=30)
    else:
        fecha_desde = datetime.fromisoformat(fecha_desde_str).date()

    print("DEBUG REPORTE: desde", fecha_desde, "hasta", fecha_hasta, "producto", filtro_nombre)

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        filtros = [
            "e.estado = 'Activo'",
            "DATE(e.fecha_entrada) >= %s",
            "DATE(e.fecha_entrada) <= %s"
        ]
        params = [fecha_desde, fecha_hasta]

        if filtro_nombre:
            filtros.append("p.nombre LIKE %s")
            params.append(f"%{filtro_nombre}%")

        where_clause = "WHERE " + " AND ".join(filtros)

        sql = f"""
            SELECT
                p.id_producto,
                p.nombre,
                SUM(ed.cantidad) AS cantidad,
                SUM(ed.peso_total_kg) AS total_kg,
                SUM(ed.valor_producto * ed.cantidad) AS total_valor,
                MIN(e.fecha_entrada) AS primer_ingreso,
                MAX(e.fecha_entrada) AS ultimo_ingreso
            FROM entradas e
            JOIN entrada_detalles ed ON e.id_entrada = ed.id_entrada
            JOIN productos p ON p.id_producto = ed.id_producto
            {where_clause}
            GROUP BY p.id_producto, p.nombre
            ORDER BY p.nombre ASC;
        """

        print("DEBUG REPORTE SQL:", sql, "PARAMS:", params)
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        print("DEBUG REPORTE rows:", len(rows))

        items = []
        total_kg_general = Decimal('0')
        total_valor_general = Decimal('0')

        for r in rows:
            cant = r["cantidad"] or 0
            total_kg = Decimal(str(r["total_kg"] or 0))
            total_valor = Decimal(str(r["total_valor"] or 0))

            total_kg_general += total_kg
            total_valor_general += total_valor

            items.append({
                "id_producto": r["id_producto"],
                "nombre": r["nombre"],
                "cantidad": int(cant),
                "total_kg": float(total_kg),
                "total_kg_str": format_kg(total_kg),
                "total_valor": float(total_valor),
                "total_valor_str": format_money(total_valor),
                "primer_ingreso": r["primer_ingreso"].strftime('%Y-%m-%d') if r["primer_ingreso"] else None,
                "ultimo_ingreso": r["ultimo_ingreso"].strftime('%Y-%m-%d') if r["ultimo_ingreso"] else None
            })

                # -----------------------------
        # Bitácora (consulta reporte donaciones por producto)
        # -----------------------------
        id_usuario = session.get("id_usuario")
        if id_usuario:
            descripcion_bit = (
                f"Consultó reporte DONACIONES por producto "
                f"(desde {fecha_desde} hasta {fecha_hasta}"
                f"{', producto: ' + filtro_nombre if filtro_nombre else ''})"
            )
            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="REPORTES",
                accion="CONSULTAR",
                descripcion=descripcion_bit,
                tabla_afectada="entradas",
                id_registro=None
            )
            conn.commit()


        return jsonify({
            "success": True,
            "items": items,
            "totales": {
                "total_kg": float(total_kg_general),
                "total_kg_str": format_kg(total_kg_general),
                "total_valor": float(total_valor_general),
                "total_valor_str": format_money(total_valor_general)
            }
        })

    except Exception as e:
        print("Error reporte donaciones:", e)
        return jsonify({"success": False, "message": "Error al generar el reporte"}), 500

    finally:
        cursor.close()
        conn.close()


# ===== 2) EXCEL DEL REPORTE =====
@reportes_bp.route('/reportes/donaciones/excel', methods=['GET'])
def reporte_donaciones_excel():
    """
    Genera el mismo reporte que /reportes/donaciones/data
    pero lo devuelve como archivo Excel.
    """
    if 'usuario' not in session:
        return "Sesión expirada", 401

    # Mismos filtros que el JSON
    fecha_desde_str = request.args.get('desde', '').strip()
    fecha_hasta_str = request.args.get('hasta', '').strip()
    filtro_nombre = request.args.get('producto', '').strip()

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
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        filtros = [
            "e.estado = 'Activo'",
            "DATE(e.fecha_entrada) >= %s",
            "DATE(e.fecha_entrada) <= %s"
        ]
        params = [fecha_desde, fecha_hasta]

        if filtro_nombre:
            filtros.append("p.nombre LIKE %s")
            params.append(f"%{filtro_nombre}%")

        where_clause = "WHERE " + " AND ".join(filtros)

        sql = f"""
            SELECT
                p.id_producto,
                p.nombre,
                SUM(ed.cantidad) AS cantidad,
                SUM(ed.peso_total_kg) AS total_kg,
                SUM(ed.valor_producto * ed.cantidad) AS total_valor,
                MIN(e.fecha_entrada) AS primer_ingreso,
                MAX(e.fecha_entrada) AS ultimo_ingreso
            FROM entradas e
            JOIN entrada_detalles ed ON e.id_entrada = ed.id_entrada
            JOIN productos p ON p.id_producto = ed.id_producto
            {where_clause}
            GROUP BY p.id_producto, p.nombre
            ORDER BY p.nombre ASC;
        """
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        # Crear Excel
        wb = Workbook()
        ws = wb.active
        ws.title = "Donaciones por producto"

        # Encabezados
        headers = [
            "ID",
            "Producto",
            "Cantidad (unidades)",
            "Total (kg)",
            "Valor total",
            "Primer ingreso",
            "Último ingreso"
        ]
        ws.append(headers)

        total_kg_general = Decimal('0')
        total_valor_general = Decimal('0')

        for r in rows:
            cant = r["cantidad"] or 0
            total_kg = Decimal(str(r["total_kg"] or 0))
            total_valor = Decimal(str(r["total_valor"] or 0))

            total_kg_general += total_kg
            total_valor_general += total_valor

            ws.append([
                r["id_producto"],
                r["nombre"],
                int(cant),
                float(total_kg),
                float(total_valor),
                r["primer_ingreso"].strftime('%Y-%m-%d') if r["primer_ingreso"] else "",
                r["ultimo_ingreso"].strftime('%Y-%m-%d') if r["ultimo_ingreso"] else ""
            ])

        # ========= GRÁFICA EN EXCEL =========
        if rows:
            # filas: encabezado en 1, datos de 2 a len(rows)+1
            data_min_row = 1
            data_max_row = len(rows) + 1  # incluye encabezado

            # Columna 4: "Total (kg)"  (con encabezado)
            data_ref = Reference(
                ws,
                min_col=4, max_col=4,
                min_row=data_min_row, max_row=data_max_row
            )

            # Columna 2: nombres (sin encabezado)
            cats_ref = Reference(
                ws,
                min_col=2, max_col=2,
                min_row=2, max_row=data_max_row
            )

            chart = BarChart()
            chart.type = "col"
            chart.title = "Productos más donados (kg)"
            chart.y_axis.title = "Cantidad (kg)"
            chart.x_axis.title = "Producto"

            chart.add_data(data_ref, titles_from_data=True)
            chart.set_categories(cats_ref)

            # ====== CONFIGURAR EJE Y CON NÚMEROS CLAROS ======
            # máximo de kg para ajustar la escala
            max_kg = max(float(r["total_kg"] or 0) for r in rows) if rows else 0.0
            if max_kg <= 0:
                max_kg = 1

            # empezamos en 0
            chart.y_axis.scaling.min = 0

            # número entero, con separador de miles y "kg"
            chart.y_axis.number_format = '#,##0" kg"'

            # tamaño del paso entre líneas del eje Y (aprox. 5 divisiones)
            chart.y_axis.majorUnit = max_kg / 5

            # mostrar las etiquetas pegadas al eje
            chart.y_axis.tickLblPos = "nextTo"

            # eje X con los nombres de los productos
            chart.x_axis.tickLblPos = "low"

            # NO ponemos etiquetas encima de cada barra
            # (solo la escala del eje Y)
            # chart.dataLabels = DataLabelList()
            # chart.dataLabels.showVal = True

            # tamaño visual del gráfico
            chart.height = 15
            chart.width = 30

            # colocamos la gráfica a la derecha de la tabla
            ws.add_chart(chart, "I2")


        # Fila de totales
        ws.append([])
        ws.append([
            "",
            "TOTALES",
            "",
            float(total_kg_general),
            float(total_valor_general),
            "",
            ""
        ])

        # Guardar en memoria
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        filename = f"reporte_donaciones_{fecha_desde.strftime('%Y%m%d')}_{fecha_hasta.strftime('%Y%m%d')}.xlsx"

                # -----------------------------
        # Bitácora (exportación Excel)
        # -----------------------------
        id_usuario = session.get("id_usuario")
        if id_usuario:
            descripcion_bit = (
                f"Exportó Excel reporte DONACIONES por producto "
                f"(desde {fecha_desde} hasta {fecha_hasta}"
                f"{', producto: ' + filtro_nombre if filtro_nombre else ''})"
            )
            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="REPORTES",
                accion="EXPORTAR_EXCEL",
                descripcion=descripcion_bit,
                tabla_afectada="entradas",
                id_registro=None
            )
            conn.commit()


        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        print("Error reporte_donaciones_excel:", e)
        return "Error al generar el Excel", 500

    finally:
        cursor.close()
        conn.close()




# =========================================================
#  REPORTE 2: DONACIONES POR DONANTE (CON EXCEL)
# =========================================================

# ----- Vista HTML -----
@reportes_bp.route('/reportes/donantes', methods=['GET'])
def vista_reporte_donantes():
    """
    Página del reporte por donante.
    (El template lo haremos después: reporte_donantes.html)
    """
    if 'usuario' not in session:
        return redirect(url_for('index'))

    return render_template(
        'reporte_donantes.html',
        usuario=session.get('usuario'),
        rol_nombre=session.get('rol_nombre')
    )


# ----- JSON para tabla / gráfica -----
@reportes_bp.route('/reportes/donantes/data', methods=['GET'])
def data_reporte_donantes():
    """
    Devuelve los datos agregados por DONANTE (solo entradas con donante).
    """
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'Sesión expirada'}), 401

    # Filtros
    fecha_desde_str = request.args.get('desde', '').strip()
    fecha_hasta_str = request.args.get('hasta', '').strip()
    filtro_donante = request.args.get('donante', '').strip()

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
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        filtros = [
            "e.estado = 'Activo'",
            "DATE(e.fecha_entrada) >= %s",
            "DATE(e.fecha_entrada) <= %s",
            "e.id_donante IS NOT NULL"
        ]
        params = [fecha_desde, fecha_hasta]

        if filtro_donante:
            filtros.append("(d.nombre LIKE %s OR d.numero_documento LIKE %s)")
            params.append(f"%{filtro_donante}%")
            params.append(f"%{filtro_donante}%")

        where_clause = "WHERE " + " AND ".join(filtros)

        sql = f"""
            SELECT
                d.id_donante,
                d.nombre,
                d.numero_documento,
                COUNT(DISTINCT e.id_entrada) AS num_donaciones,
                SUM(ed.peso_total_kg) AS total_kg,
                SUM(ed.valor_producto * ed.cantidad) AS total_valor,
                MAX(e.fecha_entrada) AS ultima_donacion
            FROM entradas e
            JOIN donantes d ON d.id_donante = e.id_donante
            JOIN entrada_detalles ed ON ed.id_entrada = e.id_entrada
            {where_clause}
            GROUP BY d.id_donante, d.nombre, d.numero_documento
            ORDER BY total_kg DESC;
        """

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        items = []
        total_kg_general = Decimal('0')
        total_valor_general = Decimal('0')

        for r in rows:
            total_kg = Decimal(str(r["total_kg"] or 0))
            total_valor = Decimal(str(r["total_valor"] or 0))

            total_kg_general += total_kg
            total_valor_general += total_valor

            items.append({
                "id_donante": r["id_donante"],
                "nombre": r["nombre"],
                "numero_documento": r["numero_documento"],
                "num_donaciones": int(r["num_donaciones"] or 0),
                "total_kg": float(total_kg),
                "total_kg_str": format_kg(total_kg),
                "total_valor": float(total_valor),
                "total_valor_str": format_money(total_valor),
                "ultima_donacion": r["ultima_donacion"].strftime('%Y-%m-%d')
                    if r["ultima_donacion"] else None
            })

                # -----------------------------
        # Bitácora (consulta reporte por donante)
        # -----------------------------
        id_usuario = session.get("id_usuario")
        if id_usuario:
            descripcion_bit = (
                f"Consultó reporte DONANTES "
                f"(desde {fecha_desde} hasta {fecha_hasta}"
                f"{', filtro: ' + filtro_donante if filtro_donante else ''})"
            )
            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="REPORTES",
                accion="CONSULTAR",
                descripcion=descripcion_bit,
                tabla_afectada="donantes",
                id_registro=None
            )
            conn.commit()


        return jsonify({
            "success": True,
            "items": items,
            "totales": {
                "total_kg": float(total_kg_general),
                "total_kg_str": format_kg(total_kg_general),
                "total_valor": float(total_valor_general),
                "total_valor_str": format_money(total_valor_general)
            }
        })

    except Exception as e:
        print("Error data_reporte_donantes:", e)
        return jsonify({"success": False, "message": "Error al generar el reporte"}), 500

    finally:
        cursor.close()
        conn.close()


# ----- Excel del reporte por donante -----
@reportes_bp.route('/reportes/donantes/excel', methods=['GET'])
def reporte_donantes_excel():
    """
    Genera Excel del reporte por donante (mismos filtros que /reportes/donantes/data),
    incluyendo una gráfica de kg donados por donante.
    """
    if 'usuario' not in session:
        return "Sesión expirada", 401

    fecha_desde_str = request.args.get('desde', '').strip()
    fecha_hasta_str = request.args.get('hasta', '').strip()
    filtro_donante = request.args.get('donante', '').strip()

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
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        filtros = [
            "e.estado = 'Activo'",
            "DATE(e.fecha_entrada) >= %s",
            "DATE(e.fecha_entrada) <= %s",
            "e.id_donante IS NOT NULL"
        ]
        params = [fecha_desde, fecha_hasta]

        if filtro_donante:
            filtros.append("(d.nombre LIKE %s OR d.numero_documento LIKE %s)")
            params.append(f"%{filtro_donante}%")
            params.append(f"%{filtro_donante}%")

        where_clause = "WHERE " + " AND ".join(filtros)

        sql = f"""
            SELECT
                d.id_donante,
                d.nombre,
                d.numero_documento,
                COUNT(DISTINCT e.id_entrada) AS num_donaciones,
                SUM(ed.peso_total_kg) AS total_kg,
                SUM(ed.valor_producto * ed.cantidad) AS total_valor,
                MAX(e.fecha_entrada) AS ultima_donacion
            FROM entradas e
            JOIN donantes d ON d.id_donante = e.id_donante
            JOIN entrada_detalles ed ON ed.id_entrada = e.id_entrada
            {where_clause}
            GROUP BY d.id_donante, d.nombre, d.numero_documento
            ORDER BY total_kg DESC;
        """

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        wb = Workbook()
        ws = wb.active
        ws.title = "Donaciones por donante"

        # Encabezados
        headers = [
            "ID Donante",
            "Nombre donante",
            "Documento",
            "N° donaciones",
            "Total (kg)",
            "Valor total",
            "Última donación"
        ]
        ws.append(headers)

        total_kg_general = Decimal('0')
        total_valor_general = Decimal('0')

        for r in rows:
            total_kg = Decimal(str(r["total_kg"] or 0))
            total_valor = Decimal(str(r["total_valor"] or 0))
            total_kg_general += total_kg
            total_valor_general += total_valor

            ws.append([
                r["id_donante"],
                r["nombre"],
                r["numero_documento"] or "",
                int(r["num_donaciones"] or 0),
                float(total_kg),
                float(total_valor),
                r["ultima_donacion"].strftime('%Y-%m-%d') if r["ultima_donacion"] else ""
            ])

        # ========= GRÁFICA EN EXCEL (por donante) =========
        if rows:
            data_min_row = 1
            data_max_row = len(rows) + 1  # incluye encabezado

            # Columna 5: "Total (kg)" (con encabezado)
            data_ref = Reference(
                ws,
                min_col=5, max_col=5,
                min_row=data_min_row, max_row=data_max_row
            )

            # Columna 2: nombres de donante
            cats_ref = Reference(
                ws,
                min_col=2, max_col=2,
                min_row=2, max_row=data_max_row
            )

            chart = BarChart()
            chart.type = "col"
            chart.title = "Donantes por peso aportado (kg)"
            chart.y_axis.title = "Cantidad (kg)"
            chart.x_axis.title = "Donante"

            chart.add_data(data_ref, titles_from_data=True)
            chart.set_categories(cats_ref)

            max_kg = max(float(r["total_kg"] or 0) for r in rows) if rows else 0.0
            if max_kg <= 0:
                max_kg = 1

            chart.y_axis.scaling.min = 0
            chart.y_axis.number_format = '#,##0" kg"'
            chart.y_axis.majorUnit = max_kg / 5 if max_kg > 0 else 1

            chart.height = 15
            chart.width = 30

            ws.add_chart(chart, "I2")

        # Totales
        ws.append([])
        ws.append([
            "",
            "TOTALES",
            "",
            "",
            float(total_kg_general),
            float(total_valor_general),
            ""
        ])

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        filename = f"reporte_donantes_{fecha_desde.strftime('%Y%m%d')}_{fecha_hasta.strftime('%Y%m%d')}.xlsx"

                # -----------------------------
        # Bitácora (exportación Excel por donante)
        # -----------------------------
        id_usuario = session.get("id_usuario")
        if id_usuario:
            descripcion_bit = (
                f"Exportó Excel reporte DONANTES "
                f"(desde {fecha_desde} hasta {fecha_hasta}"
                f"{', filtro: ' + filtro_donante if filtro_donante else ''})"
            )
            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="REPORTES",
                accion="EXPORTAR_EXCEL",
                descripcion=descripcion_bit,
                tabla_afectada="donantes",
                id_registro=None
            )
            conn.commit()


        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        print("Error reporte_donantes_excel:", e)
        return "Error al generar el Excel", 500

    finally:
        cursor.close()
        conn.close()



# =========================================================
#  REPORTE 3: DONACIONES POR CATEGORÍA (CON EXCEL)
# =========================================================

# ----- Vista HTML -----
@reportes_bp.route('/reportes/categorias', methods=['GET'])
def vista_reporte_categorias():
    """
    Página del reporte de donaciones por categoría.
    (Template: reporte_categorias.html)
    """
    if 'usuario' not in session:
        return redirect(url_for('index'))

    return render_template(
        'reporte_categorias.html',
        usuario=session.get('usuario'),
        rol_nombre=session.get('rol_nombre')
    )


# ----- JSON para tabla / gráfica -----
@reportes_bp.route('/reportes/categorias/data', methods=['GET'])
def data_reporte_categorias():
    """
    Devuelve los datos agregados por CATEGORÍA de producto.
    """
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'Sesión expirada'}), 401

    # Filtros
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
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        filtros = [
            "e.estado = 'Activo'",
            "DATE(e.fecha_entrada) >= %s",
            "DATE(e.fecha_entrada) <= %s"
        ]
        params = [fecha_desde, fecha_hasta]

        if filtro_categoria:
            filtros.append("c.nombre LIKE %s")
            params.append(f"%{filtro_categoria}%")

        where_clause = "WHERE " + " AND ".join(filtros)

        sql = f"""
            SELECT
                c.id_categoria,
                c.nombre AS categoria,
                COUNT(DISTINCT ed.id_producto) AS num_productos,
                COUNT(DISTINCT e.id_entrada) AS num_donaciones,
                SUM(ed.cantidad) AS cantidad_unidades,
                SUM(ed.peso_total_kg) AS total_kg,
                SUM(ed.valor_producto * ed.cantidad) AS total_valor,
                MIN(e.fecha_entrada) AS primera_donacion,
                MAX(e.fecha_entrada) AS ultima_donacion
            FROM entradas e
            JOIN entrada_detalles ed ON ed.id_entrada = e.id_entrada
            JOIN categorias c ON c.id_categoria = ed.id_categoria
            {where_clause}
            GROUP BY c.id_categoria, c.nombre
            ORDER BY total_kg DESC;
        """

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        items = []
        total_kg_general = Decimal('0')
        total_valor_general = Decimal('0')

        for r in rows:
            total_kg = Decimal(str(r["total_kg"] or 0))
            total_valor = Decimal(str(r["total_valor"] or 0))

            total_kg_general += total_kg
            total_valor_general += total_valor

            items.append({
                "id_categoria": r["id_categoria"],
                "categoria": r["categoria"],
                "num_productos": int(r["num_productos"] or 0),
                "num_donaciones": int(r["num_donaciones"] or 0),
                "cantidad_unidades": int(r["cantidad_unidades"] or 0),
                "total_kg": float(total_kg),
                "total_kg_str": format_kg(total_kg),
                "total_valor": float(total_valor),
                "total_valor_str": format_money(total_valor),
                "primera_donacion": r["primera_donacion"].strftime('%Y-%m-%d')
                    if r["primera_donacion"] else None,
                "ultima_donacion": r["ultima_donacion"].strftime('%Y-%m-%d')
                    if r["ultima_donacion"] else None
            })

                # -----------------------------
        # Bitácora (consulta reporte por categoría)
        # -----------------------------
        id_usuario = session.get("id_usuario")
        if id_usuario:
            descripcion_bit = (
                f"Consultó reporte CATEGORÍAS "
                f"(desde {fecha_desde} hasta {fecha_hasta}"
                f"{', filtro: ' + filtro_categoria if filtro_categoria else ''})"
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
                "total_kg": float(total_kg_general),
                "total_kg_str": format_kg(total_kg_general),
                "total_valor": float(total_valor_general),
                "total_valor_str": format_money(total_valor_general)
            }
        })

    except Exception as e:
        print("Error data_reporte_categorias:", e)
        return jsonify({"success": False, "message": "Error al generar el reporte"}), 500

    finally:
        cursor.close()
        conn.close()


# ----- Excel del reporte por categoría -----
@reportes_bp.route('/reportes/categorias/excel', methods=['GET'])
def reporte_categorias_excel():
    """
    Genera Excel del reporte por categoría (mismos filtros que /reportes/categorias/data),
    incluyendo una gráfica de barras con el total de kg por categoría.
    """
    if 'usuario' not in session:
        return "Sesión expirada", 401

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
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        filtros = [
            "e.estado = 'Activo'",
            "DATE(e.fecha_entrada) >= %s",
            "DATE(e.fecha_entrada) <= %s"
        ]
        params = [fecha_desde, fecha_hasta]

        if filtro_categoria:
            filtros.append("c.nombre LIKE %s")
            params.append(f"%{filtro_categoria}%")

        where_clause = "WHERE " + " AND ".join(filtros)

        sql = f"""
            SELECT
                c.id_categoria,
                c.nombre AS categoria,
                COUNT(DISTINCT ed.id_producto) AS num_productos,
                COUNT(DISTINCT e.id_entrada) AS num_donaciones,
                SUM(ed.cantidad) AS cantidad_unidades,
                SUM(ed.peso_total_kg) AS total_kg,
                SUM(ed.valor_producto * ed.cantidad) AS total_valor,
                MIN(e.fecha_entrada) AS primera_donacion,
                MAX(e.fecha_entrada) AS ultima_donacion
            FROM entradas e
            JOIN entrada_detalles ed ON ed.id_entrada = e.id_entrada
            JOIN categorias c ON c.id_categoria = ed.id_categoria
            {where_clause}
            GROUP BY c.id_categoria, c.nombre
            ORDER BY total_kg DESC;
        """

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        wb = Workbook()
        ws = wb.active
        ws.title = "Donaciones por categoría"

        # Encabezados
        headers = [
            "ID categoría",
            "Categoría",
            "N° productos",
            "N° donaciones",
            "Cantidad (unidades)",
            "Total (kg)",
            "Valor total",
            "Primera donación",
            "Última donación"
        ]
        ws.append(headers)

        total_kg_general = Decimal('0')
        total_valor_general = Decimal('0')

        for r in rows:
            total_kg = Decimal(str(r["total_kg"] or 0))
            total_valor = Decimal(str(r["total_valor"] or 0))
            total_kg_general += total_kg
            total_valor_general += total_valor

            ws.append([
                r["id_categoria"],
                r["categoria"],
                int(r["num_productos"] or 0),
                int(r["num_donaciones"] or 0),
                int(r["cantidad_unidades"] or 0),
                float(total_kg),
                float(total_valor),
                r["primera_donacion"].strftime('%Y-%m-%d') if r["primera_donacion"] else "",
                r["ultima_donacion"].strftime('%Y-%m-%d') if r["ultima_donacion"] else ""
            ])

        # Totales al final
        ws.append([])
        ws.append([
            "",
            "TOTALES",
            "",
            "",
            "",
            float(total_kg_general),
            float(total_valor_general),
            "",
            ""
        ])

        # ---- Gráfica en Excel (si hay datos) ----
        if rows:
            # Rango de datos: columna 6 = Total (kg), filas 1..n
            data_min_row = 1
            data_max_row = len(rows) + 1  # incluye encabezado

            data_ref = Reference(
                ws,
                min_col=6, max_col=6,   # Total (kg)
                min_row=data_min_row, max_row=data_max_row
            )

            cats_ref = Reference(
                ws,
                min_col=2, max_col=2,   # Categoría
                min_row=2, max_row=data_max_row
            )

            chart = BarChart()
            chart.type = "col"
            chart.title = "Total donado por categoría (kg)"
            chart.y_axis.title = "Cantidad (kg)"
            chart.x_axis.title = "Categoría"

            chart.add_data(data_ref, titles_from_data=True)
            chart.set_categories(cats_ref)

            # Formato eje Y
            max_kg = max(float(r["total_kg"] or 0) for r in rows) or 1.0
            chart.y_axis.scaling.min = 0
            chart.y_axis.number_format = '#,##0" kg"'
            chart.y_axis.majorUnit = max_kg / 5
            chart.y_axis.tickLblPos = "nextTo"
            chart.x_axis.tickLblPos = "low"

            chart.height = 15
            chart.width = 30

            # Colocar gráfica a la derecha de la tabla
            ws.add_chart(chart, "K2")

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        filename = f"reporte_categorias_{fecha_desde.strftime('%Y%m%d')}_{fecha_hasta.strftime('%Y%m%d')}.xlsx"

                # -----------------------------
        # Bitácora (exportación Excel por categoría)
        # -----------------------------
        id_usuario = session.get("id_usuario")
        if id_usuario:
            descripcion_bit = (
                f"Exportó Excel reporte CATEGORÍAS "
                f"(desde {fecha_desde} hasta {fecha_hasta}"
                f"{', filtro: ' + filtro_categoria if filtro_categoria else ''})"
            )
            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="REPORTES",
                accion="EXPORTAR_EXCEL",
                descripcion=descripcion_bit,
                tabla_afectada="categorias",
                id_registro=None
            )
            conn.commit()


        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        print("Error reporte_categorias_excel:", e)
        return "Error al generar el Excel", 500

    finally:
        cursor.close()
        conn.close()


# =========================================================
#  REPORTE GENERAL: DONACIONES DETALLADAS (POR PRODUCTO)
# =========================================================

@reportes_bp.route('/reportes/general', methods=['GET'])
def vista_reporte_general():
    """
    Vista HTML del reporte general de donaciones.
    (Luego creamos reporte_general.html)
    """
    if 'usuario' not in session:
        return redirect(url_for('index'))

    return render_template(
        'reporte_general.html',
        usuario=session.get('usuario'),
        rol_nombre=session.get('rol_nombre')
    )


# =========================================================
#  REPORTE GENERAL DE DONACIONES (JSON + EXCEL)
# =========================================================

@reportes_bp.route('/reportes/general/data', methods=['GET'])
def data_reporte_general():
    """
    Devuelve un listado DETALLADO por línea de producto:
    - info de la entrada (fecha, tipo, donante )
    - info del producto (cat, bodega, vencimiento)
    - totales por línea (peso_total_kg, valor_total)
    También devuelve totales generales de peso y valor.
    """
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'Sesión expirada'}), 401

    fecha_desde_str = request.args.get('desde', '').strip()
    fecha_hasta_str = request.args.get('hasta', '').strip()
    filtro_buscar = request.args.get('buscar', '').strip()

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
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        filtros = [
            "e.estado = 'Activo'",
            "DATE(e.fecha_entrada) >= %s",
            "DATE(e.fecha_entrada) <= %s"
        ]
        params = [fecha_desde, fecha_hasta]

        if filtro_buscar:
            filtros.append("""
                (
                    p.nombre LIKE %s OR
                    c.nombre LIKE %s OR
                    d.nombre LIKE %s OR
                    d.numero_documento LIKE %s OR
                )
            """)
            patron = f"%{filtro_buscar}%"
            params.extend([patron, patron, patron, patron, patron])

        where_clause = "WHERE " + " AND ".join(filtros)

        #  Versión sin JOIN a unidades (para evitar errores de columna)
        sql = f"""
            SELECT
                e.id_entrada,
                e.fecha_entrada,
                t.nombre AS tipo_entrada,
                d.numero_documento,
                d.nombre AS donante,
                p.nombre AS producto,
                c.nombre AS categoria,
                ed.cantidad,
                ed.peso_total_kg,
                (ed.valor_producto * ed.cantidad) AS valor_total,
                b.nombre_bodega AS bodega,
                ed.bodega_texto AS ubicacion,
                ed.fecha_vencimiento,
                IFNULL(a.num_archivos, 0) AS num_archivos
            FROM entradas e
            JOIN tipo_entrada t     ON t.id_tipo_entrada = e.id_tipo_entrada
            LEFT JOIN donantes d    ON d.id_donante = e.id_donante
            JOIN entrada_detalles ed ON ed.id_entrada = e.id_entrada
            JOIN productos p        ON p.id_producto = ed.id_producto
            JOIN categorias c       ON c.id_categoria = ed.id_categoria
            JOIN bodegas b          ON b.id_bodega = ed.id_bodega
            LEFT JOIN (
                SELECT id_entrada, COUNT(*) AS num_archivos
                FROM entrada_archivos
                GROUP BY id_entrada
            ) a ON a.id_entrada = e.id_entrada
            {where_clause}
            ORDER BY e.fecha_entrada DESC, e.id_entrada DESC, p.nombre ASC;
        """

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        items = []
        total_kg_general = Decimal('0')
        total_valor_general = Decimal('0')

        for r in rows:
            peso = Decimal(str(r["peso_total_kg"] or 0))
            valor = Decimal(str(r["valor_total"] or 0))

            total_kg_general += peso
            total_valor_general += valor

            items.append({
                "id_entrada": r["id_entrada"],
                "fecha_entrada": r["fecha_entrada"].strftime('%Y-%m-%d') if r["fecha_entrada"] else None,
                "tipo_entrada": r["tipo_entrada"],
                "numero_documento": r["numero_documento"],
                "donante": r["donante"],
                "producto": r["producto"],
                "categoria": r["categoria"],
                # 👇 no tenemos la unidad aún, la dejamos vacía
                "unidad": "",
                "cantidad": int(r["cantidad"] or 0),
                "peso_total_kg": float(peso),
                "valor_total": float(valor),
                "bodega": r["bodega"],
                "ubicacion": r["ubicacion"],
                "fecha_vencimiento": r["fecha_vencimiento"].strftime('%Y-%m-%d')
                    if r["fecha_vencimiento"] else None,
                "num_archivos": int(r["num_archivos"] or 0)
            })

                # -----------------------------
        # Bitácora (consulta reporte general)
        # -----------------------------
        id_usuario = session.get("id_usuario")
        if id_usuario:
            descripcion_bit = (
                f"Consultó REPORTE GENERAL "
                f"(desde {fecha_desde} hasta {fecha_hasta}"
                f"{', buscar: ' + filtro_buscar if filtro_buscar else ''})"
            )
            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="REPORTES",
                accion="CONSULTAR",
                descripcion=descripcion_bit,
                tabla_afectada="entradas",
                id_registro=None
            )
            conn.commit()


        return jsonify({
            "success": True,
            "items": items,
            "totales": {
                "total_kg": float(total_kg_general),
                "total_kg_str": format_kg(total_kg_general),
                "total_valor": float(total_valor_general),
                "total_valor_str": format_money(total_valor_general)
            }
        })

    except Exception as e:
        print("Error data_reporte_general:", e)
        return jsonify({"success": False, "message": "Error al generar el reporte"}), 500

    finally:
        cursor.close()
        conn.close()


@reportes_bp.route('/reportes/general/excel', methods=['GET'])
def reporte_general_excel():
    """
    Mismo contenido que /reportes/general/data,
    pero exportado a Excel.
    """
    if 'usuario' not in session:
        return "Sesión expirada", 401

    fecha_desde_str = request.args.get('desde', '').strip()
    fecha_hasta_str = request.args.get('hasta', '').strip()
    filtro_buscar = request.args.get('buscar', '').strip()

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
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        filtros = [
            "e.estado = 'Activo'",
            "DATE(e.fecha_entrada) >= %s",
            "DATE(e.fecha_entrada) <= %s"
        ]
        params = [fecha_desde, fecha_hasta]

        if filtro_buscar:
            filtros.append("""
                (
                    p.nombre LIKE %s OR
                    c.nombre LIKE %s OR
                    d.nombre LIKE %s OR
                    d.numero_documento LIKE %s 
                )
            """)
            patron = f"%{filtro_buscar}%"
            params.extend([patron, patron, patron, patron, patron])

        where_clause = "WHERE " + " AND ".join(filtros)

        sql = f"""
            SELECT
                e.id_entrada,
                e.fecha_entrada,
                t.nombre AS tipo_entrada,
                d.numero_documento,
                d.nombre AS donante,
                p.nombre AS producto,
                c.nombre AS categoria,
                ed.cantidad,
                ed.peso_total_kg,
                (ed.valor_producto * ed.cantidad) AS valor_total,
                b.nombre_bodega AS bodega,
                ed.bodega_texto AS ubicacion,
                ed.fecha_vencimiento,
                IFNULL(a.num_archivos, 0) AS num_archivos
            FROM entradas e
            JOIN tipo_entrada t     ON t.id_tipo_entrada = e.id_tipo_entrada
            LEFT JOIN donantes d    ON d.id_donante = e.id_donante
            JOIN entrada_detalles ed ON ed.id_entrada = e.id_entrada
            JOIN productos p        ON p.id_producto = ed.id_producto
            JOIN categorias c       ON c.id_categoria = ed.id_categoria
            JOIN bodegas b          ON b.id_bodega = ed.id_bodega
            LEFT JOIN (
                SELECT id_entrada, COUNT(*) AS num_archivos
                FROM entrada_archivos
                GROUP BY id_entrada
            ) a ON a.id_entrada = e.id_entrada
            {where_clause}
            ORDER BY e.fecha_entrada DESC, e.id_entrada DESC, p.nombre ASC;
        """

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        wb = Workbook()
        ws = wb.active
        ws.title = "Reporte general"

        headers = [
            "ID entrada",
            "Fecha",
            "Tipo",
            "Doc. donante",
            "Donante",
            "Producto",
            "Categoría",
            "Unidad",          # por ahora quedará vacío
            "Cantidad",
            "Peso total (kg)",
            "Valor total",
            "Bodega",
            "Ubicación",
            "Vencimiento",
            "N° archivos"
        ]
        ws.append(headers)

        total_kg_general = Decimal('0')
        total_valor_general = Decimal('0')

        for r in rows:
            peso = Decimal(str(r["peso_total_kg"] or 0))
            valor = Decimal(str(r["valor_total"] or 0))
            total_kg_general += peso
            total_valor_general += valor

            ws.append([
                r["id_entrada"],
                r["fecha_entrada"].strftime('%Y-%m-%d') if r["fecha_entrada"] else "",
                r["tipo_entrada"] or "",
                r["numero_documento"] or "",
                r["donante"] or "",
                r["producto"] or "",
                r["categoria"] or "",
                "",  # Unidad vacía de momento
                int(r["cantidad"] or 0),
                float(peso),
                float(valor),
                r["bodega"] or "",
                r["ubicacion"] or "",
                r["fecha_vencimiento"].strftime('%Y-%m-%d') if r["fecha_vencimiento"] else "",
                int(r["num_archivos"] or 0)
            ])

        ws.append([])
        ws.append([
            "",
            "TOTALES",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            float(total_kg_general),
            float(total_valor_general),
            "",
            "",
            "",
            ""
        ])

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        filename = f"reporte_general_{fecha_desde.strftime('%Y%m%d')}_{fecha_hasta.strftime('%Y%m%d')}.xlsx"

                # -----------------------------
        # Bitácora (exportación Excel reporte general)
        # -----------------------------
        id_usuario = session.get("id_usuario")
        if id_usuario:
            descripcion_bit = (
                f"Exportó Excel REPORTE GENERAL "
                f"(desde {fecha_desde} hasta {fecha_hasta}"
                f"{', buscar: ' + filtro_buscar if filtro_buscar else ''})"
            )
            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="REPORTES",
                accion="EXPORTAR_EXCEL",
                descripcion=descripcion_bit,
                tabla_afectada="entradas",
                id_registro=None
            )
            conn.commit()


        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        print("Error reporte_general_excel:", e)
        return "Error al generar el Excel", 500

    finally:
        cursor.close()
        conn.close()



# =========================================================
#  REPORTE 2: DONACIONES MONETARIAS (CON EXCEL)

# =========================================================
@reportes_bp.route('/reportes/monetarias', methods=['GET'])
def vista_reporte_monetarias():
    """
    Vista HTML del reporte general de donaciones monetarias.
    """
    if 'usuario' not in session:
        return redirect(url_for('index'))

    return render_template(
        'reporte_monetarias.html',
        usuario=session.get('usuario'),
        rol_nombre=session.get('rol_nombre')
    )


@reportes_bp.route('/reportes/monetarias/data', methods=['GET'])
def data_reporte_monetarias():
    """
    Reporte detallado de donaciones monetarias:
    - fecha, donante, doc, método, monto, descripción
    - número de anexos
    También devuelve totales (suma de montos).
    """
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'Sesión expirada'}), 401

    fecha_desde_str = request.args.get('desde', '').strip()
    fecha_hasta_str = request.args.get('hasta', '').strip()
    filtro_buscar = request.args.get('buscar', '').strip()

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
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        filtros = [
            "dm.estado = 'Activo'",
            "DATE(dm.fecha_donacion) >= %s",
            "DATE(dm.fecha_donacion) <= %s"
        ]
        params = [fecha_desde, fecha_hasta]

        if filtro_buscar:
            filtros.append("""
                (
                    d.nombre LIKE %s OR
                    d.numero_documento LIKE %s OR
                    m.nombre LIKE %s OR
                    dm.descripcion LIKE %s
                )
            """)
            patron = f"%{filtro_buscar}%"
            params.extend([patron, patron, patron, patron])

        where_clause = "WHERE " + " AND ".join(filtros)

        sql = f"""
            SELECT
                dm.id_donacion,
                dm.fecha_donacion,
                dm.monto,
                dm.descripcion,
                d.numero_documento,
                d.nombre AS donante,
                m.nombre AS metodo,
                IFNULL(a.num_archivos, 0) AS num_archivos
            FROM donaciones_monetarias dm
            JOIN donantes d        ON d.id_donante = dm.id_donante
            JOIN metodos_donacion m ON m.id_metodo = dm.id_metodo
            LEFT JOIN (
                SELECT id_donacion, COUNT(*) AS num_archivos
                FROM donacion_monetaria_archivos
                GROUP BY id_donacion
            ) a ON a.id_donacion = dm.id_donacion
            {where_clause}
            ORDER BY dm.fecha_donacion DESC, dm.id_donacion DESC;
        """

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        items = []
        total_monto = Decimal('0')

        for r in rows:
            monto = Decimal(str(r["monto"] or 0))
            total_monto += monto

            items.append({
                "id_donacion": r["id_donacion"],
                "fecha_donacion": r["fecha_donacion"].strftime('%Y-%m-%d') if r["fecha_donacion"] else None,
                "numero_documento": r["numero_documento"],
                "donante": r["donante"],
                "metodo": r["metodo"],
                "monto": float(monto),
                "descripcion": r["descripcion"],
                "num_archivos": int(r["num_archivos"] or 0)
            })

                # -----------------------------
        # Bitácora (consulta reporte monetarias)
        # -----------------------------
        id_usuario = session.get("id_usuario")
        if id_usuario:
            descripcion_bit = (
                f"Consultó reporte MONETARIAS "
                f"(desde {fecha_desde} hasta {fecha_hasta}"
                f"{', buscar: ' + filtro_buscar if filtro_buscar else ''})"
            )
            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="REPORTES",
                accion="CONSULTAR",
                descripcion=descripcion_bit,
                tabla_afectada="donaciones_monetarias",
                id_registro=None
            )
            conn.commit()


        return jsonify({
            "success": True,
            "items": items,
            "totales": {
                "total_monto": float(total_monto),
                "total_monto_str": format_money(total_monto)  # asumiendo que ya tienes format_money
            }
        })

    except Exception as e:
        print("Error data_reporte_monetarias:", e)
        return jsonify({"success": False, "message": "Error al generar el reporte"}), 500

    finally:
        cursor.close()
        conn.close()


@reportes_bp.route('/reportes/monetarias/excel', methods=['GET'])
def reporte_monetarias_excel():
    """
    Mismo contenido que /reportes/monetarias/data,
    pero exportado a Excel.
    """
    if 'usuario' not in session:
        return "Sesión expirada", 401

    fecha_desde_str = request.args.get('desde', '').strip()
    fecha_hasta_str = request.args.get('hasta', '').strip()
    filtro_buscar = request.args.get('buscar', '').strip()

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
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        filtros = [
            "dm.estado = 'Activo'",
            "DATE(dm.fecha_donacion) >= %s",
            "DATE(dm.fecha_donacion) <= %s"
        ]
        params = [fecha_desde, fecha_hasta]

        if filtro_buscar:
            filtros.append("""
                (
                    d.nombre LIKE %s OR
                    d.numero_documento LIKE %s OR
                    m.nombre LIKE %s OR
                    dm.descripcion LIKE %s
                )
            """)
            patron = f"%{filtro_buscar}%"
            params.extend([patron, patron, patron, patron])

        where_clause = "WHERE " + " AND ".join(filtros)

        sql = f"""
            SELECT
                dm.id_donacion,
                dm.fecha_donacion,
                dm.monto,
                dm.descripcion,
                d.numero_documento,
                d.nombre AS donante,
                m.nombre AS metodo,
                IFNULL(a.num_archivos, 0) AS num_archivos
            FROM donaciones_monetarias dm
            JOIN donantes d        ON d.id_donante = dm.id_donante
            JOIN metodos_donacion m ON m.id_metodo = dm.id_metodo
            LEFT JOIN (
                SELECT id_donacion, COUNT(*) AS num_archivos
                FROM donacion_monetaria_archivos
                GROUP BY id_donacion
            ) a ON a.id_donacion = dm.id_donacion
            {where_clause}
            ORDER BY dm.fecha_donacion DESC, dm.id_donacion DESC;
        """

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        wb = Workbook()
        ws = wb.active
        ws.title = "Donaciones monetarias"

        headers = [
            "ID donación",
            "Fecha donación",
            "Doc. donante",
            "Donante",
            "Método",
            "Monto",
            "Descripción",
            "N° anexos"
        ]
        ws.append(headers)

        total_monto = Decimal('0')

        for r in rows:
            monto = Decimal(str(r["monto"] or 0))
            total_monto += monto

            ws.append([
                r["id_donacion"],
                r["fecha_donacion"].strftime('%Y-%m-%d') if r["fecha_donacion"] else "",
                r["numero_documento"] or "",
                r["donante"] or "",
                r["metodo"] or "",
                float(monto),
                r["descripcion"] or "",
                int(r["num_archivos"] or 0)
            ])

        # Fila de totales
        ws.append([])
        ws.append([
            "",
            "TOTAL",
            "",
            "",
            "",
            float(total_monto),
            "",
            ""
        ])

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        filename = f"reporte_monetarias_{fecha_desde.strftime('%Y%m%d')}_{fecha_hasta.strftime('%Y%m%d')}.xlsx"

                # -----------------------------
        # Bitácora (exportación Excel monetarias)
        # -----------------------------
        id_usuario = session.get("id_usuario")
        if id_usuario:
            descripcion_bit = (
                f"Exportó Excel reporte MONETARIAS "
                f"(desde {fecha_desde} hasta {fecha_hasta}"
                f"{', buscar: ' + filtro_buscar if filtro_buscar else ''})"
            )
            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="REPORTES",
                accion="EXPORTAR_EXCEL",
                descripcion=descripcion_bit,
                tabla_afectada="donaciones_monetarias",
                id_registro=None
            )
            conn.commit()


        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        print("Error reporte_monetarias_excel:", e)
        return "Error al generar el Excel", 500

    finally:
        cursor.close()
        conn.close()
