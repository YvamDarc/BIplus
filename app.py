def rechercher_info_siren(siren):
    url = "https://public.opendatasoft.com/api/records/1.0/search/"
    params = {
        "dataset": "sirene",
        "q": f"siren:{siren}",
        "rows": 1
    }

    r = requests.get(url, params=params)
    data = r.json()

    if data.get("nhits", 0) == 0:
        return None, "SIREN non trouvé"

    fields = data["records"][0]["fields"]

    info = {
        "siren": siren,
        "nom_entreprise": fields.get("l1_normalisee") or fields.get("raison_sociale") or "Nom inconnu",
        "dirigeant": "Données non fournies",
        "adresse": fields.get("l4_normalisee") or "",
        "ville_cp": f"{fields.get('codpos', '')} {fields.get('libcom', '')}"
    }

    return info, "OK"
