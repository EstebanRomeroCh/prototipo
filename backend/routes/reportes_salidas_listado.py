# routes/reportes_salidas_listado.py

from flask import Blueprint, render_template, session, redirect, url_for, jsonify, request
from database import get_db_connection
import pymysql
from datetime import datetime
from decimal import Decimal, InvalidOperation
from io import BytesIO
from openpyxl import Workbook
from flask import send_file
from utils.bitacora import registrar_bitacora

reportes_salidas_listado_bp = Blueprint("reportes_salidas_listado_bp", __name__)

def _decimal_or_zero(x):
    try:
        return Decimal(str(x or 0))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal("0")

def format_kg(value):
    num = _decimal_or_zero(value)
    if num == num.to_integral():
        return str(int(num))
    return f"{num:.3f}".rstrip("0").rstrip(".")

def format_money(value):
    num = _decimal_or_zero(value)
    text = f"{num:,.0f}"
    return text.replace(",", ".")

def parse_fechas(desde_str: str, hasta_str: str):
    desde_str = (desde_str or "").strip()
    hasta_str = (hasta_str or "").strip()

    if not desde_str and not hasta_str:
        return None, None

    if desde_str and not hasta_str:
        d = datetime.fromisoformat(desde_str).date()
        return d, d

    if hasta_str and not desde_str:
        h = datetime.fromisoformat(hasta_str).date()
        return h, h

    return (
        datetime.fromisoformat(desde_str).date(),
        datetime.fromisoformat(hasta_str).date(),
    )

def cargar_tipos_salida():
    conn = get_db_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cur.execute("""
            SELECT id_tipo_salida, nombre
            FROM tipo_salida
            WHERE estado IS NULL
               OR LOWER(TRIM(estado))='activo'
               OR TRIM(estado)='1'
            ORDER BY nombre
        """)
        return cur.fetchall() or []
    except Exception as e:
        print("Error cargar_tipos_salida listado:", e)
        return []
    finally:
        cur.close()
        conn.close()


# =========================
# VISTA HTML
# =========================
@reportes_salidas_listado_bp.route("/reportes/salidas/listado", methods=["GET"])
def vista_reporte_salidas_listado():
    if "usuario" not in session:
        return redirect(url_for("rutas_dp.index"))
    return render_template(
        "reporte_salidas_listado.html",
        usuario=session.get("usuario"),
        rol_nombre=session.get("rol_nombre"),
        tipos_salida=cargar_tipos_salida(),
    )


# =========================
# JSON: listado por salida
# =========================
@reportes_salidas_listado_bp.route("/reportes/salidas/listado/data", methods=["GET"])
def data_reporte_salidas_listado():
    if "usuario" not in session:
        return jsonify({"success": False, "message": "Sesión expirada"}), 401

    desde_str = (request.args.get("desde") or "").strip()
    hasta_str = (request.args.get("hasta") or "").strip()
    q = (request.args.get("q") or "").strip()  # nombre beneficiario o doc o id_salida
    estado = (request.args.get("estado") or "").strip()  # Activo|Anulado|"" (opcional)
    id_tipo_salida = request.args.get("id_tipo_salida", type=int)
    beneficiario_tipo = (request.args.get("beneficiario_tipo") or "").strip()  # Parroquia|Fundacion|"" (opcional)
    solo_con_beneficiario = (request.args.get("solo_con_beneficiario") or "").strip().lower()  # "1" para excluir N/A

    fecha_desde, fecha_hasta = parse_fechas(desde_str, hasta_str)

    filtros = ["1=1"]
    params = []

    if fecha_desde and fecha_hasta:
        filtros.append("DATE(s.fecha_salida) >= %s")
        filtros.append("DATE(s.fecha_salida) <= %s")
        params.extend([fecha_desde, fecha_hasta])

    if estado:
        filtros.append("s.estado = %s")
        params.append(estado)

    if id_tipo_salida:
        filtros.append("s.id_tipo_salida = %s")
        params.append(id_tipo_salida)

    if beneficiario_tipo in ("Parroquia", "Fundacion"):
        if beneficiario_tipo == "Parroquia":
            filtros.append("s.id_parroquia IS NOT NULL")
        else:
            filtros.append("s.id_fundaciones IS NOT NULL")

    if solo_con_beneficiario == "1":
        filtros.append("(s.id_parroquia IS NOT NULL OR s.id_fundaciones IS NOT NULL)")

    if q:
        if q.isdigit():
            filtros.append("(s.id_salida = %s OR COALESCE(p.nombre, f.nombre) LIKE %s OR COALESCE(p.numero_documento, f.numero_documento) LIKE %s)")
            params.extend([int(q), f"%{q}%", f"%{q}%"])
        else:
            filtros.append("(COALESCE(p.nombre, f.nombre) LIKE %s OR COALESCE(p.numero_documento, f.numero_documento) LIKE %s)")
            params.extend([f"%{q}%", f"%{q}%"])

    where_clause = "WHERE " + " AND ".join(filtros)

    conn = get_db_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)

    try:
        sql = f"""
            SELECT
                s.id_salida,
                s.fecha_salida,
                s.estado,
                ts.nombre AS tipo_salida,
                s.observacion,

                CASE
                    WHEN s.id_parroquia IS NOT NULL THEN 'Parroquia'
                    WHEN s.id_fundaciones IS NOT NULL THEN 'Fundacion'
                    ELSE 'N/A'
                END AS beneficiario_tipo,

                COALESCE(p.id_parroquia, f.id_fundaciones) AS id_beneficiario,
                COALESCE(p.nombre, f.nombre) AS beneficiario_nombre,
                COALESCE(p.numero_documento, f.numero_documento) AS numero_documento,

                SUM(sd.cantidad_kg) AS total_kg,
                SUM(COALESCE(sd.valor_total, 0)) AS total_valor

            FROM salidas s
            JOIN tipo_salida ts ON ts.id_tipo_salida = s.id_tipo_salida
            LEFT JOIN parroquias p ON p.id_parroquia = s.id_parroquia
            LEFT JOIN fundacioines f ON f.id_fundaciones = s.id_fundaciones
            JOIN salida_detalles sd ON sd.id_salida = s.id_salida

            {where_clause}

            GROUP BY
                s.id_salida, s.fecha_salida, s.estado, ts.nombre, s.observacion,
                beneficiario_tipo, id_beneficiario, beneficiario_nombre, numero_documento

            ORDER BY s.fecha_salida DESC, s.id_salida DESC;
        """

        cur.execute(sql, params)
        rows = cur.fetchall() or []

        items = []
        tot_kg = Decimal("0")
        tot_val = Decimal("0")

        for r in rows:
            kg = _decimal_or_zero(r.get("total_kg"))
            val = _decimal_or_zero(r.get("total_valor"))
            tot_kg += kg
            tot_val += val

            items.append({
                "id_salida": r["id_salida"],
                "fecha_salida": r["fecha_salida"].strftime("%Y-%m-%d") if r.get("fecha_salida") else None,
                "estado": r.get("estado") or "",
                "tipo_salida": r.get("tipo_salida") or "",
                "beneficiario_tipo": r.get("beneficiario_tipo") or "N/A",
                "beneficiario_nombre": r.get("beneficiario_nombre") or "",
                "numero_documento": r.get("numero_documento") or "",
                "observacion": r.get("observacion") or "",
                "total_kg": float(kg),
                "total_kg_str": format_kg(kg),
                "total_valor": float(val),
                "total_valor_str": format_money(val),
            })

        return jsonify({
            "success": True,
            "items": items,
            "totales": {
                "total_kg": float(tot_kg),
                "total_kg_str": format_kg(tot_kg),
                "total_valor": float(tot_val),
                "total_valor_str": format_money(tot_val),
            }
        })

    except Exception as e:
        print("Error data_reporte_salidas_listado:", e)
        return jsonify({"success": False, "message": "Error al generar el listado"}), 500
    finally:
        cur.close()
        conn.close()


@reportes_salidas_listado_bp.route("/reportes/salidas/listado/detalle/<int:id_salida>", methods=["GET"])
def api_detalle_salida_listado(id_salida):
    if "usuario" not in session:
        return jsonify({"success": False, "message": "Sesión expirada"}), 401

    conn = get_db_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)

    try:
        # Cabecera (beneficiario + tipo)
        cur.execute("""
            SELECT
                s.id_salida,
                s.fecha_salida,
                s.estado,
                ts.nombre AS tipo_salida,
                s.observacion,

                CASE
                    WHEN s.id_parroquia IS NOT NULL THEN 'Parroquia'
                    WHEN s.id_fundaciones IS NOT NULL THEN 'Fundacion'
                    ELSE 'N/A'
                END AS beneficiario_tipo,

                COALESCE(p.nombre, f.nombre) AS beneficiario_nombre,
                COALESCE(p.numero_documento, f.numero_documento) AS numero_documento,
                COALESCE(p.municipio, f.municipio) AS municipio,
                COALESCE(p.departamento, f.departamento) AS departamento
            FROM salidas s
            JOIN tipo_salida ts ON ts.id_tipo_salida = s.id_tipo_salida
            LEFT JOIN parroquias p ON p.id_parroquia = s.id_parroquia
            LEFT JOIN fundacioines f ON f.id_fundaciones = s.id_fundaciones
            WHERE s.id_salida = %s
            LIMIT 1
        """, (id_salida,))
        cab = cur.fetchone()

        if not cab:
            return jsonify({"success": False, "message": "Salida no encontrada"}), 404

        # Detalles (productos)
        cur.execute("""
            SELECT
                sd.id_detalle_salida,
                p.id_producto,
                p.nombre AS producto,
                c.nombre AS categoria,
                b.nombre_bodega AS bodega,
                sd.bodega_texto AS ubicacion,
                sd.fecha_vencimiento,
                sd.cantidad_kg,
                sd.valor_unitario,
                sd.valor_total
            FROM salida_detalles sd
            JOIN productos p ON p.id_producto = sd.id_producto
            JOIN categorias c ON c.id_categoria = sd.id_categoria
            JOIN bodegas b ON b.id_bodega = sd.id_bodega
            WHERE sd.id_salida = %s
            ORDER BY p.nombre ASC, sd.fecha_vencimiento ASC
        """, (id_salida,))
        det = cur.fetchall() or []

        # Normalizar Decimal/fechas
        detalles = []
        for d in det:
            def _f(x):
                return float(x) if isinstance(x, Decimal) else (x or 0)

            detalles.append({
                "id_detalle_salida": d["id_detalle_salida"],
                "id_producto": d["id_producto"],
                "producto": d["producto"] or "",
                "categoria": d["categoria"] or "",
                "bodega": d["bodega"] or "",
                "ubicacion": d["ubicacion"] or "",
                "fecha_vencimiento": d["fecha_vencimiento"].strftime("%Y-%m-%d") if d.get("fecha_vencimiento") else None,
                "cantidad_kg": _f(d.get("cantidad_kg")),
                "valor_unitario": _f(d.get("valor_unitario")),
                "valor_total": _f(d.get("valor_total")),
            })

        cab_out = {
            "id_salida": cab["id_salida"],
            "fecha_salida": cab["fecha_salida"].strftime("%Y-%m-%d") if cab.get("fecha_salida") else None,
            "estado": cab.get("estado") or "",
            "tipo_salida": cab.get("tipo_salida") or "",
            "observacion": cab.get("observacion") or "",
            "beneficiario_tipo": cab.get("beneficiario_tipo") or "N/A",
            "beneficiario_nombre": cab.get("beneficiario_nombre") or "",
            "numero_documento": cab.get("numero_documento") or "",
            "municipio": cab.get("municipio") or "",
            "departamento": cab.get("departamento") or "",
        }

                # -----------------------------
        # Bitácora (consulta detalle salida)
        # -----------------------------
        id_usuario = session.get("id_usuario")
        if id_usuario:
            desc = f"Consultó detalle de salida ID {id_salida}"
            registrar_bitacora(
                cur,
                id_usuario=id_usuario,
                modulo="REPORTES",
                accion="CONSULTAR",
                descripcion=desc,
                tabla_afectada="salidas",
                id_registro=id_salida
            )
            conn.commit()


        return jsonify({"success": True, "cabecera": cab_out, "detalles": detalles})

    except Exception as e:
        print("Error api_detalle_salida_listado:", e)
        return jsonify({"success": False, "message": "Error cargando detalle"}), 500
    finally:
        cur.close()
        conn.close()


@reportes_salidas_listado_bp.route("/reportes/salidas/listado/excel", methods=["GET"])
def excel_reporte_salidas_listado():
    if "usuario" not in session:
        return "Sesión expirada", 401

    # mismos filtros que /data
    desde_str = (request.args.get("desde") or "").strip()
    hasta_str = (request.args.get("hasta") or "").strip()
    q = (request.args.get("q") or "").strip()
    estado = (request.args.get("estado") or "").strip()
    id_tipo_salida = request.args.get("id_tipo_salida", type=int)
    beneficiario_tipo = (request.args.get("beneficiario_tipo") or "").strip()

    fecha_desde, fecha_hasta = parse_fechas(desde_str, hasta_str)

    filtros = ["1=1"]
    params = []

    if fecha_desde and fecha_hasta:
        filtros.append("DATE(s.fecha_salida) >= %s")
        filtros.append("DATE(s.fecha_salida) <= %s")
        params.extend([fecha_desde, fecha_hasta])

    if estado:
        filtros.append("s.estado = %s")
        params.append(estado)

    if id_tipo_salida:
        filtros.append("s.id_tipo_salida = %s")
        params.append(id_tipo_salida)

    if beneficiario_tipo in ("Parroquia", "Fundacion"):
        filtros.append("s.id_parroquia IS NOT NULL" if beneficiario_tipo == "Parroquia" else "s.id_fundaciones IS NOT NULL")

    if q:
        if q.isdigit():
            filtros.append("(s.id_salida = %s OR COALESCE(p.nombre, f.nombre) LIKE %s OR COALESCE(p.numero_documento, f.numero_documento) LIKE %s)")
            params.extend([int(q), f"%{q}%", f"%{q}%"])
        else:
            filtros.append("(COALESCE(p.nombre, f.nombre) LIKE %s OR COALESCE(p.numero_documento, f.numero_documento) LIKE %s)")
            params.extend([f"%{q}%", f"%{q}%"])

    where_clause = "WHERE " + " AND ".join(filtros)

    conn = get_db_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)

    try:
        # Hoja 1: resumen por salida
        cur.execute(f"""
            SELECT
                s.id_salida,
                s.fecha_salida,
                s.estado,
                ts.nombre AS tipo_salida,
                CASE
                    WHEN s.id_parroquia IS NOT NULL THEN 'Parroquia'
                    WHEN s.id_fundaciones IS NOT NULL THEN 'Fundacion'
                    ELSE 'N/A'
                END AS beneficiario_tipo,
                COALESCE(p.nombre, f.nombre) AS beneficiario_nombre,
                COALESCE(p.numero_documento, f.numero_documento) AS numero_documento,
                SUM(sd.cantidad_kg) AS total_kg,
                SUM(COALESCE(sd.valor_total, 0)) AS total_valor,
                s.observacion
            FROM salidas s
            JOIN tipo_salida ts ON ts.id_tipo_salida = s.id_tipo_salida
            LEFT JOIN parroquias p ON p.id_parroquia = s.id_parroquia
            LEFT JOIN fundacioines f ON f.id_fundaciones = s.id_fundaciones
            JOIN salida_detalles sd ON sd.id_salida = s.id_salida
            {where_clause}
            GROUP BY
                s.id_salida, s.fecha_salida, s.estado, ts.nombre,
                beneficiario_tipo, beneficiario_nombre, numero_documento, s.observacion
            ORDER BY s.fecha_salida DESC, s.id_salida DESC
        """, params)
        rows_resumen = cur.fetchall() or []

        # Hoja 2: detalle por producto (una fila por item)
        cur.execute(f"""
            SELECT
                s.id_salida,
                s.fecha_salida,
                ts.nombre AS tipo_salida,
                CASE
                    WHEN s.id_parroquia IS NOT NULL THEN 'Parroquia'
                    WHEN s.id_fundaciones IS NOT NULL THEN 'Fundacion'
                    ELSE 'N/A'
                END AS beneficiario_tipo,
                COALESCE(pq.nombre, fd.nombre) AS beneficiario_nombre,

                sd.id_detalle_salida,
                pr.id_producto,
                pr.nombre AS producto,
                c.nombre AS categoria,
                b.nombre_bodega AS bodega,
                sd.bodega_texto AS ubicacion,
                sd.fecha_vencimiento,
                sd.cantidad_kg,
                sd.valor_unitario,
                sd.valor_total
            FROM salidas s
            JOIN tipo_salida ts ON ts.id_tipo_salida = s.id_tipo_salida
            LEFT JOIN parroquias pq ON pq.id_parroquia = s.id_parroquia
            LEFT JOIN fundacioines fd ON fd.id_fundaciones = s.id_fundaciones
            JOIN salida_detalles sd ON sd.id_salida = s.id_salida
            JOIN productos pr ON pr.id_producto = sd.id_producto
            JOIN categorias c ON c.id_categoria = sd.id_categoria
            JOIN bodegas b ON b.id_bodega = sd.id_bodega
            {where_clause}
            ORDER BY s.id_salida DESC, pr.nombre ASC
        """, params)
        rows_detalle = cur.fetchall() or []

        wb = Workbook()

        # Sheet 1
        ws1 = wb.active
        ws1.title = "Resumen por salida"
        ws1.append([
            "ID Salida","Fecha","Tipo","Estado","Beneficiario tipo","Beneficiario","Documento","Total (kg)","Valor total","Observación"
        ])

        for r in rows_resumen:
            kg = float(_decimal_or_zero(r.get("total_kg")))
            val = float(_decimal_or_zero(r.get("total_valor")))
            ws1.append([
                r.get("id_salida"),
                r["fecha_salida"].strftime("%Y-%m-%d") if r.get("fecha_salida") else "",
                r.get("tipo_salida") or "",
                r.get("estado") or "",
                r.get("beneficiario_tipo") or "",
                r.get("beneficiario_nombre") or "",
                r.get("numero_documento") or "",
                kg,
                val,
                r.get("observacion") or ""
            ])

        # Sheet 2
        ws2 = wb.create_sheet("Detalle productos")
        ws2.append([
            "ID Salida","Fecha","Tipo","Beneficiario tipo","Beneficiario",
            "ID Detalle","ID Producto","Producto","Categoría","Bodega","Ubicación","Vence",
            "Cantidad (kg)","Valor unitario","Valor total"
        ])

        for r in rows_detalle:
            ws2.append([
                r.get("id_salida"),
                r["fecha_salida"].strftime("%Y-%m-%d") if r.get("fecha_salida") else "",
                r.get("tipo_salida") or "",
                r.get("beneficiario_tipo") or "",
                r.get("beneficiario_nombre") or "",
                r.get("id_detalle_salida"),
                r.get("id_producto"),
                r.get("producto") or "",
                r.get("categoria") or "",
                r.get("bodega") or "",
                r.get("ubicacion") or "",
                r["fecha_vencimiento"].strftime("%Y-%m-%d") if r.get("fecha_vencimiento") else "",
                float(_decimal_or_zero(r.get("cantidad_kg"))),
                float(_decimal_or_zero(r.get("valor_unitario"))),
                float(_decimal_or_zero(r.get("valor_total"))),
            ])

        output = BytesIO()
        wb.save(output)
        output.seek(0)

                # -----------------------------
        # Bitácora (exportar excel listado salidas)
        # -----------------------------
        id_usuario = session.get("id_usuario")
        if id_usuario:
            desc = (
                "Exportó Excel de listado de salidas "
                f"(desde={fecha_desde or ''}, hasta={fecha_hasta or ''}, "
                f"q='{q}', estado='{estado}', id_tipo_salida='{id_tipo_salida or ''}', "
                f"beneficiario_tipo='{beneficiario_tipo}')"
            )
            registrar_bitacora(
                cur,
                id_usuario=id_usuario,
                modulo="REPORTES",
                accion="EXPORTAR",
                descripcion=desc,
                tabla_afectada="salidas",
                id_registro=None
            )
            conn.commit()


        filename = "reporte_salidas_listado.xlsx"
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    except Exception as e:
        print("Error excel_reporte_salidas_listado:", e)
        return "Error al exportar Excel", 500
    finally:
        cur.close()
        conn.close()
