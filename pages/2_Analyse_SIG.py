import streamlit as st
import pandas as pd
from sig_utils import (
    preparer_grouped,
    calcul_sig,
    filtre_detail,
    fmt,
)

st.title("Analyse du résultat (SIG)")

data_par_an = st.session_state.get("data_par_an", {})

if "N" not in data_par_an && "N-1" not in data_par_an:
    st.info("Veuillez d'abord importer au moins un fichier dans la page **Données & imports**.")
else:
    sig_par_an = {}
    grouped_par_an = {}

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
