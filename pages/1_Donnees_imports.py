import streamlit as st
from sig_utils import (
    lire_fichier_fec,
    controle_coherence,
    fmt,
)

if "data_par_an" not in st.session_state:
    st.session_state["data_par_an"] = {}

st.title("Données entreprise & imports")

st.header("Informations sur l'entreprise")
col1, col2 = st.columns(2)
with col1:
    nom = st.text_input("Nom de l'entreprise")
    adresse = st.text_input("Adresse")
with col2:
    telephone = st.text_input("Téléphone")
    email = st.text_input("Email")

st.markdown("---")
st.subheader("Imports FEC / balances")

col_fec1, col_fec2, col_fec3 = st.columns(3)
with col_fec1:
    fec_N = st.file_uploader("FEC / balance – Année N", type=["csv", "txt", "xlsx", "xls"], key="fec_N")
with col_fec2:
    fec_N1 = st.file_uploader("FEC / balance – Année N-1", type=["csv", "txt", "xlsx", "xls"], key="fec_N1")
with col_fec3:
    fec_N2 = st.file_uploader("FEC / balance – Année N-2", type=["csv", "txt", "xlsx", "xls"], key="fec_N2")

data_par_an = st.session_state["data_par_an"]


def charger(label, fichier, annee):
    if fichier is None:
        st.info(f"{label} {annee} : aucun fichier importé.")
        return
    df = lire_fichier_fec(fichier)
    if df is not None:
        data_par_an[annee] = df
        st.success(f"{label} {annee} importé ({len(df)} lignes).")


colN, colN1, colN2 = st.columns(3)
with colN:
    charger("Fichier", fec_N, "N")
with colN1:
    charger("Fichier", fec_N1, "N-1")
with colN2:
    charger("Fichier", fec_N2, "N-2")

st.session_state["data_par_an"] = data_par_an

st.markdown("---")
st.subheader("Contrôle de cohérence (classes 6-7 vs 1-5)")

for annee in ["N", "N-1", "N-2"]:
    if annee in data_par_an:
        df = data_par_an[annee]
        ecart = controle_coherence(df)
        if ecart is None:
            st.warning(f"Exercice {annee} : format non reconnu pour le contrôle.")
        else:
            if abs(ecart) < 1e-2:
                st.success(f"Exercice {annee} : balance cohérente (écart ≈ 0 €).")
            else:
                st.error(f"Exercice {annee} : écart 6-7 vs 1-5 = {fmt(ecart)}.")
    else:
        st.info(f"Exercice {annee} : aucun fichier chargé.")
