import os
from transformers import DonutFeatureExtractor, DonutForLayoutLMForInvoiceTable
from PIL import Image

class DonutExtractor:
    def __init__(self, model_path):
        self.feature_extractor = DonutFeatureExtractor.from_pretrained(model_path)
        self.model = DonutForLayoutLMForInvoiceTable.from_pretrained(model_path)

    def extract(self, image_path):
        image = Image.open(image_path)
        pixel_values = self.feature_extractor(images=image, return_tensors="pt").pixel_values
        output = self.model(pixel_values=pixel_values)

        # Extract relevant fields from the output
        numero_facture = output.numero_facture
        date_facture = output.date_facture
        client = output.client
        ice_client = output.ice_client
        affaire = output.affaire
        total_ht = output.total_ht
        tva = output.tva
        total_ttc = output.total_ttc
        designations = output.designations

        return {
            "numero_facture": numero_facture,
            "date_facture": date_facture,
            "client": client,
            "ice_client": ice_client,
            "affaire": affaire,
            "total_ht": total_ht,
            "tva": tva,
            "total_ttc": total_ttc,
            "designations": designations
        }