import streamlit as st

st.set_page_config(page_title="BI+ FEC & SIG", layout="wide")

st.sidebar.title("BI+ – Navigation")

st.sidebar.markdown("""
Les pages disponibles sont dans le menu **Pages** :

- 📥 Données & imports  
- 📊 Analyse SIG  

Si vous ne voyez pas la barre latérale, cliquez sur la flèche en haut à gauche.
""")

st.title("BI+ – Tableau de bord FEC & SIG")

st.markdown("""
Bienvenue dans votre application d'analyse à partir du **FEC**.

👉 Utilisez la **barre latérale** ou le menu **Pages** pour accéder aux fonctionnalités.
""")

st.info("Commencez par importer vos données dans la page **Données & imports**.")
