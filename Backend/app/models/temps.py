from sqlalchemy import Column, Integer, Date
from app.database import Base


class DimTemps(Base):
    __tablename__ = "dim_temps"

    temps_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    date = Column(Date, unique=True, nullable=False)
    annee = Column(Integer, nullable=False)
    trimestre = Column(Integer, nullable=False)
    mois = Column(Integer, nullable=False)
    semaine = Column(Integer, nullable=False)
    jour = Column(Integer, nullable=False)
