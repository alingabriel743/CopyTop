# app/db_init.py
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
from models import create_tables, get_session
from models import Beneficiar, Hartie, Stoc, Comanda

def create_database():
    """Creează baza de date dacă nu există"""
    # Conexiune la serverul PostgreSQL
    print(DB_PASSWORD)
    conn = psycopg2.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    
    # Verifică dacă baza de date există
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (DB_NAME,))
    exists = cursor.fetchone()
    
    if not exists:
        print(f"Creez baza de date {DB_NAME}...")
        cursor.execute(f"CREATE DATABASE {DB_NAME}")
        print(f"Baza de date {DB_NAME} a fost creată cu succes!")
    else:
        print(f"Baza de date {DB_NAME} există deja.")
    
    cursor.close()
    conn.close()

def init_db():
    """Inițializează baza de date și structura tabelelor"""
    create_database()
    create_tables()

if __name__ == "__main__":
    init_db()