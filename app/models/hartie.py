# app/models/hartie.py
from sqlalchemy import Column, Integer, String, Float, Boolean
from sqlalchemy.orm import relationship
from models import Base

class Hartie(Base):
    __tablename__ = 'hartie'
    
    id = Column(Integer, primary_key=True)
    sortiment = Column(String(100), nullable=False)
    dimensiune_1 = Column(Float, nullable=False)  # cm
    dimensiune_2 = Column(Float, nullable=False)  # cm
    gramaj = Column(Float, nullable=False)  # g
    format_hartie = Column(String(50), nullable=False)
    stoc = Column(Float, nullable=False, default=0)
    greutate = Column(Float, nullable=False)  # kg - calculat automat
    
    # Certificare FSC materie primă (Input Product Type)
    fsc_materie_prima = Column(Boolean, nullable=False, default=False)
    cod_fsc_materie_prima = Column(String(50), nullable=True)  # P 2.1, P 2.4.9, etc.
    certificare_fsc_materie_prima = Column(String(50), nullable=True)  # FSC Mix Credit, FSC Recycled, etc.
    furnizor = Column(String(200), nullable=True)  # Furnizor hârtie
    cod_certificare = Column(String(100), nullable=True)  # Cod certificare furnizor
    
    # Relații
    intrari_stoc = relationship("Stoc", back_populates="hartie")
    comenzi = relationship("Comanda", back_populates="hartie")
    
    def __repr__(self):
        return f"<Hartie(id={self.id}, sortiment='{self.sortiment}', gramaj={self.gramaj})>"
    
    def calculeaza_greutate(self):
        """Calculează greutatea totală a hârtiei în stoc"""
        return self.dimensiune_1 * self.dimensiune_2 * self.gramaj * self.stoc / 10**7
