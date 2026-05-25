# routes/parametros_certificados_api.py

from flask import Blueprint, request, jsonify, session
from db import get_db_connection
from utils.bitacora import registrar_bitacora
from psycopg2.extras import RealDictCursor

parametros_certificados_api_bp = Blueprint(
    "parametros_certificados_api_bp",
    __name__,
    url_prefix="/api/parametros_certificados"
)


# ================================
# 🔹 Helper: convertir fila en dict para el frontend (JS)
# ================================
def row_to_dict(row):
    """
    Mapea las columnas reales de la tabla parametros_certificados
    a las llaves que espera el JS.
    """
    return {
        "id_parametro": row.get("id_parametro"),
        # Para el JS, usamos nombre_organizacion también como "nombre_plantilla"
        "nombre_plantilla": row.get("nombre_organizacion") or "",
        "nombre_organizacion": row.get("nombre_organizacion") or "",
        "nit_organizacion": row.get("nit_organizacion") or "",
        "ciudad": row.get("ciudad") or "",
        "direccion_organizacion": row.get("direccion_organizacion") or "",
        "telefono_organizacion": row.get("telefono_organizacion") or "",
        "texto_cabecera": row.get("texto_encabezado") or "",
        "texto_cuerpo_base": row.get("texto_cuerpo_base") or "",
        "texto_pie": row.get("texto_despedida") or "",
        "lugar_emision": row.get("lugar_emision") or "",
        "nombre_director": row.get("firma_responsable") or "",
        "cargo_director": row.get("cargo_responsable") or "",
        "ruta_logo": row.get("ruta_logo") or "",
        "mostrar_valor_monetario": row.get("mostrar_valor_monetario") or "No",
        # No hay columna estado en la tabla, pero el JS la usa para dibujar badge
        "estado": "Activo"
    }


# ================================
# ✅ LISTAR (con filtro opcional ?q=)
# ================================
@parametros_certificados_api_bp.route("/", methods=["GET"])
def api_listar_parametros():
    if "usuario" not in session:
        return jsonify({"success": False, "message": "Sesión expirada"}), 401

    q = (request.args.get("q") or "").strip()

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        sql = """
            SELECT *
            FROM parametros_certificados
        """
        params = []

        if q:
            sql += """
                WHERE
                    nombre_organizacion LIKE %s
                    OR ciudad LIKE %s
                    OR firma_responsable LIKE %s
            """
            patron = f"%{q}%"
            params = [patron, patron, patron]

        sql += " ORDER BY id_parametro DESC"

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        items = [row_to_dict(r) for r in rows]

        return jsonify({
            "success": True,
            "items": items
        })

    except Exception as e:
        print("Error api_listar_parametros:", e)
        return jsonify({"success": False, "message": "Error al listar parámetros"}), 500
    finally:
        cursor.close()
        conn.close()


# ================================
# ✅ CREAR (POST /api/parametros_certificados/)
# ================================
@parametros_certificados_api_bp.route("/", methods=["POST"])
def api_crear_parametro():
    if "usuario" not in session:
        return jsonify({"success": False, "message": "Sesión expirada"}), 401

    data = request.get_json() or {}

    nombre_organizacion = (data.get("nombre_organizacion") or "").strip()
    ciudad = (data.get("ciudad") or "").strip()

    # Campos opcionales
    nit_organizacion = (data.get("nit_organizacion") or "").strip()
    direccion = (data.get("direccion_organizacion") or "").strip()
    telefono = (data.get("telefono_organizacion") or "").strip()

    texto_cabecera = (data.get("texto_cabecera") or "").strip()
    texto_cuerpo_base = (data.get("texto_cuerpo_base") or "").strip()
    texto_pie = (data.get("texto_pie") or "").strip()
    lugar_emision = (data.get("lugar_emision") or "").strip()

    nombre_director = (data.get("nombre_director") or "").strip()
    cargo_director = (data.get("cargo_director") or "").strip()
    ruta_logo = (data.get("ruta_logo") or "").strip()
    mostrar_valor_monetario = (data.get("mostrar_valor_monetario") or "No").strip()

    # Validaciones mínimas (ajustables)
    if not nombre_organizacion or not ciudad:
        return jsonify({
            "success": False,
            "message": "Debe diligenciar al menos organización y ciudad."
        }), 400

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute("""
            INSERT INTO parametros_certificados (
                nombre_organizacion,
                nit_organizacion,
                ciudad,
                direccion_organizacion,
                telefono_organizacion,
                texto_encabezado,
                texto_cuerpo_base,
                texto_despedida,
                lugar_emision,
                firma_responsable,
                cargo_responsable,
                ruta_logo,
                mostrar_valor_monetario
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            nombre_organizacion,
            nit_organizacion,
            ciudad,
            direccion,
            telefono,
            texto_cabecera,
            texto_cuerpo_base,
            texto_pie,
            lugar_emision,
            nombre_director,
            cargo_director,
            ruta_logo,
            mostrar_valor_monetario
        ))

        id_parametro = cursor.lastrowid

        # Bitácora
        try:
            id_usuario = session.get("id_usuario")
            if id_usuario:
                registrar_bitacora(
                    cursor,
                    id_usuario=id_usuario,
                    modulo="CERTIFICADOS",
                    accion="CREAR",
                    descripcion=f"CREÓ parámetros de certificados (id {id_parametro}) vía API",
                    tabla_afectada="parametros_certificados",
                    id_registro=id_parametro
                )
        except Exception as e_bit:
            print("Error bitácora (CREAR parámetros_certificados API):", e_bit)

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Parámetro creado correctamente.",
            "id_parametro": id_parametro
        }), 201

    except Exception as e:
        conn.rollback()
        print("Error api_crear_parametro:", e)
        return jsonify({"success": False, "message": "Error al crear el parámetro"}), 500
    finally:
        cursor.close()
        conn.close()


# ================================
# ✅ ACTUALIZAR (PUT /api/parametros_certificados/<id>)
# ================================
@parametros_certificados_api_bp.route("/<int:id_parametro>", methods=["PUT"])
def api_actualizar_parametro(id_parametro):
    if "usuario" not in session:
        return jsonify({"success": False, "message": "Sesión expirada"}), 401

    data = request.get_json() or {}

    nombre_organizacion = (data.get("nombre_organizacion") or "").strip()
    ciudad = (data.get("ciudad") or "").strip()

    nit_organizacion = (data.get("nit_organizacion") or "").strip()
    direccion = (data.get("direccion_organizacion") or "").strip()
    telefono = (data.get("telefono_organizacion") or "").strip()

    texto_cabecera = (data.get("texto_cabecera") or "").strip()
    texto_cuerpo_base = (data.get("texto_cuerpo_base") or "").strip()
    texto_pie = (data.get("texto_pie") or "").strip()
    lugar_emision = (data.get("lugar_emision") or "").strip()

    nombre_director = (data.get("nombre_director") or "").strip()
    cargo_director = (data.get("cargo_director") or "").strip()
    ruta_logo = (data.get("ruta_logo") or "").strip()
    mostrar_valor_monetario = (data.get("mostrar_valor_monetario") or "No").strip()

    if not nombre_organizacion or not ciudad:
        return jsonify({
            "success": False,
            "message": "Debe diligenciar al menos organización y ciudad."
        }), 400

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Verificar que exista
        cursor.execute("""
            SELECT id_parametro FROM parametros_certificados
            WHERE id_parametro = %s
        """, (id_parametro,))
        row = cursor.fetchone()
        if not row:
            return jsonify({
                "success": False,
                "message": "El parámetro no existe."
            }), 404

        cursor.execute("""
            UPDATE parametros_certificados
            SET nombre_organizacion   = %s,
                nit_organizacion      = %s,
                ciudad                = %s,
                direccion_organizacion= %s,
                telefono_organizacion = %s,
                texto_encabezado      = %s,
                texto_cuerpo_base     = %s,
                texto_despedida       = %s,
                lugar_emision         = %s,
                firma_responsable     = %s,
                cargo_responsable     = %s,
                ruta_logo             = %s,
                mostrar_valor_monetario = %s
            WHERE id_parametro = %s
        """, (
            nombre_organizacion,
            nit_organizacion,
            ciudad,
            direccion,
            telefono,
            texto_cabecera,
            texto_cuerpo_base,
            texto_pie,
            lugar_emision,
            nombre_director,
            cargo_director,
            ruta_logo,
            mostrar_valor_monetario,
            id_parametro
        ))

        # Bitácora
        try:
            id_usuario = session.get("id_usuario")
            if id_usuario:
                registrar_bitacora(
                    cursor,
                    id_usuario=id_usuario,
                    modulo="CERTIFICADOS",
                    accion="ACTUALIZAR",
                    descripcion=f"ACTUALIZÓ parámetros de certificados (id {id_parametro}) vía API",
                    tabla_afectada="parametros_certificados",
                    id_registro=id_parametro
                )
        except Exception as e_bit:
            print("Error bitácora (ACTUALIZAR parámetros_certificados API):", e_bit)

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Parámetro actualizado correctamente."
        })

    except Exception as e:
        conn.rollback()
        print("Error api_actualizar_parametro:", e)
        return jsonify({"success": False, "message": "Error al actualizar el parámetro"}), 500
    finally:
        cursor.close()
        conn.close()


# ================================
# ✅ ELIMINAR (DELETE /api/parametros_certificados/<id>)
# ================================
@parametros_certificados_api_bp.route("/<int:id_parametro>", methods=["DELETE"])
def api_eliminar_parametro(id_parametro):
    if "usuario" not in session:
        return jsonify({"success": False, "message": "Sesión expirada"}), 401

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute("""
            SELECT id_parametro
            FROM parametros_certificados
            WHERE id_parametro = %s
        """, (id_parametro,))
        row = cursor.fetchone()

        if not row:
            return jsonify({
                "success": False,
                "message": "El parámetro no existe."
            }), 404

        cursor.execute("""
            DELETE FROM parametros_certificados
            WHERE id_parametro = %s
        """, (id_parametro,))

        # Bitácora
        try:
            id_usuario = session.get("id_usuario")
            if id_usuario:
                registrar_bitacora(
                    cursor,
                    id_usuario=id_usuario,
                    modulo="CERTIFICADOS",
                    accion="ELIMINAR",
                    descripcion=f"ELIMINÓ parámetros de certificados (id {id_parametro}) vía API",
                    tabla_afectada="parametros_certificados",
                    id_registro=id_parametro
                )
        except Exception as e_bit:
            print("Error bitácora (ELIMINAR parámetros_certificados API):", e_bit)

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Parámetro eliminado correctamente."
        })

    except Exception as e:
        conn.rollback()
        print("Error api_eliminar_parametro:", e)
        return jsonify({"success": False, "message": "Error al eliminar el parámetro"}), 500
    finally:
        cursor.close()
        conn.close()
