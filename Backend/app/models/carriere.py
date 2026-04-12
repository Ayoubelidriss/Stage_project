from sqlalchemy import Column, Integer, String
from app.database import Base


class DimCarriere(Base):
    __tablename__ = "dim_carriere"

    carriere_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nom = Column(String(255), nullable=False)
    localisation = Column(String(255), nullable=True)
    type_materiau = Column(String(100), nullable=True)
