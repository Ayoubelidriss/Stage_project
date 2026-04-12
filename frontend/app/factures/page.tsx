"use client";
import { useEffect, useState, useRef } from "react";
import axios from "axios";

interface Facture {
  facture_id: number;
  numero: string;
  date_facture: string | null;
  total_ht: number | null;
  tva: number | null;
  total_ttc: number | null;
  statut: string;
  image_path: string | null;
}

const API = process.env.NEXT_PUBLIC_API_URL || "";

export default function FacturesPage() {
  const [factures, setFactures] = useState<Facture[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [error, setError] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const fetchFactures = async () => {
    try {
      const res = await axios.get(`${API}/api/factures/`);
      setFactures(res.data);
    } catch {
      setError("Erreur chargement factures");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchFactures(); }, []);

  const handleUpload = async () => {
    const file = fileRef.current?.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadResult(null);
    setError("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post(`${API}/api/factures/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setUploadResult(res.data);
      fetchFactures();
    } catch (e: any) {
      setError(e.response?.data?.detail || "Erreur upload");
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const statusColor: Record<string, string> = {
    en_attente: "bg-yellow-100 text-yellow-800",
    validee: "bg-green-100 text-green-800",
    rejetee: "bg-red-100 text-red-800",
  };

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-800 mb-6">🧾 Gestion des Factures</h1>

      {/* Upload */}
      <div className="bg-white rounded-xl shadow p-6 mb-8 border border-dashed border-yellow-400">
        <h2 className="text-lg font-semibold text-gray-700 mb-3">
          📤 Uploader une facture (image PNG/JPG)
        </h2>
        <p className="text-sm text-gray-500 mb-4">
          L&apos;IA Donut extraira automatiquement : numéro, client, montants, etc.
        </p>
        <div className="flex items-center gap-4">
          <input
            ref={fileRef}
            type="file"
            accept="image/png,image/jpeg,image/jpg,.pdf"
            className="border border-gray-300 rounded px-3 py-2 text-sm"
          />
          <button
            onClick={handleUpload}
            disabled={uploading}
            className="bg-yellow-500 hover:bg-yellow-600 text-white px-5 py-2 rounded font-medium disabled:opacity-50"
          >
            {uploading ? "⏳ Extraction en cours..." : "🚀 Uploader & Extraire"}
          </button>
        </div>

        {uploadResult && (
          <div className={`mt-4 p-4 rounded text-sm ${uploadResult.status === "success" ? "bg-green-50 border border-green-200" : "bg-yellow-50 border border-yellow-200"}`}>
            <p className="font-medium mb-2">
              {uploadResult.status === "success" ? "✅ Extraction réussie !" : "⚠️ " + (uploadResult.message || "Résultat partiel")}
            </p>
            {uploadResult.extracted_data && (
              <pre className="text-xs overflow-x-auto bg-white p-2 rounded border">
                {JSON.stringify(uploadResult.extracted_data, null, 2)}
              </pre>
            )}
          </div>
        )}

        {error && <p className="mt-3 text-red-600 text-sm">❌ {error}</p>}
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-yellow-50 text-gray-600 uppercase text-xs">
            <tr>
              <th className="px-4 py-3 text-left">N° Facture</th>
              <th className="px-4 py-3 text-left">Date</th>
              <th className="px-4 py-3 text-right">Total HT</th>
              <th className="px-4 py-3 text-right">TVA</th>
              <th className="px-4 py-3 text-right">Total TTC</th>
              <th className="px-4 py-3 text-center">Statut</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? (
              <tr><td colSpan={6} className="text-center py-8 text-gray-400">⏳ Chargement...</td></tr>
            ) : factures.length === 0 ? (
              <tr><td colSpan={6} className="text-center py-8 text-gray-400">Aucune facture trouvée</td></tr>
            ) : (
              factures.map((f) => (
                <tr key={f.facture_id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-800">{f.numero}</td>
                  <td className="px-4 py-3 text-gray-600">{f.date_facture ?? "—"}</td>
                  <td className="px-4 py-3 text-right text-gray-700">
                    {f.total_ht != null ? f.total_ht.toLocaleString("fr-MA") + " MAD" : "—"}
                  </td>
                  <td className="px-4 py-3 text-right text-gray-700">
                    {f.tva != null ? f.tva.toLocaleString("fr-MA") + " MAD" : "—"}
                  </td>
                  <td className="px-4 py-3 text-right font-semibold text-yellow-700">
                    {f.total_ttc != null ? f.total_ttc.toLocaleString("fr-MA") + " MAD" : "—"}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColor[f.statut] ?? "bg-gray-100 text-gray-600"}`}>
                      {f.statut}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
