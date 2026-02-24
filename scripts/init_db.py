import os
from dotenv import load_dotenv
import mysql.connector

# Carga variables del .env de la raíz
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "app_medica")

def run_sql_file(cursor, path):
    with open(path, "r", encoding="utf-8") as f:
        sql_script = f.read()
    # separa por ';' cuidando vacíos
    statements = [s.strip() for s in sql_script.split(";") if s.strip()]
    for stmt in statements:
        cursor.execute(stmt)

def main():
    print("Conectando a MySQL...")
    cnx = mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD, port=DB_PORT
    )
    cur = cnx.cursor()
    cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    cur.execute(f"USE {DB_NAME}")
    print(f"Usando base de datos: {DB_NAME}")

    # Ejecuta tu script SQL
    run_sql_file(cur, "db/init.sql")

    cnx.commit()
    cur.close()
    cnx.close()
    print("✅ Base de datos inicializada.")

if __name__ == "__main__":
    main()
