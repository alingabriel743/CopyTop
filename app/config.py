# app/config.py
import os
from dotenv import load_dotenv

# Încarcă variabilele de mediu din fișierul .env
load_dotenv()

# Configurare conexiune PostgreSQL
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "parola")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "copy_top_db")

# String conexiune pentru SQLAlchemy
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Alte configurări
SECRET_KEY = os.getenv("SECRET_KEY", "cheie_secreta_pentru_aplicatie")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"