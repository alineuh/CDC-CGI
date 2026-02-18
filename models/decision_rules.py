import json

# --- 1. FONCTION DE CALCUL (Collègue) ---
def calcul_rgdu_2026(brut, smic):
    if brut <= 0:
        return 0
    ratio = 0.5 * ((3 * smic / brut) - 1)
    ratio = max(0, ratio)
    coef = 0.02 + 0.3821 * (ratio ** 1.75)
    coef = round(coef, 4) 
    return round(brut * coef, 2)

# --- 2. IMPORT ET PRÉPARATION DES DONNÉES ---
file_path = '/Users/ines/CDC-CGI/data/json/bulletins.json'

with open(file_path, 'r', encoding='utf-8') as f:
    data_import = json.load(f)

bulletin = data_import[3] if isinstance(data_import, list) else data_import

# --- 3. EXTRACTION SÉCURISÉE DEPUIS L'ARBORESCENCE ---
brut_extrait = 0
base_tranche_a = 0
val_extraite_rgdu = 0

noms_plafond = ["Sécurité Sociale plafonnée", "Cotisation Vieillesse tranche A"]
noms_rgdu = ["EXONERATIONS, ECRETEMENTS ET ALLEGEMENTS DE COTISATIONS", "Allégement RGDU"]

if "table" in bulletin and "lignes" in bulletin["table"]:
    for ligne in bulletin["table"]["lignes"]:
        intitule = ligne.get("intitule", "")
        salarie_data = ligne.get("salarie", {})
        
        # A. Extraction du Brut (On va chercher dans salarie -> montant)
        if intitule == "Brut soumis à cotisation" or ligne.get("code") == "10000":
            brut_extrait = salarie_data.get("montant") or ligne.get("base", 0)
            
        # B. Extraction de la Base Plafond SS (On prend la colonne 'base')
        if intitule in noms_plafond:
            base_tranche_a = ligne.get("base") or salarie_data.get("base", 0)
            
        # C. Extraction du Montant RGDU (On va chercher dans salarie -> montant)
        if intitule in noms_rgdu:
            val_extraite_rgdu = salarie_data.get("montant")
            if val_extraite_rgdu is None:
                val_extraite_rgdu = ligne.get("employeur", {}).get("montant", 0)

# Valeurs de référence 2026
smic_ref = 1823.03 
plafond_legal_2026 = 4005.00

# --- 4. GÉNÉRATION DE L'ARRAY UNIQUE ---
output_array = []

if brut_extrait and brut_extrait > 0:
    val_reelle_rgdu = calcul_rgdu_2026(brut_extrait, smic_ref)
    val_reelle_plafond = min(brut_extrait, plafond_legal_2026)

    # Résultat Plafond
    etat_p = "OK" if abs(base_tranche_a - val_reelle_plafond) < 0.01 else "KO"
    output_array.append(["Plafond SS (Base T1)", etat_p, base_tranche_a, val_reelle_plafond])

    # Résultat RGDU
    etat_r = "OK" if abs(abs(val_extraite_rgdu) - abs(val_reelle_rgdu)) < 1 else "KO"
    output_array.append([noms_rgdu[0], etat_r, val_extraite_rgdu, val_reelle_rgdu])
else:
    # Diagnostic si ça échoue encore
    output_array.append(["ERREUR", "KO", 0, "Brut non trouvé. Verifiez l'arborescence du JSON."])

print(output_array)