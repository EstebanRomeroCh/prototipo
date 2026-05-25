# routes/salidas.py

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from database import get_db_connection
import pymysql
from decimal import Decimal, InvalidOperation
from datetime import datetime
from utils.bitacora import registrar_bitacora   # si ya la tienes y quieres registrar acciones
from psycopg2.extras import RealDictCursor

salidas_bp = Blueprint('salidas_bp', __name__, url_prefix='/salidas')


# ============================
# Helpers
# ============================

# ============================
# Helpers
# ============================

def decimal_or_zero(value):
    try:
        return Decimal(str(value or 0))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal('0')


def parse_fecha_yyyy_mm_dd(fecha_str):
    if not fecha_str:
        return datetime.now()
    try:
        return datetime.strptime(fecha_str, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Formato de fecha_salida inválido. Use YYYY-MM-DD.")


# ============================
# 1) Vista HTML: registrar salida
# ============================

@salidas_bp.route('/nueva', methods=['GET'])
def nueva_salida():
    if 'usuario' not in session:
        return redirect(url_for('index'))

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT id_tipo_salida, nombre
            FROM tipo_salida
            WHERE estado = 'Activo'
            ORDER BY nombre
        """)
        tipos_salida = cursor.fetchall() or []
    except Exception as e:
        print("Error cargando tipo_salida:", e)
        tipos_salida = []
    finally:
        cursor.close()
        conn.close()

    return render_template(
        "salidas_nueva.html",
        usuario=session.get("usuario"),
        tipos_salida=tipos_salida
    )


# ============================
# 2) API: tipos de salida
# ============================

@salidas_bp.route('/api/tipos-salida', methods=['GET'])
def api_tipos_salida():
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'Sesión expirada'}), 401

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT id_tipo_salida, nombre, descripcion
            FROM tipo_salida
            WHERE estado = 'Activo'
            ORDER BY nombre
        """)
        filas = cursor.fetchall() or []
        return jsonify({"success": True, "items": filas})
    except Exception as e:
        print("Error api_tipos_salida:", e)
        return jsonify({"success": False, "message": "Error al cargar tipos de salida"}), 500
    finally:
        cursor.close()
        conn.close()


# ============================
# 3) API: beneficiarios (Parroquias + Fundaciones)
# ============================

@salidas_bp.route('/api/beneficiarios', methods=['GET'])
def api_beneficiarios():
    """
    Devuelve beneficiarios activos:
        - Parroquias (tabla parroquias)
        - Fundaciones (tabla fundacioines)

    Query param:
        - q: filtra por nombre o numero_documento
    """
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'Sesión expirada'}), 401

    q = (request.args.get('q') or '').strip()

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        filtros_p = ["p.estado = 'Activo'"]
        filtros_f = ["f.estado = 'Activo'"]
        params_p = []
        params_f = []

        if q:
            filtros_p.append("(p.nombre LIKE %s OR p.numero_documento LIKE %s)")
            params_p.extend([f"%{q}%", f"%{q}%"])

            filtros_f.append("(f.nombre LIKE %s OR f.numero_documento LIKE %s)")
            params_f.extend([f"%{q}%", f"%{q}%"])

        where_p = "WHERE " + " AND ".join(filtros_p)
        where_f = "WHERE " + " AND ".join(filtros_f)

        sql = f"""
            SELECT
                'Parroquia' AS tipo,
                p.id_parroquia AS id_beneficiario,
                p.nombre,
                p.nombre_encargado AS encargado,
                p.tipo_doc_id,
                p.numero_documento,
                p.telefono,
                p.municipio,
                p.departamento
            FROM parroquias p
            {where_p}

            UNION ALL

            SELECT
                'Fundacion' AS tipo,
                f.id_fundaciones AS id_beneficiario,
                f.nombre,
                f.nombre_encargado AS encargado,
                f.tipo_doc_id,
                f.numero_documento,
                f.telefono,
                f.municipio,
                f.departamento
            FROM fundacioines f
            {where_f}

            ORDER BY nombre ASC
            LIMIT 50;
        """

        cursor.execute(sql, params_p + params_f)
        filas = cursor.fetchall() or []
        return jsonify({"success": True, "items": filas})

    except Exception as e:
        print("Error api_beneficiarios:", e)
        return jsonify({"success": False, "message": "Error al buscar beneficiarios"}), 500
    finally:
        cursor.close()
        conn.close()

# ============================
# 2) API: Lotes de producto disponibles (FEFO)
# ============================

@salidas_bp.route('/api/lotes-disponibles', methods=['GET'])
def api_lotes_disponibles():
    """
    Lotes disponibles por detalle de entrada con stock > 0.
    Parámetro opcional:
        - q: filtrar por nombre de producto o id_producto
    """
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'Sesión expirada'}), 401

    q = (request.args.get('q') or '').strip()

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        filtros = ["e.estado = 'Activo'"]
        params = []

        if q:
            if q.isdigit():
                filtros.append("(p.id_producto = %s OR p.nombre LIKE %s)")
                params.extend([int(q), f"%{q}%"])
            else:
                filtros.append("p.nombre LIKE %s")
                params.append(f"%{q}%")

        where_clause = "WHERE " + " AND ".join(filtros)

        sql = f"""
            SELECT
                ed.id_detalle            AS id_entrada_detalle,
                ed.id_producto,
                p.nombre                 AS nombre_producto,
                c.id_categoria,
                c.nombre                 AS nombre_categoria,
                ed.id_bodega,
                b.nombre_bodega,
                ed.bodega_texto,
                ed.fecha_vencimiento,
                (ed.peso_total_kg - COALESCE(SUM(sd.cantidad_kg), 0)) AS stock_disponible_kg
            FROM entrada_detalles ed
            JOIN entradas e
                ON e.id_entrada = ed.id_entrada
            JOIN productos p
                ON p.id_producto = ed.id_producto
            JOIN categorias c
                ON c.id_categoria = ed.id_categoria
            JOIN bodegas b
                ON b.id_bodega = ed.id_bodega
            LEFT JOIN salida_detalles sd
                ON sd.id_entrada_detalle = ed.id_detalle
            {where_clause}
            GROUP BY
                ed.id_detalle,
                ed.id_producto,
                p.nombre,
                c.id_categoria,
                c.nombre,
                ed.id_bodega,
                b.nombre_bodega,
                ed.bodega_texto,
                ed.fecha_vencimiento,
                ed.peso_total_kg
            HAVING stock_disponible_kg > 0
            ORDER BY
                ed.fecha_vencimiento IS NULL ASC,
                ed.fecha_vencimiento ASC,
                p.nombre ASC;
        """

        cursor.execute(sql, params)
        filas = cursor.fetchall() or []

        items = []
        for row in filas:
            stock = decimal_or_zero(row["stock_disponible_kg"])
            items.append({
                "id_entrada_detalle": row["id_entrada_detalle"],
                "id_producto": row["id_producto"],
                "producto": row["nombre_producto"],
                "id_categoria": row["id_categoria"],
                "categoria": row["nombre_categoria"],
                "id_bodega": row["id_bodega"],
                "bodega": row["nombre_bodega"],
                "bodega_texto": row.get("bodega_texto"),
                "fecha_vencimiento": row["fecha_vencimiento"].isoformat() if row["fecha_vencimiento"] else None,
                "stock_disponible_kg": float(stock)
            })

        return jsonify({"success": True, "items": items})

    except Exception as e:
        print("Error api_lotes_disponibles:", e)
        return jsonify({"success": False, "message": "Error al consultar lotes disponibles"}), 500
    finally:
        cursor.close()
        conn.close()


# ============================
# 5) API: crear salida
# ============================

@salidas_bp.route('/api/crear', methods=['POST'])
def api_crear_salida():
    """
    JSON esperado:
    {
        "tipo_beneficiario": "Parroquia" | "Fundacion",
        "id_beneficiario": 10,
        "id_tipo_salida": 1,
        "fecha_salida": "YYYY-MM-DD" (opcional),
        "observacion": "...",
        "detalles": [
        { "id_entrada_detalle": 5, "cantidad_kg": 12.5, "valor_unitario": 0 }
        ]
    }
    """
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'Sesión expirada'}), 401

    data = request.get_json(silent=True) or {}

    tipo_beneficiario = (data.get("tipo_beneficiario") or "").strip()
    id_beneficiario = data.get("id_beneficiario")
    id_tipo_salida = data.get("id_tipo_salida")
    fecha_salida_str = data.get("fecha_salida")
    observacion = (data.get("observacion") or "").strip()
    detalles = data.get("detalles") or []

    if tipo_beneficiario not in ("Parroquia", "Fundacion"):
        return jsonify({"success": False, "message": "Debe seleccionar el tipo de beneficiario."}), 400

    if not id_beneficiario or not id_tipo_salida:
        return jsonify({"success": False, "message": "Debe seleccionar beneficiario y tipo de salida."}), 400

    if not detalles:
        return jsonify({"success": False, "message": "Debe agregar al menos un producto en el detalle."}), 400

    try:
        fecha_salida = parse_fecha_yyyy_mm_dd(fecha_salida_str)
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400

    id_parroquia = int(id_beneficiario) if tipo_beneficiario == "Parroquia" else None
    id_fundaciones = int(id_beneficiario) if tipo_beneficiario == "Fundacion" else None

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        conn.autocommit(False)

        # 0) Validar existencia beneficiario
        if id_parroquia is not None:
            cursor.execute("SELECT id_parroquia FROM parroquias WHERE id_parroquia=%s AND estado='Activo' LIMIT 1", (id_parroquia,))
            if not cursor.fetchone():
                raise ValueError("La parroquia seleccionada no existe o está inactiva.")
        else:
            cursor.execute("SELECT id_fundaciones FROM fundacioines WHERE id_fundaciones=%s AND estado='Activo' LIMIT 1", (id_fundaciones,))
            if not cursor.fetchone():
                raise ValueError("La fundación seleccionada no existe o está inactiva.")

        # 1) Insert cabecera
        total_peso_kg = Decimal('0')
        total_valor = Decimal('0')

        cursor.execute("""
            INSERT INTO salidas (
                id_tipo_salida,
                id_parroquia,
                id_fundaciones,
                fecha_salida,
                observacion,
                total_peso_kg,
                total_valor,
                estado
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'Activo')
        """, (
            id_tipo_salida,
            id_parroquia,
            id_fundaciones,
            fecha_salida,
            observacion,
            total_peso_kg,
            total_valor
        ))
        id_salida = cursor.lastrowid

        # 2) Detalles
        kg_por_producto = {}

        for det in detalles:
            id_entrada_detalle = det.get("id_entrada_detalle")
            cant_kg = decimal_or_zero(det.get("cantidad_kg"))
            valor_unitario = decimal_or_zero(det.get("valor_unitario"))

            if not id_entrada_detalle or cant_kg <= 0:
                raise ValueError("Detalle inválido: id_entrada_detalle o cantidad_kg incorrectos.")

            # 2.1) Traer lote
            cursor.execute("""
                SELECT
                    ed.id_detalle,
                    ed.id_producto,
                    ed.id_categoria,
                    ed.id_bodega,
                    ed.bodega_texto,
                    ed.fecha_vencimiento,
                    ed.peso_total_kg
                FROM entrada_detalles ed
                JOIN entradas e ON e.id_entrada = ed.id_entrada
                WHERE ed.id_detalle = %s
                    AND e.estado = 'Activo'
                LIMIT 1
            """, (id_entrada_detalle,))
            lote = cursor.fetchone()

            if not lote:
                raise ValueError(f"Lote {id_entrada_detalle} no existe o está inactivo.")

            # 2.2) Stock disponible lote
            cursor.execute("""
                SELECT COALESCE(SUM(sd.cantidad_kg), 0) AS total_salida_kg
                FROM salida_detalles sd
                WHERE sd.id_entrada_detalle = %s
            """, (id_entrada_detalle,))
            row_s = cursor.fetchone() or {}
            total_salida_kg = decimal_or_zero(row_s.get("total_salida_kg"))
            stock_lote = decimal_or_zero(lote["peso_total_kg"]) - total_salida_kg

            if cant_kg > stock_lote:
                raise ValueError(
                    f"La cantidad solicitada ({cant_kg} kg) excede el stock disponible ({stock_lote} kg) del lote {id_entrada_detalle}."
                )

            # 2.3) Insert detalle
            valor_total_det = (valor_unitario * cant_kg) if valor_unitario > 0 else Decimal('0')

            cursor.execute("""
                INSERT INTO salida_detalles (
                    id_salida,
                    id_producto,
                    id_categoria,
                    id_bodega,
                    bodega_texto,
                    fecha_vencimiento,
                    cantidad_kg,
                    valor_unitario,
                    valor_total,
                    id_entrada_detalle
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                id_salida,
                lote["id_producto"],
                lote["id_categoria"],
                lote["id_bodega"],
                lote.get("bodega_texto"),
                lote.get("fecha_vencimiento"),
                cant_kg,
                float(valor_unitario) if valor_unitario > 0 else None,
                float(valor_total_det) if valor_total_det > 0 else None,
                id_entrada_detalle
            ))

            total_peso_kg += cant_kg
            total_valor += valor_total_det

            pid = lote["id_producto"]
            kg_por_producto[pid] = kg_por_producto.get(pid, Decimal('0')) + cant_kg

        # 3) Update totales
        cursor.execute("""
            UPDATE salidas
            SET total_peso_kg = %s,
                total_valor   = %s
            WHERE id_salida = %s
        """, (total_peso_kg, total_valor, id_salida))

        # 4) Restar inventario
        for id_producto, kg_salida in kg_por_producto.items():
            cursor.execute("""
                SELECT inv.cantidad_total, p.stock_minimo
                FROM inventario_productos inv
                JOIN productos p ON p.id_producto = inv.id_producto
                WHERE inv.id_producto = %s
                FOR UPDATE
            """, (id_producto,))
            inv_row = cursor.fetchone()

            if not inv_row:
                raise ValueError(f"No existe inventario_productos para el producto {id_producto}.")

            cant_actual = decimal_or_zero(inv_row["cantidad_total"])
            stock_min = decimal_or_zero(inv_row["stock_minimo"])
            nueva_cantidad = cant_actual - kg_salida

            if nueva_cantidad < 0:
                raise ValueError(
                    f"La salida sobrepasa el inventario del producto {id_producto}. Actual: {cant_actual} kg, salida: {kg_salida} kg."
                )

            if nueva_cantidad <= 0:
                estado_inv = 'AGOTADO'
                nueva_cantidad = Decimal('0')
            elif nueva_cantidad < stock_min:
                estado_inv = 'BAJO'
            else:
                estado_inv = 'OK'

            cursor.execute("""
                UPDATE inventario_productos
                SET cantidad_total = %s,
                    estado = %s,
                    ultima_actualizacion = NOW()
                WHERE id_producto = %s
            """, (nueva_cantidad, estado_inv, id_producto))

        # 5) Bitácora (opcional)
        try:
            id_usuario = session.get('id_usuario')
            if id_usuario:
                registrar_bitacora(
                    cursor,
                    id_usuario=id_usuario,
                    modulo="SALIDAS",
                    accion="CREAR",
                    descripcion=f"Registro de salida id {id_salida}",
                    tabla_afectada="salidas",
                    id_registro=id_salida
                )
        except Exception as e_bit:
            print("Bitácora (SALIDAS) falló:", e_bit)

        conn.commit()
        return jsonify({"success": True, "message": "Salida registrada correctamente.", "id_salida": id_salida})

    except ValueError as e_val:
        conn.rollback()
        return jsonify({"success": False, "message": str(e_val)}), 400

    except Exception as e:
        conn.rollback()
        print("Error api_crear_salida:", e)
        return jsonify({"success": False, "message": "Error al registrar la salida."}), 500

    finally:
        try:
            conn.autocommit(True)
        except Exception:
            pass
        cursor.close()
        conn.close()


@salidas_bp.route('/api/detalle/<int:id_salida>', methods=['GET'])
def api_detalle_salida(id_salida):
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'Sesión expirada'}), 401

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute("""
            SELECT
                s.id_salida,
                s.fecha_salida,
                s.observacion,
                s.total_peso_kg,
                s.total_valor,
                s.estado,
                ts.id_tipo_salida,
                ts.nombre AS tipo_salida,

                CASE
                    WHEN s.id_parroquia IS NOT NULL THEN 'Parroquia'
                    WHEN s.id_fundaciones IS NOT NULL THEN 'Fundacion'
                    ELSE 'N/A'
                END AS beneficiario_tipo,

                COALESCE(p.nombre, f.nombre) AS beneficiario_nombre,
                COALESCE(p.nombre_encargado, f.nombre_encargado) AS encargado,
                COALESCE(p.numero_documento, f.numero_documento) AS numero_documento,
                td.nombre AS tipo_documento,
                COALESCE(p.telefono, f.telefono) AS telefono,
                COALESCE(p.direccion, f.direccion) AS direccion,
                COALESCE(p.municipio, f.municipio) AS municipio,
                COALESCE(p.departamento, f.departamento) AS departamento

            FROM salidas s
            JOIN tipo_salida ts
                ON ts.id_tipo_salida = s.id_tipo_salida
            LEFT JOIN parroquias p
                ON p.id_parroquia = s.id_parroquia
            LEFT JOIN fundacioines f
                ON f.id_fundaciones = s.id_fundaciones
            LEFT JOIN tipo_documento td
                ON td.id_tipo_doc = COALESCE(p.tipo_doc_id, f.tipo_doc_id)
            WHERE s.id_salida = %s
            LIMIT 1
        """, (id_salida,))
        salida = cursor.fetchone()

        if not salida:
            return jsonify({"success": False, "message": "La salida no existe"}), 404

        salida["fecha_salida_str"] = salida["fecha_salida"].strftime("%Y-%m-%d") if salida.get("fecha_salida") else None

        cursor.execute("""
            SELECT
                sd.id_detalle_salida,
                sd.cantidad_kg,
                sd.fecha_vencimiento,
                sd.bodega_texto,
                p.id_producto,
                p.nombre AS producto,
                c.nombre AS categoria,
                b.nombre_bodega AS bodega
            FROM salida_detalles sd
            JOIN productos p   ON p.id_producto = sd.id_producto
            JOIN categorias c  ON c.id_categoria = sd.id_categoria
            JOIN bodegas b     ON b.id_bodega = sd.id_bodega
            WHERE sd.id_salida = %s
            ORDER BY sd.fecha_vencimiento ASC, p.nombre ASC
        """, (id_salida,))
        detalles = cursor.fetchall() or []

        for d in detalles:
            d["fecha_vencimiento_str"] = d["fecha_vencimiento"].strftime("%Y-%m-%d") if d.get("fecha_vencimiento") else None

        return jsonify({"success": True, "salida": salida, "detalles": detalles})

    except Exception as e:
        print("Error api_detalle_salida:", e)
        return jsonify({"success": False, "message": "Error al obtener detalle de la salida"}), 500
    finally:
        cursor.close()
        conn.close()


@salidas_bp.route('/comprobante/<int:id_salida>', methods=['GET'])
def comprobante_salida_view(id_salida):
    if 'usuario' not in session:
        return redirect(url_for('index'))

    # Solo renderiza la plantilla, los datos del comprobante se cargan vía JS
    return render_template(
        'comprobante_salida.html',
        usuario=session.get('usuario'),
        id_salida=id_salida
    )




# ==============================
# 1) Vista HTML: Lista de salidas
# ==============================
@salidas_bp.route('/lista', methods=['GET'])
def vista_lista_salidas():
    if 'usuario' not in session:
        # Ajusta esto al nombre real de tu ruta de login
        return redirect(url_for('login'))

    usuario = session.get('usuario')
    return render_template('salidas_lista.html', usuario=usuario)


# ==============================
# 2) API: Listado de salidas (para la tabla)
# ==============================
@salidas_bp.route('/api/lista', methods=['GET'])
def api_lista_salidas():
    """
    Filtros:
        - estado: 'Activo' | 'Anulado' (vacío = todos)
        - id_tipo_salida: int
    """
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'Sesión expirada'}), 401

    estado = (request.args.get('estado') or '').strip()
    id_tipo_salida = request.args.get('id_tipo_salida', type=int)

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        sql = """
            SELECT
                s.id_salida,
                s.fecha_salida,
                s.total_peso_kg AS total_kg,
                s.estado,
                ts.nombre AS tipo_salida,

                COALESCE(p.nombre, f.nombre) AS beneficiario_nombre,
                CASE
                    WHEN s.id_parroquia IS NOT NULL THEN 'Parroquia'
                    WHEN s.id_fundaciones IS NOT NULL THEN 'Fundacion'
                    ELSE 'N/A'
                END AS beneficiario_tipo

            FROM salidas s
            LEFT JOIN tipo_salida ts
                ON ts.id_tipo_salida = s.id_tipo_salida
            LEFT JOIN parroquias p
                ON p.id_parroquia = s.id_parroquia
            LEFT JOIN fundacioines f
                ON f.id_fundaciones = s.id_fundaciones
            WHERE 1=1
        """
        params = []

        if estado:
            sql += " AND s.estado = %s"
            params.append(estado)

        if id_tipo_salida:
            sql += " AND s.id_tipo_salida = %s"
            params.append(id_tipo_salida)

        sql += " ORDER BY s.fecha_salida DESC, s.id_salida DESC"

        cursor.execute(sql, params)
        filas = cursor.fetchall() or []

        items = []
        for row in filas:
            total_kg = row.get("total_kg")
            if isinstance(total_kg, Decimal):
                total_kg = float(total_kg)

            beneficiario_nombre = row.get("beneficiario_nombre") or "Sin registro"
            items.append({
                "id_salida": row["id_salida"],
                "fecha_salida": row["fecha_salida"].strftime("%Y-%m-%d") if row.get("fecha_salida") else None,
                "total_kg": total_kg or 0,
                "estado": row.get("estado"),
                "tipo_salida": row.get("tipo_salida") or "-",

                # compatibilidad con tu JS actual
                "parroquia_nombre": beneficiario_nombre,

                # extra opcional (por si luego quieres mostrarlo)
                "beneficiario_tipo": row.get("beneficiario_tipo") or "N/A",
            })

        return jsonify({"success": True, "items": items})

    except Exception as e:
        print("Error en api_lista_salidas:", e)
        return jsonify({"success": False, "message": "Error al obtener la lista de salidas"}), 500

    finally:
        cursor.close()
        conn.close()

# ==============================