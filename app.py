import streamlit as st
import os

st.set_page_config(page_title="BI+ FEC & SIG", layout="wide")

# -----------------------------
# Sidebar (barre verticale)
# -----------------------------
st.sidebar.title("📊 BI+ – Navigation")

page = st.sidebar.radio(
    "Sélectionner une page :",
    ["Accueil", "Données & imports", "Analyse SIG"]
)

# -----------------------------
# ROUTEUR DE PAGES
# -----------------------------

if page == "Accueil":
    st.title("BI+ – Tableau de bord FEC & SIG")

    st.markdown("""
    Bienvenue dans votre application d'analyse comptable basée sur le **FEC**.

    Utilisez le menu vertical à gauche pour accéder aux pages :
    - 📥 Données & imports  
    - 📊 Analyse SIG  
    """)

    st.info("👉 Choisissez une page dans la barre latérale à gauche.")

else:
    # Fichiers des sous-pages
    page_files = {
        "Données & imports": "pages/Donnees_imports.py",
        "Analyse SIG": "pages/Analyse_SIG.py"
    }

    page_path = page_files[page]

    # Charge et exécute le fichier Python de la page sélectionnée
    with open(page_path, "r", encoding="utf-8") as f:
        code = f.read()
        exec(code, globals())
