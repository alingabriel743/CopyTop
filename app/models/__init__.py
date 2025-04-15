# app/models/__init__.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL

# Creare engine pentru conexiunea la baza de date
engine = create_engine(DATABASE_URL)
Base = declarative_base()
Session = sessionmaker(bind=engine)

# Funcție pentru crearea tabelelor în baza de date
def create_tables():
    Base.metadata.create_all(engine)

# Funcție pentru obținerea unei sesiuni de lucru cu baza de date
def get_session():
    return Session()

# Importă modelele pentru a fi disponibile din app.models
from models.beneficiari import Beneficiar
from models.hartie import Hartie
from models.stoc import Stoc
from models.comenzi import Comanda