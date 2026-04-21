"""
OCRService — Extraction de données de factures via Donut (fine-tuné).

Le modèle fine-tuné produit une séquence XML structurée commençant par
<s_invoice> avec les sous-sections <s_client>, <s_facture>, <s_lignes>,
<s_totaux>.

Chemin du modèle calculé de façon absolue depuis ce fichier :
    Backend/app/services/ocr_service.py
    └─ ../../../donut/model  →  Stage_project/donut/model
"""

import os
import re
import sys
import logging

log = logging.getLogger(__name__)

# ─── Chemin absolu vers le modèle (indépendant du répertoire de travail) ──────
_THIS_DIR    = os.path.dirname(os.path.abspath(__file__))   # …/services
_APP_DIR     = os.path.dirname(_THIS_DIR)                    # …/app
_BACKEND_DIR = os.path.dirname(_APP_DIR)                     # …/Backend
_PROJECT_DIR = os.path.dirname(_BACKEND_DIR)                 # …/Stage_project

MODEL_PATH  = os.path.join(_PROJECT_DIR, "donut", "model")
TASK_TOKEN  = "<s_invoice>"
MAX_LENGTH  = 768

REQUIRED_FILES = [
    "config.json",
    "preprocessor_config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "model.safetensors",
]


# ─────────────────────────────────────────────────────────────────────────────
#  NETTOYAGE DE LA SÉQUENCE BRUTE
# ─────────────────────────────────────────────────────────────────────────────

def _nettoyer_sequence(seq: str) -> str:
    """
    Supprime les hallucinations du modèle :
    - Caractères CJK répétés (ex : 颱風颱風颱風...)
    - Paires/triplets répétés en boucle
    """
    # Supprimer les répétitions de caractères CJK (U+4E00–U+9FFF)
    seq = re.sub(r'([\u4e00-\u9fff]{1,4})\1{2,}', r'\1', seq)
    # Supprimer les répétitions de suites quelconques ≥ 3 fois
    seq = re.sub(r'(.{1,6})\1{3,}', r'\1', seq)
    return seq.strip()


# ─────────────────────────────────────────────────────────────────────────────
#  EXTRACTION LENIENTE (balises fermantes quelconques)
# ─────────────────────────────────────────────────────────────────────────────

def _extraire(pattern: str, texte: str, defaut: str = "") -> str:
    """Extrait le premier groupe capturant d'un pattern regex."""
    m = re.search(pattern, texte, re.DOTALL)
    return m.group(1).strip() if m else defaut


def _extraire_tag(tag: str, texte: str) -> str:
    """
    Extrait le contenu entre <tag> et la PREMIÈRE balise fermante </s_...>
    (quelle que soit son nom) — robuste aux décalages de tags du modèle.
    """
    # Essai 1 : balise fermante correcte
    m = re.search(rf"<{tag}>(.*?)</{tag}>", texte, re.DOTALL)
    if m:
        return m.group(1).strip()
    # Essai 2 : n'importe quelle balise fermante </s_xxx>
    m = re.search(rf"<{tag}>(.*?)</s_[^>]+>", texte, re.DOTALL)
    if m:
        return m.group(1).strip()
    # Essai 3 : jusqu'à la prochaine balise ouvrante ou fin
    m = re.search(rf"<{tag}>(.*?)(?=</?s_|$)", texte, re.DOTALL)
    if m:
        return m.group(1).strip()
    return ""


# ─────────────────────────────────────────────────────────────────────────────
#  POST-TRAITEMENT : séquence brute → dict structuré
# ─────────────────────────────────────────────────────────────────────────────

def sequence_vers_dict(raw_sequence: str) -> dict:
    """
    Convertit la séquence générée par Donut en dict Python structuré.
    Supporte les balises fermantes incorrectes (hallucinations du modèle).
    """
    # Nettoyage des caractères répétés
    seq = _nettoyer_sequence(raw_sequence)

    # Localise le contenu après <s_invoice> (avec ou sans </s_invoice>)
    m = re.search(r"<s_invoice>(.*?)(?:</s_invoice>|$)", seq, re.DOTALL)
    if not m:
        return {"raw_sequence": raw_sequence}

    content = m.group(1)
    result = {}

    # ── Client ────────────────────────────────────────────────────────────────
    client_m = re.search(r"<s_client>(.*?)(?:</s_client>|<s_facture>|$)", content, re.DOTALL)
    if client_m:
        cs = client_m.group(1)
        result["client"] = {
            "nom":     _extraire_tag("s_nom",     cs),
            "adresse": _extraire_tag("s_adresse", cs),
            "ice":     _extraire_tag("s_ice",     cs),
        }

    # ── Facture ───────────────────────────────────────────────────────────────
    facture_m = re.search(r"<s_facture>(.*?)(?:</s_facture>|<s_affaire>|<s_lignes>|<s_totaux>|$)",
                          content, re.DOTALL)
    if facture_m:
        fs = facture_m.group(1)
        result["facture"] = {
            "numero": _extraire_tag("s_numero", fs),
            "date":   _extraire_tag("s_date",   fs),
        }

    # ── Affaire ───────────────────────────────────────────────────────────────
    affaire_m = re.search(r"<s_affaire>(.*?)(?:</s_affaire>|<s_lignes>|<s_totaux>|$)",
                          content, re.DOTALL)
    if affaire_m:
        result["affaire"] = affaire_m.group(1).strip()

    # ── Lignes ────────────────────────────────────────────────────────────────
    lignes_m = re.search(r"<s_lignes>(.*?)(?:</s_lignes>|<s_totaux>|$)", content, re.DOTALL)
    if lignes_m:
        lignes = []
        for item in re.findall(r"<s_ligne>(.*?)(?:</s_ligne>|<s_ligne>|$)",
                               lignes_m.group(1), re.DOTALL):
            if item.strip():
                lignes.append({
                    "designation": _extraire_tag("s_designation", item),
                    "quantite":    _extraire_tag("s_quantite",    item),
                    "unite":       _extraire_tag("s_unite",       item),
                    "pu_ht":       _extraire_tag("s_pu_ht",       item),
                    "total_dh":    _extraire_tag("s_total_dh",    item),
                })
        result["lignes"] = lignes

    # ── Totaux ────────────────────────────────────────────────────────────────
    totaux_m = re.search(r"<s_totaux>(.*?)(?:</s_totaux>|$)", content, re.DOTALL)
    if totaux_m:
        ts = totaux_m.group(1)
        result["totaux"] = {
            "total_ht":        _extraire_tag("s_total_ht",        ts),
            "tva_montant":     _extraire_tag("s_tva_montant",     ts),
            "tva_pourcentage": _extraire_tag("s_tva_pourcentage", ts),
            "total_ttc":       _extraire_tag("s_total_ttc",       ts),
        }

    # ── Fallback : extraire directement du contenu brut si sections vides ─────
    if not result:
        return {"raw_sequence": raw_sequence}

    # Compléter les champs vides via extraction directe dans le contenu global
    if "facture" not in result or not result["facture"].get("numero"):
        num = _extraire_tag("s_numero", content)
        if num:
            result.setdefault("facture", {})["numero"] = num

    if "client" not in result or not result["client"].get("nom"):
        nom = _extraire_tag("s_nom", content)
        if nom:
            result.setdefault("client", {})["nom"] = nom

    return {"invoice": result}


def _flatten_result(structured: dict) -> dict:
    """
    Aplatit le dict structuré en un dict simple compatible avec la DB Facture.
    """
    inv = structured.get("invoice", {})
    client  = inv.get("client",  {})
    facture = inv.get("facture", {})
    totaux  = inv.get("totaux",  {})
    lignes  = inv.get("lignes",  [])

    return {
        "numero_facture": facture.get("numero") or None,
        "date_facture":   facture.get("date")   or None,
        "client":         client.get("nom")      or None,
        "ice_client":     client.get("ice")      or None,
        "adresse_client": client.get("adresse")  or None,
        "affaire":        inv.get("affaire")     or None,
        "total_ht":       totaux.get("total_ht")        or None,
        "tva":            totaux.get("tva_montant")      or None,
        "tva_pct":        totaux.get("tva_pourcentage")  or None,
        "total_ttc":      totaux.get("total_ttc")        or None,
        "designations":   lignes,
        "raw_sequence":   structured.get("raw_sequence"),  # None si parsing OK
    }


# ─────────────────────────────────────────────────────────────────────────────
#  CLASSE PRINCIPALE
# ─────────────────────────────────────────────────────────────────────────────

class OCRService:
    """Service d'extraction de données depuis une image de facture via Donut."""

    _processor = None
    _model     = None
    _device    = None

    def __init__(self, model_path: str | None = None):
        self.model_path = model_path or MODEL_PATH

    def _verify_model_files(self) -> tuple[bool, str]:
        if not os.path.isdir(self.model_path):
            return False, f"Dossier modèle introuvable : {self.model_path}"
        missing = [f for f in REQUIRED_FILES
                   if not os.path.isfile(os.path.join(self.model_path, f))]
        if missing:
            return False, (
                f"Fichiers manquants dans {self.model_path} : {missing}."
            )
        return True, "OK"

    def _load_model(self) -> bool:
        if OCRService._model is not None:
            return True

        ok, msg = self._verify_model_files()
        if not ok:
            log.error("[OCRService] %s", msg)
            print(f"[OCRService] ERREUR : {msg}", file=sys.stderr)
            return False

        try:
            import torch
            from transformers import DonutProcessor, VisionEncoderDecoderModel

            log.info("[OCRService] Chargement du modele Donut depuis : %s", self.model_path)
            print(f"[OCRService] Chargement du modele depuis : {self.model_path}")

            OCRService._processor = DonutProcessor.from_pretrained(
                self.model_path, local_files_only=True
            )
            OCRService._model = VisionEncoderDecoderModel.from_pretrained(
                self.model_path, local_files_only=True
            )

            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            OCRService._model.to(device)
            OCRService._model.eval()
            OCRService._device = device

            log.info("[OCRService] Modele pret sur %s", device)
            print(f"[OCRService] Modele pret sur : {device}")
            return True

        except Exception as exc:
            log.error("[OCRService] Erreur chargement modele : %s", exc)
            print(f"[OCRService] Erreur chargement modele : {exc}", file=sys.stderr)
            return False

    def extract(self, image_path: str) -> dict:
        """
        Extrait les champs d'une facture depuis une image.
        Retourne un dict avec les champs extraits, ou {"error": "..."} en cas d'échec.
        """
        if not os.path.isfile(image_path):
            return {"error": f"Fichier image introuvable : {image_path}"}

        if not self._load_model():
            ok, msg = self._verify_model_files()
            return {
                "error": f"Modele Donut non disponible : {msg}",
                "model_path": self.model_path,
                "required_files": REQUIRED_FILES,
                "numero_facture": None, "date_facture": None,
                "client": None, "ice_client": None,
                "affaire": None, "total_ht": None,
                "tva": None, "total_ttc": None, "designations": [],
            }

        try:
            import torch
            from PIL import Image

            image = Image.open(image_path).convert("RGB")

            pixel_values = OCRService._processor(
                image, return_tensors="pt"
            ).pixel_values.to(OCRService._device)

            decoder_input_ids = OCRService._processor.tokenizer(
                TASK_TOKEN,
                add_special_tokens=False,
                return_tensors="pt",
            ).input_ids.to(OCRService._device)

            with torch.no_grad():
                outputs = OCRService._model.generate(
                    pixel_values,
                    decoder_input_ids=decoder_input_ids,
                    max_length=MAX_LENGTH,
                    early_stopping=False,   # désactivé pour num_beams=1
                    pad_token_id=OCRService._processor.tokenizer.pad_token_id,
                    eos_token_id=OCRService._processor.tokenizer.eos_token_id,
                    num_beams=1,
                )

            sequence = OCRService._processor.batch_decode(
                outputs, skip_special_tokens=False
            )[0]
            sequence = sequence.replace(
                OCRService._processor.tokenizer.eos_token, ""
            ).replace(
                OCRService._processor.tokenizer.pad_token, ""
            ).strip()

            log.info("[OCRService] Sequence brute (200 car.) : %s", sequence[:200])

            structured = sequence_vers_dict(sequence)
            flat = _flatten_result(structured)
            flat["raw_sequence"] = sequence   # inclure pour débogage
            return flat

        except Exception as exc:
            log.exception("[OCRService] Erreur lors de l'extraction")
            return {"error": f"Erreur lors de l'extraction : {str(exc)}"}
