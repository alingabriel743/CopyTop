# app/models/comenzi.py
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import math
from models import Base

class Comanda(Base):
    __tablename__ = 'comenzi'
    
    id = Column(Integer, primary_key=True)
    numar_comanda = Column(Integer, nullable=False, unique=True)
    echipament = Column(String(50), nullable=False, default="Accurio Press C6085")
    data = Column(Date, nullable=False, default=datetime.now().date)
    beneficiar_id = Column(Integer, ForeignKey('beneficiari.id'), nullable=False)
    nume_lucrare = Column(String(300), nullable=False)  # Renamed and made longer
    po_client = Column(String(100), nullable=True)
    tiraj = Column(Integer, nullable=False)
    descriere_lucrare = Column(Text, nullable=True)  # Nu mai e obligatoriu
    latime = Column(Float, nullable=False)  # mm
    inaltime = Column(Float, nullable=False)  # mm
    nr_pagini = Column(Integer, nullable=False, default=2)
    indice_corectie = Column(Float, nullable=False, default=1.0)
    
    # Pentru compatibilitate temporară cu codul vechi (va fi șters)
    fsc = Column(Boolean, nullable=True, default=False)  # Permite NULL pentru compatibilitate
    
    # Câmpuri principale
    certificare_fsc_produs = Column(Boolean, nullable=False, default=False)
    cod_fsc_produs = Column(String(50), nullable=True)  # P 7.1, P 7.5, etc.
    tip_certificare_fsc_produs = Column(String(100), nullable=True)  # Notebooks, Business card, etc.
    
    hartie_id = Column(Integer, ForeignKey('hartie.id'), nullable=False)
    coala_tipar = Column(String(50), nullable=False)
    nr_culori = Column(String(10), nullable=False)
    
    # Câmpuri noi pentru calculul colilor
    ex_pe_coala = Column(Integer, nullable=False)  # Exemplare pe coală
    nr_coli_tipar = Column(Integer, nullable=True)  # Calculat: tiraj/ex_pe_coala (rotunjit în sus)
    coli_prisoase = Column(Integer, nullable=False, default=0)  # Coli prisoase
    total_coli = Column(Integer, nullable=True)  # nr_coli_tipar + coli_prisoase
    nr_pagini_pe_coala = Column(Integer, nullable=False, default=2)
    
    coli_mari = Column(Float, nullable=True)  # Pentru compatibilitate cu codul existent
    greutate = Column(Float, nullable=True)  # g - calculat
    plastifiere = Column(String(50), nullable=True)
    big = Column(Boolean, nullable=False, default=False)
    nr_biguri = Column(Integer, nullable=True)
    
    # Opțiuni finisare suplimentare
    capsat = Column(Boolean, nullable=False, default=False)
    colturi_rotunde = Column(Boolean, nullable=False, default=False)
    perfor = Column(Boolean, nullable=False, default=False)
    spiralare = Column(Boolean, nullable=False, default=False)
    stantare = Column(Boolean, nullable=False, default=False)
    lipire = Column(Boolean, nullable=False, default=False)
    codita_wobbler = Column(Boolean, nullable=False, default=False)
    
    laminare = Column(Boolean, nullable=False, default=False)
    format_laminare = Column(String(50), nullable=True)
    numar_laminari = Column(Integer, nullable=True)
    taiere_cutter = Column(Boolean, nullable=False, default=False)
    detalii_finisare = Column(Text, nullable=True)
    detalii_livrare = Column(Text, nullable=True)
    pret = Column(Float, nullable=True)
    facturata = Column(Boolean, nullable=False, default=False)
    nr_factura = Column(String(50), nullable=True)  # Număr factură
    data_facturare = Column(Date, nullable=True)  # Data facturării
    stare = Column(String(20), nullable=False, default="In lucru")  # Stare: "In lucru", "Finalizată", "Facturată"
    
    # Relații
    beneficiar = relationship("Beneficiar", back_populates="comenzi")
    hartie = relationship("Hartie", back_populates="comenzi")
    
    def __init__(self, **kwargs):
        # Sincronizează valorile FSC pentru compatibilitate
        if 'certificare_fsc_produs' in kwargs:
            kwargs['fsc'] = kwargs['certificare_fsc_produs']
        elif 'fsc' not in kwargs:
            kwargs['fsc'] = False
            kwargs['certificare_fsc_produs'] = False
        
        super().__init__(**kwargs)
    
    def __repr__(self):
        return f"<Comanda(id={self.id}, numar_comanda={self.numar_comanda}, nume_lucrare='{self.nume_lucrare}')>"
    
    def calculeaza_nr_coli_tipar(self):
        """Calculează numărul de coli de tipar conform noii formule"""
        if self.nr_pagini_pe_coala and self.nr_pagini_pe_coala > 0:
            # Formula nouă: (tiraj * nr_pagini) / (2 * nr_pagini_pe_coala)
            return math.ceil((self.tiraj * self.nr_pagini) / (2 * self.nr_pagini_pe_coala))
        return 0
    
    def calculeaza_total_coli(self):
        """Calculează totalul colilor (coli tipar + prisoase)"""
        nr_coli = self.calculeaza_nr_coli_tipar()
        return nr_coli + (self.coli_prisoase or 0)
    
    def calculeaza_greutate(self):
        """Calculează greutatea comenzii în grame - formula corectată"""
        if self.hartie and hasattr(self.hartie, 'gramaj'):
            gramaj = self.hartie.gramaj
        else:
            gramaj = 80  # Valoare implicită dacă nu există gramaj
        return self.latime * self.inaltime * self.nr_pagini * self.indice_corectie * gramaj * self.tiraj / (2 * 10**9)
