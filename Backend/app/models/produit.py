from sqlalchemy import Column, Integer, String, Numeric
from app.database import Base


class DimProduit(Base):
    __tablename__ = "dim_produit"

    produit_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nom = Column(String(255), nullable=False)
    unite = Column(String(50), nullable=True)
    prix_unitaire = Column(Numeric(12, 2), nullable=True)
    categorie = Column(String(100), nullable=True)
