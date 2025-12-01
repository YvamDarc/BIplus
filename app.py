import streamlit as st
import requests
import json

def rechercher_info_siren(siren):

    url = "https://api-siret-verification.p.rapidapi.com/api/v1/verify/siren"

    payload = {
        "siren": siren,
        "include_company_data": True
    }

    headers = {
        "x-rapidapi-key": "TA_CLE_RAPIDAPI_ICI",   # <-- remplace
        "x-rapidapi-host": "api-siret-verification.p.rapidapi.com",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(payload),
            timeout=10
        )

        response.raise_for_status()
        data = response.json()

        # Inspecte la structure
        if "company" not in data:
            return None, "Aucune donnée entreprise."

        company = data["company"]

        info = {
            "siren": siren,
            "nom_entreprise": company.get("name", "Nom inconnu"),
            "adresse": company.get("address", "Adresse inconnue"),
            "ville_cp": f"{company.get('postal_code','')} {company.get('city','')}",
            "dirigeant": company.get("representative", "Dirigeant non fourni")
        }

        return info, "OK"

    except Exception as e:
        return None, f"Erreur API RapidAPI SIREN : {e}"
