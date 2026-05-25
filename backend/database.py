from flask_sqlalchemy import SQLAlchemy
import psycopg2
from psycopg2.extras import RealDictCursor

db = SQLAlchemy()

def get_db_connection():
    try:
        connection = psycopg2.connect(
            host="aws-1-us-west-1.pooler.supabase.com",
            database="postgres",
            user="postgres.bbtannkumnuasujehhre",
            password="Es1084734914",
            port="5432",
            cursor_factory=RealDictCursor
        )

        print("Conectado a Supabase")
        return connection

    except Exception as e:
        print("Error conectando:", e)
        return None