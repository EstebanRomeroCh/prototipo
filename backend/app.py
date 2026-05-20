from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash
from flask_cors import CORS
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash
from flasgger import Swagger
import os
import pymysql


# Conexión a la base de datos PyMySQL
from database import get_db_connection

from routes.rutas import rutas_dp
from routes.bitacora_admin import bitacora_bp
from routes.usuarios import usuarios_bp
from routes.tipo_donante import tipo_donante_bp
from routes.donante import donantes_bp
from routes.tipos_organizacion import tipos_organizacion_bp
from routes.parroquias import parroquias_bp
from routes.fundaciones import fundaciones_bp
from routes.categoria import categorias_bp
from routes.subcategoria import subcategorias_bp
from routes.productos import productos_bp
from routes.unidades import unidades_bp
from routes.bodegas import bodegas_bp
from routes.tipo_entrada import tipo_entrada_bp
from routes.registro_donacion import registro_donacion_bp
from routes.comprobante_donacion import comprobante_donacion_bp
from routes.registro_monetaria import registro_monetaria_bp
from routes.metodos_donacion import metodos_bp
from routes.comprobante_monetaria import comprobante_monetaria_bp
from routes.listar_donaciones import listar_bp
from routes.tabla_inventario import tabla_inventario
from routes.notificaciones import notificaciones_bp
from routes.reportes_donaciones import reportes_bp
from routes.archivos_entradas import archivos_entradas_bp
from routes.archivos_monetarias import archivos_monetarias_bp
from routes.parametros_certificados import parametros_certificados_bp
from routes.parametros_certificados_api import parametros_certificados_api_bp
from routes.certificados import certificados_bp
from routes.salidas import salidas_bp
from routes.reportes_salidas_listado import reportes_salidas_listado_bp
from routes.reportes_salidas_beneficiarios import reportes_salidas_benef_bp 
from routes.reportes_cate_salidas import reportes_cat_bp
from routes.actas_vencimiento import actas_vencimiento_bp



from routes.tipo_documento import tipo_documento_bp

# Obtenemos la ruta absoluta de la carpeta "backend"
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
#BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(_file_)))

app = Flask(
    __name__,
      #template_folder=os.path.join(BASE_DIR, 'templates'),
      template_folder=os.path.join(BASE_DIR, 'templates', 'frontend'),
      static_folder=os.path.join(BASE_DIR, 'static')
      )

from decimal import Decimal, InvalidOperation  # puedes poner este import arriba con los otros

# ==============================
#  FILTROS JINJA PARA FORMATEAR
# ==============================
@app.template_filter('format_kg')
def format_kg(value):
    try:
        num = Decimal(str(value or 0))
    except (InvalidOperation, TypeError, ValueError):
        return "0"
    # si es entero, sin decimales
    if num == num.to_integral():
        return str(int(num))
    # si no, hasta 3 decimales, sin ceros sobrantes
    return f"{num:.3f}".rstrip('0').rstrip('.')

@app.template_filter('format_money')
def format_money(value):
    try:
        num = Decimal(str(value or 0))
    except (InvalidOperation, TypeError, ValueError):
        return "0"
    # sin decimales, con separador de miles
    text = f"{num:,.0f}"
    return text.replace(",", ".")   # 265000 -> 265.000

# ==============================
CORS(app)  # Habilitar CORS para todas las rutas
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5000", "http://127.0.0.1:5000"]}})

swagger = Swagger(app)

# ==============================
# REGISTRO DE BLUEPRINTS
# ==============================


app.register_blueprint(rutas_dp)
app.register_blueprint(bitacora_bp)
app.register_blueprint(usuarios_bp, url_prefix='/api/usuarios')
app.register_blueprint(tipo_donante_bp)
app.register_blueprint(donantes_bp, url_prefix='/api/donantes')
app.register_blueprint(tipo_documento_bp, url_prefix='/api/tipo_documento')
app.register_blueprint(tipos_organizacion_bp)
app.register_blueprint(parroquias_bp)
app.register_blueprint(fundaciones_bp)
app.register_blueprint(categorias_bp, url_prefix='/api/categorias')
app.register_blueprint(subcategorias_bp, url_prefix='/api/subcategorias')
app.register_blueprint(productos_bp, url_prefix='/api/productos')
app.register_blueprint(unidades_bp)
app.register_blueprint(bodegas_bp)
app.register_blueprint(tipo_entrada_bp)
app.register_blueprint(registro_donacion_bp)
app.register_blueprint(comprobante_donacion_bp)
app.register_blueprint(registro_monetaria_bp)
app.register_blueprint(metodos_bp)
app.register_blueprint(comprobante_monetaria_bp)
app.register_blueprint(listar_bp)
app.register_blueprint(tabla_inventario, url_prefix='/inventario')
app.register_blueprint(notificaciones_bp)
app.register_blueprint(reportes_bp)
app.register_blueprint(archivos_entradas_bp)
app.register_blueprint(archivos_monetarias_bp)
app.register_blueprint(parametros_certificados_bp)
app.register_blueprint(parametros_certificados_api_bp, url_prefix='/api/parametros_certificados')
app.register_blueprint(certificados_bp)
app.register_blueprint(salidas_bp)
app.register_blueprint(reportes_salidas_listado_bp)
app.register_blueprint(reportes_salidas_benef_bp)
app.register_blueprint(reportes_cat_bp)
app.register_blueprint(actas_vencimiento_bp)
app.config["UPLOAD_FOLDER_MONETARIAS"] = "uploads/monetarias"



@app.route('/static/<path:filename>')
def static_files(filename):
    return app.send_static_file(filename)#para llamar archivos estaticos


#app.secret_key = 'clave-segura'  #  Necesario para manejar sesiones
app.secret_key = os.environ.get("SECRET_KEY", "CAMBIA_ESTA_CLAVE_LARGA_Y_ALEATORIA")

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,  # True cuando uses HTTPS
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=10),
)

app.permanent_session_lifetime = timedelta(minutes=10)  # Duración de la sesión
# ==============================
# 2 RUTA PRINCIPAL - LOGIN
# ==============================
@app.route('/')
def index():
    return render_template('index.html')


# ==============================
# 3 PROCESAR LOGIN
# ==============================

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    if not username or not password:
        return jsonify({'success': False, 'message': 'Usuario y contraseña son requeridos'}), 400

    session.permanent = True

    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'message': 'Error al conectar con la base de datos'}), 500

    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        cursor.execute("""
            SELECT * 
            FROM usuarios 
            WHERE correo = %s
            LIMIT 1
        """, (username,))
        user = cursor.fetchone()

        if not user:
            return jsonify({'success': False, 'message': 'Usuario no registrado '}), 401
        # Validar estado del usuario
        if user.get("estado") != "Activo":
            cursor.close()
            connection.close()
            return jsonify({
                'success': False,
                'message': 'Usuario inactivo. Contacte al administrador.'
            }), 403

        # Bloqueo
        if user.get('bloqueado_hasta') and user['bloqueado_hasta'] > datetime.now():
            tiempo_restante = (user['bloqueado_hasta'] - datetime.now()).seconds // 60
            return jsonify({
                'success': False,
                'message': f'Cuenta bloqueada. Intenta de nuevo en {tiempo_restante} minutos.'
            }), 403

        # Validación de contraseña (hash)
        stored = (user.get("contrasena") or "").strip()

# 1) Intentar como hash (Werkzeug)
        ok = False
        try:
            ok = check_password_hash(stored, password)
        except Exception:
            ok = False

        # 2) Fallback: si NO era hash válido, probar texto plano (tu caso de MySQL)
        if not ok:
            ok = (stored == password)


        if ok:
            cursor.execute("""
                UPDATE usuarios 
                SET intentos_fallidos = 0, bloqueado_hasta = NULL
                WHERE id_usuario = %s
            """, (user['id_usuario'],))
            connection.commit()

            # Guardar sesión
            session['usuario'] = user['nombre_completo']
            session['rol_id'] = user['rol_id']
            session['id_usuario'] = user['id_usuario']

            cursor.execute("SELECT nombre FROM roles WHERE id_rol = %s", (user['rol_id'],))
            rol = cursor.fetchone()
            session['rol_nombre'] = (rol or {}).get('nombre')

            return jsonify({'success': True})

        # Password incorrecta -> subir intentos
        nuevos_intentos = int(user.get('intentos_fallidos') or 0) + 1
        bloqueado_hasta = None

        if nuevos_intentos >= 3:
            bloqueado_hasta = datetime.now() + timedelta(hours=2)
            mensaje = "Cuenta bloqueada por 2 horas debido a múltiples intentos fallidos."
        else:
            mensaje = f"Contraseña incorrecta. Intento {nuevos_intentos}/3."

        cursor.execute("""
            UPDATE usuarios 
            SET intentos_fallidos = %s, bloqueado_hasta = %s 
            WHERE id_usuario = %s
        """, (nuevos_intentos, bloqueado_hasta, user['id_usuario']))
        connection.commit()

        return jsonify({'success': False, 'message': mensaje}), 401

    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            connection.close()
        except Exception:
            pass

# ==============================
# 54 CERRAR SESIÓN
# ==============================
@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada correctamente', 'info')
    return redirect(url_for('index'))

    #app.run(host='127.0.0.1', port=5000, ssl_context='adhoc', debug=True)
#if __name__ == '__main__':
 #   app.run(debug=True)

if __name__ == "__main__":
    print("Flask está iniciando correctamente...")
    app.run(host="0.0.0.0", port=5000, debug=False)


