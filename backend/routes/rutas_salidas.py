# rutas_salidas.py

from flask import Blueprint, render_template, jsonify, request, session
from db import get_db   # o como tengas tu helper de conexión
from rutas import login_required  # o como tengas tu decorador de login
bp_salidas = Blueprint('rutas_salidas', __name__)

# ==========================
# Vista: Lista de salidas
# ==========================
@bp_salidas.route('/salidas/lista')
@login_required
def lista_salidas():
    """
    Renderiza la página donde se verá la tabla con todas las salidas.
    El llenado de datos lo hará JS consumiendo /salidas/api/lista
    """
    usuario = session.get('usuario')  # o como guardes el nombre
    return render_template('salidas_lista.html', usuario=usuario)


# ==========================
# API: Listado de salidas
# ==========================
@bp_salidas.route('/salidas/api/lista')
@login_required
def api_lista_salidas():
    """
    Devuelve en JSON todas las salidas registradas, con:
    - id_salida
    - tipo de salida
    - fecha_salida
    - parroquia/organización
    - total_kg entregado
    - observación
    """

    conn = get_db()
    cur = conn.cursor(dictionary=True)

    try:
        sql = """
            SELECT
                s.id_salida,
                ts.nombre AS tipo_salida,
                s.fecha_salida,
                s.observacion,
                p.id_parroquia,
                p.nombre      AS parroquia,
                p.encargado   AS encargado,
                p.telefono    AS telefono,
                p.municipio   AS municipio,
                COALESCE(SUM(sd.cantidad_kg), 0) AS total_kg
            FROM salidas s
            JOIN tipo_salida ts
                ON ts.id_tipo_salida = s.id_tipo_salida
            LEFT JOIN parroquias p
                ON p.id_parroquia = s.id_parroquia
            LEFT JOIN salida_detalles sd
                ON sd.id_salida = s.id_salida
            GROUP BY
                s.id_salida,
                ts.nombre,
                s.fecha_salida,
                s.observacion,
                p.id_parroquia,
                p.nombre,
                p.encargado,
                p.telefono,
                p.municipio
            ORDER BY s.fecha_salida DESC, s.id_salida DESC
        """
        cur.execute(sql)
        rows = cur.fetchall()

        return jsonify({
            "success": True,
            "items": rows
        })

    except Exception as e:
        print("Error api_lista_salidas:", e)
        return jsonify({
            "success": False,
            "message": "Error al cargar las salidas."
        }), 500

    finally:
        cur.close()
        # si tu helper no maneja el close, haz conn.close() aquí
