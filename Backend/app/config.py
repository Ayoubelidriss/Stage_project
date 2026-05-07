"""
Configuration de l'application - lecture des variables d'environnement.
Les valeurs par défaut correspondent à un lancement local (hors Docker).
"""
import os
from dotenv import load_dotenv

# Chargement du fichier .env situé dans le répertoire Backend/
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"), override=True)

# ── Base de données ────────────────────────────────────────────────────────
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql+pg8000://postgres:password@localhost:5432/golden_carriere_db",
)

READONLY_DATABASE_URL: str = os.getenv("READONLY_DATABASE_URL", DATABASE_URL)

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
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY") or os.getenv("GROK_API_KEY", "")
GROQ_BASE_URL: str = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Anciennes variables xAI/Grok gardees pour compatibilite.
GROK_API_KEY: str   = os.getenv("GROK_API_KEY", "")
GROK_MODEL: str = os.getenv("GROK_MODEL", "grok-4.3")

# ── Modèle Donut ───────────────────────────────────────────────────────────
DONUT_MODEL_PATH: str = os.getenv("DONUT_MODEL_PATH", "./donut/model")
