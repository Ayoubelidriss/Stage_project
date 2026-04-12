from sqlalchemy import Column, Integer, String, Date, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class FaitLivraison(Base):
    __tablename__ = "fait_livraison"

    livraison_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    num_bon = Column(String(50), nullable=True)
    date = Column(Date, nullable=False)
    client_id = Column(Integer, ForeignKey("dim_client.client_id"), nullable=True)
    produit_id = Column(Integer, ForeignKey("dim_produit.produit_id"), nullable=True)
    chantier_id = Column(Integer, ForeignKey("dim_chantier.chantier_id"), nullable=True)
    chauffeur_id = Column(Integer, ForeignKey("dim_chauffeur.chauffeur_id"), nullable=True)
    carriere_id = Column(Integer, ForeignKey("dim_carriere.carriere_id"), nullable=True)
    temps_id = Column(Integer, ForeignKey("dim_temps.temps_id"), nullable=True)
    quantite = Column(Numeric(12, 3), nullable=True)
    prix_unitaire = Column(Numeric(12, 2), nullable=True)
    montant_ht = Column(Numeric(14, 2), nullable=True)
    tva = Column(Numeric(14, 2), nullable=True)
    montant_ttc = Column(Numeric(14, 2), nullable=True)

    client = relationship("DimClient", backref="livraisons")
    produit = relationship("DimProduit", backref="livraisons")
    chantier = relationship("DimChantier", backref="livraisons")
    chauffeur = relationship("DimChauffeur", backref="livraisons")
    carriere = relationship("DimCarriere", backref="livraisons")
    temps = relationship("DimTemps", backref="livraisons")
