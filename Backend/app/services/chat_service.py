"""
Chat service: generates a SQL query through RAG, executes it, then asks
the LLM to write the final French answer.
"""
import json

from sqlalchemy.orm import Session

from app.config import GROK_API_KEY
from app.services.rag_service import RAGService


class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.rag = RAGService(db)

    def answer(self, question: str) -> dict:
        """
        1. Generate SQL through the LLM/RAG service.
        2. Execute only if the SQL is read-only.
        3. Generate the final answer through the LLM.
        """
        try:
            rag_result = self.rag.query(question)
            sql = rag_result["sql_query"]
            data = rag_result["data"]
        except ValueError as exc:
            return {
                "question": question,
                "answer": f"Requete bloquee pour securite : {exc}",
                "sql_query": None,
                "data": [],
            }
        except RuntimeError as exc:
            return {
                "question": question,
                "answer": f"Impossible de generer une reponse LLM : {exc}",
                "sql_query": None,
                "data": [],
            }

        answer_text = self._formulate_answer(question, sql, data)

        return {
            "question": question,
            "answer": answer_text,
            "sql_query": sql,
            "data": data[:20],
        }

    def _formulate_answer(self, question: str, sql: str, data: list) -> str:
        """Ask the LLM to write a richer answer from the SQL result."""
        if data and "error" in data[0]:
            return f"Erreur lors de l'execution de la requete : {data[0]['error']}"

        if not GROK_API_KEY:
            return (
                "Impossible de generer une reponse : GROK_API_KEY n'est pas configuree. "
                "Le chatbot est configure pour utiliser uniquement le LLM."
            )

        try:
            from openai import OpenAI

            client = OpenAI(api_key=GROK_API_KEY, base_url="https://api.x.ai/v1")
            data_summary = json.dumps(data[:20], ensure_ascii=False, default=str, indent=2)

            response = client.chat.completions.create(
                model="grok-beta",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Tu es un assistant d'analyse de donnees pour une carriere de materiaux au Maroc. "
                            "Tu reponds toujours en francais clair, professionnel et utile. "
                            "Ne reponds jamais par une valeur seule. "
                            "Explique le resultat, cite le chiffre principal, precise l'unite si elle est presente "
                            "(MAD, tonnes, nombre de livraisons), puis ajoute une courte interpretation metier. "
                            "Si les donnees sont vides ou insuffisantes, explique ce que cela signifie. "
                            "Garde une reponse naturelle de 4 a 7 phrases."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Question utilisateur : {question}\n\n"
                            f"Requete SQL executee :\n{sql}\n\n"
                            f"Donnees extraites de la base :\n{data_summary}\n\n"
                            "Redige la reponse finale pour l'utilisateur."
                        ),
                    },
                ],
                temperature=0.25,
                max_tokens=700,
            )
            return response.choices[0].message.content.strip()
        except Exception as exc:
            return f"Impossible de generer une reponse LLM : {exc}"
