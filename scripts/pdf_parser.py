#%%
import re
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

import pdfplumber


# -----------------------------
# Utils: nettoyage / nombres FR
# -----------------------------

def normalize_spaced_text(line: str) -> str:
    """
    Transforme des lignes du type:
      "S a l a i r e i n d i c i a i r e  C C N T  6 6  7 6 2 , 0 0  3 , 9 3 0  2 9 9 4 , 6 6"
    en:
      "Salaire indiciaire CCNT 66 762,00 3,930 2994,66"

    Heuristique:
    - si la majorité des tokens sont des caractères isolés => on "déspace" intelligemment
    - sinon, on normalise simplement les espaces.
    """
    line = line.strip()
    if not line:
        return ""

    # remplace les espaces insécables etc.
    line = line.replace("\xa0", " ")

    tokens = line.split()
    if not tokens:
        return ""

    # % tokens de longueur 1 (typiquement les PDF où chaque caractère est séparé)
    one_char = sum(1 for t in tokens if len(t) == 1)
    ratio = one_char / max(1, len(tokens))

    if ratio >= 0.65:
        # On reconstruit en regroupant les séquences de 1-char,
        # mais on conserve une séparation entre "mots" quand on détecte
        # une vraie frontière (ex: passage lettre->chiffre parfois, etc.)
        rebuilt = []
        buf = []

        def flush_buf():
            nonlocal buf
            if buf:
                rebuilt.append("".join(buf))
                buf = []

        for t in tokens:
            if len(t) == 1:
                buf.append(t)
            else:
                flush_buf()
                rebuilt.append(t)
        flush_buf()

        # Maintenant, rebuilt contient des "mots" souvent trop collés.
        # On ajoute des espaces entre eux.
        s = " ".join(rebuilt)

        # Petit nettoyage: "n °" / "d '"
        s = s.replace("n °", "n°").replace("d '", "d'").replace("l '", "l'")
        s = re.sub(r"\s+", " ", s).strip()
        return s

    # cas normal
    return re.sub(r"\s+", " ", line).strip()


def fr_float(s: str) -> Optional[float]:
    """
    Convertit un nombre français en float:
      "3 729,98" -> 3729.98
      "762,00" -> 762.0
      "3,930" -> 3.93
    Retourne None si pas convertible.
    """
    if s is None:
        return None
    s = s.strip().replace("\xa0", " ")
    if not s:
        return None
    # retire les espaces dans les nombres
    s = s.replace(" ", "")
    # remplace virgule par point
    s = s.replace(",", ".")
    # parfois des tirets ou trucs parasites
    s = re.sub(r"[^0-9.\-]", "", s)
    if not s or s in {".", "-", "-."}:
        return None
    try:
        return float(s)
    except ValueError:
        return None


# -----------------------------
# Extraction en-tête
# -----------------------------

HEADER_PATTERNS = {
    "periode": re.compile(r"P[ée]riode\s*:\s*du\s*([0-9]{2}/[0-9]{2}/[0-9]{4})\s*au\s*([0-9]{2}/[0-9]{2}/[0-9]{4})", re.IGNORECASE),
    "bulletin_num": re.compile(r"Bulletin\s*n[°o]\s*:\s*([0-9]+)", re.IGNORECASE),
    "matricule": re.compile(r"Matricule\s*:\s*([0-9]+)", re.IGNORECASE),
    "siret_ape": re.compile(r"Siret\s*:\s*([0-9]+)\s*APE\s*:\s*([0-9A-Z]+)", re.IGNORECASE),
    "convention": re.compile(r"Convention\s+Collective\s*:\s*(.+)$", re.IGNORECASE),
    "debut_contrat": re.compile(r"D[ée]but\s+de\s+contrat\s*:\s*([0-9]{2}/[0-9]{2}/[0-9]{4})", re.IGNORECASE),
    "coefficient": re.compile(r"Coefficient\s*:\s*([0-9]+)", re.IGNORECASE),
    # "Echelon : 12 APRES 28 AN(S)"
    "echelon": re.compile(r"[ÉE]chelon\s*:\s*([0-9]+)\s*APRES\s*([0-9]+)\s*AN", re.IGNORECASE),
}


def extract_header_from_lines(lines: List[str]) -> Dict[str, Any]:
    text = "\n".join(lines)

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

    m = HEADER_PATTERNS["siret_ape"].search(text)
    if m:
        header["siret"] = m.group(1)  # string (long), évite float
        header["ape"] = m.group(2)

    m = HEADER_PATTERNS["convention"].search(text)
    if m:
        header["convention_collective"] = m.group(1).strip()

    m = HEADER_PATTERNS["debut_contrat"].search(text)
    if m:
        header["debut_contrat"] = m.group(1)

    m = HEADER_PATTERNS["coefficient"].search(text)
    if m:
        header["coefficient"] = int(m.group(1))

    m = HEADER_PATTERNS["echelon"].search(text)
    if m:
        header["echelon"] = {"niveau": int(m.group(1)), "apres_ans": int(m.group(2))}

    return header


# -----------------------------
# Parsing tableau principal
# -----------------------------

SECTION_TITLES = {
    "Cotisations et contributions sociales",
    "Santé",
    "Accidents du travail-Maladies professionnelles retraite",
    "Famille",
    "Assurance chomage",
    "Autres contributions dues par l'employeur",
    "CSG deductible de l'impot sur le revenu",
    "CSG /CRDS non deductible de l'impot sur le revenu",
    "Exonerations, ecretements et allegements de cotisations",
    "Exonérations, écrêtements et allègements de cotisations",
    "Impot sur le revenu",
}

# ligne attendue: intitule + 3 nombres salarié + 1 nombre employeur (souvent)
NUM_RE = re.compile(r"(?<!\w)(?:-?\d[\d\s]*)(?:,\d+)?(?!\w)")

def parse_table_line(line: str) -> Optional[Dict[str, Any]]:
    """
    Retourne une structure:
      {
        "intitule": "...",
        "salarie": {"base": float|None, "taux": float|None, "montant": float|None},
        "employeur": {"montant": float|None}
      }
    ou None si la ligne ne ressemble pas à une ligne de tableau (ex: header, vide, etc.)
    """
    raw = line.strip()
    if not raw:
        return None

    # Exclure les lignes d'en-tête du tableau
    lowered = raw.lower()
    if lowered in {"salarié employeur", "elements de salaire", "éléments de salaire"}:
        return None
    if "base" in lowered and "taux" in lowered and "montant" in lowered:
        return None

    # Extraire les "nombres" présents dans la ligne
    nums = NUM_RE.findall(raw)
    # On convertit en floats FR
    floats = [fr_float(n) for n in nums]
    floats = [f for f in floats if f is not None]

    # Si pas assez d'info numérique, ce n'est probablement pas une ligne de données
    # (ex: "Cotisations et contributions sociales", "Santé", etc.)
    if len(floats) == 0:
        return None

    # On veut idéalement: base, taux, montant(salarié), montant(employeur)
    # Mais certains intitulés n'ont que 1-2 montants.
    # Heuristique:
    # - si >=4 => on prend les 4 derniers comme [base, taux, montant sal, montant emp]
    # - si ==3 => [base, taux, montant sal], employeur None
    # - si ==2 => [base?, montant sal?] => on met base=None, taux=None, montant=floats[-1]
    # - si ==1 => montant salarié = floats[0]
    base = taux = montant_sal = montant_emp = None

    if len(floats) >= 4:
        base, taux, montant_sal, montant_emp = floats[-4], floats[-3], floats[-2], floats[-1]
    elif len(floats) == 3:
        base, taux, montant_sal = floats
    elif len(floats) == 2:
        montant_sal = floats[-1]
    elif len(floats) == 1:
        montant_sal = floats[0]

    # Intitulé = tout ce qui est avant le premier nombre "visible"
    m_first_num = NUM_RE.search(raw)
    intitule = raw[: m_first_num.start()].strip() if m_first_num else raw.strip()

    # Nettoyage d'intitulé (éviter intitulé vide)
    if not intitule or len(intitule) < 2:
        return None

    return {
        "intitule": intitule,
        "salarie": {"base": base, "taux": taux, "montant": montant_sal},
        "employeur": {"montant": montant_emp},
    }


def extract_table_from_lines(lines: List[str]) -> Dict[str, Any]:
    """
    Extrait:
    - tableau principal: lignes avec structure voulue
    - tableau 'Impôt sur le revenu': idem (souvent 3 colonnes mais on le garde au même format)
    """
    # On repère la zone du tableau à partir de "Eléments de salaire" jusqu'à la fin.
    # (tu pourras raffiner ensuite si besoin)
    start_idx = None
    for i, l in enumerate(lines):
        if re.search(r"(El[ée]ments\s+de\s+salaire)", l, re.IGNORECASE):
            start_idx = i
            break
    if start_idx is None:
        return {"lignes": [], "warnings": ["TABLE_NOT_FOUND"]}

    table_lines = lines[start_idx:]

    current_section: Optional[str] = None
    rows: List[Dict[str, Any]] = []

    for l in table_lines:
        l = l.strip()
        if not l:
            continue

        # Détection des titres de section
        if l in SECTION_TITLES:
            current_section = l
            continue

        # Certains titres peuvent apparaître avec variations (accents, casse)
        for title in SECTION_TITLES:
            if title.lower() == l.lower():
                current_section = title
                break

        parsed = parse_table_line(l)
        if parsed:
            if current_section:
                parsed["section"] = current_section
            rows.append(parsed)

    return {"lignes": rows, "warnings": []}


# -----------------------------
# Regroupement multi-pages bulletins
# -----------------------------

def bulletin_key(header: Dict[str, Any]) -> Optional[Tuple[int, str, str, int]]:
    """
    Key: (matricule, date_du, date_au, bulletin_num)
    """
    try:
        matricule = int(header["matricule"])
        du = header["periode"]["du"]
        au = header["periode"]["au"]
        bnum = int(header["bulletin_num"])
        return (matricule, du, au, bnum)
    except Exception:
        return None


def merge_bulletins(existing: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fusionne pages d'un même bulletin:
    - vérifie cohérence matricule/période/bulletin_num
    - concatène les lignes de table
    """
    # vérifications
    for field in ["matricule", "bulletin_num"]:
        if field in existing["header"] and field in incoming["header"]:
            if existing["header"][field] != incoming["header"][field]:
                existing.setdefault("errors", []).append(
                    f"HEADER_MISMATCH_{field}: {existing['header'][field]} != {incoming['header'][field]}"
                )

    if "periode" in existing["header"] and "periode" in incoming["header"]:
        if existing["header"]["periode"] != incoming["header"]["periode"]:
            existing.setdefault("errors", []).append(
                f"HEADER_MISMATCH_periode: {existing['header']['periode']} != {incoming['header']['periode']}"
            )

    # merge tables
    existing["table"]["lignes"].extend(incoming["table"]["lignes"])
    existing["pages"].extend(incoming["pages"])
    return existing


# -----------------------------
# Pipeline PDF -> JSON
# -----------------------------

def parse_pdf_to_json(pdf_path: Path) -> List[Dict[str, Any]]:
    results_by_key: Dict[Tuple[int, str, str, int], Dict[str, Any]] = {}
    unknown_pages: List[Dict[str, Any]] = []

    with pdfplumber.open(str(pdf_path)) as pdf:
        for pno, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            raw_lines = text.splitlines()

            # normalisation des lignes
            lines = [normalize_spaced_text(l) for l in raw_lines]
            lines = [l for l in lines if l]  # remove empties

            header = extract_header_from_lines(lines)
            table = extract_table_from_lines(lines)

            page_obj = {
                "header": header,
                "table": table,
                "pages": [pno],
                "errors": [],
            }

            key = bulletin_key(header)
            if key is None:
                # page non rattachable
                unknown_pages.append(page_obj)
                continue

            if key not in results_by_key:
                results_by_key[key] = {
                    "header": header,
                    "table": {"lignes": list(table["lignes"]), "warnings": list(table["warnings"])},
                    "pages": [pno],
                    "errors": [],
                }
            else:
                results_by_key[key] = merge_bulletins(results_by_key[key], page_obj)

    # On renvoie une liste: bulletins + pages inconnues si besoin
    bulletins = list(results_by_key.values())
    if unknown_pages:
        bulletins.append({"unmatched_pages": unknown_pages})

    return bulletins


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True, help="Chemin du PDF natif")
    parser.add_argument("--out", required=True, help="Chemin du JSON de sortie")
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    out_path = Path(args.out)

    bulletins = parse_pdf_to_json(pdf_path)

    out_path.write_text(json.dumps(bulletins, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK: {len(bulletins)} objets écrits dans {out_path}")

def main():
    import argparse
    from pathlib import Path
    import json

    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", help="Chemin du PDF à parser")
    parser.add_argument("--out", default="../data/json/bulletins.json", help="Chemin du JSON de sortie")
    args = parser.parse_args()

    pdf_path = Path(args.pdf).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()

    print("PDF utilisé :", pdf_path)
    print("JSON sortie :", out_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF introuvable: {pdf_path}")

    # créer dossier si besoin
    out_path.parent.mkdir(parents=True, exist_ok=True)

    bulletins = parse_pdf_to_json(pdf_path)

    # écrire le json
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(bulletins, f, ensure_ascii=False, indent=2)

    print(f"OK -> {out_path} ({len(bulletins)} bulletins)")


if __name__ == "__main__":
    main()
