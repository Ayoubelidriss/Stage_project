import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import CORS_ORIGINS
from app.database import engine, Base

# Importer tous les modèles pour que SQLAlchemy les enregistre
import app.models  # noqa: F401

# Importer les routers
from app.routers import factures, livraisons, dashboard, chat
from app.routers import clients, chantiers

# Créer les tables si elles n'existent pas (utile en dev sans Alembic)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Golden Carrière API",
    description="API de gestion des livraisons et factures - Carrière de matériaux",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclure les routers
app.include_router(factures.router)
app.include_router(livraisons.router)
app.include_router(dashboard.router)
app.include_router(chat.router)
app.include_router(clients.router)
app.include_router(chantiers.router)


@app.get("/health", tags=["Health"])
def health_check():
    """Vérifie que l'API et la BD sont opérationnelles."""
    try:
        from sqlalchemy import text
        from app.database import SessionLocal
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return JSONResponse({"status": "ok", "db": db_status})


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Bienvenue sur l'API Golden Carrière",
        "docs": "/docs",
        "health": "/health",
    }
