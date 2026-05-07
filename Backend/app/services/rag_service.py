"""
RAG service: turns a French business question into safe read-only SQL,
then returns the database result.
"""
import re

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import GROQ_API_KEY, GROQ_BASE_URL, GROQ_MODEL


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

Regles obligatoires :
- Toujours ecrire du SQL PostgreSQL valide.
- Retourner uniquement la requete SQL, sans explication ni markdown.
- Produire uniquement une requete de lecture : SELECT ou WITH ... SELECT.
- Ne jamais utiliser INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE.
- Ajouter LIMIT 50 sauf si la requete retourne deja une seule ligne agregee.
- Utiliser CURRENT_DATE pour les periodes relatives : aujourd'hui, ce mois, cette annee.
- Si l'utilisateur parle de ventes sans precision, retourner le chiffre d'affaires TTC
  avec SUM(fait_livraison.montant_ttc), et si utile le nombre de livraisons.
- Les montants sont en MAD.
- Les quantites sont en tonnes.
- Utiliser des alias clairs pour aider la generation de la reponse finale.
"""


FORBIDDEN_SQL_KEYWORDS = (
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "create",
    "truncate",
    "merge",
    "grant",
    "revoke",
    "copy",
    "call",
    "execute",
    "do",
    "vacuum",
    "analyze",
    "refresh",
    "listen",
    "notify",
    "set",
    "reset",
)


class RAGService:
    def __init__(self, db: Session):
        self.db = db

    def generate_sql(self, question: str) -> str:
        """Use the LLM to transform a French question into SQL."""
        if not GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY n'est pas configuree. Le chatbot doit utiliser Groq Cloud."
            )

        try:
            from openai import OpenAI

            client = OpenAI(api_key=GROQ_API_KEY, base_url=GROQ_BASE_URL)
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Tu es un expert SQL PostgreSQL pour une application de gestion "
                            "d'une carriere de materiaux. Tu dois repondre uniquement par SQL.\n\n"
                            + DB_SCHEMA
                        ),
                    },
                    {"role": "user", "content": question},
                ],
                temperature=0,
                max_tokens=500,
            )
            return self._clean_sql(response.choices[0].message.content.strip())
        except Exception as exc:
            raise RuntimeError(f"Erreur pendant la generation SQL par LLM : {exc}")

    def _clean_sql(self, sql: str) -> str:
        """Remove markdown fences and a trailing semicolon from the LLM output."""
        cleaned = sql.replace("```sql", "").replace("```", "").strip()
        return cleaned.rstrip(";").strip()

    def validate_readonly_sql(self, sql: str) -> None:
        """Reject anything that is not a single read-only query."""
        normalized = sql.strip()
        lowered = normalized.lower()

        if not normalized:
            raise ValueError("La requete SQL generee est vide.")

        if not (lowered.startswith("select") or lowered.startswith("with")):
            raise ValueError("Seules les requetes SELECT ou WITH sont autorisees.")

        if ";" in normalized:
            raise ValueError("Une seule requete SQL est autorisee.")

        if "--" in normalized or "/*" in normalized or "*/" in normalized:
            raise ValueError("Les commentaires SQL sont interdits.")

        forbidden_pattern = r"\b(" + "|".join(FORBIDDEN_SQL_KEYWORDS) + r")\b"
        match = re.search(forbidden_pattern, lowered)
        if match:
            raise ValueError(f"Mot-cle SQL interdit detecte : {match.group(1).upper()}.")

    def _ensure_limit(self, sql: str) -> str:
        """Cap result size when the LLM forgets a LIMIT clause."""
        if re.search(r"\blimit\s+\d+\b", sql, flags=re.IGNORECASE):
            return sql
        return f"SELECT * FROM ({sql}) AS llm_result LIMIT 50"

    def execute_sql(self, sql: str) -> list:
        """Execute the validated SQL and return rows as dictionaries."""
        try:
            result = self.db.execute(text(sql))
            columns = list(result.keys())
            rows = result.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        except Exception as exc:
            return [{"error": str(exc), "sql": sql}]

    def query(self, question: str) -> dict:
        sql = self.generate_sql(question)
        self.validate_readonly_sql(sql)
        sql = self._ensure_limit(sql)
        self.validate_readonly_sql(sql)
        data = self.execute_sql(sql)
        return {
            "question": question,
            "sql_query": sql,
            "data": data,
        }
