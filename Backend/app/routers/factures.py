import os
import json
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.facture import Facture
from app.models.client import DimClient
from app.schemas.facture import FactureCreate, FactureOut
from app.services.ocr_service import OCRService

router = APIRouter(prefix="/api/factures", tags=["Factures"])

UPLOAD_DIR = "data/images"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/", response_model=List[FactureOut])
def list_factures(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Facture).offset(skip).limit(limit).all()


@router.get("/{facture_id}", response_model=FactureOut)
def get_facture(facture_id: int, db: Session = Depends(get_db)):
    facture = db.query(Facture).filter(Facture.facture_id == facture_id).first()
    if not facture:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    return facture


@router.post("/", response_model=FactureOut)
def create_facture(facture: FactureCreate, db: Session = Depends(get_db)):
    db_facture = Facture(**facture.model_dump())
    db.add(db_facture)
    db.commit()
    db.refresh(db_facture)
    return db_facture


@router.delete("/{facture_id}")
def delete_facture(facture_id: int, db: Session = Depends(get_db)):
    facture = db.query(Facture).filter(Facture.facture_id == facture_id).first()
    if not facture:
        raise HTTPException(status_code=404, detail="Facture non trouvée")
    db.delete(facture)
    db.commit()
    return {"message": "Facture supprimée"}


@router.post("/upload")
async def upload_facture(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload une image de facture, extrait les données via Donut et sauvegarde en DB."""
    # Sauvegarder le fichier
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Extraire via Donut (OCR)
    ocr = OCRService()
    extracted = ocr.extract(file_path)

    if "error" in extracted:
        return {
            "status": "partial",
            "message": extracted["error"],
            "file_saved": file_path,
            "extracted_data": extracted,
            "saved_to_db": False,
        }

    # Résoudre ou créer le client
    client_id = None
    if extracted.get("client"):
        client = db.query(DimClient).filter(DimClient.nom == extracted["client"]).first()
        if not client:
            client = DimClient(
                nom=extracted["client"],
                ice=extracted.get("ice_client"),
            )
            db.add(client)
            db.commit()
            db.refresh(client)
        client_id = client.client_id

    # Créer la facture
    numero = extracted.get("numero_facture", f"IMPORT-{file.filename}")
    existing = db.query(Facture).filter(Facture.numero == numero).first()
    if existing:
        return {
            "status": "duplicate",
            "message": f"Facture {numero} déjà en base",
            "facture_id": existing.facture_id,
            "saved_to_db": False,
        }

    facture = Facture(
        numero=numero,
        client_id=client_id,
        image_path=file_path,
        extracted_data=json.dumps(extracted, ensure_ascii=False),
        total_ht=_to_float(extracted.get("total_ht")),
        tva=_to_float(extracted.get("tva")),
        total_ttc=_to_float(extracted.get("total_ttc")),
    )
    db.add(facture)
    db.commit()
    db.refresh(facture)

    return {
        "status": "success",
        "extracted_data": extracted,
        "saved_to_db": True,
        "facture_id": facture.facture_id,
    }


def _to_float(value):
    if value is None:
        return None
    try:
        return float(str(value).replace(",", ".").replace(" ", ""))
    except (ValueError, TypeError):
        return None
