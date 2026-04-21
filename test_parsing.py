import sys, json, io
sys.path.insert(0, 'Backend')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from app.services.ocr_service import sequence_vers_dict, _flatten_result, _nettoyer_sequence

# Séquence brute reçue lors du dernier test (balises malformées + garbage CJK)
raw = (
    "<s_invoice><s><s_invoice><s_client><s_nom> F-2024-001</s_ice>"
    "<s_facture><s_adresse> SPRL BTP ATLAS"
    + "\u98a8\u98b1" * 200   # 颱風 x200
)

print("=== Séquence nettoyée (premiers 200 car.) ===")
seq_propre = _nettoyer_sequence(raw)
print(seq_propre[:200])

print("\n=== Résultat structuré ===")
structured = sequence_vers_dict(raw)
print(json.dumps(structured, ensure_ascii=True, indent=2))

print("\n=== Résultat aplati (DB) ===")
flat = _flatten_result(structured)
# Afficher sans raw_sequence pour lisibilité
flat_affichage = {k: v for k, v in flat.items() if k != 'raw_sequence'}
print(json.dumps(flat_affichage, ensure_ascii=True, indent=2))

sys.stdout.flush()
