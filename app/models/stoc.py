# app/models/stoc.py
from sqlalchemy import Column, Integer, Float, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from models import Base

class Stoc(Base):
    __tablename__ = 'stoc'
    
    id = Column(Integer, primary_key=True)
    hartie_id = Column(Integer, ForeignKey('hartie.id'), nullable=False)
    cantitate = Column(Float, nullable=False)
    nr_factura = Column(String(50), nullable=False)
    data = Column(Date, nullable=False, default=datetime.now().date)
    
    # Relații
    hartie = relationship("Hartie", back_populates="intrari_stoc")
    
    def __repr__(self):
        return f"<Stoc(id={self.id}, hartie_id={self.hartie_id}, cantitate={self.cantitate})>"