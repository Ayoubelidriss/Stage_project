"""
=============================================================================
  SCRIPT D'IMPORT EXCEL -> PostgreSQL  |  Golden Carriere
=============================================================================
  Auteur  : Stage_project
  Fichier source : data/dataset_golden_carriere.xlsx (feuille TOUTES_DONNEES)
  Schema cible   : voir Backend/app/models/

  Tables alimentees (dans l'ordre) :
    1. dim_client
    2. dim_produit
    3. dim_chauffeur
    4. dim_carriere
    5. dim_chantier
    6. dim_temps
    7. fait_livraison

  Strategie :
    - Les tables dimensions sont "find-or-create" : on cherche d'abord en memoire
      (cache), ensuite en base, et on insere seulement si absent.
    - fait_livraison : INSERT avec verification de doublon sur
      (num_bon, date, chantier_id) pour eviter les re-imports.
    - Transactions par batch (BATCH_SIZE lignes) pour de bonnes performances.
    - Logs detailles + resume final.
=============================================================================
"""

import sys
import logging
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, date
from decimal import Decimal, InvalidOperation

# Force stdout en UTF-8 (Windows cp1252 par defaut)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ─────────────────────────────────────────────────────────────────────────────
#  CONFIGURATION  <- Adaptez ces variables a votre environnement
# ─────────────────────────────────────────────────────────────────────────────

DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "golden_carriere_db",
    "user":     "postgres",
    "password": "password",
}

EXCEL_PATH   = "data/dataset_golden_carriere.xlsx"
SHEET_NAME   = "TOUTES_DONNEES"   # La feuille principale (toutes les livraisons)
BATCH_SIZE   = 500                 # Nombre de lignes inserees par transaction
TVA_RATE     = 0.20                # Taux de TVA par defaut (20 %)

# ─────────────────────────────────────────────────────────────────────────────
#  LOGGING (ASCII uniquement pour compatibilite Windows cp1252)
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("import_log.txt", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
#  UTILITAIRES
# ─────────────────────────────────────────────────────────────────────────────

def safe_str(val, max_len=None):
    """Convertit une valeur en str propre, None si vide."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    if not s:
        return None
    return s[:max_len] if max_len else s


def safe_decimal(val):
    """Convertit en Decimal, None si impossible."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return Decimal(str(val))
    except InvalidOperation:
        return None


def parse_date(val):
    """Tente plusieurs formats de date, retourne un objet date ou None."""
    if val is None:
        return None
    if isinstance(val, (datetime, date)):
        return val.date() if isinstance(val, datetime) else val
    s = str(val).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%y", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    log.warning("  [!] Date non parsable : '%s'", s)
    return None


def split_fullname(fullname):
    """Retourne (prenom, nom) depuis un nom complet 'Prenom Nom'."""
    parts = fullname.strip().split()
    if len(parts) == 1:
        return None, parts[0]
    return parts[0], " ".join(parts[1:])


# ─────────────────────────────────────────────────────────────────────────────
#  CLASSES GERANT LES DIMENSIONS (find-or-create avec cache local)
# ─────────────────────────────────────────────────────────────────────────────

class DimCache:
    """Cache en memoire pour eviter des SELECT repetes."""

    def __init__(self, conn):
        self.conn = conn
        self.clients    = {}   # nom          -> client_id
        self.produits   = {}   # nom          -> produit_id
        self.chauffeurs = {}   # (nom, prenom) -> chauffeur_id
        self.carrieres  = {}   # nom          -> carriere_id
        self.chantiers  = {}   # code_excel   -> chantier_id
        self.temps      = {}   # date_obj     -> temps_id

    # ── dim_client ────────────────────────────────────────────────────────────
    def get_or_create_client(self, nom_raw, ville_raw):
        nom = safe_str(nom_raw, 255)
        if nom is None:
            return None
        ville = safe_str(ville_raw, 100)
        if nom in self.clients:
            return self.clients[nom]
        cur = self.conn.cursor()
        cur.execute("SELECT client_id FROM dim_client WHERE nom = %s", (nom,))
        row = cur.fetchone()
        if row:
            self.clients[nom] = row[0]
            return row[0]
        cur.execute(
            "INSERT INTO dim_client (nom, ville) VALUES (%s, %s) RETURNING client_id",
            (nom, ville),
        )
        new_id = cur.fetchone()[0]
        self.clients[nom] = new_id
        log.debug("    [+] client '%s' -> id=%s", nom, new_id)
        return new_id

    # ── dim_produit ───────────────────────────────────────────────────────────
    def get_or_create_produit(self, nom_raw, prix_raw):
        nom = safe_str(nom_raw, 255)
        if nom is None:
            return None
        if nom in self.produits:
            return self.produits[nom]
        cur = self.conn.cursor()
        cur.execute("SELECT produit_id FROM dim_produit WHERE nom = %s", (nom,))
        row = cur.fetchone()
        if row:
            self.produits[nom] = row[0]
            return row[0]
        prix = safe_decimal(prix_raw)
        cur.execute(
            "INSERT INTO dim_produit (nom, unite, prix_unitaire) VALUES (%s, %s, %s) RETURNING produit_id",
            (nom, "tonne", prix),
        )
        new_id = cur.fetchone()[0]
        self.produits[nom] = new_id
        log.debug("    [+] produit '%s' -> id=%s", nom, new_id)
        return new_id

    # ── dim_chauffeur ─────────────────────────────────────────────────────────
    def get_or_create_chauffeur(self, fullname_raw):
        fullname = safe_str(fullname_raw, 200)
        if fullname is None:
            return None
        prenom, nom = split_fullname(fullname)
        key = (nom, prenom)
        if key in self.chauffeurs:
            return self.chauffeurs[key]
        cur = self.conn.cursor()
        if prenom:
            cur.execute(
                "SELECT chauffeur_id FROM dim_chauffeur WHERE nom = %s AND prenom = %s",
                (nom, prenom),
            )
        else:
            cur.execute(
                "SELECT chauffeur_id FROM dim_chauffeur WHERE nom = %s AND prenom IS NULL",
                (nom,),
            )
        row = cur.fetchone()
        if row:
            self.chauffeurs[key] = row[0]
            return row[0]
        cur.execute(
            "INSERT INTO dim_chauffeur (nom, prenom, statut) VALUES (%s, %s, %s) RETURNING chauffeur_id",
            (nom, prenom, "actif"),
        )
        new_id = cur.fetchone()[0]
        self.chauffeurs[key] = new_id
        log.debug("    [+] chauffeur '%s %s' -> id=%s", prenom, nom, new_id)
        return new_id

    # ── dim_carriere ──────────────────────────────────────────────────────────
    def get_or_create_carriere(self, nom_raw):
        nom = safe_str(nom_raw, 255)
        if nom is None:
            return None
        if nom in self.carrieres:
            return self.carrieres[nom]
        cur = self.conn.cursor()
        cur.execute("SELECT carriere_id FROM dim_carriere WHERE nom = %s", (nom,))
        row = cur.fetchone()
        if row:
            self.carrieres[nom] = row[0]
            return row[0]
        cur.execute(
            "INSERT INTO dim_carriere (nom) VALUES (%s) RETURNING carriere_id",
            (nom,),
        )
        new_id = cur.fetchone()[0]
        self.carrieres[nom] = new_id
        log.debug("    [+] carriere '%s' -> id=%s", nom, new_id)
        return new_id

    # ── dim_chantier ──────────────────────────────────────────────────────────
    def get_or_create_chantier(self, code_excel, nom_raw, client_id, ville_raw):
        code = safe_str(code_excel, 20)
        nom  = safe_str(nom_raw,   255)
        if code is None and nom is None:
            return None
        lookup_key = code or nom
        if lookup_key in self.chantiers:
            return self.chantiers[lookup_key]
        cur = self.conn.cursor()
        if nom:
            cur.execute("SELECT chantier_id FROM dim_chantier WHERE nom = %s", (nom,))
            row = cur.fetchone()
            if row:
                self.chantiers[lookup_key] = row[0]
                return row[0]
        localisation = safe_str(ville_raw, 255)
        cur.execute(
            """INSERT INTO dim_chantier (nom, client_id, localisation, statut)
               VALUES (%s, %s, %s, %s) RETURNING chantier_id""",
            (nom or code, client_id, localisation, "en_cours"),
        )
        new_id = cur.fetchone()[0]
        self.chantiers[lookup_key] = new_id
        log.debug("    [+] chantier '%s' -> id=%s", nom or code, new_id)
        return new_id

    # ── dim_temps ─────────────────────────────────────────────────────────────
    def get_or_create_temps(self, date_obj):
        if date_obj is None:
            return None
        if date_obj in self.temps:
            return self.temps[date_obj]
        cur = self.conn.cursor()
        cur.execute("SELECT temps_id FROM dim_temps WHERE date = %s", (date_obj,))
        row = cur.fetchone()
        if row:
            self.temps[date_obj] = row[0]
            return row[0]
        dt = datetime(date_obj.year, date_obj.month, date_obj.day)
        trimestre = (date_obj.month - 1) // 3 + 1
        cur.execute(
            """INSERT INTO dim_temps (date, annee, trimestre, mois, semaine, jour)
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING temps_id""",
            (
                date_obj,
                date_obj.year,
                trimestre,
                date_obj.month,
                dt.isocalendar()[1],
                date_obj.day,
            ),
        )
        new_id = cur.fetchone()[0]
        self.temps[date_obj] = new_id
        return new_id


# ─────────────────────────────────────────────────────────────────────────────
#  VERIFICATION DOUBLON fait_livraison
# ─────────────────────────────────────────────────────────────────────────────

def livraison_exists(cur, num_bon, date_obj, chantier_id):
    """Retourne True si une livraison identique existe deja."""
    if num_bon is None:
        return False
    cur.execute(
        """SELECT 1 FROM fait_livraison
           WHERE num_bon = %s AND date = %s AND chantier_id = %s LIMIT 1""",
        (num_bon, date_obj, chantier_id),
    )
    return cur.fetchone() is not None


# ─────────────────────────────────────────────────────────────────────────────
#  LECTURE ET NETTOYAGE DU FICHIER EXCEL
# ─────────────────────────────────────────────────────────────────────────────

def load_excel(path, sheet):
    log.info("[LECTURE] Fichier '%s', feuille '%s' ...", path, sheet)
    df = pd.read_excel(path, sheet_name=sheet, dtype=str)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    before = len(df)
    df.drop_duplicates(inplace=True)
    after = len(df)
    if before != after:
        log.info("  [INFO] %d doublons Excel supprimes avant import.", before - after)
    log.info("  [OK] %d lignes chargees depuis Excel.", after)
    return df


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    start_time = datetime.now()
    log.info("=" * 70)
    log.info("  DEMARRAGE DE L'IMPORT  --  %s", start_time.strftime("%Y-%m-%d %H:%M:%S"))
    log.info("=" * 70)

    # ── 1. Chargement Excel ───────────────────────────────────────────────────
    df = load_excel(EXCEL_PATH, SHEET_NAME)
    total_rows = len(df)

    # Compteurs
    stats = {
        "livraisons_inserees":  0,
        "livraisons_doublons":  0,
        "livraisons_erreurs":   0,
    }

    # ── 2. Connexion PostgreSQL ───────────────────────────────────────────────
    log.info("[DB] Connexion a PostgreSQL (%s:%s/%s) ...",
             DB_CONFIG["host"], DB_CONFIG["port"], DB_CONFIG["dbname"])
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        log.info("  [OK] Connecte.")
    except Exception as exc:
        log.error("  [ERREUR] Impossible de se connecter : %s", exc)
        sys.exit(1)

    cache = DimCache(conn)

    # ── 3. Traitement ligne par ligne en batch ────────────────────────────────
    log.info("[IMPORT] Traitement de %d lignes (batch=%d) ...", total_rows, BATCH_SIZE)

    batch_livraisons = []

    def flush_batch():
        if not batch_livraisons:
            return
        cur = conn.cursor()
        sql = """
            INSERT INTO fait_livraison
              (num_bon, date, client_id, produit_id, chantier_id,
               chauffeur_id, carriere_id, temps_id,
               quantite, prix_unitaire, montant_ht, tva, montant_ttc)
            VALUES %s
        """
        execute_values(cur, sql, batch_livraisons, page_size=BATCH_SIZE)
        conn.commit()
        stats["livraisons_inserees"] += len(batch_livraisons)
        log.info("  [OK] Batch de %d livraisons insere. Total: %d",
                 len(batch_livraisons), stats["livraisons_inserees"])
        batch_livraisons.clear()

    for idx, row in df.iterrows():
        row_num = idx + 2
        try:
            num_bon     = safe_str(row.get("numero_bl"), 50)
            date_obj    = parse_date(row.get("date"))
            code_ch     = safe_str(row.get("chantier_id"), 20)
            nom_ch      = safe_str(row.get("chantier_nom"), 255)
            ville       = safe_str(row.get("ville"), 100)
            nom_client  = safe_str(row.get("client"), 255)
            nom_produit = safe_str(row.get("produit"), 255)
            quantite    = safe_decimal(row.get("quantite_tonnes"))
            prix_u      = safe_decimal(row.get("prix_unitaire_dh"))
            montant_raw = safe_decimal(row.get("montant_total_dh"))
            nom_chauff  = safe_str(row.get("chauffeur"), 200)
            nom_carr    = safe_str(row.get("carriere"), 255)

            if date_obj is None:
                log.warning("  [!] Ligne %d : date invalide, ligne ignoree.", row_num)
                stats["livraisons_erreurs"] += 1
                continue

            client_id    = cache.get_or_create_client(nom_client, ville)
            produit_id   = cache.get_or_create_produit(nom_produit, prix_u)
            chauffeur_id = cache.get_or_create_chauffeur(nom_chauff)
            carriere_id  = cache.get_or_create_carriere(nom_carr)
            chantier_id  = cache.get_or_create_chantier(code_ch, nom_ch, client_id, ville)
            temps_id     = cache.get_or_create_temps(date_obj)

            cur_check = conn.cursor()
            if livraison_exists(cur_check, num_bon, date_obj, chantier_id):
                stats["livraisons_doublons"] += 1
                continue

            montant_ht  = montant_raw
            tva_montant = None
            montant_ttc = None
            if montant_ht is not None:
                tva_montant = (montant_ht * Decimal(str(TVA_RATE))).quantize(Decimal("0.01"))
                montant_ttc = (montant_ht + tva_montant).quantize(Decimal("0.01"))

            batch_livraisons.append((
                num_bon, date_obj,
                client_id, produit_id, chantier_id,
                chauffeur_id, carriere_id, temps_id,
                quantite, prix_u,
                montant_ht, tva_montant, montant_ttc,
            ))

            if len(batch_livraisons) >= BATCH_SIZE:
                flush_batch()

        except Exception as exc:
            log.error("  [ERREUR] Ligne %d : %s", row_num, exc)
            conn.rollback()
            stats["livraisons_erreurs"] += 1
            batch_livraisons.clear()
            continue

    try:
        flush_batch()
    except Exception as exc:
        log.error("  [ERREUR] Dernier batch : %s", exc)
        conn.rollback()

    conn.close()

    # ── 4. Resume final ───────────────────────────────────────────────────────
    elapsed = (datetime.now() - start_time).total_seconds()
    log.info("")
    log.info("=" * 70)
    log.info("  RESUME DE L'IMPORT")
    log.info("=" * 70)
    log.info("  Lignes Excel lues         : %d", total_rows)
    log.info("  -------------------------------------")
    log.info("  Clients  traites          : %d", len(cache.clients))
    log.info("  Produits traites          : %d", len(cache.produits))
    log.info("  Chauffeurs traites        : %d", len(cache.chauffeurs))
    log.info("  Carrieres traitees        : %d", len(cache.carrieres))
    log.info("  Chantiers traites         : %d", len(cache.chantiers))
    log.info("  Entrees dim_temps         : %d", len(cache.temps))
    log.info("  -------------------------------------")
    log.info("  Livraisons inserees [OK]  : %d", stats["livraisons_inserees"])
    log.info("  Livraisons doublons [>>]  : %d", stats["livraisons_doublons"])
    log.info("  Livraisons en erreur [!!] : %d", stats["livraisons_erreurs"])
    log.info("  -------------------------------------")
    log.info("  Duree totale              : %.2f secondes", elapsed)
    log.info("=" * 70)

    if stats["livraisons_erreurs"] > 0:
        log.warning("  Des erreurs ont eu lieu -- consultez import_log.txt")
    else:
        log.info("  Import termine sans erreur !")


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    main()
