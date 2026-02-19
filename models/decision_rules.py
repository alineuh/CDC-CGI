"""
decision_rules.py — Module d'analyse et vérification des bulletins de salaire.
Peut être importé par main.py ou exécuté en CLI.
"""

import json
from typing import Any

# ---------------------------------------------------------------------------
# 1. CONSTANTES DE RÉFÉRENCE 2026
# ---------------------------------------------------------------------------
SMIC_REF_DEFAULT   = 1823.03
PLAFOND_SS_DEFAULT = 4005.00

# ---------------------------------------------------------------------------
# 2. FONCTIONS DE CALCUL
# ---------------------------------------------------------------------------

def calcul_rgdu_2026(brut: float, smic: float) -> float:
    """Calcule la réduction générale (Fillon/RGDU) pour 2026."""
    if brut <= 0:
        return 0.0
    ratio = 0.5 * ((3 * smic / brut) - 1)
    ratio = max(0.0, ratio)
    coef  = 0.02 + 0.3821 * (ratio ** 1.75)
    coef  = round(coef, 4)
    return round(brut * coef, 2)


# ---------------------------------------------------------------------------
# 3. EXTRACTION SÉCURISÉE DEPUIS UN BULLETIN JSON
#    Compatible ancien format (lignes / intitule) ET nouveau (rows / libelle)
# ---------------------------------------------------------------------------

NOMS_BRUT    = ["Brut soumis à cotisation"]
NOMS_PLAFOND = ["Sécurité Sociale plafonnée", "Cotisation Vieillesse tranche A"]
NOMS_RGDU    = [
    "EXONERATIONS, ECRETEMENTS ET ALLEGEMENTS DE COTISATIONS",
    "Allégement RGDU",
    "Réduction générale",
]


def _extract_fields(bulletin: dict):
    """
    Parcourt les lignes d'un bulletin et retourne (brut, base_plafond, val_rgdu).
    Compatible ancien format (lignes / intitule) et nouveau format (rows / libelle).
    """
    brut         = 0.0
    base_plafond = 0.0
    val_rgdu     = 0.0

    table = bulletin.get("table", {})

    # Support des deux formats de clé
    lignes = table.get("lignes") or table.get("rows") or []

    for ligne in lignes:
        # Récupération du nom de ligne selon le format
        intitule = ligne.get("intitule")
        libelle  = ligne.get("libelle")
        numero   = ligne.get("numero")
        nom      = intitule or libelle or ""

        # Champs salarie/employeur (ancien format)
        salarie   = ligne.get("salarie", {}) or {}
        employeur = ligne.get("employeur", {}) or {}

        # --- BRUT ---
        if nom in NOMS_BRUT or numero == "10000":
            brut = (
                salarie.get("montant")
                or ligne.get("montant")
                or ligne.get("base")
                or 0.0
            )

        # --- PLAFOND SS ---
        if nom in NOMS_PLAFOND:
            base_plafond = (
                salarie.get("base")
                or ligne.get("base")
                or 0.0
            )

        # --- RGDU ---
        if nom in NOMS_RGDU:
            val_rgdu = (
                salarie.get("montant")
                or ligne.get("montant")
                or ligne.get("montant_patronal")
                or employeur.get("montant")
                or 0.0
            )

    return float(brut), float(base_plafond), float(val_rgdu)


# ---------------------------------------------------------------------------
# 4. FONCTION PRINCIPALE
# ---------------------------------------------------------------------------

def analyze_bulletin(
    bulletin: dict,
    smic_ref: float    = SMIC_REF_DEFAULT,
    plafond_ref: float = PLAFOND_SS_DEFAULT,
):
    """
    Analyse un bulletin et retourne une liste de résultats :
      [[ intitule, statut, valeur_extraite, valeur_attendue ], ...]
    statut : "OK" | "KO"
    """
    brut, base_plafond, val_rgdu = _extract_fields(bulletin)

    if not brut or brut <= 0:
        return [["ERREUR", "KO", 0, "Brut non trouvé — vérifiez l'arborescence du JSON."]]

    output = []

    # Plafond SS
    val_reelle_plafond = min(brut, plafond_ref)
    etat_p = "OK" if abs(base_plafond - val_reelle_plafond) < 0.01 else "KO"
    output.append(["Plafond SS (Base T1)", etat_p, base_plafond, val_reelle_plafond])

    # RGDU
    val_reelle_rgdu = calcul_rgdu_2026(brut, smic_ref)
    etat_r = "OK" if abs(abs(val_rgdu) - abs(val_reelle_rgdu)) < 1.0 else "KO"
    output.append(["Allégement RGDU", etat_r, val_rgdu, val_reelle_rgdu])

    return output


def analyze_all_bulletins(
    bulletins: list,
    smic_ref: float    = SMIC_REF_DEFAULT,
    plafond_ref: float = PLAFOND_SS_DEFAULT,
):
    """Analyse une liste de bulletins et retourne une liste enrichie avec les checks."""
    results = []
    for i, bulletin in enumerate(bulletins):
        if "unmatched_pages" in bulletin:
            continue
        checks     = analyze_bulletin(bulletin, smic_ref=smic_ref, plafond_ref=plafond_ref)
        has_errors = any(row[1] == "KO" for row in checks)
        results.append({
            "bulletin_index": i,
            "header":         bulletin.get("header", {}),
            "checks":         checks,
            "has_errors":     has_errors,
            "smic_used":      smic_ref,
            "plafond_used":   plafond_ref,
        })
    return results


# ---------------------------------------------------------------------------
# 5. CLI (usage manuel)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Analyse un fichier bulletins.json")
    parser.add_argument("json_path", help="Chemin vers bulletins.json (ex: data/json/bulletins_eval.json)")
    parser.add_argument("--index",   type=int,   default=0,                 help="Index du bulletin à analyser")
    parser.add_argument("--smic",    type=float, default=SMIC_REF_DEFAULT,  help="SMIC de référence")
    parser.add_argument("--plafond", type=float, default=PLAFOND_SS_DEFAULT, help="Plafond SS de référence")
    args = parser.parse_args()

    with open(args.json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    bulletins = data if isinstance(data, list) else [data]
    result    = analyze_bulletin(bulletins[args.index], smic_ref=args.smic, plafond_ref=args.plafond)
    print(json.dumps(result, ensure_ascii=False, indent=2))
