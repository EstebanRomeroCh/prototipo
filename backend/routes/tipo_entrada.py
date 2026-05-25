# routes/tipo_entrada.py
from flask import Blueprint, jsonify, session
from db import get_db_connection
from psycopg2.extras import RealDictCursor

tipo_entrada_bp = Blueprint('tipo_entrada_bp', __name__, url_prefix='/api/tipo_entrada')

# ============================
#LISTAR SOLO ACTIVAS
# ============================
@tipo_entrada_bp.route('/activas', methods=['GET'])
def listar_tipos_entrada_activas():
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'Sesión expirada'}), 401

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT id_tipo_entrada, nombre
            FROM tipo_entrada
            WHERE estado = 'Activo'
            ORDER BY nombre
        """)
        tipos = cursor.fetchall()
        return jsonify(tipos)
    except Exception as e:
        print("Error listar_tipos_entrada_activas:", e)
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()
