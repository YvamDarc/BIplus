import streamlit as st
import pandas as pd

from sig_utils import (
    lire_fichier_fec,
    controle_coherence,
    preparer_grouped,
    calcul_sig,
    filtre_detail,
    fmt,
)

st.set_page_config(page_title="BI+ FEC & SIG", layout="wide")

# ---------- ÉTAT GLOBAL ----------
if "data_par_an" not in st.session_state:
    st.session_state["data_par_an"] = {}

# ---------- MENU LATERAL ----------
st.sidebar.title("BI+ – Navigation")
page = st.sidebar.radio(
    "Aller à :",
    ["Accueil", "Données & imports", "Analyse SIG"],
)


# ---------- PAGE : ACCUEIL ----------
if page == "Accueil":
    st.title("BI+ – Tableau de bord FEC & SIG")

    st.markdown("""
Bienvenue dans votre application d'analyse à partir du **FEC**.

Utilisez le **menu de gauche** pour naviguer :

- **Données & imports** : renseigner l'entreprise, importer les FEC / balances, contrôler la cohérence.
- **Analyse SIG** : visualiser les soldes intermédiaires de gestion (N / N-1) avec le détail par poste.
    """)

    st.info("👉 Commence par **Données & imports** dans le menu à gauche.")


# ---------- PAGE : DONNÉES & IMPORTS ----------
elif page == "Données & imports":
    st.title("Données entreprise & imports")

    # --- Infos entreprise ---
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
        fec_N = st.file_uploader(
            "FEC / balance – Année N", type=["csv", "txt", "xlsx", "xls"], key="fec_N"
        )
    with col_fec2:
        fec_N1 = st.file_uploader(
            "FEC / balance – Année N-1", type=["csv", "txt", "xlsx", "xls"], key="fec_N1"
        )
    with col_fec3:
        fec_N2 = st.file_uploader(
            "FEC / balance – Année N-2", type=["csv", "txt", "xlsx", "xls"], key="fec_N2"
        )

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
    st.subheader("Contrôle de cohérence (classes 6–7 vs 1–5)")

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
                    st.error(f"Exercice {annee} : écart 6–7 vs 1–5 = {fmt(ecart)}.")
        else:
            st.info(f"Exercice {annee} : aucun fichier chargé.")


# ---------- PAGE : ANALYSE SIG ----------
elif page == "Analyse SIG":
    st.title("Analyse du résultat (SIG)")

    data_par_an = st.session_state.get("data_par_an", {})

    if "N" not in data_par_an and "N-1" not in data_par_an:
        st.info("👉 Importes au moins un fichier dans **Données & imports** avant de venir ici.")
    else:
        sig_par_an = {}
        grouped_par_an = {}

        # Préparer données pour N et N-1
        for annee in ["N", "N-1"]:
            if annee in data_par_an:
                grouped = preparer_grouped(data_par_an[annee])
                if grouped is not None:
                    grouped_par_an[annee] = grouped
                    sig_par_an[annee] = calcul_sig(grouped)

        if not sig_par_an:
            st.warning("Impossible de calculer le SIG (format de données non reconnu).")
        else:
            lignes_ordre = [
                "Chiffre d'affaires",
                "Ventes + Production réelle",
                "Achats consommés",
                "Marge globale",
                "Charges de fonctionnement",
                "Valeur ajoutée",
                "Subvention de l'exploitation",
                "Impôts et taxes",
                "Charges de personnel",
                "Excédent brut d'exploitation",
                "Transfert de charges",
                "Reprises sur provisions",
                "Autres produits d'exploitation",
                "Dotations aux amortissements",
                "Dotations aux provisions",
                "Autres charges d'exploitation",
                "Résultat d'exploitation",
                "Résultat financier",
                "Résultat courant",
                "Résultat exceptionnel",
                "Résultat de l'exercice",
                "Capacité d'autofinancement",
            ]

            # Construction du tableau de synthèse
            data_table = []
            for ligne in lignes_ordre:
                val_N = sig_par_an.get("N", {}).get(ligne, 0.0)
                val_N1 = sig_par_an.get("N-1", {}).get(ligne, 0.0)
                if "N" in sig_par_an and "N-1" in sig_par_an:
                    ecart_abs = val_N - val_N1
                    ecart_pct = (ecart_abs / val_N1 * 100) if abs(val_N1) > 1e-6 else None
                else:
                    ecart_abs = None
                    ecart_pct = None

                data_table.append(
                    {
                        "Poste": ligne,
                        "N": val_N if "N" in sig_par_an else None,
                        "N-1": val_N1 if "N-1" in sig_par_an else None,
                        "Écart": ecart_abs,
                        "%": ecart_pct,
                    }
                )

            df_sig = pd.DataFrame(data_table)

            # Mise en forme pour affichage
            def fmt_cell(v):
                if v is None or pd.isna(v):
                    return ""
                return fmt(v)

            def fmt_pct(v):
                if v is None or pd.isna(v):
                    return ""
                return f"{v:,.1f} %".replace(".", ",")

            df_aff = df_sig.copy()
            if "N" in sig_par_an:
                df_aff["N"] = df_aff["N"].apply(fmt_cell)
            if "N-1" in sig_par_an:
                df_aff["N-1"] = df_aff["N-1"].apply(fmt_cell)
            df_aff["Écart"] = df_aff["Écart"].apply(fmt_cell)
            df_aff["%"] = df_aff["%"].apply(fmt_pct)

            st.subheader("Tableau des soldes intermédiaires de gestion")
            st.dataframe(df_aff.set_index("Poste"), use_container_width=True)

            st.markdown("---")
            st.subheader("Détail par poste (cliquer pour dérouler)")

            # Volets déroulants
            for _, row in df_sig.iterrows():
                poste = row["Poste"]
                with st.expander(poste):
                    cols = st.columns(2)
                    if "N" in grouped_par_an:
                        detail_N = filtre_detail(grouped_par_an["N"], poste)
                        cols[0].markdown("**Exercice N**")
                        if detail_N.empty:
                            cols[0].write("Aucun compte pour ce poste.")
                        else:
                            cols[0].dataframe(detail_N, use_container_width=True)
                    if "N-1" in grouped_par_an:
                        detail_N1 = filtre_detail(grouped_par_an["N-1"], poste)
                        cols[1].markdown("**Exercice N-1**")
                        if detail_N1.empty:
                            cols[1].write("Aucun compte pour ce poste.")
                        else:
                            cols[1].dataframe(detail_N1, use_container_width=True)
