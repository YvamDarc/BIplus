import streamlit as st

st.set_page_config(page_title="BI+ FEC & SIG", layout="wide")

st.title("BI+ – Tableau de bord FEC & SIG")

st.markdown("""
Bienvenue dans votre application d'analyse à partir du **FEC**.

Utilisez le menu de gauche pour naviguer :

- **Données & imports** : renseigner l'entreprise, importer les FEC / balances, contrôle de cohérence.
- **Analyse SIG** : visualiser les soldes intermédiaires de gestion (N / N-1) et le détail par poste.

Les données importées sont partagées entre les pages via la session Streamlit.
""")

st.info("👉 Rendez-vous dans la page **Données & imports** pour commencer.")
