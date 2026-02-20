# CDC-CGI — Analyse de Fiches de Paie

Pipeline : **PDF → `pdf_parser` → JSON → `decision_rules` → Résultats de conformité**

---

## Structure

```
CDC-CGI/
├── data/json/bulletins.json        # JSONs parsés
├── models/decision_rules.py        # Moteur d'analyse
├── scripts/pdf_parser.py           # Parser standalone
├── src/
│   ├── api/main.py                 # Backend FastAPI
│   ├── extraction/pdf_parser.py    # Parser (importé par l'API)
│   └── ui/src/
│       ├── App.js
│       └── components/
│           ├── UploadZone.js
│           ├── ResultsPanel.js
│           └── AdminPanel.js
└── requirements.txt
```

---

## 1. Installation

### Backend

```bash
git clone https://github.com/alineuh/CDC-CGI.git
cd CDC-CGI

python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install fastapi uvicorn pdfplumber python-multipart
# ou toutes les deps :
pip install -r requirements.txt
```

### Frontend

```bash
cd src/ui
npm install

```

---

## 2. Lancer l'application

### Backend (terminal 1)

```bash
cd src/api
uvicorn main:app --reload --port 8000
```

- API → http://localhost:8000  
- Swagger → http://localhost:8000/docs

### Frontend (terminal 2)

```bash
cd src/ui
npm start
```

- UI → http://localhost:3000

---

## 3. Tests

### Via l'UI

1. http://localhost:3000
2. **Onglet Analyser** → déposer un PDF → voir les checks OK / KO
3. **Onglet Admin** → modifier SMIC / Plafond SS (rouge si > 1 an sans màj)

### Via curl

```bash
# Upload + analyse d'un PDF
curl -X POST http://localhost:8000/upload \
  -F "file=@/chemin/fiche.pdf" \
  | python3 -m json.tool

# Lire les valeurs de référence
curl http://localhost:8000/admin/values

# Mettre à jour le SMIC
curl -X PUT http://localhost:8000/admin/values/smic \
  -H "Content-Type: application/json" \
  -d '{"value": 1840.00}'

# Mettre à jour le Plafond SS
curl -X PUT http://localhost:8000/admin/values/plafond_ss \
  -H "Content-Type: application/json" \
  -d '{"value": 4050.00}'

# Healthcheck
curl http://localhost:8000/health
```

### Tester pdf_parser seul

```bash
python scripts/pdf_parser.py data/samples/fiche.pdf --out data/json/bulletins.json
cat data/json/bulletins.json | python3 -m json.tool | head -80
```

### Tester decision_rules seul

```bash
# Bulletin index 0 (défaut)
python models/decision_rules.py data/json/bulletins.json --index 0

# Avec des valeurs personnalisées
python models/decision_rules.py data/json/bulletins.json --index 0 \
  --smic 1840.00 --plafond 4050.00

# Bulletin index 3 (celui du code d'origine)
python models/decision_rules.py data/json/bulletins.json --index 3
```

Sortie attendue :
```json
[
  ["Plafond SS (Base T1)", "OK", 3783.57, 3783.57],
  ["Allégement RGDU",      "KO", 0.0,     312.45]
]
```

---

## 4. Format de réponse `/upload`

```json
{
  "success": true,
  "filename": "fiche_janvier_2026.pdf",
  "bulletins_count": 1,
  "total_checks": 2,
  "total_ko": 1,
  "analysis": [
    {
      "bulletin_index": 0,
      "header": {
        "periode": { "du": "01/01/2026", "au": "31/01/2026" },
        "bulletin_num": 219,
        "matricule": 364,
        "coefficient": 762
      },
      "checks": [
        ["Plafond SS (Base T1)", "OK", 3783.57, 3783.57],
        ["Allégement RGDU",      "KO", 0.0,     312.45]
      ],
      "has_errors": true,
      "smic_used": 1823.03,
      "plafond_used": 4005.00
    }
  ],
  "ref": { "smic": 1823.03, "plafond_ss": 4005.00 },
  "message": "1 bulletin(s) analysé(s) — 1 anomalie(s) détectée(s)"
}
```

Chaque `check` = `[intitulé, statut, valeur_extraite, valeur_attendue]`

---

## 5. Logique de vérification

### Plafond SS
```
valeur_attendue = min(brut, plafond_ss_ref)
OK si |extrait - attendu| < 0.01
```

### Allégement RGDU (Fillon 2026)
```
ratio = max(0, 0.5 × ((3 × SMIC / brut) - 1))
coef  = 0.02 + 0.3821 × (ratio ^ 1.75)
RGDU  = brut × coef
OK si |extrait - RGDU| < 1.00
```

---

## 6. Valeurs de référence Admin

| Clé | Défaut | Description |
|-----|--------|-------------|
| `smic` | `1823.03 €` | SMIC mensuel brut 151,67h |
| `plafond_ss` | `4005.00 €` | Plafond mensuel SS |

Stockées en mémoire — à brancher sur DB pour persister entre redémarrages.

---

## 7. Dépannage

**Le front ne contacte pas l'API**
```bash
curl http://localhost:8000/health
# CORS déjà configuré pour localhost:3000 dans main.py
```

**`ModuleNotFoundError: pdfplumber`**
```bash
pip install pdfplumber python-multipart
```

**`ModuleNotFoundError: extraction`**
```bash
# Lancer uvicorn depuis src/api/
cd src/api && uvicorn main:app --reload --port 8000
```

**Brut non trouvé dans les checks**
```bash
# Inspecter les intitulés parsés du bulletin
python models/decision_rules.py data/json/bulletins.json --index 0
# Si "Brut soumis à cotisation" absent, ajouter l'intitulé exact
# dans NOMS_BRUT dans models/decision_rules.py
```

**`react-dropzone` introuvable**
```bash
cd src/ui && npm install react-dropzone
```


