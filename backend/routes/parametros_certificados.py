# routes/parametros_certificados.py

from flask import Blueprint, render_template, redirect, url_for, session

parametros_certificados_bp = Blueprint(
    'parametros_certificados_bp',
    __name__,
    url_prefix='/parametros_certificados'
)

@parametros_certificados_bp.route('/', methods=['GET'])
def vista_parametros_certificados():
    if 'usuario' not in session:
        return redirect(url_for('index'))

    return render_template(
        'parametros_certificados.html', 
        usuario=session.get('usuario'),
        rol_nombre=session.get('rol_nombre')
    )
