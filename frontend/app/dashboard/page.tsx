"use client";
import { useEffect, useState } from "react";
import axios from "axios";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line,
} from "recharts";

interface Stats {
  total_livraisons: number;
  total_factures: number;
  total_clients: number;
  total_chantiers: number;
  chiffre_affaires_ttc: number;
  chiffre_affaires_ht: number;
  quantite_totale_tonnes: number;
}

interface TopItem {
  client?: string;
  chantier?: string;
  produit?: string;
  ca_ttc?: number;
  quantite?: number;
  nb_livraisons?: number;
  unite?: string;
}

interface MoisData {
  annee: number;
  mois: number;
  nb_livraisons: number;
  ca_ttc: number;
  quantite: number;
}

const API = process.env.NEXT_PUBLIC_API_URL || "";

function KpiCard({ label, value, icon }: { label: string; value: string; icon: string }) {
  return (
    <div className="bg-white rounded-xl shadow p-5 border-l-4 border-yellow-500">
      <div className="text-2xl mb-1">{icon}</div>
      <div className="text-2xl font-bold text-gray-800">{value}</div>
      <div className="text-sm text-gray-500 mt-1">{label}</div>
    </div>
  );
}

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [topClients, setTopClients] = useState<TopItem[]>([]);
  const [topChantiers, setTopChantiers] = useState<TopItem[]>([]);
  const [topProduits, setTopProduits] = useState<TopItem[]>([]);
  const [parMois, setParMois] = useState<MoisData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchAll() {
      try {
        const [s, tc, tch, tp, pm] = await Promise.all([
          axios.get(`${API}/api/dashboard/stats`),
          axios.get(`${API}/api/dashboard/top-clients`),
          axios.get(`${API}/api/dashboard/top-chantiers`),
          axios.get(`${API}/api/dashboard/top-produits`),
          axios.get(`${API}/api/dashboard/livraisons-par-mois`),
        ]);
        setStats(s.data);
        setTopClients(tc.data);
        setTopChantiers(tch.data);
        setTopProduits(tp.data);
        setParMois(pm.data);
      } catch (e) {
        setError("Impossible de charger les données. Vérifiez que le backend est démarré.");
      } finally {
        setLoading(false);
      }
    }
    fetchAll();
  }, []);

  if (loading) return <div className="text-center py-20 text-gray-500">⏳ Chargement...</div>;
  if (error) return <div className="text-center py-20 text-red-500">❌ {error}</div>;

  const moisLabels = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc"];
  const chartData = parMois.map((m) => ({
    label: `${moisLabels[m.mois - 1]} ${m.annee}`,
    CA: Math.round(m.ca_ttc),
    Quantité: Math.round(m.quantite),
    Livraisons: m.nb_livraisons,
  }));

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-800 mb-6">📊 Tableau de bord</h1>

      {/* KPIs */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <KpiCard label="Livraisons" value={stats.total_livraisons.toLocaleString()} icon="🚚" />
          <KpiCard label="Factures" value={stats.total_factures.toLocaleString()} icon="🧾" />
          <KpiCard label="Clients" value={stats.total_clients.toLocaleString()} icon="👥" />
          <KpiCard label="Chantiers" value={stats.total_chantiers.toLocaleString()} icon="🏗️" />
          <KpiCard
            label="CA TTC (MAD)"
            value={stats.chiffre_affaires_ttc.toLocaleString("fr-MA", { minimumFractionDigits: 0 })}
            icon="💰"
          />
          <KpiCard
            label="CA HT (MAD)"
            value={stats.chiffre_affaires_ht.toLocaleString("fr-MA", { minimumFractionDigits: 0 })}
            icon="📈"
          />
          <KpiCard
            label="Quantité Totale (T)"
            value={stats.quantite_totale_tonnes.toLocaleString("fr-MA", { minimumFractionDigits: 0 })}
            icon="⚖️"
          />
        </div>
      )}

      {/* Graphique CA par mois */}
      {chartData.length > 0 && (
        <div className="bg-white rounded-xl shadow p-5 mb-8">
          <h2 className="text-lg font-semibold mb-4 text-gray-700">📅 Évolution du CA mensuel (MAD TTC)</h2>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" tick={{ fontSize: 11 }} />
              <YAxis tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
              <Tooltip formatter={(v: number) => [`${v.toLocaleString()} MAD`, "CA TTC"]} />
              <Line type="monotone" dataKey="CA" stroke="#d97706" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Tops */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Top Clients */}
        <div className="bg-white rounded-xl shadow p-5">
          <h2 className="text-lg font-semibold mb-3 text-gray-700">🏆 Top Clients</h2>
          {topClients.length === 0 ? (
            <p className="text-gray-400 text-sm">Aucune donnée</p>
          ) : (
            <div className="space-y-2">
              {topClients.map((c, i) => (
                <div key={i} className="flex justify-between items-center text-sm">
                  <span className="text-gray-700 truncate max-w-[160px]">{c.client}</span>
                  <span className="text-yellow-600 font-medium">
                    {(c.ca_ttc ?? 0).toLocaleString()} MAD
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Top Chantiers */}
        <div className="bg-white rounded-xl shadow p-5">
          <h2 className="text-lg font-semibold mb-3 text-gray-700">🏗️ Top Chantiers</h2>
          {topChantiers.length === 0 ? (
            <p className="text-gray-400 text-sm">Aucune donnée</p>
          ) : (
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={topChantiers} layout="vertical">
                <XAxis type="number" tick={{ fontSize: 10 }} />
                <YAxis dataKey="chantier" type="category" width={100} tick={{ fontSize: 10 }} />
                <Tooltip />
                <Bar dataKey="quantite" fill="#f59e0b" name="Quantité (T)" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Top Produits */}
        <div className="bg-white rounded-xl shadow p-5">
          <h2 className="text-lg font-semibold mb-3 text-gray-700">⛏️ Top Produits</h2>
          {topProduits.length === 0 ? (
            <p className="text-gray-400 text-sm">Aucune donnée</p>
          ) : (
            <div className="space-y-2">
              {topProduits.map((p, i) => (
                <div key={i} className="flex justify-between items-center text-sm">
                  <span className="text-gray-700 truncate max-w-[160px]">{p.produit}</span>
                  <span className="text-yellow-600 font-medium">
                    {(p.quantite ?? 0).toLocaleString()} {p.unite ?? "T"}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
