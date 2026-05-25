# routes/metodos_donacion.py
from flask import Blueprint, jsonify
from db import get_db_connection
from psycopg2.extras import RealDictCursor

metodos_bp = Blueprint('metodos_bp', __name__, url_prefix='/api/metodos_donacion')

@metodos_bp.route('/activos')
def listar_metodos_activos():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT id_metodo, nombre
        FROM metodos_donacion
        WHERE estado = 'Activo'
        ORDER BY nombre
    """)

    metodos = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(metodos)
