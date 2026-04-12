from sqlalchemy import Column, Integer, String
from app.database import Base


class DimClient(Base):
    __tablename__ = "dim_client"

    client_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nom = Column(String(255), nullable=False)
    ice = Column(String(50), unique=True, nullable=True)
    ville = Column(String(100), nullable=True)
    telephone = Column(String(30), nullable=True)
    email = Column(String(150), nullable=True)
