import os
import sys


class DonutExtractor:
    """
    Extracteur de données depuis une image de facture via le modèle Donut.
    
    Utilise VisionEncoderDecoderModel + DonutProcessor de HuggingFace Transformers.
    Le modèle doit être placé dans le dossier spécifié par model_path.
    """

    def __init__(self, model_path: str):
        self.model_path = model_path
        self._processor = None
        self._model = None

    def _load_model(self) -> bool:
        """Charge le modèle Donut (lazy loading)."""
        if self._model is not None:
            return True

        if not os.path.isdir(self.model_path):
            print(
                f"[DonutExtractor] Modèle non trouvé dans : {self.model_path}",
                file=sys.stderr,
            )
            return False

        try:
            from transformers import DonutProcessor, VisionEncoderDecoderModel
            import torch

            self._processor = DonutProcessor.from_pretrained(self.model_path)
            self._model = VisionEncoderDecoderModel.from_pretrained(self.model_path)
            self._model.eval()
            print(f"[DonutExtractor] Modèle chargé depuis : {self.model_path}")
            return True
        except Exception as e:
            print(f"[DonutExtractor] Erreur chargement modèle : {e}", file=sys.stderr)
            return False

    def extract(self, image_path: str) -> dict:
        """
        Extrait les champs d'une facture depuis une image.

        Args:
            image_path: Chemin vers l'image (PNG, JPG)

        Returns:
            dict avec les champs extraits, ou {"error": "..."} si le modèle n'est pas disponible
        """
        if not os.path.isfile(image_path):
            return {"error": f"Fichier introuvable : {image_path}"}

        if not self._load_model():
            return {
                "error": (
                    f"Modèle Donut non disponible dans '{self.model_path}'. "
                    "Placez les fichiers du modèle (config.json, pytorch_model.bin, tokenizer…) "
                    "dans ce dossier pour activer l'extraction automatique."
                ),
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

            image = Image.open(image_path).convert("RGB")
            pixel_values = self._processor(image, return_tensors="pt").pixel_values

            task_prompt = "<s_cord-v2>"
            decoder_input_ids = self._processor.tokenizer(
                task_prompt, add_special_tokens=False, return_tensors="pt"
            ).input_ids

            with torch.no_grad():
                outputs = self._model.generate(
                    pixel_values,
                    decoder_input_ids=decoder_input_ids,
                    max_length=self._model.decoder.config.max_position_embeddings,
                    early_stopping=True,
                    pad_token_id=self._processor.tokenizer.pad_token_id,
                    eos_token_id=self._processor.tokenizer.eos_token_id,
                    use_cache=True,
                    num_beams=1,
                    bad_words_ids=[[self._processor.tokenizer.unk_token_id]],
                    return_dict_in_generate=True,
                )

            sequence = self._processor.batch_decode(outputs.sequences)[0]
            sequence = sequence.replace(
                self._processor.tokenizer.eos_token, ""
            ).replace(self._processor.tokenizer.pad_token, "")
            result = self._processor.token2json(sequence)

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
