API_SIRENE_ENTREPRISE = "https://entreprise.data.gouv.fr/api/sirene/v3/unites_legales/"

def rechercher_info_siren(siren):
    """
    Interroge l'API Sirene officielle pour récupérer les informations de l'entreprise (Nom, Dirigeant, Adresse).
    Accepte SIREN (9) ou SIRET (14) et tronque en SIREN si besoin.
    """

    # Normalisation : si SIRET (14 chiffres), on tronque les 9 premiers
    siren = siren.strip()
    if len(siren) == 14 and siren.isdigit():
        siren = siren[:9]

    # Vérification du format
    if len(siren) != 9 or not siren.isdigit():
        return None, "Format SIREN invalide (doit être 9 chiffres)."

    url = API_SIRENE_ENTREPRISE + siren

    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 404:
            return None, "SIREN non trouvé dans la base Sirene."
        r.raise_for_status()
        data = r.json()

        unite = data.get("unite_legale", {})

        # Nom de l'entreprise
        nom_entreprise = (
            unite.get("denomination")
            or unite.get("denomination_usuelle_1")
            or unite.get("denomination_usuelle_2")
            or unite.get("denomination_usuelle_3")
            or "Nom inconnu"
        )

        # Dirigeant : la vraie info dirigeant n'est pas directement accessible ici,
        # donc on met un placeholder ou on reconstruit à partir du nom / prénom si personne physique.
        prenom = unite.get("prenom_usuel") or ""
        nom = unite.get("nom_usage") or unite.get("nom") or ""
        dirigeant = (prenom + " " + nom).strip() or "Dirigeant non disponible via l'API"

        # Adresse : les adresses sont dans les périodes
        periodes = unite.get("periodes_unite_legale", [])
        adresse = ""
        ville_cp = ""

        if periodes:
            derniere = periodes[0]  # en général la première est la plus récente
            voie = derniere.get("libelle_voie") or ""
            numero_voie = derniere.get("numero_voie") or ""
            cp = derniere.get("code_postal") or ""
            commune = derniere.get("libelle_commune") or ""

            adresse = f"{numero_voie} {voie}".strip()
            ville_cp = f"{cp} {commune}".strip()

        return {
            "siren": siren,
            "nom_entreprise": nom_entreprise,
            "dirigeant": dirigeant,
            "adresse": adresse or "Adresse inconnue",
            "ville_cp": ville_cp or "",
        }, "OK"

    except requests.exceptions.HTTPError as e:
        return None, f"Erreur HTTP: {e.response.status_code} lors de l'appel à l'API Sirene."
    except requests.exceptions.RequestException:
        return None, "Erreur de connexion à l'API Sirene. Vérifiez votre réseau."
    except Exception as e:
        return None, f"Erreur inattendue lors de la lecture des données Sirene : {e}"
