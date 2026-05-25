# ==============================
# TIPO DONANTE CRUD
# ==============================
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session
from db import get_db_connection
from utils.bitacora import registrar_bitacora
import pymysql
from psycopg2.extras import RealDictCursor

tipo_donante_bp = Blueprint(
    'tipo_donante_bp',
    __name__,
    template_folder='../templates/frontend'  # Ajusta según tu estructura
)

# ==============================
# Página HTML + Formulario
# ==============================
@tipo_donante_bp.route('/tipo_donante', methods=['GET', 'POST'])
def tipo_donante_page():
    usuario = session.get("usuario", "Invitado")

    if request.method == 'POST':
        # Tomar datos del formulario
        nombre = request.form.get('nombreTipo')
        descripcion = request.form.get('descripcionTipo', '')

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute(
                "INSERT INTO tipo_donante (nombre, descripcion) VALUES (%s, %s)",
                (nombre, descripcion)
            )
            conn.commit()
            flash("Tipo de donante guardado correctamente.", "success")
        except Exception as e:
            conn.rollback()
            flash(f"Error al guardar: {str(e)}", "danger")
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('tipo_donante_bp.tipo_donante_page'))

    return render_template('tipo_donante.html', usuario=usuario)

# ==============================
# API REST JSON
# ==============================

# Listar todos los tipos de donante
@tipo_donante_bp.route('/api/tipo_donante', methods=['GET'])
def listar_tipo_donante():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM tipo_donante")
    tipos = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(tipos)

# Crear nuevo tipo de donante vía JSON
@tipo_donante_bp.route('/api/tipo_donante', methods=['POST'])
def crear_tipo_donante():
    data = request.get_json()
    nombre = data.get('nombre')
    descripcion = data.get('descripcion', '')

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute(
            "INSERT INTO tipo_donante (nombre, descripcion) VALUES (%s, %s)",
            (nombre, descripcion)
        )
        conn.commit()
        nuevo_id = cursor.lastrowid
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': str(e)}), 400

    cursor.close()
    conn.close()
    return jsonify({'success': True, 'id_tipo': nuevo_id})

# Actualizar tipo de donante vía JSON
@tipo_donante_bp.route('/api/tipo_donante/<int:id_tipo>', methods=['PUT'])
def actualizar_tipo_donante(id_tipo):
    data = request.get_json()
    nombre = data.get('nombre')
    descripcion = data.get('descripcion')
    estado = data.get('estado', 'Activo')

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute(
            "UPDATE tipo_donante SET nombre=%s, descripcion=%s, estado=%s WHERE id_tipo=%s",
            (nombre, descripcion, estado, id_tipo)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': str(e)}), 400

    cursor.close()
    conn.close()
    return jsonify({'success': True})

# Eliminar tipo de donante vía JSON
@tipo_donante_bp.route('/api/tipo_donante/<int:id_tipo>', methods=['DELETE'])
def eliminar_tipo_donante(id_tipo):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("DELETE FROM tipo_donante WHERE id_tipo=%s", (id_tipo,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': 'Tipo de donante eliminado correctamente.'}), 200

    except Exception as e:
        conn.rollback()
        mensaje_error = str(e)

        # Detectar el error 1451 (violación de clave foránea)
        if "1451" in mensaje_error:
            mensaje = "No se puede eliminar este tipo de donante porque tiene donantes asociados."
        else:
            mensaje = "Error al eliminar el tipo de donante."

        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': mensaje}), 400

