# routes/archivos_monetarias.py
from flask import Blueprint, current_app, send_from_directory
import os

archivos_monetarias_bp = Blueprint(
    'archivos_monetarias_bp',
    __name__,
    url_prefix='/archivos_monetarias'
)

@archivos_monetarias_bp.route('/<path:filename>')
def ver_archivo_monetaria(filename):
    """
    Sirve archivos de donaciones monetarias.
    """
    base_rel = current_app.config.get(
        "UPLOAD_FOLDER_MONETARIAS",
        "uploads/donaciones_monetarias"   # 👈 carpeta donde los estás guardando
    )
    base_abs = os.path.join(current_app.root_path, base_rel)
    return send_from_directory(base_abs, filename)
