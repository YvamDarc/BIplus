import streamlit as st
import requests
import pandas as pd # Nécessaire pour l'import

st.set_page_config(page_title="BI+ – Analyse FEC & SIG", layout="centered")

# --- 1. FONCTION DE RECHERCHE D'API (Réutilisée) ---

# URL de l'API Sirene Open Data pour l'exemple
API_URL = "https://public.opendatasoft.com/api/records/1.0/search/"

def rechercher_info_siret(siren):
    """
    Interroge l'API pour récupérer les informations de l'entreprise.
    Note : L'API peut accepter SIREN (9 chiffres) ou SIRET (14 chiffres).
    """
    
    # Si l'utilisateur tape un SIRET (14), on le coupe en SIREN (9)
    if len(siren) == 14:
        siren = siren[:9]
        
    if len(siren) != 9 or not siren.isdigit():
        return None, "Format SIREN invalide."

    params = {
        "dataset": "sirene_v3",
        "q": f"siren:{siren}",
        "rows": 1
    }
    
    try:
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data and data['nhits'] > 0:
            record = data['records'][0]['fields']
            
            # Extraction des champs (peut nécessiter un ajustement selon l'API)
            nom_entreprise = record.get('denomination') or record.get('nom_usage')
            dirigeant = record.get('prenom_usuel') + " " + record.get('nom_usage') if record.get('prenom_usuel') else "Non spécifié"
            
            # Stockage des données pour l'édition
            return {
                "siren": siren,
                "nom_entreprise": nom_entreprise,
                "dirigeant": dirigeant,
                "adresse": record.get('adresse_ligne_1'),
                "ville_cp": f"{record.get('code_postal')} {record.get('libelle_commune')}"
            }, "OK"
        else:
            return None, "SIREN non trouvé dans la base de données publique."
            
    except requests.exceptions.RequestException:
        return None, "Erreur de connexion à l'API Sirene."


# --- 2. FONCTION PRINCIPALE DE LA PAGE D'ACCUEIL ---

def cover_page():

    # 1. INITIALISATION DES DONNÉES DE L'ENTREPRISE (si ce n'est pas déjà fait)
    if 'info_entreprise' not in st.session_state:
        st.session_state['info_entreprise'] = {
            "siren": "",
            "nom_entreprise": "NOM À DÉFINIR",
            "dirigeant": "DIRIGEANT À DÉFINIR",
            "adresse": "",
            "ville_cp": ""
        }
    
    # 2. COLONNE DE GESTION DU SIREN
    st.sidebar.header("🔍 Infos Entreprise & SIREN")
    
    # Zone de saisie du SIREN
    siren_input = st.sidebar.text_input(
        "Saisir SIREN (9) ou SIRET (14)",
        value=st.session_state['info_entreprise']['siren'],
        max_chars=14
    )
    
    # Bouton de recherche
    if st.sidebar.button("Rechercher dans Data.gouv"):
        with st.spinner("Recherche en cours..."):
            info, statut = rechercher_info_siret(siren_input.strip())
            
            if statut == "OK":
                st.session_state['info_entreprise'] = info
                st.sidebar.success("Informations de l'entreprise trouvées et chargées.")
            else:
                st.sidebar.error(statut)


    # 3. AFFICHAGE ET MODIFICATION DES DONNÉES (Utilisation d'un formulaire pour l'édition)
    
    st.title("📘 Bienvenue dans l'application BI+ FEC & SIG")
    
    # Formulaire de modification
    with st.form("formulaire_edition_info", clear_on_submit=False):
        st.subheader("Informations de l'entreprise (Modifiables)")
        
        # Champ Nom de l'entreprise (modificable)
        st.session_state['info_entreprise']['nom_entreprise'] = st.text_input(
            "Nom de l'entreprise :", 
            value=st.session_state['info_entreprise']['nom_entreprise']
        )
        
        # Champ Dirigeant (modificable)
        st.session_state['info_entreprise']['dirigeant'] = st.text_input(
            "Nom du Dirigeant :", 
            value=st.session_state['info_entreprise']['dirigeant']
        )
        
        # Affichage du SIREN (non modifiable ici, mais peut être stocké)
        st.info(f"SIREN actuel : **{st.session_state['info_entreprise']['siren'] or 'Non défini'}**")
        
        # Bouton de soumission du formulaire d'édition
        if st.form_submit_button("Sauvegarder les modifications"):
            st.success("Informations de l'entreprise mises à jour en session.")

    # Affichage personnalisé dans le contenu principal
    nom_affichee = st.session_state['info_entreprise']['nom_entreprise']
    dirigeant_affiche = st.session_state['info_entreprise']['dirigeant']
    
    st.markdown(f"## 💼 Société : **{nom_affichee}**")
    st.markdown(f"### 👋 Bonjour, **{dirigeant_affiche}**")

    # Résumé et fonctionnalités
    st.markdown(
        """
        ---
        Cette application vous permet d'analyser vos données comptables à partir du **Fichier des Écritures Comptables (FEC)**.
        
        ### 🌟 Fonctionnalités :
        - Import des fichiers FEC et balances N / N-1 / N-2  
        - Calcul complet du **SIG** selon les normes du PCG  
        
        👉 Utilisez le **menu à gauche** pour accéder aux fonctionnalités.
        """
    )

if __name__ == "__main__":
    cover_page()
