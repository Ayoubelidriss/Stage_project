import sys, traceback

MODEL_PATH = r'c:\Users\asfou\Stage_project\donut\model'

print("=== Test 1: DonutProcessor ===")
try:
    from transformers import DonutProcessor
    proc = DonutProcessor.from_pretrained(MODEL_PATH, local_files_only=True)
    print("DonutProcessor OK:", type(proc))
except Exception as e:
    print("ERREUR DonutProcessor:", e)
    traceback.print_exc()

print("\n=== Test 2: VisionEncoderDecoderModel ===")
try:
    from transformers import VisionEncoderDecoderModel
    model = VisionEncoderDecoderModel.from_pretrained(MODEL_PATH, local_files_only=True)
    print("VisionEncoderDecoderModel OK:", type(model))
except Exception as e:
    print("ERREUR VisionEncoderDecoderModel:", e)
    traceback.print_exc()

print("\n=== Fin des tests ===")
sys.stdout.flush()
