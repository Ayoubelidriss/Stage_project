from sqlalchemy import Column, Integer, String
from app.database import Base


class DimChauffeur(Base):
    __tablename__ = "dim_chauffeur"

    chauffeur_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=True)
    cin = Column(String(20), unique=True, nullable=True)
    telephone = Column(String(30), nullable=True)
    statut = Column(String(30), default="actif")
