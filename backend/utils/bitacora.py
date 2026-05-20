# utils/bitacora.py
from flask import request

def _get_ip():
    # Si hay proxy / nginx, la IP real viene en X-Forwarded-For
    xff = request.headers.get("X-Forwarded-For", "")
    if xff:
        # el primero suele ser el cliente real
        return xff.split(",")[0].strip()
    return request.remote_addr

def registrar_bitacora(cursor, id_usuario, modulo, accion, descripcion,
                       tabla_afectada=None, id_registro=None):
    """
    Inserta un registro en bitacora_acciones usando el cursor abierto.
    NO hace commit (lo maneja la ruta).
    """
    ip = _get_ip()

    cursor.execute("""
        INSERT INTO bitacora_acciones (
            id_usuario, modulo, accion, descripcion,
            tabla_afectada, id_registro, ip_origen
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (id_usuario, modulo, accion, descripcion, tabla_afectada, id_registro, ip))
    return cursor.lastrowid