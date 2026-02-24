# backend/database.py
# --------------------------------------------
# Conexión a MySQL usando variables del .env
# --------------------------------------------
import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Cargar variables desde .env (en la raíz del proyecto)
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "1234")
DB_NAME = os.getenv("DB_NAME", "app_medica")
DB_PORT = int(os.getenv("DB_PORT", "3306"))

def get_db_connection():
    """
    Retorna una conexión a MySQL o None si falla.
    Usa dictionary=True para obtener dicts en fetchall().
    """
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=DB_PORT
        )
        return conn
    except Error as e:
        print("Error conectando a MySQL:", e)
        return None
        