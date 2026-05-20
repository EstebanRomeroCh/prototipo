from flask import Blueprint, request, jsonify, session
from db import get_db_connection
from utils.bitacora import registrar_bitacora

bodegas_bp = Blueprint('bodegas', __name__)

# LISTAR BODEGAS
@bodegas_bp.route('/api/bodegas', methods=['GET'])
def obtener_bodegas():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id_bodega, nombre_bodega, ubicacion, descripcion FROM bodegas")
    bodegas = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(bodegas)

# LISTAR BODEGAS (para selects)
@bodegas_bp.route('/api/bodegas/listar', methods=['GET'])
def listar_bodegas():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
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
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE bodegas
        SET nombre_bodega = %s, ubicacion = %s, descripcion = %s
        WHERE id_bodega = %s
    """, (data['nombre_bodega'], data['ubicacion'], data['descripcion'], id))
    try:
        id_usuario = session.get("id_usuario")
        if id_usuario:
            registrar_bitacora(
                cursor,
                id_usuario,
                "BODEGAS",
                "EDITAR",
                f"Actualizó bodega #{id}: {data.get('nombre_bodega','')}",
                "bodegas",
                id
            )
    except Exception as e:
        print("Bitácora (no bloqueante):", e)

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Bodega actualizada correctamente"})

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
