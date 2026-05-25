from database import get_db_connection

try:
    conn = get_db_connection()
    print("Conectado correctamente a Supabase")
    conn.close()

except Exception as e:
    print("Error:", e)