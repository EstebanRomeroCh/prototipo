from flask import Blueprint, render_template, session
from db import get_db_connection

comprobante_monetaria_bp = Blueprint(
    'comprobante_monetaria_bp',
    __name__,
    url_prefix='/donaciones'
)

@comprobante_monetaria_bp.route('/comprobante_monetaria/<int:id_donacion>')
def comprobante_monetaria(id_donacion):

    if 'usuario' not in session:
        return "Sesión expirada. Inicie sesión nuevamente."

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # ============================
        # 1. Cabecera de la donación
        # ============================
        cursor.execute("""
            SELECT 
                dm.id_donacion,
                dm.monto,
                dm.descripcion,
                dm.fecha_donacion,
                m.nombre AS metodo,
                d.nombre AS donante,
                d.numero_documento
            FROM donaciones_monetarias dm
            JOIN metodos_donacion m ON dm.id_metodo = m.id_metodo
            JOIN donantes d         ON dm.id_donante = d.id_donante
            WHERE dm.id_donacion = %s
        """, (id_donacion,))

        detalle = cursor.fetchone()
        if not detalle:
            return "La donación monetaria no existe."

        # ============================
        # 2. Anexos (comprobantes)
        # ============================
        cursor.execute("""
            SELECT 
                nombre_original,
                nombre_guardado,
                ruta_relativa,
                tipo_mime
            FROM donacion_monetaria_archivos
            WHERE id_donacion = %s
        """, (id_donacion,))
        anexos = cursor.fetchall()

        return render_template(
            'comprobante_monetaria.html',
            d=detalle,
            anexos=anexos
        )

    except Exception as e:
        print("Error comprobante monetaria:", e)
        return f"Error: {str(e)}"

    finally:
        cursor.close()
        conn.close()
