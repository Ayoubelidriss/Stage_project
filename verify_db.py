"""
Script de vérification de la connexion PostgreSQL et des tables.
Usage: python verify_db.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Backend"))

from dotenv import load_dotenv
load_dotenv(dotenv_path="Backend/.env")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:admin123@localhost:5432/golden_carriere_db")

try:
    from sqlalchemy import create_engine, text
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        print(f"✅ PostgreSQL connecté : {version[:60]}...")

        tables = [
            "dim_client", "dim_produit", "dim_chantier",
            "dim_chauffeur", "dim_carriere", "dim_temps",
            "fait_livraison", "factures",
        ]

        print("\n📋 Vérification des tables :")
        all_ok = True
        for table in tables:
            result = conn.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    "WHERE table_schema='public' AND table_name=:t"
                ),
                {"t": table},
            )
            count = result.fetchone()[0]
            status = "✅" if count > 0 else "❌ MANQUANTE"
            if count == 0:
                all_ok = False
            print(f"  {status}  {table}")

        if not all_ok:
            print("\n⚠️  Des tables sont manquantes.")
            print("   Exécutez: cd Backend && python -c \"from app.database import engine, Base; import app.models; Base.metadata.create_all(bind=engine); print('Tables créées !')\"")
        else:
            print("\n✅ Toutes les tables sont présentes !")

        # Compter les données
        print("\n📊 Nombre de lignes par table :")
        for table in tables:
            try:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.fetchone()[0]
                print(f"  {table:<22} : {count:>6} lignes")
            except Exception as e:
                print(f"  {table:<22} : Erreur — {e}")

except ImportError as e:
    print(f"❌ Dépendance manquante : {e}")
    print("   Installez avec : pip install sqlalchemy psycopg2-binary python-dotenv")
except Exception as e:
    print(f"❌ Connexion ÉCHOUÉE : {e}")
    print("\nVérifications à faire :")
    print("  1. PostgreSQL est-il démarré ?")
    print("  2. DATABASE_URL dans Backend/.env est-il correct ?")
    print(f"     URL actuelle : {DATABASE_URL}")
    print("  3. La base golden_carriere_db existe-t-elle ?")
    print("     Créez-la : createdb -U postgres golden_carriere_db")
