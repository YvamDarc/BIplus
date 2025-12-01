import streamlit as st

st.set_page_config(page_title="BI+ – Analyse FEC & SIG", layout="centered")

def cover_page():

    # Titre principal
    st.title("📘 Bienvenue dans l'application BI+ FEC & SIG")

    # Résumé
    st.markdown(
        """
        Cette application vous permet d'analyser vos données comptables à partir du **Fichier des Écritures Comptables (FEC)**  
        et de générer automatiquement les **Soldes Intermédiaires de Gestion (SIG)**, avec les détails par poste.

        ### 🌟 Fonctionnalités :
        - Import des fichiers FEC et balances N / N-1 / N-2  
        - Contrôle automatique de cohérence comptable  
        - Calcul complet du **SIG** selon les normes du PCG  
        - Détail cliquable par poste (charges externes, impôts, etc.)  
        - Structure multi-pages propre et professionnelle  

        👉 Utilisez le **menu à gauche** pour accéder aux fonctionnalités.
        """
    )

if __name__ == "__main__":
    cover_page()
