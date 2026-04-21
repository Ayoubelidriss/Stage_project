"""
=============================================================================
  SCRIPT DE VÉRIFICATION DES DONNÉES PostgreSQL  |  Golden Carrière
=============================================================================
  Affiche pour chaque table :
    - Si la table existe
    - Le nombre total de lignes
    - Les 5 premières lignes (aperçu)
    - Les colonnes présentes

  Connexion : pg8000 (même driver que le Backend)
  Usage     : python check_data.py
=============================================================================
"""

import sys
sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import create_engine, text, inspect

# ─── CONFIGURATION ───────────────────────────────────────────────────────────
DB_URL = "postgresql+pg8000://postgres:password@localhost:5432/golden_carriere_db"

TABLES = [
    "dim_client",
    "dim_produit",
    "dim_chauffeur",
    "dim_carriere",
    "dim_chantier",
    "dim_temps",
    "factures",
    "fait_livraison",
]

SAMPLE_ROWS = 5   # Nombre de lignes d'aperçu par table
# ─────────────────────────────────────────────────────────────────────────────


def print_sep(char="─", width=70):
    print(char * width)


def print_table_data(conn, table_name):
    """Affiche le nombre de lignes + un aperçu des données d'une table."""
    print_sep()
    print(f"📋  TABLE : {table_name.upper()}")
    print_sep()

    # Nombre de lignes
    try:
        count_res = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        count = count_res.fetchone()[0]
        print(f"   Total de lignes : {count}")
    except Exception as e:
        print(f"   ❌ Erreur lors du comptage : {e}")
        return

    if count == 0:
        print("   ⚠  Table vide.\n")
        return

    # Colonnes
    try:
        col_res = conn.execute(
            text(
                "SELECT column_name, data_type "
                "FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = :t "
                "ORDER BY ordinal_position"
            ),
            {"t": table_name},
        )
        columns = [(r[0], r[1]) for r in col_res]
        col_names = [c[0] for c in columns]
        print(f"   Colonnes        : {', '.join(col_names)}")
    except Exception as e:
        print(f"   ❌ Erreur colonnes : {e}")
        col_names = ["*"]

    # Aperçu des données
    print(f"\n   Aperçu ({SAMPLE_ROWS} premières lignes) :")
    try:
        rows_res = conn.execute(
            text(f"SELECT * FROM {table_name} LIMIT {SAMPLE_ROWS}")
        )
        rows = rows_res.fetchall()
        if rows:
            # Largeur de colonne dynamique
            col_width = max(14, 70 // max(len(col_names), 1))
            header = "   " + " | ".join(str(c).ljust(col_width)[:col_width] for c in col_names)
            print(header)
            print("   " + "-" * (len(header) - 3))
            for r in rows:
                line = "   " + " | ".join(str(v if v is not None else "NULL").ljust(col_width)[:col_width] for v in r)
                print(line)
    except Exception as e:
        print(f"   ❌ Erreur lecture : {e}")
    print()


def main():
    print()
    print_sep("═")
    print("  VÉRIFICATION DES DONNÉES  –  Golden Carrière PostgreSQL")
    print_sep("═")
    print()

    # Connexion
    print(f"🔌  Connexion à : {DB_URL}")
    try:
        engine = create_engine(DB_URL, pool_pre_ping=True)
        conn = engine.connect()
        ver = conn.execute(text("SELECT version()")).fetchone()[0]
        print(f"✅  Connecté → {ver[:65]}...")
    except Exception as e:
        print(f"❌  Connexion échouée : {e}")
        print()
        print("  💡 Solutions :")
        print("     1. Démarrer Docker Desktop puis relancer :")
        print("        docker-compose up -d postgres")
        print("     2. Attendre ~10 secondes que PostgreSQL soit prêt")
        print("     3. Relancer ce script : python check_data.py")
        sys.exit(1)

    print()

    # Vérifier tables existantes
    inspector = inspect(engine)
    existing = inspector.get_table_names(schema="public")
    print("📊  Résumé rapide :")
    total_rows_all = 0
    counts = {}
    for table in TABLES:
        if table in existing:
            try:
                c = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()[0]
            except Exception:
                c = "?"
            counts[table] = c
            marker = "✅"
            if isinstance(c, int):
                total_rows_all += c
        else:
            counts[table] = "MANQUANTE"
            marker = "❌"
        label = str(counts[table]).rjust(8)
        print(f"   {marker}  {table:<22} → {label} lignes")

    print(f"\n   Total général     →  {total_rows_all} lignes dans toutes les tables")
    print()

    # Affichage détaillé par table
    print_sep("═")
    print("  DÉTAIL PAR TABLE")
    print_sep("═")
    print()

    for table in TABLES:
        if table not in existing:
            print_sep()
            print(f"❌  TABLE MANQUANTE : {table}")
            print("   Lancez les migrations Alembic ou create_tables.py")
            print()
        else:
            print_table_data(conn, table)

    conn.close()
    print_sep("═")
    print("  FIN DE LA VÉRIFICATION")
    print_sep("═")
    print()


if __name__ == "__main__":
    main()
