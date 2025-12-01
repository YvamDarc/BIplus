import streamlit as st
import requests
import pandas as pd  # tu l'utiliseras plus tard pour le FEC

# --- CONFIG PAGE ---
st.set_page_config(page_title="BI+ – Analyse FEC & SIG", layout="centered")


# ===============================
# 1. FONCTION APPEL API SIRENE
# ===============================

API_SIRENE_ENTREPRISE = "https://entreprise.data.gouv.fr/api/sirene/v3/unites_legales/"

def rechercher_info_siren(siren: str):
    """
    Interroge l'API Sirene officielle pour récupérer les infos de l'unité légale.
    Accepte SIREN (9) ou SIRET (14) et tronque à 9 chiffres si besoin.
    Retourne (dict_info, "OK") ou (None, message_erreur).
    """
    if not siren:
        return None, "Veuillez saisir un SIREN ou SIRET."

    siren = siren.strip()

    # Si SIRET => on garde les 9 premiers chiffres
    if len(siren) == 14 and siren.isdigit():
        siren = siren[:9]

    # Vérification format SIREN
    if len(siren) != 9 or not siren.isdigit():
        return None, "Format SIREN invalide (doit être 9 chiffres, ou SIRET 14 chiffres)."

    url = API_SIRENE_ENTREPRISE + siren

    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 404:
            return None, "SIREN non trouvé dans la base Sirene."
        r.raise_for_status()
        data = r.json()

        unite = data.get("unite_legale", {})

        # Nom de l'entreprise (plusieurs possibilités selon le type)
        nom_entreprise = (
            unite.get("denomination")
            or unite.get("denomination_usuelle_1")
            or unite.get("denomination_usuelle_2")
            or unite.get("denomination_usuelle_3")
            or "Nom inconnu"
        )

        # Dirigeant : l'API Sirene ne donne pas toujours le dirigeant.
        # On utilise nom/prénom si personne physique, sinon fallback.
        prenom = unite.get("prenom_usuel") or ""
        nom = unite.get("nom_usage") or unite.get("nom") or ""
        dirigeant = (prenom + " " + nom).strip() or "Dirigeant non disponible via l'API"

        # Adresse : dans periodes_unite_legale
        periodes = unite.get("periodes_unite_legale", [])
        adresse = ""
        ville_cp = ""

        if periodes:
            derniere = periodes[0]  # généralement la plus récente
            voie = derniere.get("libelle_voie") or ""
            num_voie = derniere.get("numero_voie") or ""
            cp = derniere.get("code_postal") or ""
            commune = derniere.get("libelle_commune") or ""

            adresse = f"{num_voie} {voie}".strip()
            ville_cp = f"{cp} {commune}".strip()

        info = {
            "siren": siren,
            "nom_entreprise": nom_entreprise,
            "dirigeant": dirigeant,
            "adresse": adresse or "Adresse inconnue",
            "ville_cp": ville_cp or "",
        }
        return info, "OK"

    except requests.exceptions.HTTPError as e:
        return None, f"Erreur HTTP {e.response.status_code} lors de l'appel à l'API Sirene."
    except requests.exceptions.RequestException:
        return None, "Erreur de connexion à l'API Sirene. Vérifiez votre réseau."
    except Exception as e:
        return None, f"Erreur inattendue lors de la lecture des données Sirene : {e}"


# ===============================
# 2. PAGE D’ACCUEIL / COVER PAGE
# ===============================

def cover_page():

    # --- Initialisation des infos entreprise dans la session ---
    if "info_entreprise" not in st.session_state:
        st.session_state["info_entreprise"] = {
            "siren": "",
            "nom_entreprise": "NOM À DÉFINIR",
            "dirigeant": "DIRIGEANT À DÉFINIR",
            "adresse": "",
            "ville_cp": "",
            "adresse_complete": "",
        }

    # ========== SIDEBAR : RECHERCHE SIREN ==========
    st.sidebar.header("🔍 Infos Entreprise via SIREN")

    siren_input = st.sidebar.text_input(
        "SIREN (9) ou SIRET (14)",
        value=st.session_state["info_entreprise"]["siren"],
        max_chars=14,
    )

    if st.sidebar.button("Rechercher dans Sirene (data.gouv)"):
        with st.spinner("Recherche en cours dans l'API Sirene..."):
            info, statut = rechercher_info_siren(siren_input)

        if statut == "OK":
            st.session_state["info_entreprise"].update(info)
            st.session_state["info_entreprise"]["adresse_complete"] = (
                f"{info['adresse']} {info['ville_cp']}".strip()
            )
            st.sidebar.success(
                f"Entreprise trouvée : {info['nom_entreprise']} (SIREN {info['siren']})"
            )
        else:
            st.sidebar.error(statut)

    # ========== CONTENU PRINCIPAL ==========
    st.title("📘 Bienvenue dans l'application BI+ FEC & SIG")

    nom_affiche = st.session_state["info_entreprise"]["nom_entreprise"]
    dirigeant_affiche = st.session_state["info_entreprise"]["dirigeant"]

    st.markdown(f"## 💼 Société : **{nom_affiche}**")
    st.markdown(f"### 👤 Interlocuteur / Dirigeant : **{dirigeant_affiche}**")

    st.subheader("Informations de l'entreprise (modifiables)")

    with st.form("form_entreprise", clear_on_submit=False):
        st.session_state["info_entreprise"]["nom_entreprise"] = st.text_input(
            "Nom de l'entreprise :",
            value=st.session_state["info_entreprise"]["nom_entreprise"],
        )

        st.session_state["info_entreprise"]["dirigeant"] = st.text_input(
            "Nom du dirigeant :",
            value=st.session_state["info_entreprise"]["dirigeant"],
        )

        st.session_state["info_entreprise"]["adresse_complete"] = st.text_area(
            "Adresse complète :",
            value=st.session_state["info_entreprise"]["adresse_complete"],
        )

        submitted = st.form_submit_button("💾 Sauvegarder en session")
        if submitted:
            st.success("Informations de l'entreprise mises à jour (en mémoire).")

    st.markdown("---")
    st.markdown(
        """
        Cette application vous permet d'analyser vos données comptables à partir du **Fichier des Écritures Comptables (FEC)**  
        et de générer automatiquement les **Soldes Intermédiaires de Gestion (SIG)**, avec détail par poste.

        ### 🌟 Fonctionnalités :
        - Import des fichiers **FEC** et balances N / N-1 / N-2  
        - Contrôle automatique de cohérence des classes 1–5 vs 6–7  
        - Calcul des principaux **soldes intermédiaires de gestion**  
        - Détail cliquable par poste (charges externes, impôts & taxes, personnel, etc.)  

        👉 Utilisez le **menu à gauche** (Pages) pour accéder aux autres écrans de l’application.
        """
    )

    st.markdown("### 📥 Importer les Fichiers Comptables (raccourci)")
    col_n, col_n1 = st.columns(2)
    with col_n:
        fichier_n = st.file_uploader("FEC Année N", type=["txt", "csv"], key="fecN_cover")
    with col_n1:
        fichier_n1 = st.file_uploader(
            "FEC Année N-1 (optionnel)", type=["txt", "csv"], key="fecN1_cover"
        )
    st.caption("⚠️ L'import “officiel” pour l'analyse se fera dans la page *Données & imports*.")


# Appel direct de la cover page (Streamlit exécute le script de haut en bas)
cover_page()
