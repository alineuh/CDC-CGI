#%%
pathhh="/Users/lamialadraa/Desktop/Ecole/S9/R&D/ETb_09_Tous_Jeu_Evaluation_Détaillé.pdf"
import pdfplumber
import json

# Index réels des colonnes utiles : 0, 2, 3, 5, 6, 7, 8
HEADERS = ["numero", "libelle", "base", "taux", "montant", "taux_patronal", "montant_patronal"]
COL_INDICES = [0, 2, 3, 5, 6, 7, 8]

def extract_table(pdf_path):
    results = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            table_settings = {
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines",
            }
            tables = page.extract_tables(table_settings)
            
            for table in tables:
                for row in table:
                    if not row or not row[0]:
                        continue
                    num = row[0].strip()
                    if not num.isdigit() or len(num) != 5:
                        continue

                    entry = {}
                    for header, col_idx in zip(HEADERS, COL_INDICES):
                        val = row[col_idx].strip() if col_idx < len(row) and row[col_idx] else None
                        entry[header] = val or None
                    results.append(entry)

    return results

data = extract_table(pathhh)

with open("output.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"{len(data)} lignes extraites")
print(json.dumps(data[:5], ensure_ascii=False, indent=2))
# %%
import pdfplumber

with pdfplumber.open(pathhh) as pdf:
    page = pdf.pages[0]
    table = page.extract_table({
        "vertical_strategy": "lines",
        "horizontal_strategy": "lines",
    })
    # Afficher les premières lignes brutes pour voir le vrai nombre de colonnes
    for row in table[:10]:
        print(len(row), row)
# %%
