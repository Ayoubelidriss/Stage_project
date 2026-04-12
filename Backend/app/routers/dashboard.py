from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from app.database import get_db
from app.models.livraison import FaitLivraison
from app.models.facture import Facture
from app.models.client import DimClient
from app.models.chantier import DimChantier
from app.models.produit import DimProduit

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Retourne les KPIs principaux pour le tableau de bord."""
    total_livraisons = db.query(func.count(FaitLivraison.livraison_id)).scalar() or 0
    total_factures = db.query(func.count(Facture.facture_id)).scalar() or 0
    total_clients = db.query(func.count(DimClient.client_id)).scalar() or 0
    total_chantiers = db.query(func.count(DimChantier.chantier_id)).scalar() or 0

    ca_ttc = db.query(func.sum(FaitLivraison.montant_ttc)).scalar() or 0
    ca_ht = db.query(func.sum(FaitLivraison.montant_ht)).scalar() or 0
    quantite_totale = db.query(func.sum(FaitLivraison.quantite)).scalar() or 0

    return {
        "total_livraisons": total_livraisons,
        "total_factures": total_factures,
        "total_clients": total_clients,
        "total_chantiers": total_chantiers,
        "chiffre_affaires_ttc": float(ca_ttc),
        "chiffre_affaires_ht": float(ca_ht),
        "quantite_totale_tonnes": float(quantite_totale),
    }


@router.get("/top-clients")
def top_clients(limit: int = 5, db: Session = Depends(get_db)):
    """Top clients par chiffre d'affaires."""
    results = (
        db.query(
            DimClient.nom,
            func.sum(FaitLivraison.montant_ttc).label("ca_ttc"),
            func.count(FaitLivraison.livraison_id).label("nb_livraisons"),
        )
        .join(FaitLivraison, FaitLivraison.client_id == DimClient.client_id)
        .group_by(DimClient.client_id, DimClient.nom)
        .order_by(func.sum(FaitLivraison.montant_ttc).desc())
        .limit(limit)
        .all()
    )
    return [{"client": r.nom, "ca_ttc": float(r.ca_ttc or 0), "nb_livraisons": r.nb_livraisons} for r in results]


@router.get("/top-chantiers")
def top_chantiers(limit: int = 5, db: Session = Depends(get_db)):
    """Top chantiers par quantité livrée."""
    results = (
        db.query(
            DimChantier.nom,
            func.sum(FaitLivraison.quantite).label("quantite"),
            func.sum(FaitLivraison.montant_ttc).label("ca_ttc"),
        )
        .join(FaitLivraison, FaitLivraison.chantier_id == DimChantier.chantier_id)
        .group_by(DimChantier.chantier_id, DimChantier.nom)
        .order_by(func.sum(FaitLivraison.quantite).desc())
        .limit(limit)
        .all()
    )
    return [{"chantier": r.nom, "quantite": float(r.quantite or 0), "ca_ttc": float(r.ca_ttc or 0)} for r in results]


@router.get("/top-produits")
def top_produits(limit: int = 5, db: Session = Depends(get_db)):
    """Top produits par quantité livrée."""
    results = (
        db.query(
            DimProduit.nom,
            DimProduit.unite,
            func.sum(FaitLivraison.quantite).label("quantite"),
        )
        .join(FaitLivraison, FaitLivraison.produit_id == DimProduit.produit_id)
        .group_by(DimProduit.produit_id, DimProduit.nom, DimProduit.unite)
        .order_by(func.sum(FaitLivraison.quantite).desc())
        .limit(limit)
        .all()
    )
    return [{"produit": r.nom, "unite": r.unite, "quantite": float(r.quantite or 0)} for r in results]


@router.get("/livraisons-par-mois")
def livraisons_par_mois(db: Session = Depends(get_db)):
    """Livraisons agrégées par mois."""
    results = (
        db.query(
            extract("year", FaitLivraison.date).label("annee"),
            extract("month", FaitLivraison.date).label("mois"),
            func.count(FaitLivraison.livraison_id).label("nb"),
            func.sum(FaitLivraison.montant_ttc).label("ca_ttc"),
            func.sum(FaitLivraison.quantite).label("quantite"),
        )
        .group_by("annee", "mois")
        .order_by("annee", "mois")
        .all()
    )
    return [
        {
            "annee": int(r.annee),
            "mois": int(r.mois),
            "nb_livraisons": r.nb,
            "ca_ttc": float(r.ca_ttc or 0),
            "quantite": float(r.quantite or 0),
        }
        for r in results
    ]
