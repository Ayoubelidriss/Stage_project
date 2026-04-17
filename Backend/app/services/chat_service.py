"""
Chat Service — Répond en langage naturel aux questions sur les données
en utilisant RAG (Retrieval Augmented Generation).
"""
from sqlalchemy.orm import Session
from app.services.rag_service import RAGService
from app.config import GROK_API_KEY


class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.rag = RAGService(db)

    def answer(self, question: str) -> dict:
        """
        1. Génère le SQL via RAG
        2. Exécute la requête
        3. Formule une réponse en français via Grok (ou règle simple)
        """
        rag_result = self.rag.query(question)
        sql = rag_result["sql_query"]
        data = rag_result["data"]

        answer_text = self._formulate_answer(question, data)

        return {
            "question": question,
            "answer": answer_text,
            "sql_query": sql,
            "data": data[:20],  # Limiter les données retournées au frontend
        }

    def _formulate_answer(self, question: str, data: list) -> str:
        """Formule une réponse lisible à partir des données."""
        if not data:
            return "Aucune donnée trouvée pour cette question."

        if data and "error" in data[0]:
            return f"Erreur lors de l'exécution de la requête : {data[0]['error']}"

        # Essayer avec Grok
        if GROK_API_KEY:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=GROK_API_KEY, base_url="https://api.x.ai/v1")

                # Préparer un résumé des données
                data_summary = str(data[:10])  # max 10 lignes pour le contexte

                response = client.chat.completions.create(
                    model="grok-beta",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Tu es un assistant d'analyse de données pour une carrière de matériaux au Maroc. "
                                "Réponds en français de façon concise et professionnelle. "
                                "Utilise les données fournies pour répondre précisément à la question."
                            ),
                        },
                        {
                            "role": "user",
                            "content": (
                                f"Question : {question}\n\n"
                                f"Données extraites de la base :\n{data_summary}\n\n"
                                "Donne une réponse claire en 1-3 phrases."
                            ),
                        },
                    ],
                    temperature=0.3,
                    max_tokens=300,
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                print(f"Error calling Grok: {e}")
                return self._simple_answer(question, data)

        # Fallback : réponse simple basée sur les données
        return self._simple_answer(question, data)

    def _simple_answer(self, question: str, data: list) -> str:
        """Réponse simple sans Grok."""
        if not data:
            return "Aucune donnée trouvée."

        row = data[0]
        keys = list(row.keys())

        # Essayer de détecter le type de résultat
        if "quantite_totale" in row:
            nom_key = keys[0]
            nom = row.get(nom_key, "N/A")
            qty = row.get("quantite_totale", 0)
            return f"Le résultat principal est '{nom}' avec {qty:.2f} tonnes."

        if "ca_ttc" in row:
            nom_key = keys[0]
            nom = row.get(nom_key, "N/A")
            ca = row.get("ca_ttc", 0)
            return f"Le résultat principal est '{nom}' avec un CA de {ca:,.2f} MAD TTC."

        # Réponse générique
        return f"{len(data)} enregistrement(s) trouvé(s) pour votre question."
