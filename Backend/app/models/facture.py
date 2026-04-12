from sqlalchemy import Column, Integer, String, Date, Numeric, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class Facture(Base):
    __tablename__ = "factures"

    facture_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    numero = Column(String(50), unique=True, nullable=False)
    date_facture = Column(Date, nullable=True)
    client_id = Column(Integer, ForeignKey("dim_client.client_id"), nullable=True)
    chantier_id = Column(Integer, ForeignKey("dim_chantier.chantier_id"), nullable=True)
    total_ht = Column(Numeric(14, 2), nullable=True)
    tva = Column(Numeric(14, 2), nullable=True)
    total_ttc = Column(Numeric(14, 2), nullable=True)
    statut = Column(String(30), default="en_attente")  # en_attente, validee, rejetee
    image_path = Column(String(500), nullable=True)
    extracted_data = Column(Text, nullable=True)  # JSON string des données extraites par Donut

    client = relationship("DimClient", backref="factures")
    chantier = relationship("DimChantier", backref="factures")
