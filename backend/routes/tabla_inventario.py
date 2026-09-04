# routes/tabla_inventario.py

from flask import Blueprint, render_template, session, jsonify, request, send_file
from database import get_db_connection
from io import BytesIO
from datetime import date
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter
from psycopg2.extras import RealDictCursor


tabla_inventario = Blueprint('tabla_inventario', __name__)


# ============================================================
# VISTA DEL INVENTARIO
# ============================================================

@tabla_inventario.route('/tabla-producto', methods=['GET'])
def tabla_producto():

    if "usuario" not in session:
        return render_template("index.html"), 401

    return render_template(
        "tabla_producto.html",
        usuario=session.get("usuario")
    )


# ============================================================
# OBTENER INVENTARIO
# ============================================================

def _obtener_productos_inventario(q=""):

    q = (q or "").strip()

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:

        # ======================================================
        # FILTROS
        # ======================================================

        filtros = [
            "p.estado = 'Activo'"
        ]

        params = []

        if q:

            if q.isdigit():

                filtros.append(
                    "(p.id_producto = %s OR p.nombre ILIKE %s)"
                )

                params.append(int(q))
                params.append(f"%{q}%")

            else:

                filtros.append(
                    "p.nombre ILIKE %s"
                )

                params.append(f"%{q}%")


        where_clause = " AND ".join(filtros)


        # ======================================================
        # PRODUCTOS
        #
        # IMPORTANTE:
        # Aquí NO filtramos por cantidad_total.
        #
        # Así podemos comprobar que todos los productos
        # creados aparecen en el inventario.
        # ======================================================

        sql_productos = f"""
            SELECT
                p.id_producto,
                p.nombre,
                p.estado,

                COALESCE(
                    inv.cantidad_total,
                    0
                ) AS cantidad_total

            FROM productos p

            LEFT JOIN inventario_productos inv
                ON inv.id_producto = p.id_producto

            WHERE {where_clause}

            ORDER BY
                p.id_producto ASC;
        """


        cursor.execute(
            sql_productos,
            params
        )

        filas_productos = cursor.fetchall()


        # ======================================================
        # DETALLE DE LOTES
        #
        # Aquí calculamos el stock real de cada lote.
        # NO usamos el alias stock_kg en HAVING.
        # ======================================================

        sql_detalles = """

            SELECT

                ed.id_producto,

                ed.fecha_vencimiento,

                (
                    SUM(
                        COALESCE(
                            ed.peso_total_kg,
                            0
                        )
                    )

                    -

                    COALESCE(
                        SUM(
                            CASE

                                WHEN s.estado = 'Activo'

                                THEN COALESCE(
                                    sd.cantidad_kg,
                                    0
                                )

                                ELSE 0

                            END
                        ),
                        0
                    )
                ) AS stock_kg,

                b.nombre_bodega,

                ed.bodega_texto


            FROM entrada_detalles ed


            JOIN entradas e

                ON e.id_entrada = ed.id_entrada

                AND e.estado = 'Activo'


            LEFT JOIN bodegas b

                ON b.id_bodega = ed.id_bodega


            LEFT JOIN salida_detalles sd

                ON sd.id_entrada_detalle = ed.id_detalle


            LEFT JOIN salidas s

                ON s.id_salida = sd.id_salida


            GROUP BY

                ed.id_producto,

                ed.fecha_vencimiento,

                b.id_bodega,

                b.nombre_bodega,

                ed.bodega_texto


            ORDER BY

                ed.id_producto ASC,

                ed.fecha_vencimiento ASC;

        """


        cursor.execute(sql_detalles)

        filas_detalle = cursor.fetchall()


        # ======================================================
        # MAPA DE LOTES
        # ======================================================

        detalles_map = {}


        for d in filas_detalle:

            pid = d["id_producto"]

            stock = float(
                d["stock_kg"] or 0
            )


            # Solamente mostramos lotes con existencia
            if stock <= 0:
                continue


            fecha_vencimiento = d[
                "fecha_vencimiento"
            ]


            detalles_map.setdefault(
                pid,
                []
            ).append({

                "fecha_vencimiento":
                    fecha_vencimiento.isoformat()
                    if fecha_vencimiento
                    else None,

                "stock_kg":
                    stock,

                "nombre_bodega":
                    d.get(
                        "nombre_bodega"
                    ),

                "bodega_texto":
                    d.get(
                        "bodega_texto"
                    )
            })


        # ======================================================
        # ARMAR PRODUCTOS
        # ======================================================

        productos = []


        for p in filas_productos:

            pid = p["id_producto"]

            detalles = detalles_map.get(
                pid,
                []
            )


            # --------------------------------------------------
            # PRÓXIMO LOTE
            # --------------------------------------------------

            proximo_vencimiento = None
            proxima_bodega = None
            proxima_ubicacion = None


            if detalles:

                primer_lote = detalles[0]

                proximo_vencimiento = (
                    primer_lote[
                        "fecha_vencimiento"
                    ]
                )

                proxima_bodega = (
                    primer_lote[
                        "nombre_bodega"
                    ]
                )

                proxima_ubicacion = (
                    primer_lote[
                        "bodega_texto"
                    ]
                )


            productos.append({

                "id_producto":
                    p["id_producto"],

                "nombre":
                    p["nombre"],

                "estado":
                    p["estado"],

                "cantidad_total":
                    float(
                        p["cantidad_total"]
                        or 0
                    ),

                "proximo_vencimiento":
                    proximo_vencimiento,

                "proxima_bodega":
                    proxima_bodega,

                "proxima_ubicacion":
                    proxima_ubicacion,

                "detalles":
                    detalles
            })


        return productos


    finally:

        cursor.close()
        conn.close()


# ============================================================
# API INVENTARIO
# ============================================================

@tabla_inventario.route(
    '/api/productos',
    methods=['GET']
)
def api_productos_inventario():

    try:

        q = request.args.get(
            'q',
            ''
        ).strip()


        productos = _obtener_productos_inventario(
            q
        )


        return jsonify({

            "success": True,

            "productos":
                productos,

            "total":
                len(productos)
        })


    except Exception as e:

        print(
            "\n======================================"
        )

        print(
            "ERROR API INVENTARIO:"
        )

        print(
            repr(e)
        )

        print(
            "======================================\n"
        )


        return jsonify({

            "success": False,

            "message":
                "Error al obtener el inventario",

            "error":
                str(e)
        }), 500


# ============================================================
# EXPORTAR VENCIMIENTOS A EXCEL
# ============================================================

@tabla_inventario.route(
    '/export/vencimientos.xlsx',
    methods=['GET']
)
def export_vencimientos_excel():

    if "usuario" not in session:

        return render_template(
            "index.html"
        ), 401


    try:

        q = request.args.get(
            'q',
            ''
        ).strip()


        productos = _obtener_productos_inventario(
            q
        )


        filas = []


        for p in productos:

            for d in (
                p.get("detalles")
                or []
            ):

                filas.append([

                    p.get(
                        "id_producto"
                    ),

                    p.get(
                        "nombre"
                    ),

                    d.get(
                        "fecha_vencimiento"
                    ),

                    float(
                        d.get(
                            "stock_kg"
                        )
                        or 0
                    ),

                    d.get(
                        "nombre_bodega"
                    )
                    or "-",

                    d.get(
                        "bodega_texto"
                    )
                    or "-"
                ])


        # ======================================================
        # ORDENAR POR FECHA
        # ======================================================

        filas.sort(
            key=lambda r: (
                r[2] is None,
                r[2] or "9999-12-31",
                r[1] or ""
            )
        )


        # ======================================================
        # CREAR EXCEL
        # ======================================================

        wb = Workbook()

        ws = wb.active

        ws.title = "Vencimientos"


        headers = [

            "ID",

            "Producto",

            "Fecha vencimiento",

            "Stock lote (kg)",

            "Bodega",

            "Ubicación"
        ]


        ws.append(headers)


        # ======================================================
        # ENCABEZADOS
        # ======================================================

        bold = Font(
            bold=True
        )


        for c in range(
            1,
            len(headers) + 1
        ):

            cell = ws.cell(
                row=1,
                column=c
            )

            cell.font = bold

            cell.alignment = Alignment(
                horizontal="center"
            )


        # ======================================================
        # DATOS
        # ======================================================

        for row in filas:

            ws.append(row)


        ws.freeze_panes = "A2"


        ws.auto_filter.ref = (
            f"A1:F{ws.max_row}"
        )


        # ======================================================
        # FORMATOS
        # ======================================================

        for cell in ws["C"][1:]:

            cell.number_format = (
                "dd/mm/yyyy"
            )


        for cell in ws["D"][1:]:

            cell.number_format = (
                "0.000"
            )


        # ======================================================
        # AUTO ANCHO
        # ======================================================

        for col in range(
            1,
            ws.max_column + 1
        ):

            max_len = 0


            for cell in ws[
                get_column_letter(col)
            ]:

                value = (

                    ""

                    if cell.value is None

                    else str(
                        cell.value
                    )
                )


                max_len = max(
                    max_len,
                    len(value)
                )


            ws.column_dimensions[
                get_column_letter(col)
            ].width = min(
                max_len + 2,
                45
            )


        # ======================================================
        # GENERAR ARCHIVO
        # ======================================================

        bio = BytesIO()

        wb.save(bio)

        bio.seek(0)


        return send_file(

            bio,

            as_attachment=True,

            download_name=
                "vencimientos_inventario.xlsx",

            mimetype=
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


    except Exception as e:

        print(
            "ERROR EXPORTANDO INVENTARIO:",
            repr(e)
        )

        return jsonify({

            "success": False,

            "message":
                "No se pudo generar el archivo",

            "error":
                str(e)

        }), 500