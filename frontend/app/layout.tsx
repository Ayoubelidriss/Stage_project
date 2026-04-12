import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Golden Carrière",
  description: "Système de gestion des livraisons et factures",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr">
      <body>
        <nav className="bg-yellow-600 text-white shadow-md">
          <div className="max-w-7xl mx-auto px-4 py-3 flex items-center gap-8">
            <span className="text-xl font-bold tracking-wide">⛏️ Golden Carrière</span>
            <a href="/" className="hover:underline">Accueil</a>
            <a href="/dashboard" className="hover:underline">Dashboard</a>
            <a href="/factures" className="hover:underline">Factures</a>
            <a href="/chat" className="hover:underline">Chat IA</a>
          </div>
        </nav>
        <main className="max-w-7xl mx-auto px-4 py-6">{children}</main>
      </body>
    </html>
  );
}
