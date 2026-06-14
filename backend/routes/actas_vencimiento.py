# routes/actas_vencimiento.py

from flask import Blueprint, jsonify, request, session, render_template, redirect, url_for
from database import get_db_connection
import pymysql
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from pymysql.err import IntegrityError
from utils.bitacora import registrar_bitacora
from psycopg2.extras import RealDictCursor


actas_vencimiento_bp = Blueprint(
    "actas_vencimiento_bp",
    __name__,
    url_prefix="/actas-vencimiento"
)

# =========================
# Helpers
# =========================
def decimal_or_zero(value):
    try:
        return Decimal(str(value or 0))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal("0")

def parse_date_yyyy_mm_dd(fecha_str):
    """
    Recibe 'YYYY-MM-DD' y retorna date.
    Si viene vacío -> hoy.
    """
    if not fecha_str:
        return date.today()
    try:
        return datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Formato de fecha_acta inválido. Use YYYY-MM-DD.")

def require_session():
    if "usuario" not in session:
        return False
    return True

# =========================
# Vistas HTML (opcionales)
# =========================
@actas_vencimiento_bp.route("/lista", methods=["GET"])
def vista_lista_actas():
    if not require_session():
        return redirect(url_for("rutas_dp.index"))
    return render_template("actas_vencimiento_lista.html", usuario=session.get("usuario"))

@actas_vencimiento_bp.route("/nueva/<int:id_salida>", methods=["GET"])
def vista_nueva_acta(id_salida):
    if not require_session():
        return redirect(url_for("rutas_dp.index"))
    return render_template("acta_vencimiento_nueva.html", usuario=session.get("usuario"), id_salida=id_salida)

@actas_vencimiento_bp.route("/ver/<int:id_acta>", methods=["GET"])
def vista_ver_acta(id_acta):
    if not require_session():
        return redirect(url_for("rutas_dp.index"))
    return render_template("acta_vencimiento_ver.html", usuario=session.get("usuario"), id_acta=id_acta)

# =========================
# API: listar salidas elegibles (Baja por vencimiento sin acta)
# =========================
@actas_vencimiento_bp.route("/api/salidas-elegibles", methods=["GET"])
def api_salidas_elegibles():
    """
    Devuelve salidas:
      - tipo_salida.nombre = 'Baja por vencimiento'
      - s.estado = 'Activo'
      - NO existe acta_vencimiento para esa salida (1 a 1)
    """
    if not require_session():
        return jsonify({"success": False, "message": "Sesión expirada"}), 401

    q = (request.args.get("q") or "").strip()  # por si quieres filtrar por ID o texto
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        sql = """
            SELECT
                s.id_salida,
                s.fecha_salida,
                s.observacion,
                s.total_peso_kg,
                ts.nombre AS tipo_salida
            FROM salidas s
            JOIN tipo_salida ts ON ts.id_tipo_salida = s.id_tipo_salida
            LEFT JOIN actas_vencimiento av ON av.id_salida = s.id_salida
            WHERE ts.nombre = 'Baja por vencimiento'
              AND s.estado = 'Activo'
              AND av.id_acta IS NULL
        """
        params = []

        if q:
            # filtro flexible: por id_salida o por observación
            sql += " AND (CAST(s.id_salida AS CHAR) LIKE %s OR s.observacion LIKE %s)"
            params.extend([f"%{q}%", f"%{q}%"])

        sql += " ORDER BY s.fecha_salida DESC, s.id_salida DESC"

        cursor.execute(sql, params)
        rows = cursor.fetchall() or []

        items = []
        for r in rows:
            total_kg = r.get("total_peso_kg")
            if isinstance(total_kg, Decimal):
                total_kg = float(total_kg)

            items.append({
                "id_salida": r["id_salida"],
                "fecha_salida": r["fecha_salida"].strftime("%Y-%m-%d") if r.get("fecha_salida") else None,
                "observacion": r.get("observacion") or "",
                "total_peso_kg": total_kg or 0,
                "tipo_salida": r.get("tipo_salida") or ""
            })

        return jsonify({"success": True, "items": items})

    except Exception as e:
        print("Error api_salidas_elegibles:", e)
        return jsonify({"success": False, "message": "Error al cargar salidas elegibles"}), 500
    finally:
        cursor.close()
        conn.close()

# =========================
# API: detalle de una salida (cabecera + detalle)
# =========================
@actas_vencimiento_bp.route("/api/salida/<int:id_salida>", methods=["GET"])
def api_detalle_salida_para_acta(id_salida):
    if not require_session():
        return jsonify({"success": False, "message": "Sesión expirada"}), 401

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Cabecera salida + validar que sea baja por vencimiento
        cursor.execute("""
            SELECT
                s.id_salida,
                s.fecha_salida,
                s.observacion,
                s.total_peso_kg,
                s.estado,
                ts.nombre AS tipo_salida
            FROM salidas s
            JOIN tipo_salida ts ON ts.id_tipo_salida = s.id_tipo_salida
            WHERE s.id_salida = %s
            LIMIT 1
        """, (id_salida,))
        salida = cursor.fetchone()

        if not salida:
            return jsonify({"success": False, "message": "La salida no existe"}), 404

        if salida.get("tipo_salida") != "Baja por vencimiento":
            return jsonify({"success": False, "message": "Esta salida no es 'Baja por vencimiento'."}), 400

        if salida.get("estado") != "Activo":
            return jsonify({"success": False, "message": "La salida está anulada o inactiva."}), 400

        # Verificar que NO tenga acta ya
        cursor.execute("SELECT id_acta FROM actas_vencimiento WHERE id_salida=%s LIMIT 1", (id_salida,))
        ya = cursor.fetchone()
        if ya:
            return jsonify({"success": False, "message": "Esta salida ya tiene un acta creada.", "id_acta": ya["id_acta"]}), 409

        # Detalles de salida
        cursor.execute("""
            SELECT
                sd.id_detalle_salida,
                sd.cantidad_kg,
                sd.fecha_vencimiento,
                sd.bodega_texto,
                p.id_producto,
                p.nombre AS producto,
                c.nombre AS categoria,
                b.id_bodega,
                b.nombre_bodega AS bodega
            FROM salida_detalles sd
            JOIN productos p   ON p.id_producto = sd.id_producto
            JOIN categorias c  ON c.id_categoria = sd.id_categoria
            JOIN bodegas b     ON b.id_bodega = sd.id_bodega
            WHERE sd.id_salida = %s
            ORDER BY sd.fecha_vencimiento ASC, p.nombre ASC
        """, (id_salida,))
        detalles = cursor.fetchall() or []

        # Normalizar
        total_kg = salida.get("total_peso_kg")
        if isinstance(total_kg, Decimal):
            total_kg = float(total_kg)

        salida_out = {
            "id_salida": salida["id_salida"],
            "fecha_salida": salida["fecha_salida"].strftime("%Y-%m-%d") if salida.get("fecha_salida") else None,
            "observacion": salida.get("observacion") or "",
            "total_peso_kg": total_kg or 0,
            "tipo_salida": salida.get("tipo_salida") or ""
        }

        det_out = []
        for d in detalles:
            cant = d.get("cantidad_kg")
            if isinstance(cant, Decimal):
                cant = float(cant)

            det_out.append({
                "id_detalle_salida": d["id_detalle_salida"],
                "id_producto": d["id_producto"],
                "producto": d.get("producto") or "",
                "categoria": d.get("categoria") or "",
                "id_bodega": d.get("id_bodega"),
                "bodega": d.get("bodega") or "",
                "bodega_texto": d.get("bodega_texto") or "",
                "fecha_vencimiento": d["fecha_vencimiento"].strftime("%Y-%m-%d") if d.get("fecha_vencimiento") else None,
                "cantidad_kg": cant or 0
            })

        return jsonify({"success": True, "salida": salida_out, "detalles": det_out})

    except Exception as e:
        print("Error api_detalle_salida_para_acta:", e)
        return jsonify({"success": False, "message": "Error al consultar la salida"}), 500
    finally:
        cursor.close()
        conn.close()

# =========================
# API: crear acta (1 a 1 con salida) + copiar detalles
# =========================
@actas_vencimiento_bp.route("/api/crear", methods=["POST"])
def api_crear_acta():
    """
    JSON esperado:
    {
      "id_salida": 5,
      "fecha_acta": "2025-12-13" (opcional),
      "motivo": "Texto libre..."
    }
    """
    if not require_session():
        return jsonify({"success": False, "message": "Sesión expirada"}), 401

    data = request.get_json(silent=True) or {}
    id_salida = data.get("id_salida")
    fecha_acta_str = data.get("fecha_acta")
    motivo = (data.get("motivo") or "").strip()

    if not id_salida:
        return jsonify({"success": False, "message": "id_salida es obligatorio."}), 400

    if not motivo or len(motivo) < 5:
        return jsonify({"success": False, "message": "El motivo es obligatorio (mínimo 5 caracteres)."}), 400

    try:
        fecha_acta = parse_date_yyyy_mm_dd(fecha_acta_str)
    except ValueError as ve:
        return jsonify({"success": False, "message": str(ve)}), 400

    id_usuario = session.get("id_usuario")
    creado_por = session.get("usuario") or session.get("nombre_completo") or "Usuario"

    if not id_usuario:
        return jsonify({"success": False, "message": "No se encontró id_usuario en sesión."}), 401

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    

    try:
        conn.autocommit(False)

        # 1) Validar salida: existe, activa, baja por vencimiento
        cursor.execute("""
            SELECT
                s.id_salida,
                s.estado,
                ts.nombre AS tipo_salida
            FROM salidas s
            JOIN tipo_salida ts ON ts.id_tipo_salida = s.id_tipo_salida
            WHERE s.id_salida=%s
            LIMIT 1
        """, (id_salida,))
        srow = cursor.fetchone()

        if not srow:
            raise ValueError("La salida no existe.")
        if srow.get("estado") != "Activo":
            raise ValueError("No se puede crear acta: la salida está anulada/inactiva.")
        if srow.get("tipo_salida") != "Baja por vencimiento":
            raise ValueError("Solo se permite crear acta para salidas 'Baja por vencimiento'.")

        # 2) Validar que no exista acta ya (1 a 1)
        cursor.execute("SELECT id_acta FROM actas_vencimiento WHERE id_salida=%s LIMIT 1", (id_salida,))
        if cursor.fetchone():
            raise ValueError("Ya existe un acta para esta salida.")

        # 3) Crear cabecera acta
        cursor.execute("""
    INSERT INTO actas_vencimiento
        (id_salida, fecha_acta, motivo, creado_por, id_usuario_creador, estado)
    VALUES
        (%s, %s, %s, %s, %s, 'Activo')
        """, (id_salida, fecha_acta, motivo, creado_por, id_usuario))
        id_acta = cursor.lastrowid

        # 4) Copiar detalles desde salida_detalles -> acta_vencimiento_detalles
        #    (snapshot para impresión y auditoría)
        cursor.execute("""
                    
            INSERT INTO acta_vencimiento_detalles
                (id_acta, id_detalle_salida, id_producto, nombre_producto, fecha_vencimiento, cantidad_kg,
                 id_bodega, nombre_bodega, bodega_texto)
            SELECT
                %s AS id_acta,
                sd.id_detalle_salida,
                p.id_producto,
                p.nombre AS nombre_producto,
                sd.fecha_vencimiento,
                sd.cantidad_kg,
                b.id_bodega,
                b.nombre_bodega,
                sd.bodega_texto
            FROM salida_detalles sd
            JOIN productos p ON p.id_producto = sd.id_producto
            JOIN bodegas b   ON b.id_bodega   = sd.id_bodega
            WHERE sd.id_salida = %s
        """, (id_acta, id_salida))

        # Si por algún motivo la salida no tenía detalles
        if cursor.rowcount == 0:
            raise ValueError("La salida no tiene detalles. No se puede crear acta.")
        try:
                    registrar_bitacora(
                        cursor,
                        id_usuario,
                        "ACTAS_VENCIMIENTO",
                        "CREAR",
                        f"Creó acta #{id_acta} para salida #{id_salida}",
                        "actas_vencimiento",
                        id_acta
                    )
        except Exception as e:
            print("Bitácora (no bloqueante):", e)
        conn.commit()
        return jsonify({"success": True, "message": "Acta creada correctamente.", "id_acta": id_acta})

    except IntegrityError as ie:
        conn.rollback()
        print("IntegrityError api_crear_acta:", ie)
        # Por UNIQUE(id_salida) normalmente.
        return jsonify({"success": False, "message": "Ya existe un acta para esa salida (restricción 1 a 1)."}), 409

    except ValueError as ve:
        conn.rollback()
        return jsonify({"success": False, "message": str(ve)}), 400

    except Exception as e:
        conn.rollback()
        print("Error api_crear_acta:", e)
        return jsonify({"success": False, "message": "Error al crear el acta."}), 500

    finally:
        try:
            conn.autocommit(True)
        except Exception:
            pass
        cursor.close()
        conn.close()

# =========================
# API: detalle de acta (para ver / imprimir)
# =========================
@actas_vencimiento_bp.route("/api/detalle/<int:id_acta>", methods=["GET"])
def api_detalle_acta(id_acta):
    if not require_session():
        return jsonify({"success": False, "message": "Sesión expirada"}), 401

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute("""
            SELECT
                av.id_acta,
                av.id_salida,
                av.fecha_acta,
                av.motivo,
                av.estado,
                av.fecha_registro,
                u.id_usuario,
                u.nombre_completo AS creado_por
            FROM actas_vencimiento av
            JOIN usuarios u ON u.id_usuario = av.id_usuario_creador
            WHERE av.id_acta = %s
            LIMIT 1
        """, (id_acta,))
        acta = cursor.fetchone()

        if not acta:
            return jsonify({"success": False, "message": "El acta no existe"}), 404

        cursor.execute("""
            SELECT
                d.id_detalle_acta,
                d.id_detalle_salida,
                d.id_producto,
                d.nombre_producto,
                d.fecha_vencimiento,
                d.cantidad_kg,
                d.id_bodega,
                d.nombre_bodega,
                d.bodega_texto
            FROM acta_vencimiento_detalles d
            WHERE d.id_acta = %s
            ORDER BY d.fecha_vencimiento ASC, d.nombre_producto ASC
        """, (id_acta,))
        detalles = cursor.fetchall() or []

        # Normalizar decimals / fechas
        acta_out = {
            "id_acta": acta["id_acta"],
            "id_salida": acta["id_salida"],
            "fecha_acta": acta["fecha_acta"].strftime("%Y-%m-%d") if acta.get("fecha_acta") else None,
            "motivo": acta.get("motivo") or "",
            "estado": acta.get("estado") or "",
            "creado_por": acta.get("creado_por") or "",
            "fecha_registro": acta["fecha_registro"].strftime("%Y-%m-%d %H:%M:%S") if acta.get("fecha_registro") else None
        }

        det_out = []
        for d in detalles:
            cant = d.get("cantidad_kg")
            if isinstance(cant, Decimal):
                cant = float(cant)

            det_out.append({
                "id_detalle_acta": d["id_detalle_acta"],
                "id_detalle_salida": d["id_detalle_salida"],
                "id_producto": d["id_producto"],
                "nombre_producto": d.get("nombre_producto") or "",
                "fecha_vencimiento": d["fecha_vencimiento"].strftime("%Y-%m-%d") if d.get("fecha_vencimiento") else None,
                "cantidad_kg": cant or 0,
                "nombre_bodega": d.get("nombre_bodega") or "",
                "bodega_texto": d.get("bodega_texto") or ""
            })

        return jsonify({"success": True, "acta": acta_out, "detalles": det_out})

    except Exception as e:
        print("Error api_detalle_acta:", e)
        return jsonify({"success": False, "message": "Error al obtener detalle del acta"}), 500
    finally:
        cursor.close()
        conn.close()

# =========================
# API: anular acta
# =========================
@actas_vencimiento_bp.route("/api/anular/<int:id_acta>", methods=["POST"])
def api_anular_acta(id_acta):
    if not require_session():
        return jsonify({"success": False, "message": "Sesión expirada"}), 401

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute("SELECT estado FROM actas_vencimiento WHERE id_acta=%s LIMIT 1", (id_acta,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"success": False, "message": "Acta no encontrada"}), 404

        if row.get("estado") == "Anulado":
            return jsonify({"success": True, "message": "El acta ya estaba anulada."})

        cursor.execute("""
            UPDATE actas_vencimiento
            SET estado='Anulado'
            WHERE id_acta=%s
        """, (id_acta,))
        conn.commit()

        return jsonify({"success": True, "message": "Acta anulada correctamente."})

    except Exception as e:
        conn.rollback()
        print("Error api_anular_acta:", e)
        return jsonify({"success": False, "message": "Error al anular el acta"}), 500
    finally:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        conn.close()
