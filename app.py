import streamlit as st
import pandas as pd

st.set_page_config(page_title="Analyse SIG FEC", layout="wide")

# -----------------------------
# Utilitaires de lecture / parsing
# -----------------------------
def lire_fichier_fec(file):
    """Lecture robuste d'un fichier FEC ou balance (txt/csv) avec auto-détection du séparateur."""
    filename = file.name.lower()

    # Excel => on lit directement
    if filename.endswith((".xlsx", ".xls")):
        return pd.read_excel(file)

    # Fichiers texte : on détecte le séparateur
    sample = file.read(4096).decode("utf-8", errors="ignore")
    file.seek(0)

    if ";" in sample:
        sep = ";"
    elif "|" in sample:
        sep = "|"
    elif "\t" in sample:
        sep = "\t"
    else:
        sep = ","

    df = pd.read_csv(file, sep=sep, dtype=str, low_memory=False)
    return df


def normaliser_colonnes(df):
    """
    Essaie d'identifier les colonnes Compte / Libellé / Débit / Crédit
    dans un FEC ou une balance.
    """
    cols_norm = {c: c.lower().strip().replace(" ", "").replace("°", "") for c in df.columns}

    col_compte = None
    col_lib = None
    col_debit = None
    col_credit = None

    for c, n in cols_norm.items():
        if col_compte is None and any(n.startswith(x) for x in ["compte", "comptenum", "numcompte", "comptegeneral"]):
            col_compte = c
        if col_lib is None and any(x in n for x in ["libelle", "libellé", "intitule", "intitulé"]):
            col_lib = c
        if col_debit is None and n.startswith(("debit", "débit")):
            col_debit = c
        if col_credit is None and n.startswith(("credit", "crédit")):
            col_credit = c

    # Si pas de libellé, on en met un vide
    if col_lib is None:
        df["CompteLib"] = ""
        col_lib = "CompteLib"

    return col_compte, col_lib, col_debit, col_credit


def to_float(x):
    if pd.isna(x):
        return 0.0
    try:
        return float(str(x).replace(" ", "").replace(",", "."))
    except Exception:
        return 0.0


def preparer_grouped(df):
    """
    Retourne un DataFrame 'grouped' avec :
    - CompteNum
    - CompteLib
    - Debit
    - Credit
    - Montant (charge > 0, produit > 0)
    """
    col_compte, col_lib, col_debit, col_credit = normaliser_colonnes(df)
    if col_compte is None:
        return None  # format non reconnu

    # On s'assure que les colonnes existent
    if col_debit is None:
        df["_Debit"] = 0.0
        col_debit = "_Debit"
    if col_credit is None:
        df["_Credit"] = 0.0
        col_credit = "_Credit"

    tmp = pd.DataFrame({
        "CompteNum": df[col_compte].astype(str),
        "CompteLib": df[col_lib].astype(str),
        "Debit": df[col_debit].apply(to_float),
        "Credit": df[col_credit].apply(to_float),
    })

    # On ne garde que les classes 6 et 7 pour le SIG (mais on pourra détailler par poste)
    tmp = tmp[tmp["CompteNum"].str.match(r"^[1-7]")]
    grouped = (
        tmp.groupby(["CompteNum", "CompteLib"], dropna=False)[["Debit", "Credit"]]
        .sum()
        .reset_index()
    )

    # Montant "économique" : charges = Débit - Crédit, produits = Crédit - Débit
    def montant_row(row):
        compte = row["CompteNum"]
        if compte.startswith("7"):
            return row["Credit"] - row["Debit"]
        else:
            return row["Debit"] - row["Credit"]

    grouped["Montant"] = grouped.apply(montant_row, axis=1)
    return grouped


# -----------------------------
# Calcul SIG (par année)
# -----------------------------
def calcul_sig(grouped):
    """Calcule les grands agrégats SIG, renvoie un dict."""

    def somme_prefix(prefixes):
        return grouped[grouped["CompteNum"].str.startswith(prefixes)]["Montant"].sum()

    # Ventes & production (très simplifié)
    ventes_marchandises = somme_prefix(("707",))
    production_vendue = grouped[grouped["CompteNum"].str.match(r"^70(?!7)")]\
        ["Montant"].sum()
    production_stockee = somme_prefix(("713",))
    production_immobilisee = somme_prefix(("72",))
    production_exercice = production_vendue + production_stockee + production_immobilisee

    chiffre_affaires = ventes_marchandises + production_exercice

    # Achats consommés (achats + charges externes)
    cout_marchandises = somme_prefix(("607", "6037", "6031"))
    achats_mat = grouped[grouped["CompteNum"].str.match(r"^60(?!7)")]\
        ["Montant"].sum()
    charges_externes = somme_prefix(("61", "62"))
    achats_consommes = cout_marchandises + achats_mat + charges_externes

    marge_globale = chiffre_affaires - achats_consommes

    # Charges de fonctionnement (on prend ici achats_mat + charges externes)
    charges_fonctionnement = achats_mat + charges_externes

    # Valeur ajoutée (calculée "classique" à partir de nos éléments).
    valeur_ajoutee = marge_globale - charges_fonctionnement

    subventions_expl = somme_prefix(("74",))
    impots_taxes = somme_prefix(("63",))
    charges_personnel = somme_prefix(("64",))

    ebe = valeur_ajoutee + subventions_expl - impots_taxes - charges_personnel

    transferts_charges = somme_prefix(("79", "791"))
    reprises_provisions = somme_prefix(("78", "781"))

    autres_produits_expl = somme_prefix(("75",))
    dotations_amort = grouped[grouped["CompteNum"].str.match(r"^68(?!6|7)")]\
        ["Montant"].sum()
    dotations_provisions = somme_prefix(("681",))
    autres_charges_expl = somme_prefix(("65",))

    resultat_exploitation = ebe + transferts_charges + reprises_provisions \
        + autres_produits_expl - dotations_amort - dotations_provisions - autres_charges_expl

    produits_financiers = somme_prefix(("76",))
    charges_financieres = somme_prefix(("66",))
    resultat_financier = produits_financiers - charges_financieres

    resultat_courant = resultat_exploitation + resultat_financier

    produits_exceptionnels = somme_prefix(("77",))
    charges_exceptionnelles = somme_prefix(("67",))
    resultat_exceptionnel = produits_exceptionnels - charges_exceptionnelles

    resultat_exercice = resultat_courant + resultat_exceptionnel

    # CAF très simplifiée : Résultat + dotations - reprises
    caf = resultat_exercice + dotations_amort + dotations_provisions - reprises_provisions

    sig = {
        "Chiffre d'affaires": chiffre_affaires,
        "Ventes + Production réelle": chiffre_affaires,  # même valeur, comme ton modèle
        "Achats consommés": -achats_consommes,  # on affiche en négatif
        "Marge globale": marge_globale,
        "Charges de fonctionnement": -charges_fonctionnement,
        "Valeur ajoutée": valeur_ajoutee,
        "Subvention de l'exploitation": subventions_expl,
        "Impôts et taxes": -impots_taxes,
        "Charges de personnel": -charges_personnel,
        "Excédent brut d'exploitation": ebe,
        "Transfert de charges": transferts_charges,
        "Reprises sur provisions": reprises_provisions,
        "Autres produits d'exploitation": autres_produits_expl,
        "Dotations aux amortissements": -dotations_amort,
        "Dotations aux provisions": -dotations_provisions,
        "Autres charges d'exploitation": -autres_charges_expl,
        "Résultat d'exploitation": resultat_exploitation,
        "Résultat financier": resultat_financier,
        "Résultat courant": resultat_courant,
        "Résultat exceptionnel": resultat_exceptionnel,
        "Résultat de l'exercice": resultat_exercice,
        "Capacité d'autofinancement": caf,
    }

    return sig


# Pour le détail par ligne : mapping "ligne SIG" -> sélecteur de comptes
def filtre_detail(grouped, ligne):
    """Retourne le détail des comptes contributeurs pour une ligne SIG."""
    g = grouped.copy()
    if ligne in ("Chiffre d'affaires", "Ventes + Production réelle"):
        mask = g["CompteNum"].str.startswith(("70", "71", "72", "75"))
    elif ligne == "Achats consommés":
        mask = g["CompteNum"].str.startswith(("60", "61", "62"))
    elif ligne == "Charges de fonctionnement":
        mask = g["CompteNum"].str.startswith(("60", "61", "62"))
    elif ligne == "Impôts et taxes":
        mask = g["CompteNum"].str.startswith(("63",))
    elif ligne == "Charges de personnel":
        mask = g["CompteNum"].str.startswith(("64",))
    elif ligne == "Subvention de l'exploitation":
        mask = g["CompteNum"].str.startswith(("74",))
    elif ligne.startswith("Dotations"):
        mask = g["CompteNum"].str.startswith(("68", "681"))
    elif ligne.startswith("Autres produits d'exploitation"):
        mask = g["CompteNum"].str.startswith(("75", "78"))
    elif ligne.startswith("Autres charges d'exploitation"):
        mask = g["CompteNum"].str.startswith(("65",))
    elif ligne == "Résultat financier":
        mask = g["CompteNum"].str.startswith(("76", "66"))
    elif ligne == "Résultat exceptionnel":
        mask = g["CompteNum"].str.startswith(("77", "67"))
    else:
        # Par défaut : on montre tout 6/7
        mask = g["CompteNum"].str.match(r"^[67]")
    detail = g[mask].copy()
    detail["Montant"] = detail["Montant"].round(2)
    return detail.sort_values("CompteNum")


def fmt(v):
    return f"{v:,.0f} €".replace(",", " ").replace(".", ",")


# -----------------------------
# SESSION STATE INIT
# -----------------------------
if "data_par_an" not in st.session_state:
    st.session_state["data_par_an"] = {}

# -----------------------------
# NAVIGATION (volet gauche)
# -----------------------------
page = st.sidebar.radio(
    "Navigation",
    ["Données entreprise & imports", "Analyse SIG"],
)

# -----------------------------
# PAGE 1 : IMPORTS + CONTROLES
# -----------------------------
if page == "Données entreprise & imports":
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

    col_fec, col_bal = st.columns(2)
    with col_fec:
        fec_N = st.file_uploader("FEC – Année N", type=["csv", "txt", "xlsx", "xls"], key="fec_N")
        fec_N1 = st.file_uploader("FEC – Année N-1", type=["csv", "txt", "xlsx", "xls"], key="fec_N1")
    with col_bal:
        fec_N2 = st.file_uploader("FEC – Année N-2", type=["csv", "txt", "xlsx", "xls"], key="fec_N2")

    data_par_an = st.session_state["data_par_an"]

    def charger_fichier(label, fichier, annee):
        if fichier is None:
            st.info(f"{label} {annee} : aucun fichier importé.")
            return
        df = lire_fichier_fec(fichier)
        if df is not None:
            data_par_an[annee] = df
            st.success(f"{label} {annee} importé ({len(df)} lignes).")

    colN, colN1, colN2 = st.columns(3)
    with colN:
        charger_fichier("FEC", fec_N, "N")
    with colN1:
        charger_fichier("FEC", fec_N1, "N-1")
    with colN2:
        charger_fichier("FEC", fec_N2, "N-2")

    st.session_state["data_par_an"] = data_par_an

    st.markdown("---")
    st.subheader("Contrôle de cohérence (classes 6-7 vs 1-5)")

    def controle_coherence(df):
        col_compte, _, col_debit, col_credit = normaliser_colonnes(df)
        if col_compte is None:
            return None

        if col_debit is None:
            df["_Debit"] = 0.0
            col_debit = "_Debit"
        if col_credit is None:
            df["_Credit"] = 0.0
            col_credit = "_Credit"

        sum_1to5 = 0.0
        sum_6to7 = 0.0

        for _, row in df.iterrows():
            compte = str(row[col_compte]).strip()
            if compte == "":
                continue
            debit_val = to_float(row[col_debit])
            credit_val = to_float(row[col_credit])
            m = debit_val - credit_val
            if compte[0] in "12345":
                sum_1to5 += m
            elif compte[0] in "67":
                sum_6to7 += m

        ecart = sum_6to7 + sum_1to5
        return ecart

    for annee in ["N", "N-1", "N-2"]:
        if annee in data_par_an:
            df = data_par_an[annee]
            ecart = controle_coherence(df)
            if ecart is None:
                st.warning(f"Exercice {annee} : format de données non reconnu pour le contrôle.")
            else:
                if abs(ecart) < 1e-2:
                    st.success(f"Exercice {annee} : balance cohérente (écart ≈ 0 €).")
                else:
                    st.error(f"Exercice {annee} : écart 6-7 vs 1-5 = {fmt(ecart)}.")
        else:
            st.info(f"Exercice {annee} : pas de fichier chargé.")


# -----------------------------
# PAGE 2 : ANALYSE SIG
# -----------------------------
elif page == "Analyse SIG":
    st.header("Analyse du résultat de l'exercice (SIG)")

    data_par_an = st.session_state["data_par_an"]
    if "N" not in data_par_an and "N-1" not in data_par_an:
        st.info("Veuillez d'abord importer au moins un FEC dans la page précédente.")
    else:
        # On prépare grouped + SIG pour N et N-1 si dispo
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

            # Construction du tableau SIG type "2025 / 2024 / Evolution"
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

            # Affichage en tableau large
            def fmt_cell(v):
                if v is None or pd.isna(v):
                    return ""
                return fmt(v)

            def fmt_pct(v):
                if v is None or pd.isna(v):
                    return ""
                return f"{v:,.1f} %".replace(",", ",")

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

            # Volets déroulants pour chaque ligne
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
