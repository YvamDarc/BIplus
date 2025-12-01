import streamlit as st
import requests
import json

# --------------------------------------------------------
# CONFIGURATION DE LA PAGE
# --------------------------------------------------------
st.set_page_config(page_title="BI+ – Analyse FEC & SIG", layout="centered")

# --------------------------------------------------------
# FONCTION API : RAPIDAPI – SIREN VERIFICATION
# --------------------------------------------------------

def rechercher_info_siren(siren: str):
    """
    Appelle l'API RapidAPI / verify_siren pour récupérer :
    - nom entreprise
    - adresse
    - CP / ville
    - dirigeant (si dispo)
    """

    url = "https://api-siret-verification.p.rapidapi.com/api/v1/verify/siren"

    # Sécurisation
    siren = siren.strip()
    if len(siren) == 14 and siren.isdigit():
        siren = siren[:9]
    if not siren.isdigit() or len(siren) != 9:
        return None, "Format SIREN invalide."

    payload = {
        "siren": siren,
        "include_company_data": True
    }

    headers = {
        "x-rapidapi-key": "TA_CLE_RAPIDAPI_ICI",   # <-- À REMPLACER
        "x-rapidapi-host": "api-siret-verification.p.rapidapi.com",
        "Content-Type": "application/json"
    }

    try:
        r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
        r.raise_for_status()
        data = r.json()

        if "company" not in data:
            return None, "Aucune donnée entreprise trouvée."

        company = data["company"]

        info = {
            "siren": siren,
            "nom_entreprise": company.get("name", "Nom inconnu"),
            "adresse": company.get("address", "Adresse inconnue"),
            "ville_cp": f"{company.get('postal_code', '')} {company.get('city', '')}",
            "dirigeant": company.get("representative", "Dirigeant non fourni")
        }

        return info, "OK"

    except Exception as e:
        return None, f"Erreur API : {e}"


# --------------------------------------------------------
# PAGE PRINCIPALE – COVER PAGE
# --------------------------------------------------------

def cover_page():

    # Initialisation session
    if "info_entreprise" not in st.session_state:
        st.session_state["info_entreprise"] = {
            "siren": "",
            "nom_entreprise": "NOM À DÉFINIR",
            "dirigeant": "À définir",
            "adresse_complete": "",
            "ville_cp": ""
        }

    # ================== SIDEBAR ==================
    st.sidebar.header("🔍 Recherche SIREN (via RapidAPI)")

    siren_input = st.sidebar.text_input(
        "SIREN (9 chiffres) ou SIRET (14)",
        value=st.session_state["info_entreprise"]["siren"],
        max_chars=14
    )

    if st.sidebar.button("Rechercher"):
        with st.spinner("Recherche en cours…"):
            info, statut = rechercher_info_siren(siren_input)

        if statut == "OK":
            st.session_state["info_entreprise"].update(info)
            st.session_state["info_entreprise"]["adresse_complete"] = (
                f"{info['adresse']} {info['ville_cp']}".strip()
            )
            st.sidebar.success("Informations récupérées avec succès !")
        else:
            st.sidebar.error(statut)

    # ================== CONTENU PRINCIPAL ==================

    st.title("📘 Bienvenue dans l'application BI+ FEC & SIG")

    nom = st.session_state["info_entreprise"]["nom_entreprise"]
    dirigeant = st.session_state["info_entreprise"]["dirigeant"]

    st.markdown(f"## 💼 Société : **{nom}**")
    st.markdown(f"### 👤 Dirigeant / Contact : **{dirigeant}**")

    st.subheader("Modifier les informations (si besoin)")

    with st.form("form_infos"):
        st.session_state["info_entreprise"]["nom_entreprise"] = st.text_input(
            "Nom de l'entreprise :",
            value=st.session_state["info_entreprise"]["nom_entreprise"]
        )

        st.session_state["info_entreprise"]["dirigeant"] = st.text_input(
            "Dirigeant :",
            value=st.session_state["info_entreprise"]["dirigeant"]
        )

        st.session_state["info_entreprise"]["adresse_complete"] = st.text_area(
            "Adresse complète :",
            value=st.session_state["info_entreprise"]["adresse_complete"]
        )

        if st.form_submit_button("💾 Sauvegarder"):
            st.success("Modifications enregistrées.")

    st.markdown("---")

    st.markdown("""
    ### 📊 Fonctionnalités BI+
    - Import FEC (N, N-1, N-2)
    - Contrôle classes comptables
    - Calcul complet du **SIG**
    - Détails interactifs par poste
    - Navigation via le menu **Pages** à gauche
    """)

# --------------------------------------------------------
# Lancement
# --------------------------------------------------------

cover_page()
