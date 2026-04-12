from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class DimChantier(Base):
    __tablename__ = "dim_chantier"

    chantier_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nom = Column(String(255), nullable=False)
    client_id = Column(Integer, ForeignKey("dim_client.client_id"), nullable=True)
    localisation = Column(String(255), nullable=True)
    date_debut = Column(Date, nullable=True)
    date_fin = Column(Date, nullable=True)
    statut = Column(String(50), default="en_cours")

    client = relationship("DimClient", backref="chantiers")
