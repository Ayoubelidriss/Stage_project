from pydantic import BaseModel
from typing import Optional
from datetime import date


class FactureBase(BaseModel):
    numero: str
    date_facture: Optional[date] = None
    client_id: Optional[int] = None
    chantier_id: Optional[int] = None
    total_ht: Optional[float] = None
    tva: Optional[float] = None
    total_ttc: Optional[float] = None
    statut: Optional[str] = "en_attente"


class FactureCreate(FactureBase):
    pass


class FactureOut(FactureBase):
    facture_id: int
    image_path: Optional[str] = None
    extracted_data: Optional[str] = None

    class Config:
        from_attributes = True
