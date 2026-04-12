from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.chat_service import ChatService

router = APIRouter(prefix="/api/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    question: str


@router.post("/")
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """Répond à une question en langage naturel sur les données de la carrière."""
    service = ChatService(db)
    result = service.answer(request.question)
    return result
