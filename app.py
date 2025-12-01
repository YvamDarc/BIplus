import streamlit as st

st.set_page_config(page_title="BI+ FEC & SIG", layout="wide")

# --------- MENU LATERAL (VOLET GAUCHE) ---------
with st.sidebar:
    st.title("BI+")

    st.page_link("app.py", label="🏠 Accueil")
    st.page_link("pages/1_Donnees_imports.py", label="📥 Données & imports")
    st.page_link("pages/2_Analyse_SIG.py", label="📊 Analyse SIG")

# --------- CONTENU PAGE D'ACCUEIL ---------
st.title("BI+ – Tableau de bord FEC & SIG")

st.markdown("""
Bienvenue dans votre application d'analyse à partir du **FEC**.

Utilisez le menu de gauche pour naviguer :

- **📥 Données & imports** : renseigner l'entreprise, importer les FEC / balances, contrôle de cohérence.
- **📊 Analyse SIG** : visualiser les soldes intermédiaires de gestion (N / N-1) et le détail par poste.

Les données importées sont partagées entre les pages via la session Streamlit.
""")

st.info("👉 Commencez par la page **Données & imports** dans le menu de gauche.")
