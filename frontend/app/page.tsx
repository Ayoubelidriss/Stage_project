export default function HomePage() {
  return (
    <div className="text-center py-16">
      <h1 className="text-4xl font-bold text-yellow-600 mb-4">
        ⛏️ Golden Carrière
      </h1>
      <p className="text-lg text-gray-600 mb-8">
        Système de gestion intelligent des livraisons et factures
      </p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-3xl mx-auto mt-10">
        <a
          href="/dashboard"
          className="block p-6 bg-white rounded-xl shadow hover:shadow-lg border border-yellow-200 hover:border-yellow-400 transition"
        >
          <div className="text-3xl mb-2">📊</div>
          <h2 className="text-xl font-semibold text-gray-800">Dashboard</h2>
          <p className="text-gray-500 text-sm mt-1">KPIs, statistiques, graphiques</p>
        </a>
        <a
          href="/factures"
          className="block p-6 bg-white rounded-xl shadow hover:shadow-lg border border-yellow-200 hover:border-yellow-400 transition"
        >
          <div className="text-3xl mb-2">🧾</div>
          <h2 className="text-xl font-semibold text-gray-800">Factures</h2>
          <p className="text-gray-500 text-sm mt-1">Upload et extraction automatique via IA</p>
        </a>
        <a
          href="/chat"
          className="block p-6 bg-white rounded-xl shadow hover:shadow-lg border border-yellow-200 hover:border-yellow-400 transition"
        >
          <div className="text-3xl mb-2">💬</div>
          <h2 className="text-xl font-semibold text-gray-800">Chat IA</h2>
          <p className="text-gray-500 text-sm mt-1">Interrogez vos données en français</p>
        </a>
      </div>
    </div>
  );
}
