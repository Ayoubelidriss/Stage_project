from pydantic import BaseModel
from typing import Optional
from datetime import date


class LivraisonBase(BaseModel):
    num_bon: Optional[str] = None
    date: date
    client_id: Optional[int] = None
    produit_id: Optional[int] = None
    chantier_id: Optional[int] = None
    chauffeur_id: Optional[int] = None
    carriere_id: Optional[int] = None
    quantite: Optional[float] = None
    prix_unitaire: Optional[float] = None
    montant_ht: Optional[float] = None
    tva: Optional[float] = None
    montant_ttc: Optional[float] = None


class LivraisonCreate(LivraisonBase):
    pass


class LivraisonOut(LivraisonBase):
    livraison_id: int

    class Config:
        from_attributes = True
