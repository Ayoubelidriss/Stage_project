"use client";
import { useState, useRef, useEffect } from "react";
import axios from "axios";

interface Message {
  role: "user" | "assistant";
  content: string;
  sql?: string;
  data?: any[];
}

const SUGGESTIONS = [
  "Quel chantier a consommé le plus de gravette ?",
  "Quels sont les 5 meilleurs clients par chiffre d'affaires ?",
  "Combien de livraisons ont été effectuées ce mois ?",
  "Quel est le produit le plus vendu en tonnes ?",
  "Liste les factures en attente de validation",
];

const API = process.env.NEXT_PUBLIC_API_URL || "";

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Bonjour ! Je suis l'assistant IA de Golden Carrière. Posez-moi n'importe quelle question sur vos livraisons, clients, chantiers ou factures.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (question?: string) => {
    const q = question || input.trim();
    if (!q) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: q }]);
    setLoading(true);

    try {
      const res = await axios.post(`${API}/api/chat/`, { question: q });
      const { answer, sql_query, data } = res.data;
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: answer, sql: sql_query, data: data },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "❌ Erreur de connexion au backend. Vérifiez que le serveur est démarré.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-120px)]">
      <h1 className="text-2xl font-bold text-gray-800 mb-4">💬 Chat IA — Analysez vos données</h1>

      {/* Suggestions */}
      <div className="flex flex-wrap gap-2 mb-4">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => sendMessage(s)}
            className="text-xs bg-yellow-50 border border-yellow-300 text-yellow-800 px-3 py-1 rounded-full hover:bg-yellow-100 transition"
          >
            {s}
          </button>
        ))}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto bg-white rounded-xl shadow p-4 space-y-4 mb-4">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[80%] rounded-xl px-4 py-3 text-sm ${
                msg.role === "user"
                  ? "bg-yellow-500 text-white"
                  : "bg-gray-100 text-gray-800"
              }`}
            >
              <p>{msg.content}</p>
              {msg.sql && (
                <details className="mt-2">
                  <summary className="text-xs cursor-pointer text-gray-500 hover:text-gray-700">
                    🔍 Voir la requête SQL
                  </summary>
                  <pre className="mt-1 text-xs bg-gray-800 text-green-300 p-2 rounded overflow-x-auto">
                    {msg.sql}
                  </pre>
                </details>
              )}
              {msg.data && msg.data.length > 0 && (
                <details className="mt-2">
                  <summary className="text-xs cursor-pointer text-gray-500 hover:text-gray-700">
                    📋 Voir les données ({msg.data.length} ligne{msg.data.length > 1 ? "s" : ""})
                  </summary>
                  <div className="mt-1 overflow-x-auto">
                    <table className="text-xs border-collapse min-w-full">
                      <thead>
                        <tr>
                          {Object.keys(msg.data[0]).map((k) => (
                            <th key={k} className="border border-gray-300 bg-gray-200 px-2 py-1 text-left">
                              {k}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {msg.data.slice(0, 10).map((row, ri) => (
                          <tr key={ri}>
                            {Object.values(row).map((val: any, vi) => (
                              <td key={vi} className="border border-gray-200 px-2 py-1">
                                {val != null ? String(val) : "—"}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </details>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-xl px-4 py-3 text-sm text-gray-500 animate-pulse">
              ⏳ Analyse en cours...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="flex gap-3">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
          placeholder="Posez votre question en français..."
          className="flex-1 border border-gray-300 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-yellow-500"
          disabled={loading}
        />
        <button
          onClick={() => sendMessage()}
          disabled={loading || !input.trim()}
          className="bg-yellow-500 hover:bg-yellow-600 text-white px-6 py-3 rounded-xl font-medium disabled:opacity-50"
        >
          Envoyer
        </button>
      </div>
    </div>
  );
}
