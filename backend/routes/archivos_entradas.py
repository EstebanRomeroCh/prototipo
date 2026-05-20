# routes/archivos_entradas.py
from flask import Blueprint, current_app, send_from_directory
import os

archivos_entradas_bp = Blueprint('archivos_entradas_bp', __name__)

@archivos_entradas_bp.route('/archivos_entrada/<path:filename>')
def ver_archivo_entrada(filename):
    """
    Sirve un archivo de la carpeta de entradas.
    filename será el nombre_guardado que guardamos en la BD.
    """
    base_rel = current_app.config.get("UPLOAD_FOLDER_ENTRADAS", "uploads/entradas")
    base_abs = os.path.join(current_app.root_path, base_rel)

    return send_from_directory(base_abs, filename)
# Fin de archivo