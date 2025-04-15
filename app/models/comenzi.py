# app/models/comenzi.py
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from models import Base

class Comanda(Base):
    __tablename__ = 'comenzi'
    
    id = Column(Integer, primary_key=True)
    numar_comanda = Column(Integer, nullable=False, unique=True)
    echipament = Column(String(50), nullable=False, default="Accurio Press C6085")
    data = Column(Date, nullable=False, default=datetime.now().date)
    beneficiar_id = Column(Integer, ForeignKey('beneficiari.id'), nullable=False)
    lucrare = Column(String(200), nullable=False)
    po_client = Column(String(100), nullable=True)
    tiraj = Column(Integer, nullable=False)
    descriere_lucrare = Column(Text, nullable=False)
    latime = Column(Float, nullable=False)  # mm
    inaltime = Column(Float, nullable=False)  # mm
    nr_pagini = Column(Integer, nullable=False, default=2)
    indice_corectie = Column(Float, nullable=False, default=1.0)
    fsc = Column(Boolean, nullable=False, default=False)
    cod_fsc = Column(String(50), nullable=True)
    certificare_fsc = Column(String(50), nullable=True)
    hartie_id = Column(Integer, ForeignKey('hartie.id'), nullable=False)
    coala_tipar = Column(String(50), nullable=False)
    nr_culori = Column(String(10), nullable=False)
    nr_coli = Column(Integer, nullable=True)
    coli_mari = Column(Float, nullable=True)
    greutate = Column(Float, nullable=True)  # g - calculat
    plastifiere = Column(String(50), nullable=True)
    big = Column(Boolean, nullable=False, default=False)
    nr_biguri = Column(Integer, nullable=True)
    laminare = Column(Boolean, nullable=False, default=False)
    format_laminare = Column(String(50), nullable=True)
    numar_laminari = Column(Integer, nullable=True)
    taiere_cutter = Column(Boolean, nullable=False, default=False)
    detalii_finisare = Column(Text, nullable=True)
    detalii_livrare = Column(Text, nullable=True)
    pret = Column(Float, nullable=True)
    facturata = Column(Boolean, nullable=False, default=False)
    
    # Relații
    beneficiar = relationship("Beneficiar", back_populates="comenzi")
    hartie = relationship("Hartie", back_populates="comenzi")
    
    def __repr__(self):
        return f"<Comanda(id={self.id}, numar_comanda={self.numar_comanda}, lucrare='{self.lucrare}')>"
    
    def calculeaza_greutate(self):
        """Calculează greutatea comenzii în grame"""
        return self.tiraj * self.latime * self.inaltime * self.nr_pagini * self.indice_corectie / (2 * 10**6)