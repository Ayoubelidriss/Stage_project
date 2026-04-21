import pandas as pd

EXCEL_PATH = "data/dataset_golden_carriere.xlsx"

# Sheet principale
df = pd.read_excel(EXCEL_PATH, sheet_name='TOUTES_DONNEES', nrows=3)
print("=== TOUTES_DONNEES ===")
print("Colonnes:", list(df.columns))
print(df.head(3).to_string())
print()

# Un chantier
df2 = pd.read_excel(EXCEL_PATH, sheet_name='CH001', nrows=3)
print("=== CH001 ===")
print("Colonnes:", list(df2.columns))
print(df2.head(3).to_string())
