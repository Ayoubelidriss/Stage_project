from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import date

from app.database import get_db
from app.models.chantier import DimChantier

router = APIRouter(prefix="/api/chantiers", tags=["Chantiers"])


class ChantierOut(BaseModel):
    chantier_id: int
    nom: str
    client_id: Optional[int] = None
    localisation: Optional[str] = None
    date_debut: Optional[date] = None
    date_fin: Optional[date] = None
    statut: Optional[str] = None

    class Config:
        from_attributes = True


@router.get("/", response_model=List[ChantierOut])
def list_chantiers(skip: int = 0, limit: int = 200, db: Session = Depends(get_db)):
    return db.query(DimChantier).offset(skip).limit(limit).all()


@router.get("/{chantier_id}", response_model=ChantierOut)
def get_chantier(chantier_id: int, db: Session = Depends(get_db)):
    chantier = db.query(DimChantier).filter(DimChantier.chantier_id == chantier_id).first()
    if not chantier:
        raise HTTPException(status_code=404, detail="Chantier non trouvé")
    return chantier
