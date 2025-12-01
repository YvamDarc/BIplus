import streamlit as st
import requests

# --- CONFIG ---
st.set_page_config(page_title="BI+ – Analyse FEC & SIG", layout="centered")


# =====================================================
#   APPEL API OPEN DATA SOFT 100% COMPATIBLE STREAMLIT
# =====================================================

API_URL = "https://public.opendatasoft.com/api/records/1.0/search/"

def rechercher_info_siren(siren: str):
    """
    Recherche d'informations via OpenDataSoft - dataset 'sirene'
    Compatible Streamlit Cloud.
    """

    if not siren:
        return None, "Veuillez saisir un SIREN ou SIRET."

    siren = siren.strip()

    # SIRET => on garde le SIREN
    if len(siren) == 14 and siren.isdigit():
        siren = siren[:9]

    # Vérification format
    if len(siren) != 9 or not siren.isdigit():
        return None, "Format SIREN invalide."

    params = {
        "dataset": "sirene",         # DATASET FONCTIONNEL !
        "q": f"siren:{siren}",
        "rows": 1
    }

    try:
        r = requests.get(API_URL, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()

        if data.get("nhits", 0) == 0:
            return None, "SIREN introuvable dans le dataset Sirene."

        fields = data["records"][0]["fields"]

        info = {
            "siren": siren,
            "nom_entreprise": fields.get("l1_normalisee")
                                or fields.get("raison_sociale")
                                or "Nom inconnu",
            "dirigeant": "Donnée non disponible dans OpenDataSoft",
            "adresse": fields.get("l4_normalisee", "Adresse inconnue"),
            "ville_cp": f"{fields.get('codpos', '')} {fields.get('libcom', '')}".strip()
        }

        return info, "OK"

    except requests.exceptions.RequestException:
        return None, "Erreur réseau OpenDataSoft."
    except Exception as e:
        return None, f"Erreur inattendue : {e}"


# =====================================================
#   COVER PAGE (HOME) – AVEC SIDEBAR SIREN 
# =====================================================

def cover_page():

    # INITIALISATION
    if "info_entreprise" not in st.session_state:
        st.session_state["info_entreprise"] = {
            "siren": "",
            "nom_entreprise": "NOM À DÉFINIR",
            "dirigeant": "À définir",
            "adresse": "",
            "ville_cp": "",
            "adresse_complete": ""
        }

    # -----------------------
    # SIDEBAR : RECHERCHE SIREN
    # -----------------------
    st.sidebar.header("🔍 Recherche SIREN")

    siren_input = st.sidebar.text_input(
        "SIREN (9) ou SIRET (14)",
        value=st.session_state["info_entreprise"]["siren"],
        max_chars=14
    )

    if st.sidebar.button("Rechercher via OpenDataSoft"):
        with st.spinner("Recherche en cours..."):
            info, statut = rechercher_info_siren(siren_input)

        if statut == "OK":
            st.session_state["info_entreprise"].update(info)
            st.session_state["info_entreprise"]["adresse_complete"] = \
                f"{info['adresse']} {info['ville_cp']}".strip()
            st.sidebar.success(f"Entreprise trouvée : {info['nom_entreprise']}")
        else:
            st.sidebar.error(statut)

    # -----------------------
    # CONTENU PRINCIPAL
    # -----------------------

    st.title("📘 Bienvenue dans l'application BI+ FEC & SIG")

    nom = st.session_state["info_entreprise"]["nom_entreprise"]
    dirigeant = st.session_state["info_entreprise"]["dirigeant"]

    st.markdown(f"## 💼 Société : **{nom}**")
    st.markdown(f"### 👤 Dirigeant / Interlocuteur : **{dirigeant}**")

    st.subheader("Informations modifiables (au besoin)")

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

        if st.form_submit_button("💾 Enregistrer"):
            st.success("Informations enregistrées en session.")

    st.markdown("---")

    st.markdown(
        """
        ### 🎯 Fonctionnalités principales :
        - Import FEC (N / N-1 / N-2)
        - Contrôle des classes comptables
        - Calcul du **SIG complet**
        - Détails par poste (charges externes, taxes, personnel, etc.)

        👉 Utilisez le **menu Pages** à gauche pour naviguer.
        """
    )


# LANCEMENT DE LA PAGE
cover_page()
