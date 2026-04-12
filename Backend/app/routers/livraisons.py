from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.livraison import FaitLivraison
from app.schemas.livraison import LivraisonCreate, LivraisonOut

router = APIRouter(prefix="/api/livraisons", tags=["Livraisons"])


@router.get("/", response_model=List[LivraisonOut])
def list_livraisons(skip: int = 0, limit: int = 200, db: Session = Depends(get_db)):
    return db.query(FaitLivraison).offset(skip).limit(limit).all()


@router.get("/{livraison_id}", response_model=LivraisonOut)
def get_livraison(livraison_id: int, db: Session = Depends(get_db)):
    livraison = db.query(FaitLivraison).filter(
        FaitLivraison.livraison_id == livraison_id
    ).first()
    if not livraison:
        raise HTTPException(status_code=404, detail="Livraison non trouvée")
    return livraison


@router.post("/", response_model=LivraisonOut)
def create_livraison(livraison: LivraisonCreate, db: Session = Depends(get_db)):
    db_livraison = FaitLivraison(**livraison.model_dump())
    db.add(db_livraison)
    db.commit()
    db.refresh(db_livraison)
    return db_livraison


@router.delete("/{livraison_id}")
def delete_livraison(livraison_id: int, db: Session = Depends(get_db)):
    livraison = db.query(FaitLivraison).filter(
        FaitLivraison.livraison_id == livraison_id
    ).first()
    if not livraison:
        raise HTTPException(status_code=404, detail="Livraison non trouvée")
    db.delete(livraison)
    db.commit()
    return {"message": "Livraison supprimée"}
