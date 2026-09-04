from flask import Blueprint, request, jsonify, session
from db import get_db_connection
from utils.bitacora import registrar_bitacora
from psycopg2.extras import RealDictCursor

bodegas_bp = Blueprint('bodegas', __name__)

# LISTAR BODEGAS
@bodegas_bp.route('/api/bodegas', methods=['GET'])
def obtener_bodegas():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT 
            id_bodega,
            nombre_bodega,
            ubicacion,
            capacidad,
            estado
        FROM bodegas
        ORDER BY id_bodega ASC
    """)

    bodegas = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(bodegas)
# LISTAR BODEGAS (para selects)
@bodegas_bp.route('/api/bodegas/listar', methods=['GET'])
def listar_bodegas():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT id_bodega, nombre_bodega FROM bodegas")
    bodegas = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(bodegas)

# CREAR BODEGA
@bodegas_bp.route('/api/bodegas', methods=['POST'])
def crear_bodega():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO bodegas (nombre_bodega, ubicacion, descripcion)
        VALUES (%s, %s, %s)
    """, (data['nombre_bodega'], data['ubicacion'], data['descripcion']))
    try:
            id_usuario = session.get("id_usuario")
            if id_usuario:
                id_bodega = cursor.lastrowid
                registrar_bitacora(
                    cursor,
                    id_usuario,
                    "BODEGAS",
                    "CREAR",
                    f"Creó bodega #{id_bodega}: {data.get('nombre_bodega','')}",
                    "bodegas",
                    id_bodega
                )
    except Exception as e:
            print("Bitácora (no bloqueante):", e)

    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({"message": "Bodega registrada correctamente"}), 201

# ACTUALIZAR BODEGA
@bodegas_bp.route('/api/bodegas/<int:id>', methods=['PUT'])
def actualizar_bodega(id):
    conn = None
    cursor = None

    try:
        data = request.get_json()

        nombre_bodega = data.get('nombre_bodega', '').strip()
        ubicacion = data.get('ubicacion', '').strip()
        capacidad = data.get('capacidad')
        estado = data.get('estado', '').strip()
        
        if not nombre_bodega:
            return jsonify({
                "error": "El nombre de la bodega es obligatorio"
            }), 400

        if capacidad in (None, ""):
            return jsonify({
                "error": "La capacidad es obligatoria"
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE bodegas
            SET
                nombre_bodega = %s,
                ubicacion = %s,
                capacidad = %s,
                estado = %s
            WHERE id_bodega = %s
        """, (
            nombre_bodega,
            ubicacion,
            capacidad,
            estado,
            id
        ))

        # Verificar si realmente existe la bodega
        if cursor.rowcount == 0:
            conn.rollback()

            return jsonify({
                "error": "No se encontró la bodega"
            }), 404

        # Bitácora
        try:
            id_usuario = session.get("id_usuario")

            if id_usuario:
                registrar_bitacora(
                    cursor,
                    id_usuario,
                    "BODEGAS",
                    "EDITAR",
                    f"Actualizó bodega #{id}: {nombre_bodega}",
                    "bodegas",
                    id
                )

        except Exception as e:
            print("⚠️ Bitácora (no bloqueante):", e)

        conn.commit()

        return jsonify({
            "message": "Bodega actualizada correctamente"
        }), 200

    except Exception as e:

        if conn:
            conn.rollback()

        print("❌ ERROR ACTUALIZANDO BODEGA:", e)

        return jsonify({
            "error": "No se pudo actualizar la bodega",
            "detalle": str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()

# ELIMINAR BODEGA
@bodegas_bp.route('/api/bodegas/<int:id>', methods=['DELETE'])
def eliminar_bodega(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM bodegas WHERE id_bodega = %s", (id,))
    try:
        id_usuario = session.get("id_usuario")
        if id_usuario:
            registrar_bitacora(
                cursor,
                id_usuario,
                "BODEGAS",
                "ELIMINAR",
                f"Eliminó bodega #{id}",
                "bodegas",
                id
            )
    except Exception as e:
        print("Bitácora (no bloqueante):", e)
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Bodega eliminada correctamente"})
