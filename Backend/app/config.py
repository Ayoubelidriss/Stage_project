"""
Configuration de l'application - lecture des variables d'environnement.
Les valeurs par défaut correspondent à un lancement local (hors Docker).
"""
import os
from dotenv import load_dotenv

# Chargement du fichier .env situé dans le répertoire Backend/
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

# ── Base de données ────────────────────────────────────────────────────────
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql+pg8000://postgres:password@localhost:5432/golden_carriere_db",
)

# ── Sécurité ───────────────────────────────────────────────────────────────
SECRET_KEY: str = os.getenv(
    "SECRET_KEY",
    "changeme-in-production",
)

# ── CORS ───────────────────────────────────────────────────────────────────
_cors_raw: str = os.getenv("CORS_ORIGINS", "http://localhost:3000")
CORS_ORIGINS: list[str] = [o.strip() for o in _cors_raw.split(",") if o.strip()]

# ── OpenAI / Grok ──────────────────────────────────────────────────────────
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
GROK_API_KEY: str   = os.getenv("GROK_API_KEY", "")

# ── Modèle Donut ───────────────────────────────────────────────────────────
DONUT_MODEL_PATH: str = os.getenv("DONUT_MODEL_PATH", "./donut/model")
