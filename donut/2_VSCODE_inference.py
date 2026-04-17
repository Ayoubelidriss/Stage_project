"""
2_VSCODE_inference.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Script d'inférence VS Code — Modèle Donut fine-tuné
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ÉTAPES AVANT DE LANCER :
  1. Téléchargez le dossier 'donut_factures_model' depuis Google Drive
  2. Placez-le dans le même dossier que ce script
  3. Installez les dépendances :
       pip install transformers torch torchvision Pillow sentencepiece
  4. Lancez :
       python 2_VSCODE_inference.py --image /chemin/vers/facture.png

Structure attendue :
  mon_projet/
  ├── 2_VSCODE_inference.py   ← ce fichier
  └── donut_factures_model/   ← dossier téléchargé depuis Drive
      ├── config.json
      ├── model.safetensors   (ou pytorch_model.bin)
      ├── tokenizer.json
      ├── tokenizer_config.json
      ├── special_tokens_map.json
      └── preprocessor_config.json
"""

import os
import re
import sys
import json
import argparse
import torch
from PIL import Image
from transformers import DonutProcessor, VisionEncoderDecoderModel


# ═════════════════════════════════════════════════════════════════════════════
# CONFIGURATION — Modifier si besoin
# ═════════════════════════════════════════════════════════════════════════════

# Chemin vers le modèle téléchargé depuis Google Drive
MODEL_PATH  = os.path.join(os.path.dirname(__file__), 'donut_factures_model')

TASK_TOKEN  = '<s_invoice>'
MAX_LENGTH  = 768


# ═════════════════════════════════════════════════════════════════════════════
# CHARGEMENT DU MODÈLE
# ═════════════════════════════════════════════════════════════════════════════

def charger_modele():
    """Charge le processor et le modèle depuis le dossier local."""

    if not os.path.exists(MODEL_PATH):
        print(f"\n❌ ERREUR : Dossier modèle introuvable : {MODEL_PATH}")
        print("\nÀ faire :")
        print("  1. Allez sur Google Drive → donut_factures_model")
        print("  2. Téléchargez le dossier complet")
        print(f"  3. Placez-le ici : {MODEL_PATH}")
        sys.exit(1)

    print(f"Chargement du modèle depuis : {MODEL_PATH}")
    processor = DonutProcessor.from_pretrained(MODEL_PATH)
    model     = VisionEncoderDecoderModel.from_pretrained(MODEL_PATH)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.to(device)
    model.eval()

    gpu_info = torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'
    print(f"✅ Modèle prêt sur : {device} ({gpu_info})")
    return processor, model, device


# ═════════════════════════════════════════════════════════════════════════════
# POST-TRAITEMENT : séquence brute → dict JSON
# CORRECTION : toutes les regex utilisent </s_XXX> (pas </XXX>)
# ═════════════════════════════════════════════════════════════════════════════

def _extraire(pattern, texte, defaut=''):
    """Extrait le premier groupe d'un pattern regex."""
    m = re.search(pattern, texte, re.DOTALL)
    return m.group(1).strip() if m else defaut


def sequence_vers_json(raw_sequence: str) -> dict:
    """
    Convertit la séquence brute générée par Donut en dict structuré.

    CORRECTION APPLIQUÉE : tous les closing tags sont </s_XXX>
    (le bug original utilisait </XXX> sans le préfixe s_)
    """
    result = {}

    invoice_match = re.search(r'<s_invoice>(.*?)</s_invoice>', raw_sequence, re.DOTALL)
    if not invoice_match:
        return {'raw_sequence': raw_sequence}

    content = invoice_match.group(1)

    # ── Client ──────────────────────────────
    m = re.search(r'<s_client>(.*?)</s_client>', content, re.DOTALL)
    if m:
        cs = m.group(1)
        result['client'] = {
            'nom':     _extraire(r'<s_nom>(.*?)</s_nom>',         cs),
            'adresse': _extraire(r'<s_adresse>(.*?)</s_adresse>', cs),
            'ice':     _extraire(r'<s_ice>(.*?)</s_ice>',         cs),
        }

    # ── Facture ─────────────────────────────
    m = re.search(r'<s_facture>(.*?)</s_facture>', content, re.DOTALL)
    if m:
        fs = m.group(1)
        result['facture'] = {
            'numero': _extraire(r'<s_numero>(.*?)</s_numero>', fs),
            'date':   _extraire(r'<s_date>(.*?)</s_date>',     fs),
        }

    # ── Affaire ─────────────────────────────
    m = re.search(r'<s_affaire>(.*?)</s_affaire>', content, re.DOTALL)
    if m:
        result['affaire'] = m.group(1).strip()

    # ── Lignes ──────────────────────────────
    m = re.search(r'<s_lignes>(.*?)</s_lignes>', content, re.DOTALL)
    if m:
        lignes = []
        for item_str in re.findall(r'<s_ligne>(.*?)</s_ligne>', m.group(1), re.DOTALL):
            lignes.append({
                'designation': _extraire(r'<s_designation>(.*?)</s_designation>', item_str),
                'quantite':    _extraire(r'<s_quantite>(.*?)</s_quantite>',       item_str),
                'unite':       _extraire(r'<s_unite>(.*?)</s_unite>',             item_str),
                'pu_ht':       _extraire(r'<s_pu_ht>(.*?)</s_pu_ht>',            item_str),
                'total_dh':    _extraire(r'<s_total_dh>(.*?)</s_total_dh>',      item_str),
            })
        result['lignes'] = lignes

    # ── Totaux ──────────────────────────────
    m = re.search(r'<s_totaux>(.*?)</s_totaux>', content, re.DOTALL)
    if m:
        ts = m.group(1)
        result['totaux'] = {
            'total_ht':        _extraire(r'<s_total_ht>(.*?)</s_total_ht>',               ts),
            'tva_montant':     _extraire(r'<s_tva_montant>(.*?)</s_tva_montant>',         ts),
            'tva_pourcentage': _extraire(r'<s_tva_pourcentage>(.*?)</s_tva_pourcentage>', ts),
            'total_ttc':       _extraire(r'<s_total_ttc>(.*?)</s_total_ttc>',             ts),
        }

    return {'invoice': result} if result else {'raw_sequence': raw_sequence}


# ═════════════════════════════════════════════════════════════════════════════
# FONCTION D'INFÉRENCE PRINCIPALE
# ═════════════════════════════════════════════════════════════════════════════

def analyser_facture(image_input, processor, model, device) -> dict:
    """
    Analyse une image de facture et retourne les données extraites.

    Args:
        image_input : chemin (str) ou objet PIL.Image
        processor   : DonutProcessor chargé depuis MODEL_PATH
        model       : VisionEncoderDecoderModel chargé depuis MODEL_PATH
        device      : torch.device (cuda ou cpu)

    Returns:
        dict avec les données structurées de la facture
    """
    # Chargement image
    if isinstance(image_input, str):
        if not os.path.exists(image_input):
            raise FileNotFoundError(f"Image non trouvée : {image_input}")
        image = Image.open(image_input).convert('RGB')
    elif isinstance(image_input, Image.Image):
        image = image_input.convert('RGB')
    else:
        raise TypeError("image_input doit être un str (chemin) ou PIL.Image")

    # Encodage image
    # NOTE : PAS de .squeeze() ici → on garde la dimension batch (1, C, H, W)
    pixel_values = processor(image, return_tensors='pt').pixel_values.to(device)

    # Token de départ du décodeur
    decoder_input_ids = processor.tokenizer(
        TASK_TOKEN,
        add_special_tokens=False,
        return_tensors='pt'
    ).input_ids.to(device)

    # Génération de la séquence
    with torch.no_grad():
        outputs = model.generate(
            pixel_values,
            decoder_input_ids = decoder_input_ids,
            max_length        = MAX_LENGTH,
            early_stopping    = True,
            pad_token_id      = processor.tokenizer.pad_token_id,
            eos_token_id      = processor.tokenizer.eos_token_id,
            num_beams         = 1,
        )

    # Décodage
    sequence = processor.batch_decode(outputs, skip_special_tokens=False)[0]
    sequence = sequence.replace(processor.tokenizer.eos_token, '')
    sequence = sequence.replace(processor.tokenizer.pad_token, '')

    # Conversion en JSON structuré
    try:
        return sequence_vers_json(sequence)
    except Exception as e:
        print(f"  ⚠️  Erreur parsing : {e}")
        return {'raw_sequence': sequence}


# ═════════════════════════════════════════════════════════════════════════════
# POINT D'ENTRÉE — ligne de commande
# ═════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description='Analyse de factures avec le modèle Donut fine-tuné'
    )
    parser.add_argument(
        '--image', type=str, required=True,
        help='Chemin vers l\'image de la facture à analyser (PNG ou JPG)'
    )
    parser.add_argument(
        '--output', type=str, default=None,
        help='(Optionnel) Chemin vers un fichier JSON pour sauvegarder le résultat'
    )
    args = parser.parse_args()

    # Chargement modèle
    processor, model, device = charger_modele()

    # Analyse
    print(f"\nAnalyse de : {args.image}")
    result = analyser_facture(args.image, processor, model, device)

    # Affichage
    print("\n" + "=" * 55)
    print("DONNÉES EXTRAITES DE LA FACTURE")
    print("=" * 55)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # Sauvegarde optionnelle
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Résultat sauvegardé dans : {args.output}")


# ═════════════════════════════════════════════════════════════════════════════
# UTILISATION COMME MODULE (import dans votre propre code)
# ═════════════════════════════════════════════════════════════════════════════
#
# from inference_vscode import charger_modele, analyser_facture
#
# processor, model, device = charger_modele()
# result = analyser_facture('ma_facture.png', processor, model, device)
# print(result)
#

if __name__ == '__main__':
    main()
