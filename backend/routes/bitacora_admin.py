# routes/bitacora_admin.py

from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from database import get_db_connection
import pymysql   # 👈 IMPORTANTE para DictCursor

bitacora_bp = Blueprint('bitacora_bp', __name__)

# ---------- VISTA HTML ----------
@bitacora_bp.route('/bitacora', methods=['GET'])
def vista_bitacora():
    if 'usuario' not in session:
        return redirect(url_for('index'))

    # Solo admin (ajusta si quieres permitir otros roles)
    if session.get('rol_nombre') != 'Administrador':
        return redirect(url_for('rutas_dp.menu_central'))

    return render_template(
        "bitacora.html",
        usuario=session.get("usuario"),
        rol_nombre=session.get("rol_nombre")
    )


# ---------- ENDPOINT JSON ----------
@bitacora_bp.route('/bitacora/data', methods=['GET'])
def data_bitacora():
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'Sesión expirada'}), 401

    # Filtros desde query string
    fecha_desde = request.args.get('desde', '').strip()
    fecha_hasta = request.args.get('hasta', '').strip()
    modulo = request.args.get('modulo', '').strip()
    accion = request.args.get('accion', '').strip()

    filtros = []
    params = []

    if fecha_desde:
        filtros.append("b.fecha >= %s")
        params.append(fecha_desde + " 00:00:00")

    if fecha_hasta:
        filtros.append("b.fecha <= %s")
        params.append(fecha_hasta + " 23:59:59")

    if modulo:
        filtros.append("b.modulo = %s")
        params.append(modulo)

    if accion:
        filtros.append("b.accion = %s")
        params.append(accion)

    where_clause = ""
    if filtros:
        where_clause = "WHERE " + " AND ".join(filtros)

    conn = get_db_connection()
    cursor = None

    try:
        # 👇 AQUÍ USAMOS DictCursor DE PYMysql (NADA DE dictionary=True)
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        sql = f"""
            SELECT
                b.id_bitacora,
                b.modulo,
                b.accion,
                b.descripcion,
                b.tabla_afectada,
                b.id_registro,
                b.ip_origen,
                b.fecha,
                u.nombre_completo AS usuario
            FROM bitacora_acciones b
            JOIN usuarios u ON u.id_usuario = b.id_usuario
            {where_clause}
            ORDER BY b.fecha DESC
            LIMIT 200;
        """
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        items = []
        for r in rows:
            items.append({
                "id_bitacora": r["id_bitacora"],
                "usuario": r["usuario"],
                "modulo": r["modulo"],
                "accion": r["accion"],
                "descripcion": r["descripcion"],
                "tabla_afectada": r["tabla_afectada"],
                "id_registro": r["id_registro"],
                "ip_origen": r["ip_origen"],
                "fecha": r["fecha"].strftime('%Y-%m-%d %H:%M:%S') if r["fecha"] else None
            })

        return jsonify({
            "success": True,
            "items": items
        })

    except Exception as e:
        print("Error cargando bitácora:", e)
        return jsonify({"success": False, "message": "Error al cargar bitácora"}), 500

    finally:
        if cursor:
            cursor.close()
        conn.close()
