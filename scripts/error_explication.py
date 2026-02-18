#%%
import requests
import time
from datetime import datetime
TOKEN = "UGkwKgcH0LSeKP6I9T5s70dk1VRWvKoBuuOFdHrRhCWkNkYcJ5mFiX"
CLIENT_ID = "0ba90d68-8f46-441c-b4b6-bb6e79f5bbb7"
CLIENT_SECRET = "654c2b30-25c4-49bf-ba5d-d20b41119c4b"
BASE_URL = "https://sandbox-api.piste.gouv.fr/dila/legifrance/lf-engine-app"




LEGAL_MAPPING = {
    "SMIC": {
        "code": "Code du travail",
        "articles": ["L3231-2", "R3231-1"],
        "keywords": ["SMIC montant mensuel 151,67 heures"]
    },
    "PLAFOND_SS": {
        "code": "Code de la sécurité sociale",
        "articles": ["L241-3"],
        "keywords": ["plafond mensuel sécurité sociale 2026"]
    },
    "EXONERATION": {
        "code": "Code de la sécurité sociale",
        "articles": ["L241-13"],
        "keywords": ["allègement général cotisations patronales réduction Fillon"]
    }
}

def classify_error(error_dict):
    line = error_dict["intitule_ligne"].lower()

    if "smic" in line:
        return "SMIC"
    if "plafond" in line:
        return "PLAFOND_SS"
    if "exoneration" in line or "allègement" in line:
        return "EXONERATION"

    raise ValueError("Type d'erreur non reconnu")

def get_access_token():

    url = "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"

    response = requests.post(
        url,
        auth=(CLIENT_ID, CLIENT_SECRET),
        headers={
            "Content-Type": "application/x-www-form-urlencoded"
        },
        data={
            "grant_type": "client_credentials",
            "scope": "openid"
        }
    )

    print(response.status_code)
    print(response.text)

    response.raise_for_status()

    return response.json()["access_token"]


def search_article(token, code_name, article_number, date_timestamp):

    url = f"{BASE_URL}/search"

    payload = {
        "recherche": {
            "champs": [
                {
                    "typeChamp": "NUM_ARTICLE",
                    "criteres": [
                        {
                            "typeRecherche": "EXACTE",
                            "valeur": article_number,
                            "operateur": "ET"
                        }
                    ],
                    "operateur": "ET"
                }
            ],
            "filtres": [
                {
                    "facette": "NOM_CODE",
                    "valeurs": [code_name]
                },
                {
                    "facette": "DATE_VERSION",
                    "singleDate": date_timestamp
                }
            ],
            "pageNumber": 1,
            "pageSize": 1,
            "operateur": "ET",
            "typePagination": "ARTICLE"
        },
        "fond": "CODE_DATE"
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()

    results = response.json()["results"]

    if not results:
        raise ValueError("Article non trouvé")

    return results[0]["id"]

def get_article(token, article_id):

    url = f"{BASE_URL}/consult/getArticle"

    payload = {
        "id": article_id
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()

    print(response.status_code)
    print(response.text)

    return response.json()

def build_explanation(error_dict, article_data):

    texte_article = article_data["article"]["texte"]
    reference = article_data["article"]["num"]

    return f"""
Une anomalie a été détectée sur la ligne "{error_dict['intitule_ligne']}".

Valeur déclarée : {error_dict['valeur_erreur']} €
Valeur conforme : {error_dict['valeur_corrigee']} €

Conformément à l'article {reference},
le montant doit être calculé selon les dispositions légales en vigueur.

Extrait du texte applicable :
{texte_article[:500]}...

Un écart peut entraîner un risque de redressement URSSAF.
"""


def explain_payroll_error(error_dict, date_fiche):

    token = get_access_token()

    error_type = classify_error(error_dict)
    mapping = LEGAL_MAPPING[error_type]

    date_timestamp = int(datetime.strptime(
        date_fiche, "%Y-%m-%d"
    ).timestamp() * 1000)

    article_id = search_article(
        token,
        mapping["code"],
        mapping["articles"],
        date_timestamp
    )

    article_data = get_article(token, article_id)

    explanation = build_explanation(error_dict, article_data)

    return explanation

#%%

error_dict = {
    "intitule_ligne": "SMIC mensuel brut",
    "intitule_colonne": "Base",
    "valeur_erreur": 1700,
    "valeur_corrigee": 1766.92
}

print(explain_payroll_error(error_dict, "2026-01-01"))

# %%


# %%
