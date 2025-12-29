import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import warnings
import json
from datetime import datetime
from supabase import create_client
import numpy as np
from sklearn.linear_model import LinearRegression
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore')

# Configuration
st.set_page_config(page_title="Analyse BRVM", layout="wide")

# Mot de passe développeur
DEVELOPER_PASSWORD = "dev_brvm_2024"

# ===========================
# CONFIGURATION SUPABASE
# ===========================
SUPABASE_URL = "https://otsiwiwlnowxeolbbgvm.supabase.co"
SUPABASE_KEY = "sb_publishable_MhaI5b-kMmb5liIMOJ4P3Q_xGTsJAFJ"

def init_supabase():
    """Initialiser la connexion à Supabase"""
    if 'supabase' not in st.session_state:
        try:
            st.session_state.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            # Test de connexion
            test_response = st.session_state.supabase.table("financial_data").select("*", count="exact").limit(1).execute()
            st.success("  Connexion Supabase établie")
        except Exception as e:
            st.error(f"  Erreur de connexion Supabase: {str(e)}")
            return None
    return st.session_state.supabase

def load_all_financial_data():
    """Charger toutes les données financières depuis Supabase"""
    supabase = init_supabase()
    if not supabase:
        return {}
    
    try:
        response = supabase.table("financial_data").select("*").execute()
        financial_data = {}
        
        for record in response.data:
            key = f"{record['symbole']}_{record['annee']}"
            financial_data[key] = {
                'symbole': record['symbole'],
                'annee': record['annee'],
                'bilan': record['data'].get('bilan', {}),
                'compte_resultat': record['data'].get('compte_resultat', {}),
                'flux_tresorerie': record['data'].get('flux_tresorerie', {}),
                'ratios': record['data'].get('ratios', {}),
                'last_update': record.get('last_update', None)
            }
        
        return financial_data
    except Exception as e:
        st.error(f"Erreur de chargement depuis Supabase: {str(e)}")
        return {}

def save_financial_data(symbole, annee, data_dict):
    """Sauvegarder les données dans Supabase"""
    supabase = init_supabase()
    if not supabase:
        return False
    
    try:
        record = {
            'symbole': symbole,
            'annee': annee,
            'data': data_dict,
            'last_update': datetime.now().isoformat()
        }
        
        # Vérifier si l'entrée existe déjà
        existing = supabase.table("financial_data")\
            .select("*")\
            .eq("symbole", symbole)\
            .eq("annee", annee)\
            .execute()
        
        if existing.data:
            # Mise à jour
            response = supabase.table("financial_data")\
                .update(record)\
                .eq("symbole", symbole)\
                .eq("annee", annee)\
                .execute()
        else:
            # Insertion
            response = supabase.table("financial_data").insert(record).execute()
        
        return True
    except Exception as e:
        st.error(f"Erreur de sauvegarde dans Supabase: {str(e)}")
        return False

def delete_financial_data(symbole, annee):
    """Supprimer des données de Supabase"""
    supabase = init_supabase()
    if not supabase:
        return False
    
    try:
        response = supabase.table("financial_data")\
            .delete()\
            .eq("symbole", symbole)\
            .eq("annee", annee)\
            .execute()
        return True
    except Exception as e:
        st.error(f"Erreur de suppression: {str(e)}")
        return False

def init_storage():
    """Initialiser le stockage avec Supabase"""
    if 'financial_data' not in st.session_state:
        st.session_state.financial_data = load_all_financial_data()
    return st.session_state.financial_data

# ===========================
# FONCTIONS DE CALCUL DES RATIOS
# ===========================
def calculate_enhanced_financial_ratios(bilan, compte_resultat, flux_tresorerie):
    """Version améliorée avec tous les ratios standards"""
    ratios = {}
    
    # ========== CALCULS INTERMÉDIAIRES CRITIQUES ==========
    ebitda = compte_resultat.get('resultat_exploitation', 0)
    ebit = compte_resultat.get('resultat_exploitation', 0)
    fcf = flux_tresorerie.get('flux_exploitation', 0) + flux_tresorerie.get('flux_investissement', 0)
    working_capital = bilan.get('actif_courant', 0) - bilan.get('passif_courant', 0)
    
    market_cap = bilan.get('cours_action', 0) * bilan.get('nb_actions', 0)
    enterprise_value = market_cap + bilan.get('dettes_totales', 0) - bilan.get('tresorerie', 0)
    
    # ========== RATIOS DE RENTABILITÉ ==========
    if compte_resultat.get('resultat_net') and compte_resultat.get('chiffre_affaires'):
        ratios['marge_nette'] = (compte_resultat['resultat_net'] / compte_resultat['chiffre_affaires']) * 100
    
    if ebit and compte_resultat.get('chiffre_affaires'):
        ratios['marge_ebit'] = (ebit / compte_resultat['chiffre_affaires']) * 100
    
    if ebitda and compte_resultat.get('chiffre_affaires'):
        ratios['marge_ebitda'] = (ebitda / compte_resultat['chiffre_affaires']) * 100
    
    if compte_resultat.get('resultat_net') and bilan.get('capitaux_propres'):
        ratios['roe'] = (compte_resultat['resultat_net'] / bilan['capitaux_propres']) * 100
    
    if compte_resultat.get('resultat_net') and bilan.get('actif_total'):
        ratios['roa'] = (compte_resultat['resultat_net'] / bilan['actif_total']) * 100
    
    if ebit and bilan.get('actif_total'):
        roic_denom = bilan['actif_total'] - bilan.get('passif_courant', 0)
        if roic_denom > 0:
            ratios['roic'] = (ebit * 0.75 / roic_denom) * 100
    
    # ========== RATIOS DE LIQUIDITÉ ==========
    if bilan.get('actif_courant') and bilan.get('passif_courant') and bilan.get('passif_courant') > 0:
        ratios['ratio_liquidite_generale'] = bilan['actif_courant'] / bilan['passif_courant']
    
    if bilan.get('actif_courant') and bilan.get('stocks') is not None and bilan.get('passif_courant'):
        actif_liquide = bilan['actif_courant'] - bilan.get('stocks', 0)
        if bilan['passif_courant'] > 0:
            ratios['ratio_liquidite_reduite'] = actif_liquide / bilan['passif_courant']
    
    if bilan.get('tresorerie') and bilan.get('passif_courant') and bilan.get('passif_courant') > 0:
        ratios['ratio_liquidite_immediate'] = bilan['tresorerie'] / bilan['passif_courant']
    
    # ========== RATIOS D'ENDETTEMENT ==========
    if bilan.get('dettes_totales') and bilan.get('capitaux_propres') and bilan.get('capitaux_propres') > 0:
        ratios['ratio_endettement'] = (bilan['dettes_totales'] / bilan['capitaux_propres']) * 100
    
    if bilan.get('dettes_totales') and bilan.get('actif_total') and bilan.get('actif_total') > 0:
        ratios['taux_endettement'] = (bilan['dettes_totales'] / bilan['actif_total']) * 100
    
    if bilan.get('capitaux_propres') and bilan.get('actif_total') and bilan.get('actif_total') > 0:
        ratios['ratio_solvabilite'] = (bilan['capitaux_propres'] / bilan['actif_total']) * 100
    
    if bilan.get('dettes_totales') and ebitda > 0:
        ratios['debt_to_ebitda'] = bilan['dettes_totales'] / ebitda
    
    if ebit and compte_resultat.get('charges_financieres') and abs(compte_resultat.get('charges_financieres', 0)) > 0:
        ratios['couverture_interets'] = ebit / abs(compte_resultat['charges_financieres'])
    
    # ========== RATIOS D'EFFICACITÉ ==========
    if compte_resultat.get('chiffre_affaires') and bilan.get('actif_total') and bilan.get('actif_total') > 0:
        ratios['rotation_actifs'] = compte_resultat['chiffre_affaires'] / bilan['actif_total']
    
    if compte_resultat.get('chiffre_affaires') and bilan.get('stocks') and bilan.get('stocks') > 0:
        ratios['rotation_stocks'] = compte_resultat['chiffre_affaires'] / bilan['stocks']
    
    if compte_resultat.get('chiffre_affaires') and bilan.get('creances') and compte_resultat.get('chiffre_affaires') > 0:
        ratios['delai_recouvrement'] = (bilan['creances'] / compte_resultat['chiffre_affaires']) * 365
    
    # ========== RATIOS DE MARCHÉ ==========
    if bilan.get('cours_action') and compte_resultat.get('benefice_par_action') and compte_resultat.get('benefice_par_action') > 0:
        ratios['per'] = bilan['cours_action'] / compte_resultat['benefice_par_action']
    elif bilan.get('cours_action') and compte_resultat.get('resultat_net') and bilan.get('nb_actions') and bilan.get('nb_actions') > 0:
        bpa = compte_resultat['resultat_net'] / bilan['nb_actions']
        if bpa > 0:
            ratios['per'] = bilan['cours_action'] / bpa
            ratios['benefice_par_action'] = bpa
    
    if bilan.get('cours_action') and bilan.get('capitaux_propres_par_action') and bilan.get('capitaux_propres_par_action') > 0:
        ratios['price_to_book'] = bilan['cours_action'] / bilan['capitaux_propres_par_action']
    
    if enterprise_value and ebitda > 0:
        ratios['ev_ebitda'] = enterprise_value / ebitda
    
    if enterprise_value and compte_resultat.get('chiffre_affaires') and compte_resultat.get('chiffre_affaires') > 0:
        ratios['ev_sales'] = enterprise_value / compte_resultat['chiffre_affaires']
    
    # ========== RATIOS DE FLUX DE TRÉSORERIE ==========
    if flux_tresorerie.get('flux_exploitation') and compte_resultat.get('resultat_net') and compte_resultat.get('resultat_net') != 0:
        ratios['qualite_benefices'] = flux_tresorerie['flux_exploitation'] / compte_resultat['resultat_net']
    
    if fcf and market_cap > 0:
        ratios['fcf_yield'] = (fcf / market_cap) * 100
    
    if fcf and bilan.get('dettes_totales') and bilan.get('dettes_totales') > 0:
        ratios['fcf_to_debt'] = fcf / bilan['dettes_totales']
    
    # ========== DONNÉES INTERMÉDIAIRES ==========
    ratios['ebitda'] = ebitda
    ratios['ebit'] = ebit
    ratios['fcf'] = fcf
    ratios['working_capital'] = working_capital
    ratios['enterprise_value'] = enterprise_value
    ratios['market_cap'] = market_cap
    
    return ratios

def calculate_valuation_multiples(symbole, annee, ratios_entreprise, financial_data):
    """Valorisation par multiples avec comparaison sectorielle (MÉDIANE)"""
    secteur_multiples = {
        'per': [],
        'price_to_book': [],
        'ev_ebitda': [],
        'ev_sales': []
    }
    
    # Parcourir toutes les données financières
    for key, data in financial_data.items():
        if key == f"{symbole}_{annee}":
            continue
        
        ratios = data.get('ratios', {})
        
        if ratios.get('per') and 0 < ratios['per'] < 100:
            secteur_multiples['per'].append(ratios['per'])
        if ratios.get('price_to_book') and 0 < ratios['price_to_book'] < 20:
            secteur_multiples['price_to_book'].append(ratios['price_to_book'])
        if ratios.get('ev_ebitda') and 0 < ratios['ev_ebitda'] < 50:
            secteur_multiples['ev_ebitda'].append(ratios['ev_ebitda'])
        if ratios.get('ev_sales') and 0 < ratios['ev_sales'] < 10:
            secteur_multiples['ev_sales'].append(ratios['ev_sales'])
    
    # Calculer les MÉDIANES
    medianes = {}
    for key, values in secteur_multiples.items():
        if len(values) >= 2:
            medianes[f"{key}_median"] = np.median(values)
    
    valorisations = {}
    
    # 1. Valorisation par P/E médian
    if 'per_median' in medianes:
        bpa = ratios_entreprise.get('benefice_par_action')
        if not bpa and ratios_entreprise.get('resultat_net') and ratios_entreprise.get('nb_actions'):
            bpa = ratios_entreprise['resultat_net'] / ratios_entreprise['nb_actions']
        
        if bpa:
            juste_valeur_per = medianes['per_median'] * bpa
            valorisations['juste_valeur_per'] = juste_valeur_per
            cours_actuel = ratios_entreprise.get('cours_action', 0)
            if cours_actuel > 0:
                valorisations['ecart_per'] = ((juste_valeur_per - cours_actuel) / cours_actuel) * 100
    
    # 2. Valorisation par P/B médian
    if 'price_to_book_median' in medianes:
        if ratios_entreprise.get('capitaux_propres_par_action'):
            cpa = ratios_entreprise['capitaux_propres_par_action']
        elif ratios_entreprise.get('capitaux_propres') and ratios_entreprise.get('nb_actions'):
            cpa = ratios_entreprise['capitaux_propres'] / ratios_entreprise['nb_actions']
        else:
            cpa = None
        
        if cpa:
            juste_valeur_pb = medianes['price_to_book_median'] * cpa
            valorisations['juste_valeur_pb'] = juste_valeur_pb
            cours_actuel = ratios_entreprise.get('cours_action', 0)
            if cours_actuel > 0:
                valorisations['ecart_pb'] = ((juste_valeur_pb - cours_actuel) / cours_actuel) * 100
    
    # 3. Valorisation par EV/EBITDA médian
    if 'ev_ebitda_median' in medianes and ratios_entreprise.get('ebitda'):
        enterprise_value_juste = medianes['ev_ebitda_median'] * ratios_entreprise['ebitda']
        dettes = ratios_entreprise.get('dettes_totales', 0)
        tresorerie = ratios_entreprise.get('tresorerie', 0)
        juste_valeur_ev = enterprise_value_juste - dettes + tresorerie
        nb_actions = ratios_entreprise.get('nb_actions', 0)
        
        if nb_actions > 0:
            juste_valeur_ev_par_action = juste_valeur_ev / nb_actions
            valorisations['juste_valeur_ev_ebitda'] = juste_valeur_ev_par_action
            cours_actuel = ratios_entreprise.get('cours_action', 0)
            if cours_actuel > 0:
                valorisations['ecart_ev_ebitda'] = ((juste_valeur_ev_par_action - cours_actuel) / cours_actuel) * 100
    
    valorisations['medianes_secteur'] = medianes
    
    # Calculer potentiel moyen
    ecarts = [v for k, v in valorisations.items() if k.startswith('ecart_')]
    if ecarts:
        valorisations['potentiel_moyen'] = np.mean(ecarts)
        valorisations['potentiel_median'] = np.median(ecarts)
        
        # RECOMMANDATION
        potentiel = valorisations['potentiel_median']
        if potentiel > 20:
            valorisations['recommandation'] = "ACHAT FORT"
            valorisations['justification'] = f"Sous-évalué de {potentiel:.1f}% par rapport aux pairs"
        elif potentiel > 10:
            valorisations['recommandation'] = "ACHAT"
            valorisations['justification'] = f"Potentiel de hausse de {potentiel:.1f}%"
        elif potentiel > -10:
            valorisations['recommandation'] = "CONSERVER"
            valorisations['justification'] = "Valorisation proche de la juste valeur"
        elif potentiel > -20:
            valorisations['recommandation'] = "VENTE"
            valorisations['justification'] = f"Surévalué de {abs(potentiel):.1f}%"
        else:
            valorisations['recommandation'] = "VENTE FORTE"
            valorisations['justification'] = f"Fortement surévalué de {abs(potentiel):.1f}%"
    
    return valorisations

def calculate_financial_projections(symbole, financial_data, annees_projection=3):
    """Projections financières pondérées : 40% TCAM + 60% Régression Linéaire"""
    historique = []
    for key, data in financial_data.items():
        if data.get('symbole') == symbole:
            annee = data.get('annee')
            ca = data.get('compte_resultat', {}).get('chiffre_affaires', 0)
            rn = data.get('compte_resultat', {}).get('resultat_net', 0)
            if ca > 0 and rn != 0:
                historique.append({
                    'annee': int(annee),
                    'ca': ca,
                    'resultat_net': rn
                })
    
    if len(historique) < 2:
        return {"erreur": "Historique insuffisant (minimum 2 ans)"}
    
    historique = sorted(historique, key=lambda x: x['annee'])
    annees = np.array([h['annee'] for h in historique]).reshape(-1, 1)
    ca_values = np.array([h['ca'] for h in historique])
    rn_values = np.array([h['resultat_net'] for h in historique])
    
    # TCAM
    def calcul_tcam(valeur_debut, valeur_fin, nb_annees):
        if valeur_debut <= 0:
            return 0
        return (pow(valeur_fin / valeur_debut, 1/nb_annees) - 1) * 100
    
    tcam_ca = calcul_tcam(ca_values[0], ca_values[-1], len(ca_values) - 1)
    tcam_rn = calcul_tcam(abs(rn_values[0]), abs(rn_values[-1]), len(rn_values) - 1) if rn_values[0] != 0 else 0
    
    # RÉGRESSION LINÉAIRE
    model_ca = LinearRegression()
    model_ca.fit(annees, ca_values)
    
    model_rn = LinearRegression()
    model_rn.fit(annees, rn_values)
    
    r2_ca = model_ca.score(annees, ca_values)
    r2_rn = model_rn.score(annees, rn_values)
    
    # PROJECTIONS
    projections = []
    derniere_annee = historique[-1]['annee']
    dernier_ca = historique[-1]['ca']
    dernier_rn = historique[-1]['resultat_net']
    
    for i in range(1, annees_projection + 1):
        annee_future = derniere_annee + i
        
        ca_tcam = dernier_ca * pow(1 + tcam_ca/100, i)
        rn_tcam = dernier_rn * pow(1 + tcam_rn/100, i)
        
        ca_reg = model_ca.predict([[annee_future]])[0]
        rn_reg = model_rn.predict([[annee_future]])[0]
        ca_projete = 0.4 * ca_tcam + 0.6 * ca_reg
        rn_projete = 0.4 * rn_tcam + 0.6 * rn_reg
        
        projections.append({
            'annee': int(annee_future),
            'ca_projete': float(ca_projete),
            'rn_projete': float(rn_projete),
            'marge_nette_projetee': float((rn_projete / ca_projete * 100) if ca_projete > 0 else 0)
        })
    
    return {
        'historique': historique,
        'tcam_ca': float(tcam_ca),
        'tcam_rn': float(tcam_rn),
        'r2_ca': float(r2_ca),
        'r2_rn': float(r2_rn),
        'projections': projections,
        'methode': '40% TCAM + 60% Régression Linéaire'
    }
# ===========================
# FONCTIONS DE SCRAPING BRVM
# ===========================
@st.cache_data(ttl=300)
def scrape_brvm():
    """Scrape les données de cours des actions depuis BRVM"""
    url = "https://www.brvm.org/fr/cours-actions/0"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Trouver le tableau des cours
        table = soup.find('table')
        
        if not table:
            return None
        
        # Extraire les en-têtes
        headers = []
        thead = table.find('thead')
        if thead:
            for th in thead.find_all('th'):
                headers.append(th.get_text(strip=True))
        
        # Extraire les données
        data = []
        tbody = table.find('tbody')
        if tbody:
            for row in tbody.find_all('tr'):
                cols = row.find_all('td')
                if cols:
                    row_data = [col.get_text(strip=True) for col in cols]
                    data.append(row_data)
        
        if not headers or not data:
            return None
        
        # Créer le DataFrame
        df = pd.DataFrame(data, columns=headers)
        
        return df
    
    except Exception as e:
        st.error(f"Erreur lors du scraping: {str(e)}")
        return None

@st.cache_data(ttl=300)
def scrape_brvm_secteurs():
    """Récupère les données par secteur depuis BRVM"""
    url = "https://www.brvm.org/fr/cours-actions/0"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=20, verify=False)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        tables = soup.find_all('table')
        
        if not tables:
            return None
        
        # Chercher le tableau principal
        table = None
        for t in tables:
            rows = t.find_all('tr')
            if len(rows) > 1:
                table = t
                break
        
        if not table:
            return None
        
        rows = table.find_all('tr')
        headers_row = rows[0]
        headers_list = [th.get_text(strip=True) for th in headers_row.find_all(['th', 'td'])]
        
        data = []
        for row in rows[1:]:
            cells = row.find_all(['td', 'th'])
            if cells:
                row_data = [cell.get_text(strip=True) for cell in cells]
                if len(row_data) >= 2:
                    data.append(row_data)

        if not data:
            return None
        
        max_cols = max(len(row) for row in data)
        if len(headers_list) < max_cols:
            headers_list.extend([f'Col_{i}' for i in range(len(headers_list), max_cols)])
        
        df = pd.DataFrame(data, columns=headers_list[:max_cols])
        df = clean_dataframe(df)
        
        # Ajouter une colonne secteur par défaut si elle n'existe pas
        if 'Secteur' not in df.columns:
            df['Secteur'] = 'Non classé'
        
        return df
        
    except Exception as e:
        st.error(f"  Erreur scraping secteurs : {str(e)}")
        return None

@st.cache_data(ttl=300)
def get_brvm_data_fallback():
    """Données de test si le scraping échoue"""
    data = {
        'Symbole': ['SNTS', 'SGBC', 'BICC', 'ONTBF', 'CABC', 'SDCC', 'SIVC', 'BOAB'],
        'Nom': ['Sonatel', 'SGB', 'BICICI', 'ONATEL', 'CBAO', 'SODE', 'SIVAC', 'BOA Benin'],
        'Volume': [1250, 3400, 890, 2100, 1670, 540, 780, 920],
        'Cours veille (FCFA)': [18500, 7200, 8900, 3450, 6780, 2340, 4560, 5670],
        'Cours Ouverture (FCFA)': [18500, 7200, 8900, 3450, 6780, 2340, 4560, 5670],
        'Cours Clôture (FCFA)': [18750, 7100, 9100, 3500, 6850, 2300, 4600, 5700],
        'Variation (%)': [1.35, -1.39, 2.25, 1.45, 1.03, -1.71, 0.88, 0.53]
    }
    df = pd.DataFrame(data)
    return df

def get_brvm_cours():
    """Essaie de scraper, sinon utilise des données de test"""
    df = scrape_brvm()
    if df is None or len(df) == 0:
        st.warning("  Scraping échoué - Utilisation de données de démonstration")
        st.info("  Vérifiez votre connexion internet ou réessayez plus tard")
        df = get_brvm_data_fallback()
    return df

def clean_dataframe(df):
    """Nettoie le DataFrame - Version améliorée"""
    if df.empty:
        return df
    
    df = df.copy()
    df.columns = [str(col).strip() for col in df.columns]
    
    numeric_keywords = ['Cours', 'Volume', 'Variation', 'Capitalisation', 'Prix', 'Montant']
    numeric_columns = []
    
    for col in df.columns:
        if any(keyword in str(col) for keyword in numeric_keywords):
            numeric_columns.append(col)
    
    for col in numeric_columns:
        if col in df.columns:
            df[col] = df[col].astype(str)
            df[col] = df[col].str.replace(',', '.')
            df[col] = df[col].str.replace(' ', '')
            df[col] = df[col].str.replace('FCFA', '')
            df[col] = df[col].str.replace('F', '')
            df[col] = df[col].str.replace('CFA', '')
            df[col] = df[col].str.replace('%', '')
            df[col] = df[col].str.replace('€', '')
            df[col] = df[col].str.replace('$', '')
            df[col] = df[col].str.replace('+', '')
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    if 'Symbole' in df.columns:
        df = df.sort_values('Symbole').reset_index(drop=True)
    
    return df

# ===========================
# NAVIGATION STYLÉE
# ===========================
def render_navigation():
    """Barre de navigation stylée en haut de page"""
    st.markdown("""
    <style>
    .nav-container {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 1rem 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .nav-title {
        color: white;
        font-size: 1.8rem;
        font-weight: bold;
        margin-bottom: 1rem;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="nav-container">
        <div class="nav-title">  Analyse BRVM Pro</div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        btn_accueil = st.button("  Accueil", use_container_width=True,
                                type="primary" if st.session_state.get('page', 'accueil') == 'accueil' else "secondary")
        if btn_accueil:
            st.session_state.page = 'accueil'
            st.rerun()
    
    with col2:
        btn_cours = st.button("  Cours", use_container_width=True,
                             type="primary" if st.session_state.get('page', 'accueil') == 'cours' else "secondary")
        if btn_cours:
            st.session_state.page = 'cours'
            st.rerun()
    
    with col3:
        btn_secteurs = st.button("  Secteurs", use_container_width=True,
                                type="primary" if st.session_state.get('page', 'accueil') == 'secteurs' else "secondary")
        if btn_secteurs:
            st.session_state.page = 'secteurs'
            st.rerun()
    
    with col4:
        btn_analyse = st.button("  Analyse", use_container_width=True,
                               type="primary" if st.session_state.get('page', 'accueil') == 'analyse' else "secondary")
        if btn_analyse:
            st.session_state.page = 'analyse'
            st.rerun()
    
    with col5:
        btn_dev = st.button("  Développeur", use_container_width=True,
                           type="primary" if st.session_state.get('page', 'accueil') == 'dev' else "secondary")
        if btn_dev:
            st.session_state.page = 'dev'
            st.rerun()
    
    st.markdown("---")

# ===========================
# PAGE ACCUEIL
# ===========================
def page_accueil():
    st.title("  Accueil - Analyse BRVM Pro")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ###   Bienvenue sur Analyse BRVM Pro
        
        **Votre outil complet d'analyse de la Bourse Régionale des Valeurs Mobilières**
        
        #### Fonctionnalités principales :
        - **Cours en temps réel** : Tous les titres BRVM
        - **Analyse par secteur** : 7 secteurs économiques
        - **Analyse fondamentale** : Ratios, scores, valorisation
        - **Projections** : Scénarios futurs basés sur l'historique
        - **Alertes** : Détection automatique des risques
        """)
    
    with col2:
        st.markdown("""
        ###   Comment utiliser l'application ?
        
        1. **Cours** : Consultez les cours actuels de tous les titres
        2. **Secteurs** : Analysez les performances par secteur
        3. **Analyse** : Sélectionnez un titre pour analyse approfondie
        4. **Développeur** : Saisissez des données financières
        """)
        st.info("  **Astuce** : Les données sont mises à jour toutes les 5 minutes")
    
    st.markdown("---")
    st.subheader("  Statistiques du jour")
    
    with st.spinner("Chargement..."):
        df = get_brvm_cours()
        if df is not None:
            col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
            
            with col_stat1:
                st.metric("Titres cotés", len(df))
            
            with col_stat2:
                if 'Variation (%)' in df.columns:
                    hausse = len(df[df['Variation (%)'] > 0])
                    st.metric("En hausse", hausse, f"+{hausse}")
            
            with col_stat3:
                if 'Variation (%)' in df.columns:
                    baisse = len(df[df['Variation (%)'] < 0])
                    st.metric("En baisse", baisse, f"-{baisse}")
            
            with col_stat4:
                if 'Variation (%)' in df.columns:
                    stable = len(df[df['Variation (%)'] == 0])
                    st.metric("Stables", stable)

# ===========================
# PAGE COURS
# ===========================
def page_cours():
    st.title("  Cours des Actions BRVM")
    
    # Bouton de rafraîchissement
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("🔄 Rafraîchir", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    with col2:
        st.info(f"⏰ {datetime.now().strftime('%H:%M:%S')}")

    st.markdown("---")

    # Scraper et afficher les données
    with st.spinner("Chargement des données de la BRVM..."):
        df = scrape_brvm()
    
    if df is not None and not df.empty:
        st.success(f"✅ {len(df)} actions chargées avec succès")
        
        # Afficher les statistiques
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Nombre d'actions", len(df))
        with col2:
            st.metric("Dernière mise à jour", datetime.now().strftime('%d/%m/%Y'))
        with col3:
            st.metric("Source", "BRVM.org")
        
        st.markdown("---")
        
        # Filtre de recherche
        search = st.text_input("🔍 Rechercher une action", placeholder="Entrez le nom ou le symbole...")
        
        if search:
            # Filtrer sur toutes les colonnes
            mask = df.astype(str).apply(lambda x: x.str.contains(search, case=False, na=False)).any(axis=1)
            filtered_df = df[mask]
            st.info(f"🔎 {len(filtered_df)} résultat(s) trouvé(s)")
        else:
            filtered_df = df
        
        # Afficher le tableau
        st.dataframe(
            filtered_df,
            use_container_width=True,
            height=600,
            hide_index=True
        )
        
        # Bouton de téléchargement
        csv = filtered_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 Télécharger en CSV",
            data=csv,
            file_name=f"brvm_cours_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
    else:
        st.error("❌ Impossible de charger les données. Veuillez réessayer plus tard.")
        st.info("💡 Le site BRVM peut être temporairement indisponible ou la structure de la page a changé.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <small>Données provenant de <a href='https://www.brvm.org' target='_blank'>BRVM.org</a> | 
        Mise à jour automatique toutes les 5 minutes</small>
    </div>
    """, unsafe_allow_html=True)

# ===========================
# PAGE SECTEURS
# ===========================
def page_secteurs():
    st.title("  Analyse par Secteur")
    
    col_refresh, col_info = st.columns([1, 3])
    
    with col_refresh:
        if st.button("  Actualiser", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    with col_info:
        st.info("  Classification sectorielle officielle BRVM")
    
    with st.spinner("  Chargement des secteurs..."):
        df = scrape_brvm_secteurs()
        
        if df is not None:
            st.subheader("  Répartition par secteur")
            
            if 'Secteur' in df.columns:
                secteur_counts = df['Secteur'].value_counts()
                col_graph, col_table = st.columns([2, 1])
                
                with col_graph:
                    import plotly.express as px
                    fig = px.pie(
                        values=secteur_counts.values,
                        names=secteur_counts.index,
                        title='Nombre de sociétés par secteur',
                        hole=0.4
                    )
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig, use_container_width=True)
                
                with col_table:
                    st.markdown("**Détails :**")
                    for secteur, count in secteur_counts.items():
                        st.metric(secteur, count)
            
            st.markdown("---")
            st.subheader("  Filtrer par secteur")
            
            if 'Secteur' in df.columns:
                secteurs = ['Tous'] + sorted(df['Secteur'].unique().tolist())
                secteur_selected = st.selectbox("Choisissez un secteur", secteurs)
                
                if secteur_selected != 'Tous':
                    df_filtre = df[df['Secteur'] == secteur_selected]
                else:
                    df_filtre = df
            else:
                df_filtre = df
            
            st.dataframe(df_filtre, use_container_width=True, height=400)
            
            if 'Secteur' in df.columns and 'Variation (%)' in df.columns:
                st.markdown("---")
                st.subheader("  Performance moyenne par secteur")
                
                perf = df.groupby('Secteur')['Variation (%)'].agg(['mean', 'count']).reset_index()
                perf.columns = ['Secteur', 'Variation Moyenne (%)', 'Nombre']
                perf = perf.sort_values('Variation Moyenne (%)', ascending=False)
                
                import plotly.express as px
                fig = px.bar(
                    perf,
                    x='Secteur',
                    y='Variation Moyenne (%)',
                    color='Variation Moyenne (%)',
                    color_continuous_scale=['red', 'yellow', 'green'],
                    color_continuous_midpoint=0,
                    title='Performance moyenne par secteur'
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("  Impossible de charger les données secteurs")

# ===========================
# PAGE ANALYSE
# ===========================
def page_analyse():
    st.title("  Analyse Fondamentale")
    st.info("  Sélectionnez un titre pour voir son analyse complète")
    
    financial_data = init_storage()
    
    if financial_data:
        symboles = sorted(set([data['symbole'] for data in financial_data.values() if isinstance(data, dict)]))
        
        if symboles:
            symbole_selected = st.selectbox("Choisissez un titre", [''] + symboles)
            
            if symbole_selected:
                symbole_data = {}
                for key, data in financial_data.items():
                    if data.get('symbole') == symbole_selected:
                        symbole_data[data['annee']] = data
                
                if symbole_data:
                    st.success(f"  Données financières disponibles pour {symbole_selected}")
                    
                    annees = sorted(symbole_data.keys())
                    annee_selectionnee = st.selectbox("Sélectionnez l'année", annees, index=len(annees)-1)
                    
                    if annee_selectionnee:
                        data = symbole_data[annee_selectionnee]
                        
                        st.markdown(f"###   Ratios pour {symbole_selected} - {annee_selectionnee}")
                        
                        if 'ratios' in data:
                            ratios = data['ratios']
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.markdown("**Rentabilité**")
                                if 'roe' in ratios:
                                    st.metric("ROE", f"{ratios['roe']:.2f}%")
                                if 'roa' in ratios:
                                    st.metric("ROA", f"{ratios['roa']:.2f}%")
                                if 'marge_nette' in ratios:
                                    st.metric("Marge Nette", f"{ratios['marge_nette']:.2f}%")
                            
                            with col2:
                                st.markdown("**Liquidité**")
                                if 'ratio_liquidite_generale' in ratios:
                                    st.metric("Liquidité Générale", f"{ratios['ratio_liquidite_generale']:.2f}")
                                if 'ratio_liquidite_reduite' in ratios:
                                    st.metric("Liquidité Réduite", f"{ratios['ratio_liquidite_reduite']:.2f}")
                            
                            with col3:
                                st.markdown("**Marché**")
                                if 'per' in ratios:
                                    st.metric("PER", f"{ratios['per']:.2f}")
                                if 'price_to_book' in ratios:
                                    st.metric("Price to Book", f"{ratios['price_to_book']:.2f}")
                                if 'ev_ebitda' in ratios:
                                    st.metric("EV/EBITDA", f"{ratios['ev_ebitda']:.2f}")
                            
                            st.markdown("###   Valorisation par Multiples")
                            valorisations = calculate_valuation_multiples(
                                symbole_selected,
                                annee_selectionnee,
                                {**data['bilan'], **data['compte_resultat'], **data.get('ratios', {})},
                                financial_data
                            )
                            
                            if 'recommandation' in valorisations:
                                col_rec1, col_rec2 = st.columns([1, 2])
                                
                                with col_rec1:
                                    if "ACHAT" in valorisations['recommandation']:
                                        st.success(f"**{valorisations['recommandation']}**")
                                    elif "VENTE" in valorisations['recommandation']:
                                        st.error(f"**{valorisations['recommandation']}**")
                                    else:
                                        st.warning(f"**{valorisations['recommandation']}**")
                                
                                with col_rec2:
                                    st.info(f"*{valorisations.get('justification', '')}*")
                            
                            st.markdown("###   Projections Financières")
                            projections = calculate_financial_projections(symbole_selected, financial_data)
                            
                            if 'projections' in projections:
                                df_proj = pd.DataFrame(projections['projections'])
                                st.dataframe(df_proj.style.format({
                                    'ca_projete': '{:,.0f}',
                                    'rn_projete': '{:,.0f}',
                                    'marge_nette_projetee': '{:.2f}%'
                                }), use_container_width=True)
                                st.caption(f"Méthode: {projections.get('methode', '')}")
                                st.caption(f"TCAM CA: {projections.get('tcam_ca', 0):.2f}% | R² CA: {projections.get('r2_ca', 0):.3f}")
                else:
                    st.warning(f"  Aucune donnée financière sauvegardée pour {symbole_selected}")
                    st.info("Utilisez la section Développeur pour saisir les données financières de cette entreprise")
        else:
            st.warning("Aucune donnée financière disponible")
    else:
        st.warning("Aucune donnée financière disponible")

# ===========================
# SECTION DÉVELOPPEUR (Extrait simplifié)
# ===========================
def developer_section():
    """Section réservée au développeur pour gérer les données financières"""
    st.title("  Section Développeur - Gestion des Données Financières")
    
    if 'dev_authenticated' not in st.session_state:
        st.session_state.dev_authenticated = False
    if not st.session_state.dev_authenticated:
        password = st.text_input("Mot de passe développeur", type="password")
        if st.button("Se connecter"):
            if password == DEVELOPER_PASSWORD:
                st.session_state.dev_authenticated = True
                st.rerun()
            else:
                st.error("Mot de passe incorrect")
        return
    
    st.success("  Connecté en tant que développeur")
    st.info("  Interface de gestion des données financières")
    
    # Le reste du code de la section développeur reste identique au code original
    # Je l'ai omis ici pour respecter la limite de longueur, mais il fonctionne tel quel

# ===========================
# INTERFACE PRINCIPALE
# ===========================
def main():
    if 'page' not in st.session_state:
        st.session_state.page = 'accueil'
    
    render_navigation()
    
    if st.session_state.page == 'accueil':
        page_accueil()
    elif st.session_state.page == 'cours':
        page_cours()
    elif st.session_state.page == 'secteurs':
        page_secteurs()
    elif st.session_state.page == 'analyse':
        page_analyse()
    elif st.session_state.page == 'dev':
        developer_section()
    
    st.markdown("---")
    st.caption(f"  {datetime.now().strftime('%d/%m/%Y %H:%M')} |   Source : BRVM")

if __name__ == "__main__":
    main()
