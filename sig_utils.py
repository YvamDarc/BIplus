import pandas as pd
import streamlit as st


# ---------- Utilitaires généraux ----------

def to_float(x):
    if pd.isna(x):
        return 0.0
    try:
        return float(str(x).replace(" ", "").replace(",", "."))
    except Exception:
        return 0.0


def fmt(v):
    if v is None or pd.isna(v):
        return ""
    return f"{v:,.0f} €".replace(",", " ").replace(".", ",")


# ---------- Lecture FEC / balance ----------

def lire_fichier_fec(file):
    """Lecture robuste d'un fichier FEC / balance (txt/csv/xls/xlsx)."""
    filename = file.name.lower()

    # Cas Excel
    if filename.endswith((".xlsx", ".xls")):
        try:
            return pd.read_excel(file)
        except Exception as e:
            st.error(f"Erreur lecture Excel {file.name} : {e}")
            return None

    # Cas texte : auto-détection du séparateur
    try:
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
    except Exception as e:
        st.error(f"Erreur lecture texte {file.name} : {e}")
        return None


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

    # Compte
    for c, n in cols_norm.items():
        if col_compte is None and any(n.startswith(x) for x in ["compte", "comptenum", "numcompte", "comptegeneral"]):
            col_compte = c
        if col_lib is None and any(x in n for x in ["libelle", "libellé", "intitule", "intitulé"]):
            col_lib = c
        if col_debit is None and n.startswith(("debit", "débit")):
            col_debit = c
        if col_credit is None and n.startswith(("credit", "crédit")):
            col_credit = c

    if col_lib is None:
        df["CompteLib"] = ""
        col_lib = "CompteLib"

    return col_compte, col_lib, col_debit, col_credit


# ---------- Préparation des données comptables ----------

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

    tmp = tmp[tmp["CompteNum"].str.match(r"^[1-7]")]

    grouped = (
        tmp.groupby(["CompteNum", "CompteLib"], dropna=False)[["Debit", "Credit"]]
        .sum()
        .reset_index()
    )

    def montant_row(row):
        compte = row["CompteNum"]
        if compte.startswith("7"):
            return row["Credit"] - row["Debit"]
        else:
            return row["Debit"] - row["Credit"]

    grouped["Montant"] = grouped.apply(montant_row, axis=1)
    return grouped


# ---------- Contrôle de cohérence balance ----------

def controle_coherence(df):
    """Retourne l'écart (6-7 + 1-5). 0 => cohérent."""
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


# ---------- Calcul SIG ----------

def calcul_sig(grouped):
    """Calcule les agrégats SIG, renvoie un dict {libellé: montant}."""

    def somme_prefix(prefixes):
        return grouped[grouped["CompteNum"].str.startswith(prefixes)]["Montant"].sum()

    ventes_marchandises = somme_prefix(("707",))
    production_vendue = grouped[grouped["CompteNum"].str.match(r"^70(?!7)")]\
        ["Montant"].sum()
    production_stockee = somme_prefix(("713",))
    production_immobilisee = somme_prefix(("72",))
    production_exercice = production_vendue + production_stockee + production_immobilisee

    chiffre_affaires = ventes_marchandises + production_exercice

    cout_marchandises = somme_prefix(("607", "6037", "6031"))
    achats_mat = grouped[grouped["CompteNum"].str.match(r"^60(?!7)")]\
        ["Montant"].sum()
    charges_externes = somme_prefix(("61", "62"))
    achats_consommes = cout_marchandises + achats_mat + charges_externes

    marge_globale = chiffre_affaires - achats_consommes

    charges_fonctionnement = achats_mat + charges_externes
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

    resultat_exploitation = (
        ebe
        + transferts_charges
        + reprises_provisions
        + autres_produits_expl
        - dotations_amort
        - dotations_provisions
        - autres_charges_expl
    )

    produits_financiers = somme_prefix(("76",))
    charges_financieres = somme_prefix(("66",))
    resultat_financier = produits_financiers - charges_financieres

    resultat_courant = resultat_exploitation + resultat_financier

    produits_exceptionnels = somme_prefix(("77",))
    charges_exceptionnelles = somme_prefix(("67",))
    resultat_exceptionnel = produits_exceptionnels - charges_exceptionnelles

    resultat_exercice = resultat_courant + resultat_exceptionnel

    caf = resultat_exercice + dotations_amort + dotations_provisions - reprises_provisions

    sig = {
        "Chiffre d'affaires": chiffre_affaires,
        "Ventes + Production réelle": chiffre_affaires,
        "Achats consommés": -achats_consommes,
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


def filtre_detail(grouped, ligne):
    """Retourne le détail des comptes pour une ligne SIG donnée."""
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
        mask = g["CompteNum"].str.match(r"^[67]")

    detail = g[mask].copy()
    detail["Montant"] = detail["Montant"].round(2)
    return detail.sort_values("CompteNum")
