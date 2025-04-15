# app/models/beneficiari.py
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from models import Base

class Beneficiar(Base):
    __tablename__ = 'beneficiari'
    
    id = Column(Integer, primary_key=True)
    nume = Column(String(100), nullable=False)
    persoana_contact = Column(String(100), nullable=False)
    telefon = Column(String(20), nullable=False)
    email = Column(String(100), nullable=False)
    
    # Relații
    comenzi = relationship("Comanda", back_populates="beneficiar")
    
    def __repr__(self):
        return f"<Beneficiar(id={self.id}, nume='{self.nume}')>"