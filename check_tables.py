import sys
sys.stdout.reconfigure(encoding='utf-8')
from sqlalchemy import create_engine, text

URL = "postgresql+pg8000://postgres:password@localhost:5432/golden_carriere_db"
engine = create_engine(URL)

try:
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='public' ORDER BY table_name"
        ))
        tables = [row[0] for row in result]
        print(f"Tables trouvees ({len(tables)}):")
        for t in tables:
            print(f"  OK  {t}")
        
        expected = ["dim_carriere","dim_chauffeur","dim_chantier","dim_client",
                    "dim_produit","dim_temps","factures","fait_livraison"]
        missing = [t for t in expected if t not in tables]
        if missing:
            print(f"\nTables manquantes: {missing}")
        else:
            print("\nToutes les 8 tables sont presentes!")
except Exception as e:
    print(f"ERREUR: {e}")
