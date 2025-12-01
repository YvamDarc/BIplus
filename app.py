import streamlit as st

st.set_page_config(page_title="BI+ FEC & SIG", layout="wide")

st.title("BI+ – Tableau de bord FEC & SIG")
st.markdown("""
Bienvenue dans votre application d'analyse comptable basée sur le **FEC**.

Choisissez ce que vous souhaitez faire :
""")

st.write("### 🚀 Navigation")

col1, col2 = st.columns(2)

with col1:
    if st.button("📥 Aller aux données & imports"):
        st.switch_page("pages/1_Donnees_imports.py")

with col2:
    if st.button("📊 Aller à l'analyse SIG"):
        st.switch_page("pages/2_Analyse_SIG.py")

st.markdown("---")
st.info("Vous pouvez aussi utiliser le menu de navigation dans la barre latérale.")
