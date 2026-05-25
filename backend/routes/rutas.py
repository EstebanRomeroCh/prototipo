from flask import Blueprint, render_template, session, redirect, url_for, jsonify, flash, request, make_response
from functools import wraps
import pymysql
from database import get_db_connection
from psycopg2.extras import RealDictCursor

# ==============================
# 4️ PÁGINA PRINCIPAL (POST LOGIN)
# ==============================
rutas_dp = Blueprint('rutas_dp', __name__)

def _wants_json():
    return (
        request.path.startswith("/api/")
        or request.is_json
        or "application/json" in (request.headers.get("Accept") or "")
    )

def rol_required(*roles_permitidos):
    """Protege una ruta según el rol del usuario.
       - En páginas (HTML): redirige + flash (NO JSON).
       - En API (JSON): retorna JSON con código 401/403.
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            rol = session.get("rol_nombre")

            # No hay sesión/rol
            if not rol:
                if _wants_json():
                    return jsonify({'success': False, 'message': 'Debes iniciar sesión'}), 401
                flash("Debes iniciar sesión.", "warning")
                return redirect(url_for('rutas_dp.index'))

            # No autorizado
            if rol not in roles_permitidos:
                if _wants_json():
                    return jsonify({'success': False, 'message': 'No tienes permisos para acceder a esta página'}), 403
                flash("No tienes permisos para acceder a esta página.", "danger")
                # redirige a una página segura
                return redirect(url_for('rutas_dp.pagina_principal'))

            return f(*args, **kwargs)
        return wrapper
    return decorator


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 1) Debe existir sesión
        if 'usuario' not in session or 'id_usuario' not in session:
            if _wants_json():
                return jsonify({'success': False, 'message': 'Debes iniciar sesión'}), 401
            return redirect(url_for('rutas_dp.index'))

        # 2) Verificar que el usuario siga activo
        conn = get_db_connection()
        if not conn:
            if _wants_json():
                return jsonify({'success': False, 'message': 'Error de conexión a BD'}), 500
            flash("Error al conectar con la base de datos.", "danger")
            return redirect(url_for('rutas_dp.index'))

        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            "SELECT estado FROM usuarios WHERE id_usuario = %s LIMIT 1",
            (session.get("id_usuario"),)
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if not row or row.get("estado") != "Activo":
            session.clear()
            if _wants_json():
                return jsonify({'success': False, 'message': 'Usuario inactivo'}), 403
            return redirect(url_for('rutas_dp.index'))

        # 3) Ejecuta la ruta
        response = make_response(f(*args, **kwargs))

        # 4) Evitar cache
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    return decorated_function


# ==============================
# RUTAS
# ==============================

@rutas_dp.route('/index')
def index():
    return render_template('index.html')


@rutas_dp.route('/pagina_principal')
@login_required
@rol_required('Administrador', 'Asistente', 'Auxiliar de Bodega')
def pagina_principal():
    return render_template('pagina_principal.html', usuario=session['usuario'])


@rutas_dp.route('/menu_central')
@login_required
@rol_required('Administrador', 'Asistente', 'Auxiliar de Bodega')
def menu_central():
    usuario = session["usuario"]
    return render_template('menu_central.html', usuario=usuario)


@rutas_dp.route('/menu_de_parroquias')
@login_required
@rol_required('Administrador', 'Asistente')
def menu_de_parroquias():
    usuario = session["usuario"]
    return render_template('menu_de_parroquias.html', usuario=usuario)

@rutas_dp.route('/crear_organizacion')
@login_required
@rol_required('Administrador', 'Asistente')
def crear_organizacion():
    usuario = session["usuario"]
    return render_template('crear_organizacion.html', usuario=usuario)

@rutas_dp.route('/gestion_parroquia')
@login_required
@rol_required('Administrador', 'Asistente')
def gestion_parroquias():
    usuario = session["usuario"]
    return render_template('gestion_parroquia.html', usuario=usuario)

@rutas_dp.route('/fundaciones')
@login_required
@rol_required('Administrador', 'Asistente')
def fundaciones():
    usuario = session["usuario"]
    return render_template('fundaciones.html', usuario=usuario)


# ========= Productos =========

@rutas_dp.route('/menu_producto')
@login_required
@rol_required('Administrador', 'Asistente')
def menu_producto():
    usuario = session["usuario"]
    return render_template('menu_producto.html', usuario=usuario)

@rutas_dp.route('/categoria')
@login_required
@rol_required('Administrador', 'Asistente')
def categoria():
    usuario = session["usuario"]
    return render_template('categoria.html', usuario=usuario)

@rutas_dp.route('/subcategoria')
@login_required
@rol_required('Administrador', 'Asistente')
def subcategoria():
    usuario = session["usuario"]
    return render_template('subcategoria.html', usuario=usuario)

@rutas_dp.route('/producto')
@login_required
@rol_required('Administrador', 'Asistente')
def producto():
    usuario = session["usuario"]
    return render_template('producto.html', usuario=usuario)

@rutas_dp.route('/bodegas')
@login_required
@rol_required('Administrador')
def bodegas():
    usuario = session["usuario"]
    return render_template('bodegas.html', usuario=usuario)

@rutas_dp.route('/unidades_medida')
@login_required
@rol_required('Administrador')
def unidades_medida():
    usuario = session["usuario"]
    return render_template('unidades_medida.html', usuario=usuario)


# ========= Donantes =========

@rutas_dp.route('/menu_donante')
@login_required
@rol_required('Administrador', 'Asistente')
def menu_donante():
    usuario = session["usuario"]
    return render_template('menu_donante.html', usuario=usuario)

@rutas_dp.route('/tipo_donante')
@login_required
@rol_required('Administrador', 'Asistente', 'Auxiliar de Bodega')
def tipo_donante_page():
    usuario = session["usuario"]
    return render_template('tipo_donante.html', usuario=usuario)

@rutas_dp.route('/donante')
@login_required
@rol_required('Administrador', 'Asistente', 'Auxiliar de Bodega')
def donante_page():
    usuario = session["usuario"]
    return render_template('donante.html', usuario=usuario)


@rutas_dp.route('/lista_salidas')
@login_required
@rol_required('Administrador')
def lista_salidas():
    usuario = session["usuario"]
    return render_template('lista_salidas.html', usuario=usuario)

@rutas_dp.route('/lista_donaciones')
@login_required
@rol_required('Administrador')
def lista_donaciones():
    usuario = session["usuario"]
    return render_template('lista_donaciones.html', usuario=usuario)

@rutas_dp.route('/tabla_producto')
@login_required
@rol_required('Administrador', 'Asistente')
def tabla_producto():
    usuario = session["usuario"]
    return render_template('tabla_producto.html', usuario=usuario)

@rutas_dp.route('/movimiento_inv')
@login_required
@rol_required('Administrador', 'Asistente')
def movimiento_inv():
    usuario = session["usuario"]
    return render_template('movimiento_inv.html', usuario=usuario)


# ========= Gastos =========

@rutas_dp.route('/menu_gastos')
@login_required
@rol_required('Administrador', 'Asistente')
def menu_gastos():
    usuario = session["usuario"]
    return render_template('menu_gastos.html', usuario=usuario)


# ========= Reportes / Salidas =========

@rutas_dp.route('/reporte_salidas_listado')
@login_required
@rol_required('Administrador', 'Asistente')
def reporte_salidas_listado():
    usuario = session["usuario"]
    return render_template('reporte_salidas_listado.html', usuario=usuario)

@rutas_dp.route('/reporte_salidas_beneficiarios')
@login_required
@rol_required('Administrador', 'Asistente')
def reporte_salidas_beneficiarios():
    usuario = session["usuario"]
    return render_template('reporte_salidas_beneficiarios.html', usuario=usuario)

@rutas_dp.route('/reporte_categoria_salidas')
@login_required
@rol_required('Administrador', 'Asistente')
def reporte_categoria_salidas():
    usuario = session["usuario"]
    return render_template('reporte_categoria_salidas.html', usuario=usuario)

@rutas_dp.route('/menu_reportes')
@login_required
@rol_required('Administrador', 'Asistente')
def menu_reportes():
    usuario = session["usuario"]
    return render_template('menu_reportes.html', usuario=usuario)

@rutas_dp.route('/reportes')
@login_required
@rol_required('Administrador', 'Asistente')
def reportes():
    usuario = session["usuario"]
    return render_template('reporte_donaciones.html', usuario=usuario)

@rutas_dp.route('/reporte_donantes')
@login_required
@rol_required('Administrador', 'Asistente')
def donaciones_producto():
    usuario = session["usuario"]
    return render_template('reporte_donantes.html', usuario=usuario)

@rutas_dp.route('/reporte_categorias')
@login_required
@rol_required('Administrador', 'Asistente')
def reporte_categorias():
    usuario = session["usuario"]
    return render_template('reporte_categorias.html', usuario=usuario)

@rutas_dp.route('/reporte_generales')
@login_required
@rol_required('Administrador', 'Asistente')
def reporte_generales():
    usuario = session["usuario"]
    return render_template('reporte_general.html', usuario=usuario)

@rutas_dp.route('/reporte_monetarias')
@login_required
@rol_required('Administrador', 'Asistente')
def reporte_monetarias():
    usuario = session["usuario"]
    return render_template('reporte_monetarias.html', usuario=usuario)

@rutas_dp.route('/semaforos')
@login_required
@rol_required('Administrador', 'Asistente')
def semaforos():
    usuario = session["usuario"]
    return render_template('semaforos.html', usuario=usuario)

@rutas_dp.route('/certificacion_donante')
@login_required
@rol_required('Administrador', 'Asistente')
def certificacion_donante():
    usuario = session["usuario"]
    return render_template('certificacion_donante.html', usuario=usuario)

@rutas_dp.route('/parametros_certificados')
@login_required
@rol_required('Administrador', 'Asistente')
def parametros_certificados():
    usuario = session["usuario"]
    return render_template('parametros_certificados_lista.html', usuario=usuario)

@rutas_dp.route('/acta_vencimiento')
@login_required
@rol_required('Administrador', 'Asistente')
def acta_vencimiento():
    usuario = session["usuario"]
    return render_template('acta_vencimiento.html', usuario=usuario)


# ========= Configuración =========

@rutas_dp.route('/pag_confi')
@login_required
@rol_required('Administrador', 'Asistente')
def pag_confi():
    usuario = session["usuario"]
    return render_template('pag_confi.html', usuario=usuario)

@rutas_dp.route('/permisos_asistentes')
@login_required
@rol_required('Administrador')
def permisos_asistentes():
    usuario = session["usuario"]
    return render_template('permisos_asistentes.html', usuario=usuario)

@rutas_dp.route('/comprobante_donacion')
@login_required
@rol_required('Administrador')
def comprobante_donacion():
    usuario = session["usuario"]
    return render_template('comprobante_donacion.html', usuario=usuario)

@rutas_dp.route('/parametros')
@login_required
@rol_required('Administrador')
def parametros():
    usuario = session["usuario"]
    return render_template('parametros.html', usuario=usuario)

@rutas_dp.route('/configuracion')
@login_required
@rol_required('Administrador')
def configuracion():
    usuario = session["usuario"]
    return render_template('configuracion.html', usuario=usuario)


# ========= Manual / Técnico =========

@rutas_dp.route('/menu_manual')
@login_required
@rol_required('Administrador', 'Asistente')
def menu_manual():
    usuario = session["usuario"]
    return render_template('menu_manual.html', usuario=usuario)

@rutas_dp.route('/tecnico')
@login_required
@rol_required('Administrador', 'Asistente')
def tecnico():
    usuario = session["usuario"]
    return render_template('tecnico.html', usuario=usuario)

@rutas_dp.route('/manual_usuario')
@login_required
@rol_required('Administrador', 'Asistente')
def manual_usuario():
    usuario = session["usuario"]
    return render_template('manual_usuario.html', usuario=usuario)

@rutas_dp.route('/instalacion')
@login_required
@rol_required('Administrador', 'Asistente')
def instalacion():
    usuario = session["usuario"]
    return render_template('instalacion.html', usuario=usuario)


# ========= Bitácora =========

@rutas_dp.route('/bitacora')
@login_required
@rol_required('Administrador')
def bitacora():
    usuario = session["usuario"]
    return render_template('bitacora.html', usuario=usuario)


# ==============================
# (OPCIONAL) API verificar rol:
# Si la abres en navegador, ahora REDIRIGE.
# Si la consumes con fetch(), devuelve JSON.
# ==============================
@rutas_dp.route('/api/verificar_rol/<pagina>')
@login_required
def verificar_rol(pagina):
    rol = session.get("rol_nombre")

    permisos = {
        'pagina_principal': ['Administrador', 'Asistente', 'Auxiliar de Bodega'],
        'menu_central': ['Administrador', 'Asistente', 'Auxiliar de Bodega'],

        'menu_de_parroquias': ['Administrador', 'Asistente'],
        'crear_organizacion': ['Administrador', 'Asistente'],
        'gestion_parroquia': ['Administrador', 'Asistente'],
        'fundaciones': ['Administrador', 'Asistente'],

        'menu_producto': ['Administrador', 'Asistente'],
        'categoria': ['Administrador', 'Asistente'],
        'subcategoria': ['Administrador', 'Asistente'],
        'producto': ['Administrador', 'Asistente'],
        'bodegas': ['Administrador'],
        'unidades_medida': ['Administrador'],
        'tabla_producto': ['Administrador', 'Asistente'],
        'movimiento_inv': ['Administrador', 'Asistente'],

        'menu_donante': ['Administrador', 'Asistente'],
        'tipo_donante': ['Administrador', 'Asistente', 'Auxiliar de Bodega'],
        'donante': ['Administrador', 'Asistente', 'Auxiliar de Bodega'],
        'lista_donaciones': ['Administrador'],

        'menu_gastos': ['Administrador', 'Asistente'],

        'menu_reportes': ['Administrador', 'Asistente'],
        'reportes': ['Administrador', 'Asistente'],

        'donaciones_producto': ['Administrador', 'Asistente'],
        'semaforos': ['Administrador', 'Asistente'],
        'certificacion_donante': ['Administrador', 'Asistente'],
        'acta_vencimiento': ['Administrador', 'Asistente'],

        'pag_confi': ['Administrador', 'Asistente'],
        'permisos_asistentes': ['Administrador'],
        'parametros': ['Administrador'],
        'configuracion': ['Administrador'],

        'menu_manual': ['Administrador', 'Asistente'],
        'tecnico': ['Administrador', 'Asistente'],
        'manual_usuario': ['Administrador', 'Asistente'],
        'instalacion': ['Administrador', 'Asistente'],

        'index': ['Administrador', 'Asistente', 'Auxiliar de Bodega'],
    }

    roles_permitidos = permisos.get(pagina, [])

    if not rol:
        if _wants_json():
            return jsonify({'success': False, 'message': 'Debes iniciar sesión'}), 401
        flash("Debes iniciar sesión.", "warning")
        return redirect(url_for("rutas_dp.index"))

    if rol not in roles_permitidos:
        if _wants_json():
            return jsonify({'success': False, 'message': 'No tienes permisos para acceder a esta página'}), 403
        flash("No tienes permisos para acceder a esta página.", "danger")
        return redirect(url_for("rutas_dp.pagina_principal"))

    if _wants_json():
        return jsonify({'success': True, 'message': 'Acceso permitido'})

    # Si lo abren desde navegador, no mostrar JSON
    flash("Acceso permitido.", "success")
    return redirect(url_for("rutas_dp.pagina_principal"))
