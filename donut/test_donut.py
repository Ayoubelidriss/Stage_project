import os
from donut.donut_extractor import DonutExtractor

def test_donut_extractor():
    model_path = "donut/model"
    image_path = "data/images/test_invoice.jpg"

    extractor = DonutExtractor(model_path)
    result = extractor.extract(image_path)

    print(result)

if __name__ == "__main__":
    test_donut_extractor()