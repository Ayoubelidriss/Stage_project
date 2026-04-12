"""
ETL Service — importe des données depuis des fichiers CSV/XLSX
et les charge dans les tables de la base PostgreSQL.
"""
import os
import glob
import pandas as pd
from datetime import date
from sqlalchemy.orm import Session

from app.models.client import DimClient
from app.models.produit import DimProduit
from app.models.chantier import DimChantier
from app.models.chauffeur import DimChauffeur
from app.models.carriere import DimCarriere
from app.models.temps import DimTemps
from app.models.livraison import FaitLivraison


class ETLService:
    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #
    def _get_or_create_client(self, nom: str, ice: str = None) -> int:
        if not nom or (isinstance(nom, float)):
            return None
        client = self.db.query(DimClient).filter(DimClient.nom == str(nom)).first()
        if not client:
            client = DimClient(nom=str(nom), ice=str(ice) if ice else None)
            self.db.add(client)
            self.db.commit()
            self.db.refresh(client)
        return client.client_id

    def _get_or_create_produit(self, nom: str, unite: str = None) -> int:
        if not nom or (isinstance(nom, float)):
            return None
        produit = self.db.query(DimProduit).filter(DimProduit.nom == str(nom)).first()
        if not produit:
            produit = DimProduit(nom=str(nom), unite=str(unite) if unite else None)
            self.db.add(produit)
            self.db.commit()
            self.db.refresh(produit)
        return produit.produit_id

    def _get_or_create_chantier(self, nom: str, client_id: int = None) -> int:
        if not nom or (isinstance(nom, float)):
            return None
        chantier = self.db.query(DimChantier).filter(DimChantier.nom == str(nom)).first()
        if not chantier:
            chantier = DimChantier(nom=str(nom), client_id=client_id)
            self.db.add(chantier)
            self.db.commit()
            self.db.refresh(chantier)
        return chantier.chantier_id

    def _get_or_create_chauffeur(self, nom: str) -> int:
        if not nom or (isinstance(nom, float)):
            return None
        chauffeur = self.db.query(DimChauffeur).filter(DimChauffeur.nom == str(nom)).first()
        if not chauffeur:
            chauffeur = DimChauffeur(nom=str(nom))
            self.db.add(chauffeur)
            self.db.commit()
            self.db.refresh(chauffeur)
        return chauffeur.chauffeur_id

    def _get_or_create_carriere(self, nom: str) -> int:
        if not nom or (isinstance(nom, float)):
            return None
        carriere = self.db.query(DimCarriere).filter(DimCarriere.nom == str(nom)).first()
        if not carriere:
            carriere = DimCarriere(nom=str(nom))
            self.db.add(carriere)
            self.db.commit()
            self.db.refresh(carriere)
        return carriere.carriere_id

    def _get_or_create_temps(self, d: date) -> int:
        if d is None:
            return None
        temps = self.db.query(DimTemps).filter(DimTemps.date == d).first()
        if not temps:
            import datetime
            if isinstance(d, str):
                d = datetime.date.fromisoformat(d)
            temps = DimTemps(
                date=d,
                annee=d.year,
                trimestre=(d.month - 1) // 3 + 1,
                mois=d.month,
                semaine=d.isocalendar()[1],
                jour=d.day,
            )
            self.db.add(temps)
            self.db.commit()
            self.db.refresh(temps)
        return temps.temps_id

    def _to_float(self, value):
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        try:
            return float(str(value).replace(",", ".").replace(" ", "").replace("\xa0", ""))
        except (ValueError, TypeError):
            return None

    def _to_date(self, value):
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        try:
            return pd.to_datetime(value).date()
        except Exception:
            return None

    # ------------------------------------------------------------------ #
    #  Main import
    # ------------------------------------------------------------------ #
    def import_dataframe(self, df: pd.DataFrame) -> dict:
        """
        Importe un DataFrame dans les tables de la BD.
        Colonnes attendues (insensibles à la casse) :
          date, client, produit, unite, chantier, chauffeur, carriere,
          quantite, prix_unitaire, montant_ht, tva, montant_ttc, num_bon
        """
        # Normaliser les noms de colonnes
        df.columns = [c.strip().lower() for c in df.columns]

        inserted = 0
        errors = []

        for i, row in df.iterrows():
            try:
                d = self._to_date(row.get("date"))
                if d is None:
                    errors.append(f"Ligne {i}: date manquante — ligne ignorée")
                    continue

                client_id = self._get_or_create_client(
                    row.get("client"), row.get("ice")
                )
                produit_id = self._get_or_create_produit(
                    row.get("produit"), row.get("unite")
                )
                chantier_id = self._get_or_create_chantier(
                    row.get("chantier"), client_id
                )
                chauffeur_id = self._get_or_create_chauffeur(row.get("chauffeur"))
                carriere_id = self._get_or_create_carriere(row.get("carriere"))
                temps_id = self._get_or_create_temps(d)

                livraison = FaitLivraison(
                    num_bon=str(row.get("num_bon", "")) or None,
                    date=d,
                    client_id=client_id,
                    produit_id=produit_id,
                    chantier_id=chantier_id,
                    chauffeur_id=chauffeur_id,
                    carriere_id=carriere_id,
                    temps_id=temps_id,
                    quantite=self._to_float(row.get("quantite")),
                    prix_unitaire=self._to_float(row.get("prix_unitaire")),
                    montant_ht=self._to_float(row.get("montant_ht")),
                    tva=self._to_float(row.get("tva")),
                    montant_ttc=self._to_float(row.get("montant_ttc")),
                )
                self.db.add(livraison)
                inserted += 1

            except Exception as e:
                errors.append(f"Ligne {i}: {str(e)}")

        self.db.commit()
        return {"inserted": inserted, "errors": errors}

    def import_file(self, file_path: str) -> dict:
        """Importe un fichier CSV ou XLSX."""
        ext = os.path.splitext(file_path)[1].lower()
        try:
            if ext == ".csv":
                df = pd.read_csv(file_path, encoding="utf-8-sig", sep=None, engine="python")
            elif ext in (".xlsx", ".xls"):
                df = pd.read_excel(file_path)
            else:
                return {"error": f"Format non supporté: {ext}"}
            result = self.import_dataframe(df)
            result["file"] = file_path
            return result
        except Exception as e:
            return {"error": str(e), "file": file_path}
