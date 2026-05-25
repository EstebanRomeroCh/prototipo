import psycopg2

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host="aws-1-us-west-1.pooler.supabase.com",
            database="postgres",
            user="postgres.bbtannkumnuasujehhre",
            password="Es1084734914",
            port=5432
        )

        print("Conectado a Supabase")
        return conn

    except Exception as e:
        print("Error conexión Supabase:", e)
        return None