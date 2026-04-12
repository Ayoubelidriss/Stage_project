import sys, os
sys.stdout.reconfigure(encoding='utf-8')

# Ajouter Backend au path
BACKEND = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Backend")
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)

from dotenv import load_dotenv
load_dotenv(os.path.join(BACKEND, ".env"))

print(f"DATABASE_URL: {os.getenv('DATABASE_URL')}")

try:
    from app.database import engine, Base
    print("Engine cree OK")
    
    # Import all models
    from app.models.client import DimClient
    from app.models.produit import DimProduit
    from app.models.chantier import DimChantier
    from app.models.chauffeur import DimChauffeur
    from app.models.carriere import DimCarriere
    from app.models.temps import DimTemps
    from app.models.livraison import FaitLivraison
    from app.models.facture import Facture
    print("Modeles importes OK")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("create_all execute OK")
    
    # Verify
    from sqlalchemy import text
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='public' ORDER BY table_name"
        ))
        tables = [row[0] for row in result]
        print(f"\nTables ({len(tables)}):")
        for t in tables:
            print(f"  OK  {t}")
        
        if len(tables) == 8:
            print("\nSUCCES: Toutes les 8 tables creees!")
        else:
            print(f"\nATTENTION: {len(tables)}/8 tables trouvees")

except Exception as e:
    import traceback
    print(f"ERREUR: {e}")
    traceback.print_exc()
