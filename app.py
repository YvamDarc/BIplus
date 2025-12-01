import streamlit as st
import requests
import pandas as pd
import time # Import ajouté pour simuler un chargement plus long

# --- Configuration de la Page ---
st.set_page_config(page_title="BI+ – Analyse FEC & SIG", layout="centered")

# --- 1. FONCTION DE RECHERCHE D'API SIRENE ---

# URL de l'API Sirene Open Data
API_URL = "https://public.opendatasoft.com/api/records/1.0/search/"

def rechercher_info_siren(siren):
    """
    Interroge l'API pour récupérer les informations de l'entreprise (Nom, Dirigeant, Adresse).
    """
    
    # Normalisation du SIREN
    if len(siren) == 14:
        siren = siren[:9]
        
    if len(siren) != 9 or not siren.isdigit():
        return None, "Format SIREN invalide (doit être 9 chiffres)."

    params = {
        "dataset": "sirene_v3",
        "q": f"siren:{siren}",
        "rows": 1
    }
    
    # Simulation d'un délai pour bien voir le spinner fonctionner
    time.sleep(1.5) 

    try:
        response = requests.get(API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data and data['nhits'] > 0:
            record = data['records'][0]['fields']
            
            # Extraction des champs
            nom_entreprise = record.get('denomination') or record.get('nom_usage')
            
            prenom = record.get('prenom_usuel', '')
            nom = record.get('nom_usage', '')
            dirigeant = f"{prenom} {nom}".strip() or "Non spécifié"

            adresse = record.get('adresse_ligne_1')
            ville_cp = f"{record.get('code_postal')} {record.get('libelle_commune')}"
            
            return {
                "siren": siren,
                "nom_entreprise": nom_entreprise or "Nom inconnu",
                "dirigeant": dirigeant,
                "adresse": adresse or "Adresse inconnue",
                "ville_cp": ville_cp or ""
            }, "OK"
        else:
            return None, "SIREN non trouvé dans la base de données publique."
            
    except requests.exceptions.HTTPError as e:
        return None, f"Erreur HTTP: {e.response.status_code}. Problème côté API."
    except requests.exceptions.RequestException:
        return None, "Erreur de connexion à l'API Sirene. Vérifiez votre réseau."


# --- 2. FONCTION PRINCIPALE DE LA PAGE D'ACCUEIL ---

def cover_page():

    # 1. INITIALISATION DES DONNÉES DE L'ENTREPRISE (Session State)
    if 'info_entreprise' not in st.session_state:
        st.session_state['info_entreprise'] = {
            "siren": "",
            "nom_entreprise": "NOM À DÉFINIR",
            "dirigeant": "DIRIGEANT À DÉFINIR",
            "adresse": "",
            "ville_cp": ""
        }
    
    # 2. COLONNE LATÉRALE : RECHERCHE SIREN
    st.sidebar.header("🔍 Infos Entreprise & SIREN")
    
    siren_input = st.sidebar.text_input(
        "Saisir SIREN (9) ou SIRET (14)",
        value=st.session_state['info_entreprise']['siren'],
        max_chars=14,
        key="siren_key"
    )
    
    # Bouton de recherche
    if st.sidebar.button("Rechercher dans Data.gouv"):
        # --- CORRECTION DE L'ERREUR ICI : st.spinner au lieu de st.sidebar.spinner ---
        with st.spinner("Recherche en cours..."): 
            info, statut = rechercher_info_siren(siren_input.strip())
            
            if statut == "OK":
                st.session_state['info_entreprise'] = info
                st.sidebar.success("Informations de l'entreprise trouvées et chargées.")
            else:
                st.sidebar.error(statut)

    # 3. CONTENU PRINCIPAL : TITRE ET ÉDITION DES DONNÉES
    
    st.title("📘 Bienvenue dans l'application BI+ FEC & SIG")
    
    # Affichage personnalisé après la recherche/l'édition
    nom_affichee = st.session_state['info_entreprise']['nom_entreprise']
    dirigeant_affiche = st.session_state['info_entreprise']['dirigeant']
    
    st.markdown(f"## 💼 Société : **{nom_affichee}**")
    st.markdown(f"### 👋 Utilisateur (Dirigeant) : **{dirigeant_affiche}**")

    st.subheader("Informations de l'entreprise (Modifiables si API incorrecte)")
    
    # Utilisation d'un formulaire pour regrouper les champs d'édition
    with st.form("formulaire_edition_info", clear_on_submit=False):
        
        # Le contenu du st.session_state est mis à jour directement via les keys
        st.session_state['info_entreprise']['nom_entreprise'] = st.text_input(
            "Nom de l'entreprise :", 
            value=st.session_state['info_entreprise']['nom_entreprise'],
            key="edit_nom"
        )
        
        st.session_state['info_entreprise']['dirigeant'] = st.text_input(
            "Nom du Dirigeant :", 
            value=st.session_state['info_entreprise']['dirigeant'],
            key="edit_dirigeant"
        )
        
        # On affiche l'adresse et le CP dans un seul champ d'édition
        adresse_complete = f"{st.session_state['info_entreprise']['adresse']} {st.session_state['info_entreprise']['ville_cp']}".strip()
        st.session_state['info_entreprise']['adresse_complete'] = st.text_area(
            "Adresse complète :", 
            value=adresse_complete,
            key="edit_adresse"
        )
        
        # Bouton de soumission du formulaire d'édition
        if st.form_submit_button("Sauvegarder les modifications"):
            st.success("Informations de l'entreprise mises à jour en session.")

    # 4. Bloc d'information et d'import
    st.markdown("---")
    st.markdown(
        """
        Cette application vous permet d'analyser vos données comptables à partir du **Fichier des Écritures Comptables (FEC)**.
        
        ### 🌟 Fonctionnalités :
        - Import des fichiers **FEC** et balances N / N-1 / N-2  
        - Contrôle automatique de cohérence comptable  
        - Calcul complet du **SIG** selon les normes du PCG  
        - Détail cliquable par poste (charges externes, impôts, etc.)  
        
        👉 Utilisez le **menu à gauche** pour accéder aux fonctionnalités.
        """
    )
    
    # Zone d'import de fichiers FEC (non implémentée ici, juste l'interface)
    st.markdown("### 📥 Importer les Fichiers Comptables")
    fichier_n = st.file_uploader("Importer le FEC Année N", type=['txt', 'csv'])
    fichier_n_1 = st.fileploader("Importer le FEC Année N-1 (Optionnel)", type=['txt', 'csv'])


if __name__ == "__main__":
    cover_page()
