from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models.client import DimClient

router = APIRouter(prefix="/api/clients", tags=["Clients"])


class ClientOut(BaseModel):
    client_id: int
    nom: str
    ice: Optional[str] = None
    ville: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[str] = None

    class Config:
        from_attributes = True


@router.get("/", response_model=List[ClientOut])
def list_clients(skip: int = 0, limit: int = 200, db: Session = Depends(get_db)):
    return db.query(DimClient).offset(skip).limit(limit).all()


@router.get("/{client_id}", response_model=ClientOut)
def get_client(client_id: int, db: Session = Depends(get_db)):
    client = db.query(DimClient).filter(DimClient.client_id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    return client
