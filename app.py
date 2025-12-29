# ======================
# THE CAPITAL PROJECT
# ======================

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

# Désactiver les warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore')

# ======================
# CONFIGURATION
# ======================

# Configuration Streamlit
st.set_page_config(page_title="Analyse BRVM", layout="wide")

# Mot de passe développeur
DEVELOPER_PASSWORD = "dev_brvm_2024"

# Configuration Supabase
SUPABASE_URL = "https://otsiwiwnowxeolbbgvm.supabase.co"
SUPABASE_KEY = "sb_publishable_Mhal5b-kMmb5liIMOJ4P3Q_xGTsJAFJ"

# ======================
# INITIALISATION SUPABASE
# ======================

def init_supabase():
    """Initialiser la connexion à Supabase"""
    if 'supabase' not in st.session_state:
        try:
            st.session_state.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            # Test de connexion
            test_response = st.session_state.supabase.table("financial_data").select("*", count="exact").limit(1).execute()
            if not hasattr(st, '__supabase_success_shown'):
                st._supabase_success_shown = True
        except Exception as e:
            st.error(f"Erreur de connexion Supabase: {str(e)}")
            return None
    return st.session_state.supabase

def init_storage():
    """Initialiser le stockage avec Supabase"""
    if 'financial_data' not in st.session_state:
        st.session_state.financial_data = load_all_financial_data()
    if 'symbol_mapping' not in st.session_state:
        st.session_state.symbol_mapping = load_symbol_mapping()
    return st.session_state.financial_data

# ======================
# FONCTIONS DE GESTION SUPABASE AVEC NOMS
# ======================

def get_company_name(symbole):
    """Récupérer le nom complet d'une entreprise à partir de son symbole"""
    if not hasattr(st.session_state, 'symbol_mapping'):
        st.session_state.symbol_mapping = load_symbol_mapping()
    
    mapping = st.session_state.symbol_mapping
    return mapping.get(symbole, symbole)  # Retourne le nom complet ou le symbole si non trouvé

def format_company_display(symbole):
    """Formater l'affichage symbole - nom pour l'interface"""
    nom_complet = get_company_name(symbole)
    return f"{symbole} - {nom_complet}"

def load_symbol_mapping():
    """Charger le mapping des symboles depuis Supabase"""
    supabase = init_supabase()
    if not supabase:
        return {}

    try:
        response = supabase.table("symbol_mapping").select("*").execute()
        mapping = {}
        for record in response.data:
            mapping[record['symbole']] = record['nom_complet']
        return mapping
    except Exception as e:
        st.error(f"Erreur de chargement du mapping: {str(e)}")
        return {}

def save_symbol_mapping(symbole, nom_complet):
    """Sauvegarder un mapping dans Supabase"""
    supabase = init_supabase()
    if not supabase:
        return False

    try:
        record = {
            'symbole': symbole,
            'nom_complet': nom_complet,
            'last_update': datetime.now().isoformat()
        }

        # Vérifier si l'entrée existe déjà
        existing = supabase.table("symbol_mapping") \
            .select("*") \
            .eq("symbole", symbole) \
            .execute()

        if existing.data:
            # Mise à jour
            response = supabase.table("symbol_mapping") \
                .update(record) \
                .eq("symbole", symbole) \
                .execute()
        else:
            # Insertion
            response = supabase.table("symbol_mapping").insert(record).execute()
        
        # Mettre à jour le cache local
        if 'symbol_mapping' in st.session_state:
            st.session_state.symbol_mapping[symbole] = nom_complet
        
        return True
    except Exception as e:
        st.error(f"Erreur de sauvegarde du mapping: {str(e)}")
        return False

def delete_symbol_mapping(symbole):
    """Supprimer un mapping de Supabase"""
    supabase = init_supabase()
    if not supabase:
        return False

    try:
        response = supabase.table("symbol_mapping") \
            .delete() \
            .eq("symbole", symbole) \
            .execute()
        
        # Mettre à jour le cache local
        if 'symbol_mapping' in st.session_state and symbole in st.session_state.symbol_mapping:
            del st.session_state.symbol_mapping[symbole]
        
        return True
    except Exception as e:
        st.error(f"Erreur de suppression du mapping: {str(e)}")
        return False

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
        existing = supabase.table("financial_data") \
            .select("*") \
            .eq("symbole", symbole) \
            .eq("annee", annee) \
            .execute()

        if existing.data:
            # Mise à jour
            response = supabase.table("financial_data") \
                .update(record) \
                .eq("symbole", symbole) \
                .eq("annee", annee) \
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
        response = supabase.table("financial_data") \
            .delete() \
            .eq("symbole", symbole) \
            .eq("annee", annee) \
            .execute()
        
        return True
    except Exception as e:
        st.error(f"Erreur de suppression: {str(e)}")
        return False

# ======================
# FONCTIONS DE CALCUL DES RATIOS
# ======================

def calculate_enhanced_financial_ratios(bilan, compte_resultat, flux_tresorerie):
    """Version améliorée avec tous les ratios standards"""
    ratios = {}

    # ====================== CALCULS INTERMÉDIAIRES CRITIQUES ====================
    ebitda = compte_resultat.get('resultat_exploitation', 0)
    ebit = compte_resultat.get('resultat_exploitation', 0)
    fcf = flux_tresorerie.get('flux_exploitation', 0) + flux_tresorerie.get('flux_investissement', 0)
    working_capital = bilan.get('actif_courant', 0) - bilan.get('passif_courant', 0)

    market_cap = bilan.get('cours_action', 0) * bilan.get('nb_actions', 0)
    enterprise_value = market_cap + bilan.get('dettes_totales', 0) - bilan.get('tresorerie', 0)

    # ====================== RATIOS DE RENTABILITÉ ====================
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

    # 1. Valorisation par P/E median
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

    # 2. Valorisation par P/B median
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

    # 3. Valorisation par EV/EBITDA median
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
    def calcul_team(valeur_debut, valeur_fin, nb_annees):
        if valeur_debut <= 0:
            return 0
        return (pow(valeur_fin / valeur_debut, 1/nb_annees) - 1) * 100

    tcam_ca = calcul_team(ca_values[0], ca_values[-1], len(ca_values) - 1)
    tcam_rn = calcul_team(abs(rn_values[0]), abs(rn_values[-1]), len(rn_values) - 1) if rn_values[0] != 0 else 0

    # REGRESSION LINEAIRE
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

        ca_team = dernier_ca * pow(1 + tcam_ca/100, i)
        rn_team = dernier_rn * pow(1 + tcam_rn/100, i)

        ca_reg = model_ca.predict([[annee_future]])[0]
        rn_reg = model_rn.predict([[annee_future]])[0]
        ca_projete = 0.4 * ca_team + 0.6 * ca_reg
        rn_projete = 0.4 * rn_team + 0.6 * rn_reg

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
        'methode': '40% TCAM + 60% Regression Linéaire'
    }

# ======================
# FONCTIONS DE SCRAPING DES COURS
# ======================

@st.cache_data(ttl=300)
def scrape_brvm():
    """Scrape les données de cours des actions depuis Sikafinance"""
    url = "https://www.sikafinance.com/marches/aaz"

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        }

        # Requête avec vérification SSL désactivée
        response = requests.get(url, headers=headers, verify=False, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Trouver toutes les tables
        tables = soup.find_all('table')

        if len(tables) < 2:
            return None, None

        # Première table : Les indices
        indices_table = tables[0]
        indices_data = []
        indices_headers = []

        # Extraire les en-têtes des indices
        thead = indices_table.find('thead')
        if thead:
            for th in thead.find_all('th'):
                indices_headers.append(th.get_text(strip=True))
        else:
            # Si pas de thead, prendre la première ligne comme en-tête
            first_row = indices_table.find('tr')
            if first_row:
                for th in first_row.find_all(['th', 'td']):
                    indices_headers.append(th.get_text(strip=True))

        # Extraire les données des indices
        tbody = indices_table.find('tbody')
        if tbody:
            for row in tbody.find_all('tr'):
                cols = row.find_all('td')
                if cols and len(cols) > 0:
                    row_data = [col.get_text(strip=True) for col in cols]
                    indices_data.append(row_data)

        # Deuxième table : Les actions
        actions_table = tables[1]
        actions_data = []
        actions_headers = []

        # Extraire les en-têtes des actions
        thead = actions_table.find('thead')
        if thead:
            for th in thead.find_all('th'):
                actions_headers.append(th.get_text(strip=True))
        else:
            # Si pas de thead, prendre la première ligne comme en-tête
            first_row = actions_table.find('tr')
            if first_row:
                for th in first_row.find_all(['th', 'td']):
                    actions_headers.append(th.get_text(strip=True))

        # Extraire les données des actions
        tbody = actions_table.find('tbody')
        if tbody:
            for row in tbody.find_all('tr'):
                cols = row.find_all('td')
                if cols and len(cols) > 0:
                    row_data = [col.get_text(strip=True) for col in cols]
                    actions_data.append(row_data)

        # Créer les DataFrames
        df_indices = None
        df_actions = None

        if indices_headers and indices_data:
            df_indices = pd.DataFrame(indices_data, columns=indices_headers)

        if actions_headers and actions_data:
            df_actions = pd.DataFrame(actions_data, columns=actions_headers)

        return df_indices, df_actions

    except Exception as e:
        st.error(f"Erreur lors du scraping: {str(e)}")
        return None, None

# ======================
# NAVIGATION STYLÉE
# ======================
def render_navigation():
    """Barre de navigation style en haut de page"""
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
    <div class="nav-title">📊 Analyse BRVM Pro</div>  
    </div>  
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        btn_accueil = st.button("🏠 Accueil", use_container_width=True,
                               type="primary" if st.session_state.get('page', 'accueil') == 'accueil' else "secondary")
        if btn_accueil:
            st.session_state.page = 'accueil'
            st.rerun()

    with col2:
        btn_cours = st.button("📈 Cours", use_container_width=True,
                             type="primary" if st.session_state.get('page', 'accueil') == 'cours' else "secondary")
        if btn_cours:
            st.session_state.page = 'cours'
            st.rerun()

    with col3:
        btn_analyse = st.button("📊 Analyse", use_container_width=True,
                               type="primary" if st.session_state.get('page', 'accueil') == 'analyse' else "secondary")
        if btn_analyse:
            st.session_state.page = 'analyse'
            st.rerun()

    with col4:
        btn_dev = st.button("⚙️ Développeur", use_container_width=True,
                           type="primary" if st.session_state.get('page', 'accueil') == 'dev' else "secondary")
        if btn_dev:
            st.session_state.page = 'dev'
            st.rerun()

    st.markdown("---")

# ======================
# PAGES DE L'APPLICATION
# ======================
def page_accueil():
    st.title("🏠 Accueil - Analyse BRVM Pro")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        ### 📊 Bienvenue sur Analyse BRVM Pro

        **Votre outil d'analyse fondamentale pour la Bourse Régionale des Valeurs Mobilières**

        ### Fonctionnalités :
        - **📈 Cours en direct**: Données de marché depuis Sika Finance
        - **📊 Analyse fondamentale**: Ratios financiers et valorisation
        - **🔮 Projections**: Scénarios futurs basés sur l'historique
        - **📊 Comparaisons sectorielles**: Multiples de valorisation
        """)

    with col2:
        st.markdown("""
        ### 📝 Comment utiliser ?

        1. **⚙️ Développeur**: Configurez les entreprises et les données
        2. **📊 Analyse**: Sélectionnez un titre pour analyse détaillée
        3. **📈 Cours**: Suivez les cotations en temps réel
        """)

    st.info("💡 **Conseil** : Commencez par configurer vos entreprises dans la section Développeur")

    st.markdown("---")
    st.subheader("📊 Statistiques")

    financial_data = init_storage()
    if financial_data:
        entreprises = set([data['symbole'] for data in financial_data.values() if isinstance(data, dict)])
        total_donnees = len(financial_data)

        col_stat1, col_stat2, col_stat3 = st.columns(3)

        with col_stat1:
            st.metric("🏢 Entreprises", len(entreprises))

        with col_stat2:
            st.metric("📄 Données financières", total_donnees)

        with col_stat3:
            if 'symbol_mapping' in st.session_state:
                noms_configures = len(st.session_state.symbol_mapping)
                st.metric("📝 Noms configurés", noms_configures)
            else:
                st.metric("📝 Noms configurés", 0)
    else:
        st.info("ℹ️ Aucune donnée financière disponible. Rendez-vous dans la section Développeur pour configurer.")

def page_cours():
    st.title("📈 Cours des Actions BRVM")

    # Scraper et afficher les données
    with st.spinner("🔄 Chargement des données de la BRVM..."):
        df_indices, df_actions = scrape_brvm()

    if df_indices is not None or df_actions is not None:
        st.success("✅ Données chargées avec succès depuis Sikafinance")

        # Onglets pour séparer indices et actions
        tab1, tab2 = st.tabs(["📊 Actions Cotées", "📈 Indices BRVM"])

        with tab1:
            if df_actions is not None and not df_actions.empty:
                # Statistiques des actions
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Nombre d'actions", len(df_actions))
                with col2:
                    st.metric("Dernière mise à jour", datetime.now().strftime('%d/%m/%Y %H:%M'))
                with col3:
                    st.metric("Source", "Sikafinance")
                st.markdown("---")

                # Filtre de recherche
                search = st.text_input("🔍 Rechercher une action", placeholder="Entrez le nom ou le symbole...")

                if search:
                    mask = df_actions.astype(str).apply(lambda x: x.str.contains(search, case=False, na=False)).any(axis=1)
                    filtered_df = df_actions[mask]
                    st.info(f"🔍 {len(filtered_df)} résultat(s) trouvé(s)")
                else:
                    filtered_df = df_actions

                # Afficher le tableau des actions
                st.dataframe(
                    filtered_df,
                    use_container_width=True,
                    height=500,
                    hide_index=True)

                # Bouton de téléchargement
                csv_actions = filtered_df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="💾 Télécharger les actions en CSV",
                    data=csv_actions,
                    file_name=f"brvm_actions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("⚠️ Aucune donnée d'action disponible")

        with tab2:
            if df_indices is not None and not df_indices.empty:
                st.subheader("📈 Indices du marché BRVM")

                # Afficher le tableau des indices
                st.dataframe(
                    df_indices,
                    use_container_width=True,
                    height=500,
                    hide_index=True
                )

                # Bouton de téléchargement
                csv_indices = df_indices.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="💾 Télécharger les indices en CSV",
                    data=csv_indices,
                    file_name=f"brvm_indices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("⚠️ Aucune donnée d'indice disponible")
    else:
        st.error("❌ Impossible de charger les données. Veuillez réessayer plus tard.")
        st.info("💡 Le site source peut être temporairement indisponible.")

def page_analyse():
    st.title("📊 Analyse Fondamentale")

    financial_data = init_storage()

    if not financial_data:
        st.warning("⚠️ Aucune donnée financière disponible.")
        st.info("ℹ️ Rendez-vous dans la section Développeur pour saisir des données financières.")
        return

    symboles = sorted(set([data['symbole'] for data in financial_data.values() if isinstance(data, dict)]))

    if not symboles:
        st.warning("⚠️ Aucune entreprise trouvée dans les données.")
        return

    # Créer les options avec format: "SNTS - Sonatel S.A."
    options = []
    for symbole in symboles:
        display_name = format_company_display(symbole)
        options.append(display_name)

    # Sélection de l'entreprise
    selected_option = st.selectbox("📋 Choisissez une entreprise", [""] + options)

    if selected_option:
        # Extraire le symbole de l'option sélectionnée
        symbole_selected = selected_option.split(" - ")[0]
        nom_complet_entreprise = get_company_name(symbole_selected)

        # Récupérer les données de cette entreprise
        symbole_data = {}
        for key, data in financial_data.items():
            if data.get('symbole') == symbole_selected:
                symbole_data[data['annee']] = data

        if symbole_data:
            # Afficher le nom complet
            st.success(f"✅ Données disponibles pour {nom_complet_entreprise}")

            # Sélection de l'année
            annees = sorted(symbole_data.keys())
            annee_selectionnee = st.selectbox("📅 Sélectionnez l'année", annees, index=len(annees)-1)

            if annee_selectionnee:
                data = symbole_data[annee_selectionnee]

                # Onglets pour l'analyse
                tab1, tab2, tab3, tab4 = st.tabs([
                    "📊 Ratios Financiers", 
                    "💰 Valorisation", 
                    "🔮 Projections", 
                    "📄 Données Brutes"
                ])

                with tab1:
                    st.subheader(f"📊 Ratios Financiers - {annee_selectionnee} - {nom_complet_entreprise}")

                    if 'ratios' in data:
                        ratios = data['ratios']
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.markdown("**📈 Rentabilité**")
                            if 'roe' in ratios:
                                st.metric("ROE (Rentabilité des Capitaux Propres)", f"{ratios['roe']:.2f}%")
                            if 'roa' in ratios:
                                st.metric("ROA (Rentabilité de l'Actif)", f"{ratios['roa']:.2f}%")
                            if 'marge_nette' in ratios:
                                st.metric("Marge Nette", f"{ratios['marge_nette']:.2f}%")

                        with col2:
                            st.markdown("**💧 Liquidité**")
                            if 'ratio_liquidite_generale' in ratios:
                                st.metric("Liquidité Générale", f"{ratios['ratio_liquidite_generale']:.2f}")
                            if 'ratio_liquidite_reduite' in ratios:
                                st.metric("Liquidité Réduite", f"{ratios['ratio_liquidite_reduite']:.2f}")
                            if 'ratio_liquidite_immediate' in ratios:
                                st.metric("Liquidité Immédiate", f"{ratios['ratio_liquidite_immediate']:.2f}")

                        with col3:
                            st.markdown("**🏦 Endettement**")
                            if 'ratio_endettement' in ratios:
                                st.metric("Ratio d'Endettement", f"{ratios['ratio_endettement']:.2f}%")
                            if 'debt_to_ebitda' in ratios:
                                st.metric("Dette/EBITDA", f"{ratios['debt_to_ebitda']:.2f}")
                            if 'couverture_interets' in ratios:
                                st.metric("Couverture des Intérêts", f"{ratios['couverture_interets']:.2f}x")

                with tab2:
                    st.subheader(f"💰 Valorisation par Multiples - {nom_complet_entreprise}")

                    valorisations = calculate_valuation_multiples(
                        symbole_selected,
                        annee_selectionnee,
                        {**data['bilan'], **data['compte_resultat'], **data.get('ratios', {})},
                        financial_data
                    )
                    
                    if 'recommandation' in valorisations:
                        col_rec1, col_rec2 = st.columns([1, 3])
                        with col_rec1:
                            if "ACHAT FORT" in valorisations['recommandation']:
                                st.success(f"## {valorisations['recommandation']}")
                            elif "ACHAT" in valorisations['recommandation']:
                                st.success(f"## {valorisations['recommandation']}")
                            elif "VENTE" in valorisations['recommandation']:
                                st.error(f"## {valorisations['recommandation']}")
                            elif "VENTE FORTE" in valorisations['recommandation']:
                                st.error(f"## {valorisations['recommandation']}")
                            else:
                                st.warning(f"## {valorisations['recommandation']}")
                        with col_rec2:
                            st.info(f"**Justification :** {valorisations.get('justification', '')}")

                    # Afficher les multiples de valorisation
                    if 'medianes_secteur' in valorisations:
                        st.markdown("### 📊 Multiples Sectoriels (Médiane)")
                        medianes = valorisations['medianes_secteur']
                        if medianes:
                            df_medianes = pd.DataFrame(list(medianes.items()), columns=['Multiple', 'Valeur'])
                            st.dataframe(df_medianes, use_container_width=True)

                with tab3:
                    st.subheader(f"🔮 Projections Financières - {nom_complet_entreprise}")

                    projections = calculate_financial_projections(symbole_selected, financial_data)

                    if 'projections' in projections:
                        st.markdown(f"**Méthode :** {projections.get('methode', '')}")
                        st.markdown(f"**TCAM du CA :** {projections.get('tcam_ca', 0):.2f}%")
                        st.markdown(f"**TCAM du Résultat Net :** {projections.get('tcam_rn', 0):.2f}%")

                        df_proj = pd.DataFrame(projections['projections'])
                        st.dataframe(df_proj.style.format({
                            'ca_projete': '{:.0f}',
                            'rn_projete': '{:.0f}',
                            'marge_nette_projetee': '{:.2f}%'
                        }), use_container_width=True)
                    elif 'erreur' in projections:
                        st.warning(projections['erreur'])

                with tab4:
                    st.subheader(f"📄 Données Brutes - {nom_complet_entreprise}")

                    col_brut1, col_brut2 = st.columns(2)

                    with col_brut1:
                        if data.get('bilan'):
                            st.markdown("**📊 Bilan**")
                            df_bilan = pd.DataFrame(list(data['bilan'].items()), columns=['Poste', 'Valeur'])
                            st.dataframe(df_bilan, use_container_width=True)

                    with col_brut2:
                        if data.get('compte_resultat'):
                            st.markdown("**📈 Compte de résultat**")
                            df_cr = pd.DataFrame(list(data['compte_resultat'].items()), columns=['Poste', 'Valeur'])
                            st.dataframe(df_cr, use_container_width=True)

# ======================
# SECTION DÉVELOPPEUR SIMPLIFIÉE
# ======================
def developer_section():
    """Section réservée au développeur pour gérer les données"""
    st.title("⚙️ Section Développeur")

    if 'dev_authenticated' not in st.session_state:
        st.session_state.dev_authenticated = False
    
    if not st.session_state.dev_authenticated:
        password = st.text_input("🔐 Mot de passe développeur", type="password")
        if st.button("🔓 Se connecter"):
            if password == DEVELOPER_PASSWORD:
                st.session_state.dev_authenticated = True
                st.rerun()
            else:
                st.error("❌ Mot de passe incorrect")
        return

    st.success("✅ Connecté en tant que développeur")

    # Onglets développeur
    tab1, tab2, tab3 = st.tabs([
        "📊 Données Financières",
        "🏢 Noms des Entreprises",
        "⚙️ Paramètres"
    ])
    
    with tab1:
        st.header("📊 Gestion des Données Financières")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("➕ Ajouter/Modifier des données")
            symbole = st.text_input("Symbole BRVM (ex: SNTS)", key="dev_symbole")
            annee = st.number_input("Année", min_value=2000, max_value=2030, value=2023, key="dev_annee")

            with st.expander("📊 Bilan"):
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    actif_total = st.number_input("Actif Total", value=0.0, key="bilan_actif_total")
                    actif_courant = st.number_input("Actif Courant", value=0.0, key="bilan_actif_courant")
                    stocks = st.number_input("Stocks", value=0.0, key="bilan_stocks")
                    creances = st.number_input("Créances", value=0.0, key="bilan_creances")
                    tresorerie = st.number_input("Trésorerie", value=0.0, key="bilan_tresorerie")
                with col_b2:
                    capitaux_propres = st.number_input("Capitaux Propres", value=0.0, key="bilan_capitaux_propres")
                    dettes_totales = st.number_input("Dettes Totales", value=0.0, key="bilan_dettes_totales")
                    passif_courant = st.number_input("Passif Courant", value=0.0, key="bilan_passif_courant")
                    cours_action = st.number_input("Cours Action", value=0.0, key="bilan_cours_action")
                    nb_actions = st.number_input("Nombre d'Actions", value=0.0, key="bilan_nb_actions")

            with st.expander("📈 Compte de Résultat"):
                chiffre_affaires = st.number_input("Chiffre d'Affaires", value=0.0, key="cr_chiffre_affaires")
                resultat_exploitation = st.number_input("Résultat Exploitation", value=0.0, key="cr_resultat_exploitation")
                resultat_net = st.number_input("Résultat Net", value=0.0, key="cr_resultat_net")
                charges_financieres = st.number_input("Charges Financières", value=0.0, key="cr_charges_financieres")
                benefice_par_action = st.number_input("Bénéfice par Action", value=0.0, key="cr_benefice_par_action")

            with st.expander("💸 Flux de Trésorerie"):
                flux_exploitation = st.number_input("Flux d'Exploitation", value=0.0, key="ft_flux_exploitation")
                flux_investissement = st.number_input("Flux d'investissement", value=0.0, key="ft_flux_investissement")
                flux_financement = st.number_input("Flux de Financement", value=0.0, key="ft_flux_financement")

            if st.button("💾 Sauvegarder les Données", type="primary", use_container_width=True):
                if symbole and annee:
                    data_dict = {
                        'bilan': {
                            'actif_total': actif_total,
                            'actif_courant': actif_courant,
                            'stocks': stocks,
                            'creances': creances,
                            'tresorerie': tresorerie,
                            'capitaux_propres': capitaux_propres,
                            'dettes_totales': dettes_totales,
                            'passif_courant': passif_courant,
                            'cours_action': cours_action,
                            'nb_actions': nb_actions
                        },
                        'compte_resultat': {
                            'chiffre_affaires': chiffre_affaires,
                            'resultat_exploitation': resultat_exploitation,
                            'resultat_net': resultat_net,
                            'charges_financieres': charges_financieres,
                            'benefice_par_action': benefice_par_action
                        },
                        'flux_tresorerie': {
                            'flux_exploitation': flux_exploitation,
                            'flux_investissement': flux_investissement,
                            'flux_financement': flux_financement
                        }
                    }

                    # Calculer les ratios
                    ratios = calculate_enhanced_financial_ratios(
                        data_dict['bilan'], data_dict['compte_resultat'], data_dict['flux_tresorerie']
                    )
                    data_dict['ratios'] = ratios

                    if save_financial_data(symbole, annee, data_dict):
                        st.success(f"✅ Données sauvegardées pour {symbole} - {annee}")
                        st.session_state.financial_data = load_all_financial_data()
                        st.rerun()
                    else:
                        st.error("❌ Erreur lors de la sauvegarde")
                else:
                    st.error("⚠️ Veuillez remplir le symbole et l'année")

        with col2:
            st.subheader("🗑️ Supprimer des données")

            financial_data = init_storage()
            if financial_data:
                options = []
                for key, data in financial_data.items():
                    if isinstance(data, dict):
                        symbole = data.get('symbole', '')
                        annee = data.get('annee', '')
                        nom_complet = get_company_name(symbole)
                        options.append(f"{format_company_display(symbole)} ({annee})")

                if options:
                    selected = st.selectbox("Sélectionnez les données à supprimer", [""] + options)

                    if selected and st.button("🗑️ Supprimer", type="secondary", use_container_width=True):
                        # Extraire symbole et année
                        parts = selected.split(" (")
                        symbole = parts[0].split(" - ")[0]
                        annee = parts[1].replace(")", "")

                        if delete_financial_data(symbole, int(annee)):
                            st.success(f"✅ Données supprimées pour {symbole} - {annee}")
                            st.session_state.financial_data = load_all_financial_data()
                            st.rerun()
                        else:
                            st.error("❌ Erreur lors de la suppression")
                else:
                    st.info("📄 Aucune donnée à supprimer")

    with tab2:
        st.header("🏢 Noms des Entreprises")
        st.info("""
        🔗 Associez un nom complet à chaque symbole BRVM pour améliorer l'interface.
        
        **Exemple:**
        - Symbole: "SNTS" → Nom: "Sonatel S.A."
        - Symbole: "SHEC" → Nom: "Vivo Energy Côte d'Ivoire"
        """)

        # Afficher les mappings existants
        symbol_mapping = load_symbol_mapping()
        st.session_state.symbol_mapping = symbol_mapping

        if symbol_mapping:
            st.subheader("📝 Noms configurés")
            df_mapping = pd.DataFrame(
                [(k, v) for k, v in symbol_mapping.items()],
                columns=["Symbole BRVM", "Nom Complet"]
            )
            st.dataframe(df_mapping, use_container_width=True)

        # Ajouter/Modifier un mapping
        st.subheader("➕ Ajouter/Modifier un nom")

        # Charger les symboles existants dans les données financières
        financial_data = init_storage()
        symboles_existants = sorted(set([data['symbole'] for data in financial_data.values() if isinstance(data, dict)]))
        
        col_map1, col_map2 = st.columns(2)

        with col_map1:
            if symboles_existants:
                symbole = st.selectbox("Symbole BRVM", [""] + symboles_existants)
            else:
                symbole = st.text_input("Symbole BRVM", placeholder="Ex: SNTS")

        with col_map2:
            nom_complet = st.text_input("Nom complet de l'entreprise", placeholder="Ex: Sonatel S.A.")

        col_btn1, col_btn2 = st.columns(2)

        with col_btn1:
            if st.button("💾 Sauvegarder", type="primary", use_container_width=True):
                if symbole and nom_complet:
                    if save_symbol_mapping(symbole, nom_complet):
                        st.success(f"✅ Nom sauvegardé: {symbole} → {nom_complet}")
                        st.session_state.symbol_mapping = load_symbol_mapping()
                        st.rerun()
                    else:
                        st.error("❌ Erreur lors de la sauvegarde")
                else:
                    st.error("⚠️ Veuillez remplir tous les champs")

        with col_btn2:
            if symbol_mapping and symbole in symbol_mapping:
                if st.button("🗑️ Supprimer", type="secondary", use_container_width=True):
                    if delete_symbol_mapping(symbole):
                        st.success(f"✅ Nom supprimé pour {symbole}")
                        st.session_state.symbol_mapping = load_symbol_mapping()
                        st.rerun()
                    else:
                        st.error("❌ Erreur lors de la suppression")

    with tab3:
        st.header("⚙️ Paramètres")

        st.subheader("🔌 Configuration Supabase")
        st.info(f"URL: {SUPABASE_URL}")

        if st.button("🔍 Tester la connexion Supabase", use_container_width=True):
            supabase = init_supabase()
            if supabase:
                st.success("✅ Connexion Supabase active")
            else:
                st.error("❌ Erreur de connexion Supabase")

        st.subheader("🗑️ Gestion du cache")
        if st.button("🧹 Vider le cache", type="secondary", use_container_width=True):
            st.cache_data.clear()
            st.success("✅ Cache vidé")

        st.subheader("🔓 Déconnexion")
        if st.button("🚪 Se déconnecter", type="secondary", use_container_width=True):
            st.session_state.dev_authenticated = False
            st.rerun()

# ======================
# INTERFACE PRINCIPALE
# ======================
def main():
    if 'page' not in st.session_state:
        st.session_state.page = 'accueil'

    render_navigation()

    if st.session_state.page == 'accueil':
        page_accueil()
    elif st.session_state.page == 'cours':
        page_cours()
    elif st.session_state.page == 'analyse':
        page_analyse()
    elif st.session_state.page == 'dev':
        developer_section()

    st.markdown("---")
    st.caption(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')} | 📊 Analyse BRVM Pro v1.0")

if __name__ == "__main__":
    main()
