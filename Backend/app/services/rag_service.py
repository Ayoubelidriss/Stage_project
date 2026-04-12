"""
RAG Service — Génère du SQL à partir d'une question en langage naturel
et retourne les résultats depuis la base de données.
"""
import os
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.config import OPENAI_API_KEY

# Schéma de la base transmis au modèle comme contexte
DB_SCHEMA = """
Tables disponibles dans la base golden_carriere_db :

1. dim_client(client_id, nom, ice, ville, telephone, email)
2. dim_produit(produit_id, nom, unite, prix_unitaire, categorie)
3. dim_chantier(chantier_id, nom, client_id, localisation, date_debut, date_fin, statut)
4. dim_chauffeur(chauffeur_id, nom, prenom, cin, telephone, statut)
5. dim_carriere(carriere_id, nom, localisation, type_materiau)
6. dim_temps(temps_id, date, annee, trimestre, mois, semaine, jour)
7. fait_livraison(livraison_id, num_bon, date, client_id, produit_id, chantier_id,
                  chauffeur_id, carriere_id, temps_id, quantite, prix_unitaire,
                  montant_ht, tva, montant_ttc)
8. factures(facture_id, numero, date_facture, client_id, chantier_id, total_ht,
            tva, total_ttc, statut, image_path, extracted_data)

Règles :
- Toujours écrire du SQL PostgreSQL valide.
- Retourner UNIQUEMENT la requête SQL, sans explication.
- Limiter les résultats à 50 lignes avec LIMIT 50 si nécessaire.
- Les montants sont en MAD (dirhams marocains).
- Les quantités sont en tonnes.
"""


class RAGService:
    def __init__(self, db: Session):
        self.db = db

    def generate_sql(self, question: str) -> str:
        """Utilise OpenAI pour transformer une question en SQL."""
        if not OPENAI_API_KEY:
            return self._fallback_sql(question)

        try:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Tu es un expert SQL PostgreSQL. "
                            "On te donne le schéma d'une base de données d'une carrière de matériaux. "
                            "Réponds UNIQUEMENT avec la requête SQL, sans aucun texte ni markdown.\n\n"
                            + DB_SCHEMA
                        ),
                    },
                    {"role": "user", "content": question},
                ],
                temperature=0,
                max_tokens=500,
            )
            sql = response.choices[0].message.content.strip()
            # Nettoyer les balises markdown si présentes
            sql = sql.replace("```sql", "").replace("```", "").strip()
            return sql
        except Exception as e:
            return self._fallback_sql(question)

    def _fallback_sql(self, question: str) -> str:
        """SQL par défaut si OpenAI n'est pas disponible."""
        q = question.lower()
        if "chantier" in q and ("plus" in q or "max" in q or "consomm" in q):
            return (
                "SELECT c.nom AS chantier, SUM(fl.quantite) AS quantite_totale "
                "FROM fait_livraison fl "
                "JOIN dim_chantier c ON c.chantier_id = fl.chantier_id "
                "GROUP BY c.nom ORDER BY quantite_totale DESC LIMIT 10"
            )
        if "client" in q and ("plus" in q or "max" in q or "chiffre" in q):
            return (
                "SELECT cl.nom AS client, SUM(fl.montant_ttc) AS ca_ttc "
                "FROM fait_livraison fl "
                "JOIN dim_client cl ON cl.client_id = fl.client_id "
                "GROUP BY cl.nom ORDER BY ca_ttc DESC LIMIT 10"
            )
        if "produit" in q or "materiau" in q or "gravette" in q or "concasse" in q:
            return (
                "SELECT p.nom AS produit, SUM(fl.quantite) AS quantite_totale "
                "FROM fait_livraison fl "
                "JOIN dim_produit p ON p.produit_id = fl.produit_id "
                "GROUP BY p.nom ORDER BY quantite_totale DESC LIMIT 10"
            )
        if "facture" in q:
            return "SELECT * FROM factures ORDER BY facture_id DESC LIMIT 20"
        # Requête générique
        return (
            "SELECT cl.nom AS client, p.nom AS produit, fl.quantite, fl.montant_ttc "
            "FROM fait_livraison fl "
            "LEFT JOIN dim_client cl ON cl.client_id = fl.client_id "
            "LEFT JOIN dim_produit p ON p.produit_id = fl.produit_id "
            "ORDER BY fl.livraison_id DESC LIMIT 20"
        )

    def execute_sql(self, sql: str) -> list:
        """Exécute le SQL généré et retourne les résultats."""
        try:
            result = self.db.execute(text(sql))
            columns = list(result.keys())
            rows = result.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            return [{"error": str(e), "sql": sql}]

    def query(self, question: str) -> dict:
        sql = self.generate_sql(question)
        data = self.execute_sql(sql)
        return {
            "question": question,
            "sql_query": sql,
            "data": data,
        }
