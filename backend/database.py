import pymysql

def get_db_connection():
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='Es1084734914',
            db='banco_alimentos',
            cursorclass=pymysql.cursors.DictCursor
        )

        print("✅ Conexión exitosa a MySQL")
        return connection

    except Exception as e:
        print("❌ ERROR AL CONECTAR A MYSQL:")
        print(e)
        return None