"""
Backend CDC-CGI — PDF Upload → Parse → Analyze
Pipeline: pdf_parser → decision_rules → JSON results
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import sys
import tempfile
import os

# --- Résolution des chemins (robuste peu importe d'où on lance) ---
API_DIR    = Path(__file__).resolve().parent          # .../CDC-CGI/src/api
SRC_DIR    = API_DIR.parent                            # .../CDC-CGI/src
ROOT_DIR   = SRC_DIR.parent                            # .../CDC-CGI

# On ajoute les dossiers qui contiennent nos modules
for p in [str(SRC_DIR), str(ROOT_DIR / "models"), str(ROOT_DIR / "scripts")]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Import direct du fichier pdf_parser (sans passer par le package extraction)
import importlib.util

def _load_module(name: str, *search_paths):
    """Charge un module Python depuis un chemin de fichier."""
    for path in search_paths:
        candidate = Path(path) / f"{name}.py"
        if candidate.exists():
            spec = importlib.util.spec_from_file_location(name, candidate)
            mod  = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
    raise ImportError(f"Module '{name}' introuvable dans : {search_paths}")

_parser = _load_module(
    "pdf_parser",
    SRC_DIR / "extraction",
    ROOT_DIR / "scripts",
)
parse_pdf_to_json = _parser.parse_pdf_to_json

_rules = _load_module(
    "decision_rules",
    ROOT_DIR / "models",
)
analyze_all_bulletins = _rules.analyze_all_bulletins
SMIC_REF_DEFAULT      = _rules.SMIC_REF_DEFAULT
PLAFOND_SS_DEFAULT    = _rules.PLAFOND_SS_DEFAULT

# --- App ---
app = FastAPI(
    title="CDC-CGI Payslip Analyzer API",
    description="Upload PDF payslips -> Parse -> Validate",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Valeurs de référence en mémoire
_ref_values = {
    "smic":       {"value": SMIC_REF_DEFAULT,   "updated": "2026-01-01T00:00:00.000Z"},
    "plafond_ss": {"value": PLAFOND_SS_DEFAULT,  "updated": "2026-01-01T00:00:00.000Z"},
}


# ---------------------------------------------------------------------------
# ROUTES
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    return {"message": "CDC-CGI Payslip Analyzer API", "status": "operational"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/admin/values")
async def get_ref_values():
    return _ref_values


@app.put("/admin/values/{key}")
async def update_ref_value(key: str, payload: dict = Body(...)):
    if key not in _ref_values:
        raise HTTPException(status_code=404, detail=f"Cle inconnue: {key}")
    value = payload.get("value")
    if value is None or not isinstance(value, (int, float)) or float(value) <= 0:
        raise HTTPException(status_code=400, detail="Valeur invalide")
    from datetime import datetime, timezone
    _ref_values[key]["value"]   = float(value)
    _ref_values[key]["updated"] = datetime.now(timezone.utc).isoformat()
    return {"success": True, "key": key, **_ref_values[key]}


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Seuls les fichiers PDF sont acceptes.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        bulletins = parse_pdf_to_json(Path(tmp_path))
        if not bulletins:
            raise HTTPException(status_code=400, detail="Impossible de parser ce PDF.")

        smic    = _ref_values["smic"]["value"]
        plafond = _ref_values["plafond_ss"]["value"]
        analysis = analyze_all_bulletins(bulletins, smic_ref=smic, plafond_ref=plafond)

        total_checks = sum(len(b["checks"]) for b in analysis)
        total_ko     = sum(sum(1 for r in b["checks"] if r[1] == "KO") for b in analysis)

        return {
            "success":         True,
            "filename":        file.filename,
            "bulletins_count": len(analysis),
            "total_checks":    total_checks,
            "total_ko":        total_ko,
            "analysis":        analysis,
            "raw_bulletins":   bulletins,
            "ref":             {"smic": smic, "plafond_ss": plafond},
            "message":         f"{len(analysis)} bulletin(s) analyse(s) - {total_ko} anomalie(s) detectee(s)",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur d'analyse: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


if __name__ == "__main__":
    import uvicorn
    print("CDC-CGI Backend starting...")
    print("API   -> http://localhost:8000")
    print("Docs  -> http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
