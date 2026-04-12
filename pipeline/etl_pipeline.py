"""
ETL Pipeline — Script standalone pour importer des fichiers CSV/XLSX
dans la base de données PostgreSQL golden_carriere_db.

Usage:
    python pipeline/etl_pipeline.py
    python pipeline/etl_pipeline.py --dir data/csv
    python pipeline/etl_pipeline.py --file data/csv/livraisons.csv
"""
import os
import sys
import glob
import argparse

# Ajouter le dossier Backend au PYTHONPATH
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(BASE_DIR, "Backend")
sys.path.insert(0, BACKEND_DIR)

import pandas as pd
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(BACKEND_DIR, ".env"))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.database import Base
import app.models  # noqa — enregistrer tous les modèles
from app.services.etl_service import ETLService


def get_session():
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:password@localhost:5432/golden_carriere_db",
    )
    engine = create_engine(database_url, pool_pre_ping=True)
    # Créer les tables si elles n'existent pas
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    return Session(), engine


def verify_connection(engine):
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Connecté à PostgreSQL : {version[:50]}...")
        return True
    except Exception as e:
        print(f"❌ Erreur de connexion PostgreSQL : {e}")
        return False


def verify_tables(engine):
    tables = [
        "dim_client", "dim_produit", "dim_chantier",
        "dim_chauffeur", "dim_carriere", "dim_temps",
        "fait_livraison", "factures",
    ]
    print("\n📋 Vérification des tables :")
    with engine.connect() as conn:
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
            print(f"  {status}  {table}")


def find_files(directory: str) -> list:
    """Cherche tous les fichiers CSV et XLSX dans un dossier."""
    files = []
    for ext in ("*.csv", "*.xlsx", "*.xls"):
        files.extend(glob.glob(os.path.join(directory, ext)))
    return sorted(files)


def run_etl(files: list, db):
    service = ETLService(db)
    total_inserted = 0
    total_errors = 0

    for file_path in files:
        print(f"\n📂 Import : {os.path.basename(file_path)}")
        result = service.import_file(file_path)

        if "error" in result and result.get("inserted", 0) == 0:
            print(f"  ❌ Erreur : {result['error']}")
            total_errors += 1
        else:
            inserted = result.get("inserted", 0)
            errors = result.get("errors", [])
            print(f"  ✅ {inserted} ligne(s) insérée(s)")
            if errors:
                print(f"  ⚠️  {len(errors)} ligne(s) ignorée(s) :")
                for err in errors[:5]:
                    print(f"     - {err}")
                if len(errors) > 5:
                    print(f"     ... et {len(errors)-5} autres")
            total_inserted += inserted
            total_errors += len(errors)

    return total_inserted, total_errors


def print_summary(engine):
    """Affiche le nombre de lignes dans chaque table."""
    tables = [
        "dim_client", "dim_produit", "dim_chantier",
        "dim_chauffeur", "dim_carriere", "dim_temps",
        "fait_livraison", "factures",
    ]
    print("\n📊 Résumé des données chargées :")
    with engine.connect() as conn:
        for table in tables:
            try:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.fetchone()[0]
                print(f"  ✅ {table:<20} : {count:>6} lignes")
            except Exception as e:
                print(f"  ❌ {table:<20} : Erreur — {e}")


def main():
    parser = argparse.ArgumentParser(description="Pipeline ETL Golden Carrière")
    parser.add_argument("--dir", default=None, help="Dossier contenant les fichiers à importer")
    parser.add_argument("--file", default=None, help="Fichier spécifique à importer")
    args = parser.parse_args()

    print("=" * 60)
    print("  🚀 ETL Pipeline — Golden Carrière")
    print("=" * 60)

    # Connexion
    db, engine = get_session()

    if not verify_connection(engine):
        print("\n❌ Impossible de se connecter. Vérifiez DATABASE_URL dans Backend/.env")
        sys.exit(1)

    verify_tables(engine)

    # Déterminer les fichiers à importer
    if args.file:
        files = [args.file]
    elif args.dir:
        files = find_files(args.dir)
    else:
        # Chercher dans data/csv et data/xlsx par défaut
        csv_dir = os.path.join(BASE_DIR, "data", "csv")
        xlsx_dir = os.path.join(BASE_DIR, "data", "xlsx")
        files = []
        if os.path.isdir(csv_dir):
            files.extend(find_files(csv_dir))
        if os.path.isdir(xlsx_dir):
            files.extend(find_files(xlsx_dir))

    if not files:
        print("\n⚠️  Aucun fichier CSV/XLSX trouvé.")
        print("   Placez vos fichiers dans data/csv/ ou data/xlsx/")
        print("   Format attendu des colonnes :")
        print("   date, client, produit, unite, chantier, chauffeur,")
        print("   carriere, quantite, prix_unitaire, montant_ht, tva,")
        print("   montant_ttc, num_bon")
        db.close()
        sys.exit(0)

    print(f"\n📁 {len(files)} fichier(s) trouvé(s) :")
    for f in files:
        print(f"   - {os.path.basename(f)}")

    # Lancer l'ETL
    total_inserted, total_errors = run_etl(files, db)

    # Résumé
    print_summary(engine)

    print("\n" + "=" * 60)
    print(f"  ✅ ETL Pipeline terminé !")
    print(f"     Lignes insérées : {total_inserted}")
    print(f"     Lignes ignorées : {total_errors}")
    print("=" * 60)

    db.close()


if __name__ == "__main__":
    main()
