from flask import Blueprint, jsonify, request, session
from db import get_db_connection
from utils.bitacora import registrar_bitacora


listar_bp = Blueprint("listar_bp", __name__, url_prefix="/api/donaciones")

# =====================================================
#  LISTAR DONACIONES DE PRODUCTO
# =====================================================
@listar_bp.route("/productos")
def listar_donaciones_producto():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            e.id_entrada AS id,
            COALESCE(d.nombre, 'Sin registro') AS nombre,
            e.fecha_entrada AS fecha,
            t.id_tipo_entrada,
            t.nombre AS tipo
        FROM entradas e
        LEFT JOIN donantes d ON e.id_donante = d.id_donante
        JOIN tipo_entrada t ON e.id_tipo_entrada = t.id_tipo_entrada
        WHERE e.estado = 'Activo'
        ORDER BY e.id_entrada DESC
    """)

    datos = cursor.fetchall()
    try:
        id_usuario = session.get("id_usuario")
        if id_usuario:
            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="DONACIONES",
                accion="CONSULTAR",
                descripcion="Listó donaciones de productos.",
                tabla_afectada="entradas",
                id_registro=None
            )
            conn.commit()
    except Exception as e:
        print("Bitácora (listar_donaciones_producto) error:", e)
    cursor.close()
    conn.close()
    return jsonify(datos)


# =====================================================
#  LISTAR DONACIONES MONETARIAS
# =====================================================
@listar_bp.route("/monetaria")
def listar_donaciones_monetaria():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            dm.id_donacion AS id,
            d.nombre AS donante,
            dm.monto,
            dm.fecha_donacion AS fecha
        FROM donaciones_monetarias dm
        LEFT JOIN donantes d ON dm.id_donante = d.id_donante
        WHERE dm.estado = 'Activo'
        ORDER BY dm.id_donacion DESC
    """)

    datos = cursor.fetchall()
    try:
        id_usuario = session.get("id_usuario")
        if id_usuario:
            registrar_bitacora(
                cursor,
                id_usuario=id_usuario,
                modulo="DONACIONES",
                accion="CONSULTAR",
                descripcion="Listó donaciones monetarias.",
                tabla_afectada="donaciones_monetarias",
                id_registro=None
            )
            conn.commit()
    except Exception as e:
        print("Bitácora (listar_donaciones_monetaria) error:", e)
    cursor.close()
    conn.close()
    return jsonify(datos)


# =====================================================
#  OBTENER UNA DONACIÓN DE PRODUCTO PARA EDITAR
# =====================================================
@listar_bp.route("/producto/<int:id_entrada>")
def obtener_donacion_producto(id_entrada):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Cabecera (sin responsable porque ya NO existe en la tabla)
        cursor.execute("""
            SELECT 
                e.id_entrada,
                e.id_tipo_entrada,
                e.fecha_entrada,
                e.observacion,
                d.id_donante,
                d.nombre AS donante_nombre,
                d.numero_documento AS donante_documento
            FROM entradas e
            LEFT JOIN donantes d ON e.id_donante = d.id_donante
            WHERE e.id_entrada = %s
        """, (id_entrada,))
        cabecera = cursor.fetchone()

        if not cabecera:
            return jsonify({"success": False, "message": "La donación no existe"}), 404

        # Detalles
        cursor.execute("""
            SELECT 
                ed.id_producto,
                p.nombre,
                ed.cantidad,
                ed.peso_unitario,
                ed.id_unidad,
                u.nombre AS unidad,
                ed.id_bodega,
                b.nombre_bodega AS bodega,
                ed.fecha_vencimiento,
                ed.valor_producto,
                p.id_categoria
            FROM entrada_detalles ed
            JOIN productos p ON ed.id_producto = p.id_producto
            LEFT JOIN unidades_medida u ON ed.id_unidad = u.id_unidad
            LEFT JOIN bodegas b ON ed.id_bodega = b.id_bodega
            WHERE ed.id_entrada = %s
        """, (id_entrada,))
        detalles = cursor.fetchall()

        try:
            id_usuario = session.get("id_usuario")
            if id_usuario:
                registrar_bitacora(
                    cursor,
                    id_usuario=id_usuario,
                    modulo="DONACIONES",
                    accion="CONSULTAR",
                    descripcion=f"Consultó donación de producto (entrada) ID {id_entrada} para editar/ver.",
                    tabla_afectada="entradas",
                    id_registro=id_entrada
                )
                conn.commit()
        except Exception as e:
            print("Bitácora (obtener_donacion_producto) error:", e)
            
        return jsonify({
            "success": True,
            "id_entrada": cabecera["id_entrada"],
            "id_tipo_entrada": cabecera["id_tipo_entrada"],
            "fecha_entrada": cabecera["fecha_entrada"].isoformat() if cabecera["fecha_entrada"] else None,
            "observacion": cabecera["observacion"],
            "id_donante": cabecera["id_donante"],
            "donante_documento": cabecera["donante_documento"],
            "donante_nombre": cabecera["donante_nombre"],
            "productos": detalles
        })

    except Exception as e:
        print("ERROR obteniendo donación:", e)
        return jsonify({"success": False, "message": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


@listar_bp.route("/tipos_entrada")
def obtener_tipos_entrada():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id_tipo_entrada, nombre 
        FROM tipo_entrada
        WHERE estado = 'Activo'
        ORDER BY nombre ASC
    """)

    tipos = cursor.fetchall()

    cursor.close()
    conn.close()
    return jsonify(tipos)


@listar_bp.route("/filtrar")
def filtrar_donaciones():
    tipo = request.args.get("tipo")  # viene el id_tipo_entrada o vacío

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT 
            e.id_entrada AS id,
            COALESCE(d.nombre, 'Sin registro') AS nombre,
            e.fecha_entrada AS fecha,
            t.id_tipo_entrada,
            t.nombre AS tipo
        FROM entradas e
        LEFT JOIN donantes d ON e.id_donante = d.id_donante
        JOIN tipo_entrada t ON e.id_tipo_entrada = t.id_tipo_entrada
        WHERE e.estado = 'Activo'
    """

    params = []

    # Si viene un tipo seleccionado, filtramos por ID
    if tipo:
        query += " AND t.id_tipo_entrada = %s"
        params.append(tipo)

    query += " ORDER BY e.id_entrada ASC"

    cursor.execute(query, params)
    datos = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(datos)
