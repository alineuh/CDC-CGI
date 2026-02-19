#%%
# -*- coding: utf-8 -*-
import re
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

import pdfplumber


# ============================================================
# 1) Utils
# ============================================================

def fr_float(s: str) -> Optional[float]:
    if s is None:
        return None
    s = s.strip().replace("\xa0", " ")
    if not s:
        return None
    s = s.replace(" ", "").replace(",", ".")
    s = re.sub(r"[^0-9.\-]", "", s)
    if not s or s in {".", "-", "-."}:
        return None
    try:
        return float(s)
    except ValueError:
        return None


# ============================================================
# 2) Regex header
# ============================================================

DATE_RE = r"[0-9]{2}/[0-9]{2}/[0-9]{4}"

HEADER_PATTERNS = {
    "periode": re.compile(r"P[ée]riode\s*:\s*du\s*(" + DATE_RE + r")\s*au\s*(" + DATE_RE + r")", re.IGNORECASE),
    "bulletin_num": re.compile(r"Bulletin\s*n[°o]\s*:\s*([0-9]+)", re.IGNORECASE),
    "matricule": re.compile(r"Matricule\s*:\s*([0-9]+)", re.IGNORECASE),
    "siret": re.compile(r"Siret\s*:\s*([0-9]{10,14})", re.IGNORECASE),
    "ape": re.compile(r"\bAPE\s*:\s*([0-9A-Z]+)\b", re.IGNORECASE),
    "debut_contrat": re.compile(r"D[ée]but\s+de\s+contrat\s*:\s*(" + DATE_RE + r")", re.IGNORECASE),
    "coefficient": re.compile(r"Coefficient\s*:\s*([0-9]+)", re.IGNORECASE),
    "echelon": re.compile(r"[ÉE]chelon\s*:\s*(?:(\d+)\s*)?APRES\s*(\d+)\s*AN", re.IGNORECASE),
    "convention": re.compile(r"Convention\s+collective\s*(?::)?\s*(.+)$", re.IGNORECASE),
}

def extract_header(text: str) -> Dict[str, Any]:
    header: Dict[str, Any] = {}

    m = HEADER_PATTERNS["periode"].search(text)
    if m:
        header["periode"] = {"du": m.group(1), "au": m.group(2)}

    m = HEADER_PATTERNS["bulletin_num"].search(text)
    if m:
        header["bulletin_num"] = int(m.group(1))

    m = HEADER_PATTERNS["matricule"].search(text)
    if m:
        header["matricule"] = int(m.group(1))

    m = HEADER_PATTERNS["siret"].search(text)
    if m:
        header["siret"] = m.group(1)

    m = HEADER_PATTERNS["ape"].search(text)
    if m:
        header["ape"] = m.group(1)

    m = HEADER_PATTERNS["debut_contrat"].search(text)
    if m:
        header["debut_contrat"] = m.group(1)

    m = HEADER_PATTERNS["coefficient"].search(text)
    if m:
        header["coefficient"] = int(m.group(1))

    m = HEADER_PATTERNS["echelon"].search(text)
    if m:
        niveau = m.group(1)
        apres = m.group(2)
        header["echelon"] = {"niveau": int(niveau) if niveau else None, "apres_ans": int(apres)}

    conv_matches = HEADER_PATTERNS["convention"].findall(text)
    if conv_matches:
        header["convention_collective"] = max((c.strip() for c in conv_matches), key=len)

    return header


# ============================================================
# 3) Clé bulletin + comparaison
# ============================================================

def bulletin_key(header: Dict[str, Any]) -> Optional[Tuple[int, str, str, int]]:
    """
    Une "identité" stable du bulletin.
    Ajuste si tu veux être plus/moins strict.
    """
    try:
        matricule = int(header["matricule"])
        du = header["periode"]["du"]
        au = header["periode"]["au"]
        bnum = int(header["bulletin_num"])
        return (matricule, du, au, bnum)
    except Exception:
        return None

def same_bulletin(prev_header: Dict[str, Any], new_header: Dict[str, Any]) -> bool:
    """
    Si on peut calculer une key sur les deux -> comparaison stricte.
    Sinon -> on considère "pas fiable".
    """
    k1 = bulletin_key(prev_header) if prev_header else None
    k2 = bulletin_key(new_header) if new_header else None
    if k1 is None or k2 is None:
        return False
    return k1 == k2


# ============================================================
# 4) Extraction TABLE (ton code "du bas", adapté par page)
# ============================================================

# Index réels des colonnes utiles : 0, 2, 3, 5, 6, 7, 8
HEADERS = ["numero", "libelle", "base", "taux", "montant", "taux_patronal", "montant_patronal"]
COL_INDICES = [0, 2, 3, 5, 6, 7, 8]

def extract_table_from_page(page) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []

    table_settings = {
        "vertical_strategy": "lines",
        "horizontal_strategy": "lines",
    }
    tables = page.extract_tables(table_settings) or []

    for table in tables:
        for row in table:
            if not row or not row[0]:
                continue

            num = (row[0] or "").strip()
            if not num.isdigit() or len(num) != 5:
                continue

            entry: Dict[str, Any] = {}
            for header, col_idx in zip(HEADERS, COL_INDICES):
                val = row[col_idx].strip() if col_idx < len(row) and row[col_idx] else None
                entry[header] = val or None

            # Optionnel: conversion FR -> float sur les champs numériques
            # (si tu veux garder en str, supprime ce bloc)
            for k in ["base", "taux", "montant", "taux_patronal", "montant_patronal"]:
                if entry.get(k) is not None:
                    entry[k] = fr_float(entry[k])

            results.append(entry)

    return results


# ============================================================
# 5) Parsing NET / CUMUL (si tu les as déjà, tu peux les remettre)
# (je laisse minimal ici, tu peux plugger tes fonctions)
# ============================================================

def extract_net_block(text: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    m = re.search(r"(Net\s+pay[ée]\s+en\s+euros|Net\s+[àa]\s+payer)\s*[:\-]?\s*([\d\s]+,\d{2})",
                  text, re.IGNORECASE)
    if m:
        out["net_a_payer"] = fr_float(m.group(2))
    return out

def extract_cumul_block(text: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    m = re.search(r"Cumul\s+Brut\s*[:\-]?\s*([\d\s]+,\d{2})", text, re.IGNORECASE)
    if m:
        out["cumul_brut"] = fr_float(m.group(1))
    return out


# ============================================================
# 6) Pipeline multi-bulletins / multi-pages
# ============================================================

def parse_pdf_multi_bulletins(pdf_path: Path) -> List[Dict[str, Any]]:
    bulletins: List[Dict[str, Any]] = []

    current: Optional[Dict[str, Any]] = None
    current_header: Dict[str, Any] = {}
    current_key: Optional[Tuple[int, str, str, int]] = None

    def flush_current():
        nonlocal current
        if current is not None:
            # warnings table
            if not current["table"]["rows"]:
                current["table"]["warnings"].append("TABLE_EMPTY")
            bulletins.append(current)
            current = None

    with pdfplumber.open(str(pdf_path)) as pdf:
        for pno, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text() or ""

            # 1) header détecté sur cette page (peut être vide)
            h = extract_header(page_text)
            k = bulletin_key(h) if h else None

            # 2) Décision: nouveau bulletin ?
            if current is None:
                # Premier bulletin: on exige un header utilisable, sinon on démarre "inconnu"
                current_header = h if h else {}
                current_key = k
                current = {
                    "header": current_header,
                    "table": {"rows": [], "warnings": []},
                    "net": {},
                    "cumul": {},
                    "pages": [],
                    "errors": []
                }
            else:
                # Si on a un header exploitable sur cette page
                if k is not None:
                    # Si la key diffère -> nouveau bulletin
                    if current_key is not None and k != current_key:
                        flush_current()
                        current_header = h
                        current_key = k
                        current = {
                            "header": current_header,
                            "table": {"rows": [], "warnings": []},
                            "net": {},
                            "cumul": {},
                            "pages": [],
                            "errors": []
                        }
                    else:
                        # même bulletin -> on peut mettre à jour header si besoin
                        current_header = h
                        current_key = k
                        current["header"] = current_header
                else:
                    # pas d'entête sur cette page -> continuation: on garde current_header
                    pass

            # 3) Ajout page
            current["pages"].append(pno)

            # 4) Table: extraire depuis la page et ajouter au bulletin courant
            rows = extract_table_from_page(page)
            current["table"]["rows"].extend(rows)

            # 5) Net / cumul: on merge en gardant les premières valeurs non nulles
            net = extract_net_block(page_text)
            cumul = extract_cumul_block(page_text)

            for kk, vv in net.items():
                if kk not in current["net"] and vv is not None:
                    current["net"][kk] = vv
            for kk, vv in cumul.items():
                if kk not in current["cumul"] and vv is not None:
                    current["cumul"][kk] = vv

    flush_current()
    return bulletins


# ============================================================
# 7) Main
# ============================================================

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Parse un PDF de fiches de paie en JSON")
    parser.add_argument("pdf", help="Chemin vers le PDF (ex: data/pdfs/bulletin.pdf)")
    parser.add_argument("--out", default="data/json/bulletins_eval.json", help="Chemin JSON de sortie")
    args = parser.parse_args()

    pdf_path = Path(args.pdf).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF introuvable: {pdf_path}")

    bulletins = parse_pdf_multi_bulletins(pdf_path)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(bulletins, f, ensure_ascii=False, indent=2)

    print(f"OK -> {out_path}")
    print(f"Nb bulletins: {len(bulletins)}")
    print(f"Nb lignes total: {sum(len(b['table']['rows']) for b in bulletins)}")

# %%