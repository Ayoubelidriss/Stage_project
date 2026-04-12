import os
import sys
from app.config import DONUT_MODEL_PATH


class OCRService:
    """Service d'extraction de données depuis une image de facture via le modèle Donut."""

    def __init__(self):
        self.model_path = DONUT_MODEL_PATH
        self._model = None
        self._feature_extractor = None

    def _load_model(self):
        """Charge le modèle Donut (chargement paresseux)."""
        if self._model is not None:
            return True

        if not os.path.isdir(self.model_path):
            return False

        try:
            from transformers import DonutProcessor, VisionEncoderDecoderModel
            import torch

            self._feature_extractor = DonutProcessor.from_pretrained(self.model_path)
            self._model = VisionEncoderDecoderModel.from_pretrained(self.model_path)
            self._model.eval()
            return True
        except Exception as e:
            print(f"[OCRService] Erreur chargement modèle: {e}", file=sys.stderr)
            return False

    def extract(self, image_path: str) -> dict:
        """
        Extrait les champs d'une facture depuis une image.

        Returns:
            dict avec les champs extraits ou {"error": "..."}
        """
        if not os.path.isfile(image_path):
            return {"error": f"Fichier image introuvable : {image_path}"}

        model_loaded = self._load_model()

        if not model_loaded:
            # Mode dégradé : retourner les métadonnées du fichier seulement
            return {
                "error": (
                    f"Modèle Donut non disponible dans '{self.model_path}'. "
                    "Placez les fichiers du modèle dans ce dossier pour activer l'extraction automatique."
                ),
                "image_path": image_path,
                "numero_facture": None,
                "date_facture": None,
                "client": None,
                "ice_client": None,
                "affaire": None,
                "total_ht": None,
                "tva": None,
                "total_ttc": None,
                "designations": [],
            }

        try:
            from PIL import Image
            import torch
            import re

            image = Image.open(image_path).convert("RGB")
            pixel_values = self._feature_extractor(
                image, return_tensors="pt"
            ).pixel_values

            task_prompt = "<s_cord-v2>"
            decoder_input_ids = self._feature_extractor.tokenizer(
                task_prompt, add_special_tokens=False, return_tensors="pt"
            ).input_ids

            with torch.no_grad():
                outputs = self._model.generate(
                    pixel_values,
                    decoder_input_ids=decoder_input_ids,
                    max_length=self._model.decoder.config.max_position_embeddings,
                    early_stopping=True,
                    pad_token_id=self._feature_extractor.tokenizer.pad_token_id,
                    eos_token_id=self._feature_extractor.tokenizer.eos_token_id,
                    use_cache=True,
                    num_beams=1,
                    bad_words_ids=[[self._feature_extractor.tokenizer.unk_token_id]],
                    return_dict_in_generate=True,
                )

            sequence = self._feature_extractor.batch_decode(outputs.sequences)[0]
            sequence = sequence.replace(
                self._feature_extractor.tokenizer.eos_token, ""
            ).replace(self._feature_extractor.tokenizer.pad_token, "")
            result = self._feature_extractor.token2json(sequence)

            return {
                "numero_facture": result.get("numero_facture"),
                "date_facture": result.get("date_facture"),
                "client": result.get("client"),
                "ice_client": result.get("ice_client"),
                "affaire": result.get("affaire"),
                "total_ht": result.get("total_ht"),
                "tva": result.get("tva"),
                "total_ttc": result.get("total_ttc"),
                "designations": result.get("designations", []),
            }

        except Exception as e:
            return {"error": f"Erreur lors de l'extraction : {str(e)}"}
