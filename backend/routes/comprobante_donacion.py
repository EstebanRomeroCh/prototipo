# routes/comprobante_donacion.py
from flask import Blueprint, render_template, session
from db import get_db_connection
from psycopg2.extras import RealDictCursor

comprobante_donacion_bp = Blueprint('comprobante_donacion_bp', __name__, url_prefix='/donaciones')

@comprobante_donacion_bp.route('/comprobante/<int:id_entrada>')
def comprobante_donacion(id_entrada):

    # Verificar sesión
    if 'usuario' not in session:
        return "Sesión expirada. Inicie sesión de nuevo."

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # ✅ Encabezado de la entrada, incluyendo totales
        cursor.execute("""
            SELECT 
                e.id_entrada, 
                e.fecha_entrada, 
                e.observacion,
                e.total_peso_kg,
                e.total_valor,
                t.nombre AS tipo_entrada,
                d.nombre AS donante,
                d.numero_documento
            FROM entradas e
            JOIN tipo_entrada t ON e.id_tipo_entrada = t.id_tipo_entrada
            LEFT JOIN donantes d ON e.id_donante = d.id_donante
            WHERE e.id_entrada = %s
        """, (id_entrada,))
        entrada = cursor.fetchone()


        # ✅ Detalle de productos
                # ✅ Detalle de productos
        cursor.execute("""
            SELECT 
                p.nombre AS producto,
                c.nombre AS categoria,
                b.nombre_bodega AS bodega, 
                ed.bodega_texto AS ubicacion, 
                ed.cantidad,
                ed.peso_unitario,
                ed.peso_total_kg,                      -- 👈 total en kg
                ed.valor_producto,                     -- unitario
                (ed.cantidad * ed.valor_producto) AS valor_total,  -- 👈 total del ítem
                ed.fecha_vencimiento,
                ed.codigo_barras
            FROM entrada_detalles ed
            JOIN productos p ON ed.id_producto = p.id_producto
            JOIN categorias c ON ed.id_categoria = c.id_categoria
            JOIN bodegas b ON ed.id_bodega = b.id_bodega 
            WHERE ed.id_entrada = %s
        """, (id_entrada,))
        detalles = cursor.fetchall()


        # ✅ Anexos asociados a la entrada
        cursor.execute("""
            SELECT 
                nombre_original,
                nombre_guardado,
                ruta_relativa,
                tipo_mime
            FROM entrada_archivos
            WHERE id_entrada = %s
        """, (id_entrada,))
        archivos = cursor.fetchall()

        return render_template(
            "comprobante_donacion.html",
            entrada=entrada,
            detalles=detalles,
            archivos=archivos
        )

    except Exception as e:
        print("Error comprobante:", e)
        return f"Error cargando comprobante: {str(e)}"

    finally:
        cursor.close()
        conn.close()
