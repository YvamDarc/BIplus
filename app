import streamlit as st
import pandas as pd

# Configuration de la page
st.set_page_config(page_title="Application SIG et Contrôle de Balance", layout="wide")

# Titre de l'application
st.title("Application d'analyse financière")

# Création des onglets
onglet1, onglet2 = st.tabs(["Informations Générales & Contrôle de la Balance", "SIG (Solde Intermédiaire de Gestion)"])

# Dictionnaire pour stocker les données chargées par année
data_par_an = {}

with onglet1:
    st.header("Informations sur l'entreprise")
    # Champs de saisie pour les informations de l'entreprise
    nom_entreprise = st.text_input("Nom de l'entreprise")
    adresse = st.text_input("Adresse")
    telephone = st.text_input("Téléphone")
    email = st.text_input("Email")
    
    st.header("Chargement des fichiers comptables")
    st.write("Veuillez charger les fichiers FEC ou les balances (format FEC au 31/12) pour les exercices **N**, **N-1** et **N-2**.")
    
    # Colonnes pour organiser les champs de chargement FEC vs Balance
    col_fec, col_bal = st.columns(2)
    with col_fec:
        fec_N = st.file_uploader("FEC – Année N", type=['csv', 'xlsx', 'xls', 'txt'])
        fec_N1 = st.file_uploader("FEC – Année N-1", type=['csv', 'xlsx', 'xls', 'txt'])
        fec_N2 = st.file_uploader("FEC – Année N-2", type=['csv', 'xlsx', 'xls', 'txt'])
    with col_bal:
        bal_N = st.file_uploader("Balance – Année N (optionnel)", type=['csv', 'xlsx', 'xls', 'txt'])
        bal_N1 = st.file_uploader("Balance – Année N-1 (optionnel)", type=['csv', 'xlsx', 'xls', 'txt'])
        bal_N2 = st.file_uploader("Balance – Année N-2 (optionnel)", type=['csv', 'xlsx', 'xls', 'txt'])
    
    # Fonction utilitaire pour lire un fichier comptable en DataFrame pandas
    def lire_fichier_comptable(file):
        filename = file.name.lower()
        try:
            # Lecture selon l'extension du fichier
            if filename.endswith('.xlsx') or filename.endswith('.xls'):
                df = pd.read_excel(file)
            else:
                # Essayer avec séparateur ';' puis ',' si nécessaire
                try:
                    df = pd.read_csv(file, sep=';', decimal='.', encoding='utf-8')
                except Exception:
                    file.seek(0)  # réinitialiser le pointeur du fichier
                    df = pd.read_csv(file, sep=',', decimal='.', encoding='utf-8')
            return df
        except Exception as e:
            st.error(f"Erreur lors de la lecture du fichier {file.name} : {e}")
            return None
    
    # Chargement des fichiers pour chaque année (priorité au FEC si les deux fournis)
    df_N = None
    if fec_N is not None:
        df_N = lire_fichier_comptable(fec_N)
    elif bal_N is not None:
        df_N = lire_fichier_comptable(bal_N)
    if df_N is not None:
        data_par_an["N"] = df_N
    
    df_N1 = None
    if fec_N1 is not None:
        df_N1 = lire_fichier_comptable(fec_N1)
    elif bal_N1 is not None:
        df_N1 = lire_fichier_comptable(bal_N1)
    if df_N1 is not None:
        data_par_an["N-1"] = df_N1
    
    df_N2 = None
    if fec_N2 is not None:
        df_N2 = lire_fichier_comptable(fec_N2)
    elif bal_N2 is not None:
        df_N2 = lire_fichier_comptable(bal_N2)
    if df_N2 is not None:
        data_par_an["N-2"] = df_N2
    
    # Contrôle automatique de cohérence de la balance
    st.subheader("Contrôle de cohérence de la balance")
    if not data_par_an:
        st.info("Aucun fichier n'a été chargé pour le moment.")
    else:
        def controle_coherence(df):
            # Identification des colonnes pour comptes, débit, crédit, ou montant
            cols = [c.lower() for c in df.columns]
            col_compte = None
            for c in ['compte', 'comptenum', 'account']:
                if c in cols:
                    col_compte = df.columns[cols.index(c)]
                    break
            col_debit = None
            col_credit = None
            for c in ['debit', 'débit']:
                if c in cols:
                    col_debit = df.columns[cols.index(c)]
                    break
            for c in ['credit', 'crédit']:
                if c in cols:
                    col_credit = df.columns[cols.index(c)]
                    break
            col_montant = None
            if col_debit is None or col_credit is None:
                for c in ['montant', 'amount', 'balance', 'solde']:
                    if c in cols:
                        col_montant = df.columns[cols.index(c)]
                        break
            # Calcul des totaux pour classes 1-5 et 6-7
            sum_1to5 = 0.0
            sum_6to7 = 0.0
            if col_compte is None:
                return None  # format non reconnu
            if col_montant:
                # Si une seule colonne montant/solde existe
                for _, row in df.iterrows():
                    compte = str(row[col_compte]) if not pd.isna(row[col_compte]) else ''
                    if compte.strip() == '':
                        continue
                    try:
                        m = float(str(row[col_montant]).replace(',', '.'))
                    except:
                        m = 0.0
                    if compte[0] in ['1', '2', '3', '4', '5']:
                        sum_1to5 += m
                    elif compte[0] in ['6', '7']:
                        sum_6to7 += m
            else:
                # Si colonnes Débit/Crédit distinctes
                for _, row in df.iterrows():
                    compte = str(row[col_compte]) if not pd.isna(row[col_compte]) else ''
                    if compte.strip() == '':
                        continue
                    # Valeurs débit/crédit (0 si NaN)
                    debit_val = 0.0
                    credit_val = 0.0
                    if col_debit:
                        val = row[col_debit]
                        if not pd.isna(val):
                            try:
                                debit_val = float(str(val).replace(',', '.'))
                            except:
                                debit_val = 0.0
                    if col_credit:
                        val = row[col_credit]
                        if not pd.isna(val):
                            try:
                                credit_val = float(str(val).replace(',', '.'))
                            except:
                                credit_val = 0.0
                    montant = debit_val - credit_val
                    if compte[0] in ['1', '2', '3', '4', '5']:
                        sum_1to5 += montant
                    elif compte[0] in ['6', '7']:
                        sum_6to7 += montant
            ecart = sum_6to7 + sum_1to5
            return ecart
        
        # Vérifier chaque année disponible
        for year in ["N", "N-1", "N-2"]:
            if year in data_par_an:
                df = data_par_an[year]
                ecart = controle_coherence(df)
                if ecart is None:
                    st.warning(f"Exercice {year} : impossible de vérifier la cohérence (format de données non reconnu).")
                else:
                    if abs(ecart) < 1e-6:
                        st.success(f"Exercice {year} : Balance équilibrée (aucun écart).")
                    else:
                        st.error(f"Exercice {year} : Écart détecté de {ecart:,.2f} € (comptes 6-7 vs 1-5).")
            else:
                st.info(f"Exercice {year} : fichier non fourni.")

with onglet2:
    st.header("Soldes Intermédiaires de Gestion (SIG)")
    if not data_par_an:
        st.info("Aucune donnée disponible. Veuillez charger des fichiers dans l'onglet précédent.")
    else:
        def calculer_SIG(df):
            # Préparation des colonnes
            cols = [c.lower() for c in df.columns]
            col_compte = None
            for c in ['compte', 'comptenum', 'account']:
                if c in cols:
                    col_compte = df.columns[cols.index(c)]
                    break
            col_debit = None
            col_credit = None
            for c in ['debit', 'débit']:
                if c in cols:
                    col_debit = df.columns[cols.index(c)]
                    break
            for c in ['credit', 'crédit']:
                if c in cols:
                    col_credit = df.columns[cols.index(c)]
                    break
            col_montant = None
            if col_debit is None or col_credit is None:
                for c in ['montant', 'amount', 'balance', 'solde']:
                    if c in cols:
                        col_montant = df.columns[cols.index(c)]
                        break
            # Calcul des soldes par compte
            comptes_sommes = {}
            for _, row in df.iterrows():
                if col_compte is None:
                    continue
                compte = str(row[col_compte]) if not pd.isna(row[col_compte]) else ''
                if compte.strip() == '':
                    continue
                # Montant de la ligne (débit - crédit, ou solde direct)
                if col_montant:
                    try:
                        m = float(str(row[col_montant]).replace(',', '.'))
                    except:
                        m = 0.0
                else:
                    debit_val = 0.0
                    credit_val = 0.0
                    if col_debit:
                        val = row[col_debit]
                        if not pd.isna(val):
                            try:
                                debit_val = float(str(val).replace(',', '.'))
                            except:
                                debit_val = 0.0
                    if col_credit:
                        val = row[col_credit]
                        if not pd.isna(val):
                            try:
                                credit_val = float(str(val).replace(',', '.'))
                            except:
                                credit_val = 0.0
                    m = debit_val - credit_val
                comptes_sommes[compte] = comptes_sommes.get(compte, 0.0) + m
            # Calcul des soldes intermédiaires de gestion
            # Marge commerciale = ventes de marchandises - coût d'achat des marchandises vendues
            ventes_marchandises = sum(val for acct, val in comptes_sommes.items() if str(acct).startswith("707"))
            rabais_ventes_marchandises = sum(val for acct, val in comptes_sommes.items() if str(acct).startswith("7097"))
            ventes_net_marchandises = ventes_marchandises + rabais_ventes_marchandises
            achats_marchandises = sum(val for acct, val in comptes_sommes.items() if str(acct).startswith("607"))
            frais_achats_marchandises = sum(val for acct, val in comptes_sommes.items() if str(acct).startswith("608")) if achats_marchandises != 0 else 0.0
            variation_stocks_marchandises = sum(val for acct, val in comptes_sommes.items() if str(acct).startswith("6037"))
            rabais_achats_marchandises = sum(val for acct, val in comptes_sommes.items() if str(acct).startswith("6097"))
            cout_achats_marchandises = achats_marchandises + frais_achats_marchandises + variation_stocks_marchandises + rabais_achats_marchandises
            marge_commerciale = -ventes_net_marchandises - cout_achats_marchandises
            # Production de l'exercice = ventes de produits (biens et services) + production stockée + production immobilisée
            ventes_produits = sum(val for acct, val in comptes_sommes.items() if str(acct).startswith("70") and not str(acct).startswith("707"))
            # Retirer les rabais sur ventes de marchandises éventuellement inclus (7097)
            ventes_produits -= rabais_ventes_marchandises
            variation_stocks_produits = sum(val for acct, val in comptes_sommes.items() if str(acct).startswith("71"))
            production_immobilisee = sum(val for acct, val in comptes_sommes.items() if str(acct).startswith("72"))
            production_exercice = -(ventes_produits + variation_stocks_produits + production_immobilisee)
            # Consommations en provenance de tiers = achats de matières et approvisionnements + services extérieurs
            consommations_matieres = sum(val for acct, val in comptes_sommes.items() if str(acct).startswith("60") and not str(acct).startswith("607"))
            # Exclure la variation de stocks de marchandises et les rabais fournisseurs déjà pris en compte
            consommations_matieres -= variation_stocks_marchandises
            consommations_matieres -= rabais_achats_marchandises
            # Exclure les frais d'achats de marchandises si déjà comptabilisés dans la marge
            if achats_marchandises != 0:
                consommations_matieres -= sum(val for acct, val in comptes_sommes.items() if str(acct).startswith("608"))
            services_exterieurs = sum(val for acct, val in comptes_sommes.items() if str(acct).startswith("61") or str(acct).startswith("62"))
            conso_tiers = consommations_matieres + services_exterieurs
            valeur_ajoutee = marge_commerciale + production_exercice - conso_tiers
            # Excédent Brut d'Exploitation (EBE) = Valeur ajoutée + subventions d'exploitation - charges de personnel - impôts et taxes
            subventions = sum(val for acct, val in comptes_sommes.items() if str(acct).startswith("74"))
            charges_personnel = sum(val for acct, val in comptes_sommes.items() if str(acct).startswith("64"))
            impots_taxes = sum(val for acct, val in comptes_sommes.items() if str(acct).startswith("63"))
            ebe = valeur_ajoutee - charges_personnel - impots_taxes + (-subventions)
            # Résultat d'exploitation = EBE + autres produits d'exploitation - autres charges d'exploitation
            autres_prod_expl = sum(val for acct, val in comptes_sommes.items() 
                                   if str(acct).startswith("75") or str(acct).startswith("791") or 
                                   (str(acct).startswith("78") and not (str(acct).startswith("786") or str(acct).startswith("787"))))
            autres_charges_expl = sum(val for acct, val in comptes_sommes.items() 
                                      if str(acct).startswith("65") or 
                                      (str(acct).startswith("68") and not (str(acct).startswith("686") or str(acct).startswith("687"))))
            resultat_exploitation = ebe + (-autres_prod_expl) - autres_charges_expl
            # Résultat financier = produits financiers - charges financières
            produits_financiers = sum(val for acct, val in comptes_sommes.items() if str(acct).startswith("76"))
            charges_financieres = sum(val for acct, val in comptes_sommes.items() if str(acct).startswith("66"))
            resultat_financier = -produits_financiers - charges_financieres
            # Résultat exceptionnel = produits exceptionnels - charges exceptionnelles
            produits_exceptionnels = sum(val for acct, val in comptes_sommes.items() if str(acct).startswith("77"))
            charges_exceptionnelles = sum(val for acct, val in comptes_sommes.items() if str(acct).startswith("67"))
            resultat_exceptionnel = -produits_exceptionnels - charges_exceptionnelles
            # Résultat courant avant impôts et résultat net
            resultat_courant = resultat_exploitation + resultat_financier
            resultat_avant_impot = resultat_courant + resultat_exceptionnel
            impot_benef = sum(val for acct, val in comptes_sommes.items() if str(acct).startswith("69"))
            resultat_net = resultat_avant_impot - impot_benef
            # Indicateurs de présence de données pour marge et production
            has_merch = any(str(acct).startswith("707") or str(acct).startswith("607") for acct in comptes_sommes.keys())
            has_prod = any((str(acct).startswith("70") and not str(acct).startswith("707")) or str(acct).startswith("71") or str(acct).startswith("72") 
                           for acct in comptes_sommes.keys())
            return {
                "Marge commerciale": marge_commerciale,
                "Production de l'exercice": production_exercice,
                "Valeur ajoutée": valeur_ajoutee,
                "Excédent Brut d'Exploitation (EBE)": ebe,
                "Résultat d'exploitation": resultat_exploitation,
                "Résultat financier": resultat_financier,
                "Résultat courant avant impôts": resultat_courant,
                "Résultat exceptionnel": resultat_exceptionnel,
                "Résultat net": resultat_net,
                "_has_merch": has_merch,
                "_has_prod": has_prod
            }
        
        # Affichage du SIG pour chaque exercice disponible
        for year in ["N", "N-1", "N-2"]:
            if year in data_par_an:
                st.subheader(f"Exercice {year}")
                sig = calculer_SIG(data_par_an[year])
                has_merch = sig.get("_has_merch", False)
                has_prod = sig.get("_has_prod", False)
                # Retirer les clés internes du dictionnaire
                sig.pop("_has_merch", None)
                sig.pop("_has_prod", None)
                # Retirer l'affichage de la marge ou de la production si non applicable
                if not has_merch and "Marge commerciale" in sig:
                    sig.pop("Marge commerciale")
                if not has_prod and "Production de l'exercice" in sig:
                    sig.pop("Production de l'exercice")
                # Afficher chaque ligne calculée du SIG
                for libelle, valeur in sig.items():
                    st.write(f"- **{libelle} :** {valeur:,.2f} €")
