# ======================
# THE CAPITAL PROJECT - VERSION PROFESSIONNELLE
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
st.set_page_config(
    page_title="Capital Project - Analyse BRVM Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Mot de passe développeur (À DÉPLACER DANS SECRETS STREAMLIT)
DEVELOPER_PASSWORD = st.secrets.get("DEV_PASSWORD", "dev_brvm_2024")

# Configuration Supabase (À DÉPLACER DANS SECRETS STREAMLIT)
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "https://otsiwiwlnowxeolbbgvm.supabase.co")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "sb_publishable_MhaI5b-kMmb5liIMOJ4P3Q_xGTsJAFJ")

# ======================
# STYLES CSS PROFESSIONNELS
# ======================
def load_custom_css():
    st.markdown("""
    <style>
    /* Variables de couleur */
    :root {
        --primary-color: #1e3c72;
        --secondary-color: #2a5298;
        --accent-color: #00d4ff;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --danger-color: #ef4444;
        --bg-dark: #0f172a;
        --text-light: #f1f5f9;
    }
    
    /* Navigation moderne */
    .nav-container {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    }
    
    .nav-title {
        color: white;
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 1rem;
        text-align: center;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    /* Cartes statistiques */
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        transition: transform 0.3s ease;
    }
    
    .stat-card:hover {
        transform: translateY(-5px);
    }
    
    /* Tables professionnelles */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    /* Boutons d'action */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    
    /* Secteur drag & drop zone */
    .sector-dropzone {
        border: 2px dashed var(--accent-color);
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background: rgba(0, 212, 255, 0.05);
        transition: all 0.3s ease;
    }
    
    .sector-dropzone:hover {
        background: rgba(0, 212, 255, 0.1);
        border-color: var(--success-color);
    }
    
    /* Tag entreprise */
    .company-tag {
        display: inline-block;
        background: var(--primary-color);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        margin: 0.3rem;
        font-size: 0.9rem;
        cursor: move;
        transition: all 0.2s ease;
    }
    
    .company-tag:hover {
        background: var(--accent-color);
        transform: scale(1.05);
    }
    
    /* Recommandations d'achat/vente */
    .recommendation-buy-strong {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 1rem 2rem;
        border-radius: 10px;
        font-size: 1.5rem;
        font-weight: bold;
        text-align: center;
        animation: pulse 2s infinite;
    }
    
    .recommendation-sell-strong {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
        padding: 1rem 2rem;
        border-radius: 10px;
        font-size: 1.5rem;
        font-weight: bold;
        text-align: center;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
    }
    
    /* Masquer "Powered by Streamlit" */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Professional footer */
    .custom-footer {
        text-align: center;
        padding: 2rem;
        color: #64748b;
        font-size: 0.9rem;
        border-top: 1px solid #e2e8f0;
        margin-top: 3rem;
    }
    </style>
    """, unsafe_allow_html=True)

# ======================
# INITIALISATION SUPABASE
# ======================
@st.cache_resource
def init_supabase():
    """Initialiser la connexion à Supabase avec gestion d'erreurs"""
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        # Test de connexion silencieux
        test_response = supabase.table("financial_data").select("*", count="exact").limit(1).execute()
        return supabase
    except Exception as e:
        st.error(f"⚠️ Erreur de connexion base de données: {str(e)}")
        return None

def init_storage():
    """Initialiser le stockage avec cache local"""
    if 'financial_data' not in st.session_state:
        st.session_state.financial_data = load_all_financial_data()
    if 'symbol_mapping' not in st.session_state:
        st.session_state.symbol_mapping = load_symbol_mapping()
    if 'sector_mapping' not in st.session_state:
        st.session_state.sector_mapping = load_sector_mapping()
    return st.session_state.financial_data

# ======================
# GESTION DES SECTEURS (NOUVEAU)
# ======================
def load_sector_mapping():
    """Charger le mapping secteur → entreprises depuis Supabase"""
    supabase = init_supabase()
    if not supabase:
        return {}
    
    try:
        response = supabase.table("sector_mapping").select("*").execute()
        sector_map = {}
        for record in response.data:
            sector_name = record['sector_name']
            companies = record.get('companies', [])
            sector_map[sector_name] = companies
        return sector_map
    except Exception as e:
        # Table n'existe pas encore, retourner dict vide
        return {}

def save_sector_mapping(sector_name, companies):
    """Sauvegarder un secteur avec ses entreprises"""
    supabase = init_supabase()
    if not supabase:
        return False
    
    try:
        record = {
            'sector_name': sector_name,
            'companies': companies,
            'last_update': datetime.now().isoformat()
        }
        
        # Vérifier si le secteur existe
        existing = supabase.table("sector_mapping").select("*").eq("sector_name", sector_name).execute()
        
        if existing.data:
            response = supabase.table("sector_mapping").update(record).eq("sector_name", sector_name).execute()
        else:
            response = supabase.table("sector_mapping").insert(record).execute()
        
        # Mettre à jour le cache
        if 'sector_mapping' in st.session_state:
            st.session_state.sector_mapping[sector_name] = companies
        
        return True
    except Exception as e:
        st.error(f"Erreur sauvegarde secteur: {str(e)}")
        return False

def delete_sector(sector_name):
    """Supprimer un secteur"""
    supabase = init_supabase()
    if not supabase:
        return False
    
    try:
        response = supabase.table("sector_mapping").delete().eq("sector_name", sector_name).execute()
        
        if 'sector_mapping' in st.session_state and sector_name in st.session_state.sector_mapping:
            del st.session_state.sector_mapping[sector_name]
        
        return True
    except Exception as e:
        st.error(f"Erreur suppression secteur: {str(e)}")
        return False

# ======================
# GESTION NOMS ENTREPRISES
# ======================
def get_company_name(symbole):
    """Récupérer le nom complet d'une entreprise"""
    if 'symbol_mapping' not in st.session_state:
        st.session_state.symbol_mapping = load_symbol_mapping()
    
    mapping = st.session_state.symbol_mapping
    return mapping.get(symbole, symbole)

def format_company_display(symbole):
    """Formater l'affichage: SYMBOLE - Nom Complet"""
    nom_complet = get_company_name(symbole)
    if nom_complet == symbole:
        return symbole
    return f"{symbole} - {nom_complet}"

def load_symbol_mapping():
    """Charger le mapping symboles → noms"""
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
        return {}

def save_symbol_mapping(symbole, nom_complet):
    """Sauvegarder un mapping symbole → nom"""
    supabase = init_supabase()
    if not supabase:
        return False
    
    try:
        # Validation
        if not symbole or not nom_complet:
            st.error("❌ Symbole et nom complet requis")
            return False
        
        symbole = symbole.strip().upper()
        nom_complet = nom_complet.strip()
        
        record = {
            'symbole': symbole,
            'nom_complet': nom_complet,
            'last_update': datetime.now().isoformat()
        }
        
        existing = supabase.table("symbol_mapping").select("*").eq("symbole", symbole).execute()
        
        if existing.data:
            response = supabase.table("symbol_mapping").update(record).eq("symbole", symbole).execute()
        else:
            response = supabase.table("symbol_mapping").insert(record).execute()
        
        if 'symbol_mapping' in st.session_state:
            st.session_state.symbol_mapping[symbole] = nom_complet
        
        return True
    except Exception as e:
        st.error(f"Erreur sauvegarde: {str(e)}")
        return False

def delete_symbol_mapping(symbole):
    """Supprimer un mapping"""
    supabase = init_supabase()
    if not supabase:
        return False
    
    try:
        response = supabase.table("symbol_mapping").delete().eq("symbole", symbole).execute()
        
        if 'symbol_mapping' in st.session_state and symbole in st.session_state.symbol_mapping:
            del st.session_state.symbol_mapping[symbole]
        
        return True
    except Exception as e:
        st.error(f"Erreur suppression: {str(e)}")
        return False

# ======================
# GESTION DONNÉES FINANCIÈRES
# ======================
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
        st.error(f"⚠️ Erreur chargement données: {str(e)}")
        return {}

def save_financial_data(symbole, annee, data_dict):
    """Sauvegarder les données financières avec validation"""
    supabase = init_supabase()
    if not supabase:
        return False
    
    try:
        # Validation des données
        if not symbole or not annee:
            st.error("❌ Symbole et année requis")
            return False
        
        symbole = symbole.strip().upper()
        
        if not isinstance(annee, int) or annee < 2000 or annee > 2030:
            st.error("❌ Année invalide (2000-2030)")
            return False
        
        record = {
            'symbole': symbole,
            'annee': annee,
            'data': data_dict,
            'last_update': datetime.now().isoformat()
        }
        
        existing = supabase.table("financial_data") \
            .select("*") \
            .eq("symbole", symbole) \
            .eq("annee", annee) \
            .execute()
        
        if existing.data:
            response = supabase.table("financial_data") \
                .update(record) \
                .eq("symbole", symbole) \
                .eq("annee", annee) \
                .execute()
        else:
            response = supabase.table("financial_data").insert(record).execute()
        
        # Mettre à jour le cache
        key = f"{symbole}_{annee}"
        if 'financial_data' in st.session_state:
            st.session_state.financial_data[key] = {
                'symbole': symbole,
                'annee': annee,
                **data_dict
            }
        
        return True
    except Exception as e:
        st.error(f"⚠️ Erreur sauvegarde: {str(e)}")
        return False

def delete_financial_data(symbole, annee):
    """Supprimer des données financières"""
    supabase = init_supabase()
    if not supabase:
        return False
    
    try:
        response = supabase.table("financial_data") \
            .delete() \
            .eq("symbole", symbole) \
            .eq("annee", annee) \
            .execute()
        
        # Mettre à jour le cache
        key = f"{symbole}_{annee}"
        if 'financial_data' in st.session_state and key in st.session_state.financial_data:
            del st.session_state.financial_data[key]
        
        return True
    except Exception as e:
        st.error(f"⚠️ Erreur suppression: {str(e)}")
        return False

# ======================
# CALCULS FINANCIERS AVANCÉS
# ======================
def calculate_enhanced_financial_ratios(bilan, compte_resultat, flux_tresorerie):
    """Calcul de tous les ratios financiers avec validation"""
    ratios = {}
    
    # Validation des données d'entrée
    if not isinstance(bilan, dict) or not isinstance(compte_resultat, dict):
        return ratios
    
    # Calculs intermédiaires critiques
    ebitda = compte_resultat.get('resultat_exploitation', 0)
    ebit = compte_resultat.get('resultat_exploitation', 0)
    fcf = flux_tresorerie.get('flux_exploitation', 0) + flux_tresorerie.get('flux_investissement', 0)
    working_capital = bilan.get('actif_courant', 0) - bilan.get('passif_courant', 0)
    market_cap = bilan.get('cours_action', 0) * bilan.get('nb_actions', 0)
    enterprise_value = market_cap + bilan.get('dettes_totales', 0) - bilan.get('tresorerie', 0)
    
    # ========== RATIOS DE RENTABILITÉ ==========
    try:
        if compte_resultat.get('resultat_net') and compte_resultat.get('chiffre_affaires', 0) > 0:
            ratios['marge_nette'] = (compte_resultat['resultat_net'] / compte_resultat['chiffre_affaires']) * 100
    except (ZeroDivisionError, TypeError):
        pass
    
    try:
        if ebit and compte_resultat.get('chiffre_affaires', 0) > 0:
            ratios['marge_ebit'] = (ebit / compte_resultat['chiffre_affaires']) * 100
    except (ZeroDivisionError, TypeError):
        pass
    
    try:
        if ebitda and compte_resultat.get('chiffre_affaires', 0) > 0:
            ratios['marge_ebitda'] = (ebitda / compte_resultat['chiffre_affaires']) * 100
    except (ZeroDivisionError, TypeError):
        pass
    
    try:
        if compte_resultat.get('resultat_net') and bilan.get('capitaux_propres', 0) > 0:
            ratios['roe'] = (compte_resultat['resultat_net'] / bilan['capitaux_propres']) * 100
    except (ZeroDivisionError, TypeError):
        pass
    
    try:
        if compte_resultat.get('resultat_net') and bilan.get('actif_total', 0) > 0:
            ratios['roa'] = (compte_resultat['resultat_net'] / bilan['actif_total']) * 100
    except (ZeroDivisionError, TypeError):
        pass
    
    try:
        if ebit and bilan.get('actif_total', 0) > 0:
            roic_denom = bilan['actif_total'] - bilan.get('passif_courant', 0)
            if roic_denom > 0:
                ratios['roic'] = (ebit * 0.75 / roic_denom) * 100
    except (ZeroDivisionError, TypeError):
        pass
    
    # ========== RATIOS DE LIQUIDITÉ ==========
    try:
        if bilan.get('actif_courant', 0) > 0 and bilan.get('passif_courant', 0) > 0:
            ratios['ratio_liquidite_generale'] = bilan['actif_courant'] / bilan['passif_courant']
    except (ZeroDivisionError, TypeError):
        pass
    
    try:
        if bilan.get('actif_courant', 0) > 0 and bilan.get('passif_courant', 0) > 0:
            actif_liquide = bilan['actif_courant'] - bilan.get('stocks', 0)
            ratios['ratio_liquidite_reduite'] = actif_liquide / bilan['passif_courant']
    except (ZeroDivisionError, TypeError):
        pass
    
    try:
        if bilan.get('tresorerie', 0) > 0 and bilan.get('passif_courant', 0) > 0:
            ratios['ratio_liquidite_immediate'] = bilan['tresorerie'] / bilan['passif_courant']
    except (ZeroDivisionError, TypeError):
        pass
    
    # ========== RATIOS D'ENDETTEMENT ==========
    try:
        if bilan.get('dettes_totales', 0) > 0 and bilan.get('capitaux_propres', 0) > 0:
            ratios['ratio_endettement'] = (bilan['dettes_totales'] / bilan['capitaux_propres']) * 100
    except (ZeroDivisionError, TypeError):
        pass
    
    try:
        if bilan.get('dettes_totales', 0) > 0 and bilan.get('actif_total', 0) > 0:
            ratios['taux_endettement'] = (bilan['dettes_totales'] / bilan['actif_total']) * 100
    except (ZeroDivisionError, TypeError):
        pass
    
    try:
        if bilan.get('capitaux_propres', 0) > 0 and bilan.get('actif_total', 0) > 0:
            ratios['ratio_solvabilite'] = (bilan['capitaux_propres'] / bilan['actif_total']) * 100
    except (ZeroDivisionError, TypeError):
        pass
    
    try:
        if bilan.get('dettes_totales', 0) > 0 and ebitda > 0:
            ratios['debt_to_ebitda'] = bilan['dettes_totales'] / ebitda
    except (ZeroDivisionError, TypeError):
        pass
    
    try:
        if ebit and compte_resultat.get('charges_financieres', 0) != 0:
            ratios['couverture_interets'] = ebit / abs(compte_resultat['charges_financieres'])
    except (ZeroDivisionError, TypeError):
        pass
    
    # ========== RATIOS D'EFFICACITÉ ==========
    try:
        if compte_resultat.get('chiffre_affaires', 0) > 0 and bilan.get('actif_total', 0) > 0:
            ratios['rotation_actifs'] = compte_resultat['chiffre_affaires'] / bilan['actif_total']
    except (ZeroDivisionError, TypeError):
        pass
    
    try:
        if compte_resultat.get('chiffre_affaires', 0) > 0 and bilan.get('stocks', 0) > 0:
            ratios['rotation_stocks'] = compte_resultat['chiffre_affaires'] / bilan['stocks']
    except (ZeroDivisionError, TypeError):
        pass
    
    try:
        if bilan.get('creances', 0) > 0 and compte_resultat.get('chiffre_affaires', 0) > 0:
            ratios['delai_recouvrement'] = (bilan['creances'] / compte_resultat['chiffre_affaires']) * 365
    except (ZeroDivisionError, TypeError):
        pass
    
    # ========== RATIOS DE MARCHÉ ==========
    try:
        if bilan.get('cours_action', 0) > 0 and compte_resultat.get('benefice_par_action', 0) > 0:
            ratios['per'] = bilan['cours_action'] / compte_resultat['benefice_par_action']
        elif bilan.get('cours_action', 0) > 0 and compte_resultat.get('resultat_net') and bilan.get('nb_actions', 0) > 0:
            bpa = compte_resultat['resultat_net'] / bilan['nb_actions']
            if bpa > 0:
                ratios['per'] = bilan['cours_action'] / bpa
                ratios['benefice_par_action'] = bpa
    except (ZeroDivisionError, TypeError):
        pass
    
    try:
        if bilan.get('cours_action', 0) > 0 and bilan.get('capitaux_propres_par_action', 0) > 0:
            ratios['price_to_book'] = bilan['cours_action'] / bilan['capitaux_propres_par_action']
        elif bilan.get('cours_action', 0) > 0 and bilan.get('capitaux_propres', 0) > 0 and bilan.get('nb_actions', 0) > 0:
            cpa = bilan['capitaux_propres'] / bilan['nb_actions']
            ratios['price_to_book'] = bilan['cours_action'] / cpa
    except (ZeroDivisionError, TypeError):
        pass
    
    try:
        if enterprise_value > 0 and ebitda > 0:
            ratios['ev_ebitda'] = enterprise_value / ebitda
    except (ZeroDivisionError, TypeError):
        pass
    
    try:
        if enterprise_value > 0 and compte_resultat.get('chiffre_affaires', 0) > 0:
            ratios['ev_sales'] = enterprise_value / compte_resultat['chiffre_affaires']
    except (ZeroDivisionError, TypeError):
        pass
    
    # ========== RATIOS DE FLUX DE TRÉSORERIE ==========
    try:
        if flux_tresorerie.get('flux_exploitation') and compte_resultat.get('resultat_net', 0) != 0:
            ratios['qualite_benefices'] = flux_tresorerie['flux_exploitation'] / compte_resultat['resultat_net']
    except (ZeroDivisionError, TypeError):
        pass
    
    try:
        if fcf and market_cap > 0:
            ratios['fcf_yield'] = (fcf / market_cap) * 100
    except (ZeroDivisionError, TypeError):
        pass
    
    try:
        if fcf and bilan.get('dettes_totales', 0) > 0:
            ratios['fcf_to_debt'] = fcf / bilan['dettes_totales']
    except (ZeroDivisionError, TypeError):
        pass
    
    # ========== DONNÉES INTERMÉDIAIRES ==========
    ratios['ebitda'] = ebitda
    ratios['ebit'] = ebit
    ratios['fcf'] = fcf
    ratios['working_capital'] = working_capital
    ratios['enterprise_value'] = enterprise_value
    ratios['market_cap'] = market_cap
    
    return ratios

def calculate_valuation_multiples(symbole, annee, ratios_entreprise, financial_data):
    """Valorisation par multiples sectoriels (MÉDIANE)"""
    secteur_multiples = {
        'per': [],
        'price_to_book': [],
        'ev_ebitda': [],
        'ev_sales': []
    }
    
    # Récupérer le secteur de l'entreprise
    sector_mapping = st.session_state.get('sector_mapping', {})
    current_sector = None
    
    for sector_name, companies in sector_mapping.items():
        if symbole in companies:
            current_sector = sector_name
            break
    
    # Si secteur trouvé, comparer uniquement avec les entreprises du même secteur
    if current_sector:
        companies_in_sector = sector_mapping[current_sector]
        
        for key, data in financial_data.items():
            if key == f"{symbole}_{annee}":
                continue
            
            data_symbole = data.get('symbole')
            if data_symbole not in companies_in_sector:
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
    else:
        # Pas de secteur, comparer avec toutes les entreprises
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
        if not bpa:
            resultat_net = ratios_entreprise.get('resultat_net')
            nb_actions = ratios_entreprise.get('nb_actions')
            if resultat_net and nb_actions and nb_actions > 0:
                bpa = resultat_net / nb_actions
        
        if bpa and bpa > 0:
            juste_valeur_per = medianes['per_median'] * bpa
            valorisations['juste_valeur_per'] = juste_valeur_per
            
            cours_actuel = ratios_entreprise.get('cours_action', 0)
            if cours_actuel > 0:
                valorisations['ecart_per'] = ((juste_valeur_per - cours_actuel) / cours_actuel) * 100
    
    # 2. Valorisation par P/B median
    if 'price_to_book_median' in medianes:
        cpa = ratios_entreprise.get('capitaux_propres_par_action')
        if not cpa:
            capitaux_propres = ratios_entreprise.get('capitaux_propres')
            nb_actions = ratios_entreprise.get('nb_actions')
            if capitaux_propres and nb_actions and nb_actions > 0:
                cpa = capitaux_propres / nb_actions
        
        if cpa and cpa > 0:
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
    valorisations['secteur_utilise'] = current_sector if current_sector else "Toutes entreprises"
    
    # Calculer potentiel moyen
    ecarts = [v for k, v in valorisations.items() if k.startswith('ecart_')]
    if ecarts:
        valorisations['potentiel_moyen'] = np.mean(ecarts)
        valorisations['potentiel_median'] = np.median(ecarts)
        
        # RECOMMANDATION
        potentiel = valorisations['potentiel_median']
        if potentiel > 20:
            valorisations['recommandation'] = "ACHAT FORT"
            valorisations['justification'] = f"Sous-évalué de {potentiel:.1f}% par rapport au secteur"
            valorisations['style_class'] = "recommendation-buy-strong"
        elif potentiel > 10:
            valorisations['recommandation'] = "ACHAT"
            valorisations['justification'] = f"Potentiel de hausse de {potentiel:.1f}%"
            valorisations['style_class'] = "recommendation-buy"
        elif potentiel > -10:
            valorisations['recommandation'] = "CONSERVER"
            valorisations['justification'] = "Valorisation proche de la juste valeur"
            valorisations['style_class'] = "recommendation-hold"
        elif potentiel > -20:
            valorisations['recommandation'] = "VENTE"
            valorisations['justification'] = f"Surévalué de {abs(potentiel):.1f}%"
            valorisations['style_class'] = "recommendation-sell"
        else:
            valorisations['recommandation'] = "VENTE FORTE"
            valorisations['justification'] = f"Fortement surévalué de {abs(potentiel):.1f}%"
            valorisations['style_class'] = "recommendation-sell-strong"
    
    return valorisations

def calculate_financial_projections(symbole, financial_data, annees_projection=3):
    """Projections financières: 40% TCAM + 60% Régression Linéaire"""
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
        return {"erreur": "Historique insuffisant (minimum 2 ans requis)"}
    
    historique = sorted(historique, key=lambda x: x['annee'])
    
    annees = np.array([h['annee'] for h in historique]).reshape(-1, 1)
    ca_values = np.array([h['ca'] for h in historique])
    rn_values = np.array([h['resultat_net'] for h in historique])
    
    # TCAM (Taux de Croissance Annuel Moyen)
    def calcul_tcam(valeur_debut, valeur_fin, nb_annees):
        if valeur_debut <= 0:
            return 0
        return (pow(valeur_fin / valeur_debut, 1/nb_annees) - 1) * 100
    
    tcam_ca = calcul_tcam(ca_values[0], ca_values[-1], len(ca_values) - 1)
    tcam_rn = calcul_tcam(abs(rn_values[0]), abs(rn_values[-1]), len(rn_values) - 1) if rn_values[0] != 0 else 0
    
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
        
        # Projection TCAM
        ca_tcam = dernier_ca * pow(1 + tcam_ca/100, i)
        rn_tcam = dernier_rn * pow(1 + tcam_rn/100, i)
        
        # Projection Régression
        ca_reg = model_ca.predict([[annee_future]])[0]
        rn_reg = model_rn.predict([[annee_future]])[0]
        
        # Pondération: 40% TCAM + 60% Régression
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

# ======================
# SCRAPING DONNÉES MARCHÉ
# ======================
@st.cache_data(ttl=300)
def scrape_brvm():
    """Scraper professionnel des données de marché (source masquée)"""
    url = "https://www.sikafinance.com/marches/aaz"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        
        response = requests.get(url, headers=headers, verify=False, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        tables = soup.find_all('table')
        
        if len(tables) < 2:
            return None, None
        
        # Table des indices
        indices_table = tables[0]
        indices_data = []
        indices_headers = []
        
        thead = indices_table.find('thead')
        if thead:
            for th in thead.find_all('th'):
                indices_headers.append(th.get_text(strip=True))
        else:
            first_row = indices_table.find('tr')
            if first_row:
                for th in first_row.find_all(['th', 'td']):
                    indices_headers.append(th.get_text(strip=True))
        
        tbody = indices_table.find('tbody')
        if tbody:
            for row in tbody.find_all('tr'):
                cols = row.find_all('td')
                if cols:
                    row_data = [col.get_text(strip=True) for col in cols]
                    indices_data.append(row_data)
        
        # Table des actions
        actions_table = tables[1]
        actions_data = []
        actions_headers = []
        
        thead = actions_table.find('thead')
        if thead:
            for th in thead.find_all('th'):
                actions_headers.append(th.get_text(strip=True))
        else:
            first_row = actions_table.find('tr')
            if first_row:
                for th in first_row.find_all(['th', 'td']):
                    actions_headers.append(th.get_text(strip=True))
        
        tbody = actions_table.find('tbody')
        if tbody:
            for row in tbody.find_all('tr'):
                cols = row.find_all('td')
                if cols:
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
        st.error(f"⚠️ Erreur lors de la récupération des données: {str(e)}")
        return None, None

# ======================
# NAVIGATION PROFESSIONNELLE
# ======================
def render_navigation():
    """Barre de navigation moderne et professionnelle"""
    st.markdown("""
    <div class="nav-container">
        <div class="nav-title">📊 Capital Project - Analyse BRVM Pro</div>
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
        btn_cours = st.button("📈 Cotations", use_container_width=True,
                              type="primary" if st.session_state.get('page', 'accueil') == 'cours' else "secondary")
        if btn_cours:
            st.session_state.page = 'cours'
            st.rerun()
    
    with col3:
        btn_analyse = st.button("🔍 Analyse", use_container_width=True,
                                type="primary" if st.session_state.get('page', 'accueil') == 'analyse' else "secondary")
        if btn_analyse:
            st.session_state.page = 'analyse'
            st.rerun()
    
    with col4:
        btn_dev = st.button("⚙️ Admin", use_container_width=True,
                            type="primary" if st.session_state.get('page', 'accueil') == 'dev' else "secondary")
        if btn_dev:
            st.session_state.page = 'dev'
            st.rerun()
    
    st.markdown("---")

# ======================
# PAGE ACCUEIL
# ======================
def page_accueil():
    st.title("🏠 Tableau de Bord")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### Bienvenue sur Capital Project
        **Votre plateforme professionnelle d'analyse fondamentale pour la BRVM**
        
        ---
        
        #### 🎯 Fonctionnalités Premium
        
        **📊 Analyse Fondamentale Complète**
        - 25+ ratios financiers calculés automatiquement
        - ROE, ROA, ROIC, marges bénéficiaires
        - Ratios de liquidité et solvabilité
        
        **💎 Valorisation par Multiples Sectoriels**
        - Comparaison avec les médianes du secteur
        - P/E, P/B, EV/EBITDA, EV/Sales
        - Recommandations d'achat/vente algorithmiques
        
        **🔮 Projections Financières**
        - Modèles hybrides (TCAM + Régression)
        - Prévisions sur 3-5 ans
        - Analyse de tendances
        
        **📈 Cotations en Temps Réel**
        - Suivi des cours actualisés
        - Indices BRVM
        - Export CSV
        """)
    
    with col2:
        st.markdown("""
        ### 🚀 Démarrage Rapide
        
        **1️⃣ Configuration**
        Accédez à la section **Admin** pour :
        - Ajouter vos entreprises
        - Saisir les données financières
        - Créer des secteurs personnalisés
        
        **2️⃣ Analyse**
        Sélectionnez une entreprise dans **Analyse** pour :
        - Voir les ratios détaillés
        - Obtenir une recommandation
        - Consulter les projections
        
        **3️⃣ Suivi**
        Consultez les **Cotations** pour :
        - Suivre les cours en direct
        - Surveiller les indices
        - Exporter les données
        """)
    
    st.markdown("---")
    
    # Statistiques du système
    st.subheader("📊 Statistiques de la Plateforme")
    
    financial_data = init_storage()
    
    if financial_data:
        entreprises = set([data['symbole'] for data in financial_data.values() if isinstance(data, dict)])
        total_donnees = len(financial_data)
        
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        
        with col_stat1:
            st.markdown(f"""
            <div class="stat-card">
                <h2 style="margin:0;">{len(entreprises)}</h2>
                <p style="margin:0;">Entreprises</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col_stat2:
            st.markdown(f"""
            <div class="stat-card">
                <h2 style="margin:0;">{total_donnees}</h2>
                <p style="margin:0;">Données Annuelles</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col_stat3:
            noms_configures = len(st.session_state.get('symbol_mapping', {}))
            st.markdown(f"""
            <div class="stat-card">
                <h2 style="margin:0;">{noms_configures}</h2>
                <p style="margin:0;">Noms Configurés</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col_stat4:
            nb_secteurs = len(st.session_state.get('sector_mapping', {}))
            st.markdown(f"""
            <div class="stat-card">
                <h2 style="margin:0;">{nb_secteurs}</h2>
                <p style="margin:0;">Secteurs Définis</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("💡 **Aucune donnée disponible.** Commencez par configurer vos entreprises dans la section Admin.")

# ======================
# PAGE COTATIONS
# ======================
def page_cours():
    st.title("📈 Cotations du Marché")
    
    with st.spinner("⏳ Chargement des données de marché..."):
        df_indices, df_actions = scrape_brvm()
    
    if df_indices is not None or df_actions is not None:
        st.success("✅ Données actualisées avec succès")
        
        tab1, tab2 = st.tabs(["📊 Actions Cotées", "📉 Indices"])
        
        with tab1:
            if df_actions is not None and not df_actions.empty:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("📌 Nombre d'actions", len(df_actions))
                
                with col2:
                    st.metric("🕐 Dernière mise à jour", datetime.now().strftime('%H:%M:%S'))
                
                with col3:
                    st.metric("📅 Date", datetime.now().strftime('%d/%m/%Y'))
                
                st.markdown("---")
                
                # Recherche intelligente avec correspondance symbole/nom
                search = st.text_input("🔍 Rechercher une action", placeholder="Entrez le symbole (ex: SNTS) ou le nom complet...")
                
                if search:
                    search_upper = search.strip().upper()
                    
                    # Recherche dans les symboles ET les noms complets
                    mask = df_actions.astype(str).apply(
                        lambda x: x.str.contains(search, case=False, na=False)
                    ).any(axis=1)
                    
                    # Recherche aussi dans le mapping symbole → nom
                    symbol_mapping = st.session_state.get('symbol_mapping', {})
                    matching_symbols = []
                    
                    for symbole, nom_complet in symbol_mapping.items():
                        if search_upper in symbole.upper() or search.lower() in nom_complet.lower():
                            matching_symbols.append(symbole)
                    
                    # Combiner les résultats
                    if matching_symbols:
                        mask_symbols = df_actions.astype(str).apply(
                            lambda x: x.str.contains('|'.join(matching_symbols), case=False, na=False)
                        ).any(axis=1)
                        mask = mask | mask_symbols
                    
                    filtered_df = df_actions[mask]
                    
                    if len(filtered_df) > 0:
                        st.success(f"✅ {len(filtered_df)} résultat(s) trouvé(s)")
                    else:
                        st.warning(f"⚠️ Aucun résultat pour '{search}'")
                else:
                    filtered_df = df_actions
                
                # Afficher le tableau avec les noms complets si disponibles
                display_df = filtered_df.copy()
                
                # Ajouter une colonne "Nom Complet" si on peut identifier le symbole
                if 'Symbole' in display_df.columns or 'Code' in display_df.columns:
                    symbole_col = 'Symbole' if 'Symbole' in display_df.columns else 'Code'
                    
                    def add_company_name(row):
                        symbole = str(row[symbole_col]).strip().upper()
                        nom = get_company_name(symbole)
                        return nom if nom != symbole else ""
                    
                    display_df['Nom Complet'] = display_df.apply(add_company_name, axis=1)
                
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    height=500,
                    hide_index=True
                )
                
                # Export CSV
                csv_actions = filtered_df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="💾 Télécharger en CSV",
                    data=csv_actions,
                    file_name=f"brvm_actions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.warning("⚠️ Aucune donnée d'action disponible")
        
        with tab2:
            if df_indices is not None and not df_indices.empty:
                st.subheader("📉 Indices Boursiers")
                
                st.dataframe(
                    df_indices,
                    use_container_width=True,
                    height=400,
                    hide_index=True
                )
                
                csv_indices = df_indices.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="💾 Télécharger en CSV",
                    data=csv_indices,
                    file_name=f"brvm_indices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.warning("⚠️ Aucune donnée d'indice disponible")
    else:
        st.error("❌ Impossible de charger les données du marché")
        st.info("💡 Le service de données est temporairement indisponible. Veuillez réessayer dans quelques instants.")

# ======================
# PAGE ANALYSE
# ======================
def page_analyse():
    st.title("🔍 Analyse Fondamentale")
    
    financial_data = init_storage()
    
    if not financial_data:
        st.warning("⚠️ Aucune donnée financière disponible.")
        st.info("💡 Rendez-vous dans la section **Admin** pour saisir vos premières données.")
        return
    
    symboles = sorted(set([data['symbole'] for data in financial_data.values() if isinstance(data, dict)]))
    
    if not symboles:
        st.warning("⚠️ Aucune entreprise trouvée.")
        return
    
    # Options de sélection avec noms complets
    options = [format_company_display(symbole) for symbole in symboles]
    
    selected_option = st.selectbox("🏢 Sélectionnez une entreprise", ["-- Choisir --"] + options)
    
    if selected_option and selected_option != "-- Choisir --":
        symbole_selected = selected_option.split(" - ")[0]
        nom_complet_entreprise = get_company_name(symbole_selected)
        
        # Récupérer les données
        symbole_data = {}
        for key, data in financial_data.items():
            if data.get('symbole') == symbole_selected:
                symbole_data[data['annee']] = data
        
        if symbole_data:
            st.success(f"✅ Analyse de **{nom_complet_entreprise}**")
            
            # Sélection de l'année
            annees = sorted(symbole_data.keys(), reverse=True)
            annee_selectionnee = st.selectbox("📅 Année d'analyse", annees)
            
            if annee_selectionnee:
                data = symbole_data[annee_selectionnee]
                
                # Onglets d'analyse
                tab1, tab2, tab3, tab4 = st.tabs([
                    "📊 Ratios Financiers",
                    "💎 Valorisation",
                    "🔮 Projections",
                    "📄 Données Brutes"
                ])
                
                with tab1:
                    st.subheader(f"📊 Ratios Financiers - {annee_selectionnee}")
                    
                    if 'ratios' in data and data['ratios']:
                        ratios = data['ratios']
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.markdown("### 💰 Rentabilité")
                            if 'roe' in ratios:
                                st.metric("ROE", f"{ratios['roe']:.2f}%", help="Rentabilité des Capitaux Propres")
                            if 'roa' in ratios:
                                st.metric("ROA", f"{ratios['roa']:.2f}%", help="Rentabilité de l'Actif")
                            if 'roic' in ratios:
                                st.metric("ROIC", f"{ratios['roic']:.2f}%", help="Rentabilité du Capital Investi")
                            if 'marge_nette' in ratios:
                                st.metric("Marge Nette", f"{ratios['marge_nette']:.2f}%")
                            if 'marge_ebitda' in ratios:
                                st.metric("Marge EBITDA", f"{ratios['marge_ebitda']:.2f}%")
                        
                        with col2:
                            st.markdown("### 💧 Liquidité")
                            if 'ratio_liquidite_generale' in ratios:
                                st.metric("Liquidité Générale", f"{ratios['ratio_liquidite_generale']:.2f}x")
                            if 'ratio_liquidite_reduite' in ratios:
                                st.metric("Liquidité Réduite", f"{ratios['ratio_liquidite_reduite']:.2f}x")
                            if 'ratio_liquidite_immediate' in ratios:
                                st.metric("Liquidité Immédiate", f"{ratios['ratio_liquidite_immediate']:.2f}x")
                            if 'working_capital' in ratios:
                                st.metric("Fonds de Roulement", f"{ratios['working_capital']:,.0f}")
                        
                        with col3:
                            st.markdown("### 📉 Endettement")
                            if 'ratio_endettement' in ratios:
                                st.metric("Ratio d'Endettement", f"{ratios['ratio_endettement']:.2f}%")
                            if 'debt_to_ebitda' in ratios:
                                st.metric("Dette/EBITDA", f"{ratios['debt_to_ebitda']:.2f}x")
                            if 'couverture_interets' in ratios:
                                st.metric("Couverture Intérêts", f"{ratios['couverture_interets']:.2f}x")
                            if 'ratio_solvabilite' in ratios:
                                st.metric("Solvabilité", f"{ratios['ratio_solvabilite']:.2f}%")
                        
                        st.markdown("---")
                        
                        col4, col5 = st.columns(2)
                        
                        with col4:
                            st.markdown("### 📈 Ratios de Marché")
                            if 'per' in ratios:
                                st.metric("P/E Ratio", f"{ratios['per']:.2f}x", help="Price to Earnings")
                            if 'price_to_book' in ratios:
                                st.metric("P/B Ratio", f"{ratios['price_to_book']:.2f}x", help="Price to Book")
                            if 'ev_ebitda' in ratios:
                                st.metric("EV/EBITDA", f"{ratios['ev_ebitda']:.2f}x")
                            if 'ev_sales' in ratios:
                                st.metric("EV/Sales", f"{ratios['ev_sales']:.2f}x")
                        
                        with col5:
                            st.markdown("### 💸 Flux de Trésorerie")
                            if 'fcf' in ratios:
                                st.metric("Free Cash Flow", f"{ratios['fcf']:,.0f}")
                            if 'fcf_yield' in ratios:
                                st.metric("FCF Yield", f"{ratios['fcf_yield']:.2f}%")
                            if 'qualite_benefices' in ratios:
                                st.metric("Qualité des Bénéfices", f"{ratios['qualite_benefices']:.2f}")
                    else:
                        st.info("💡 Aucun ratio calculé pour cette période")
                
                with tab2:
                    st.subheader(f"💎 Valorisation - {nom_complet_entreprise}")
                    
                    valorisations = calculate_valuation_multiples(
                        symbole_selected,
                        annee_selectionnee,
                        {**data['bilan'], **data['compte_resultat'], **data.get('ratios', {})},
                        financial_data
                    )
                    
                    if 'recommandation' in valorisations:
                        # Afficher la recommandation avec style
                        style_class = valorisations.get('style_class', 'recommendation-hold')
                        st.markdown(f"""
                        <div class="{style_class}">
                            {valorisations['recommandation']}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.info(f"**📊 Analyse :** {valorisations.get('justification', '')}")
                        
                        if 'secteur_utilise' in valorisations:
                            st.caption(f"🏷️ Comparaison basée sur: **{valorisations['secteur_utilise']}**")
                        
                        st.markdown("---")
                        
                        # Détails de valorisation
                        col_val1, col_val2, col_val3 = st.columns(3)
                        
                        with col_val1:
                            if 'juste_valeur_per' in valorisations:
                                st.metric(
                                    "Juste Valeur (P/E)",
                                    f"{valorisations['juste_valeur_per']:.2f}",
                                    delta=f"{valorisations.get('ecart_per', 0):.1f}%"
                                )
                        
                        with col_val2:
                            if 'juste_valeur_pb' in valorisations:
                                st.metric(
                                    "Juste Valeur (P/B)",
                                    f"{valorisations['juste_valeur_pb']:.2f}",
                                    delta=f"{valorisations.get('ecart_pb', 0):.1f}%"
                                )
                        
                        with col_val3:
                            if 'juste_valeur_ev_ebitda' in valorisations:
                                st.metric(
                                    "Juste Valeur (EV/EBITDA)",
                                    f"{valorisations['juste_valeur_ev_ebitda']:.2f}",
                                    delta=f"{valorisations.get('ecart_ev_ebitda', 0):.1f}%"
                                )
                        
                        # Multiples sectoriels
                        if 'medianes_secteur' in valorisations and valorisations['medianes_secteur']:
                            st.markdown("### 📊 Multiples Sectoriels (Médiane)")
                            
                            medianes = valorisations['medianes_secteur']
                            df_medianes = pd.DataFrame([
                                {"Multiple": k.replace("_median", "").upper(), "Valeur Médiane": f"{v:.2f}"}
                                for k, v in medianes.items()
                            ])
                            
                            st.dataframe(df_medianes, use_container_width=True, hide_index=True)
                    else:
                        st.warning("⚠️ Données insuffisantes pour la valorisation")
                
                with tab3:
                    st.subheader(f"🔮 Projections Financières - {nom_complet_entreprise}")
                    
                    projections = calculate_financial_projections(symbole_selected, financial_data)
                    
                    if 'projections' in projections:
                        col_proj1, col_proj2, col_proj3 = st.columns(3)
                        
                        with col_proj1:
                            st.metric("📊 Méthode", projections.get('methode', 'Hybride'))
                        
                        with col_proj2:
                            st.metric("📈 TCAM CA", f"{projections.get('tcam_ca', 0):.2f}%", help="Taux de Croissance Annuel Moyen du CA")
                        
                        with col_proj3:
                            st.metric("💰 TCAM RN", f"{projections.get('tcam_rn', 0):.2f}%", help="Taux de Croissance Annuel Moyen du Résultat Net")
                        
                        st.markdown("---")
                        
                        # Tableau des projections
                        df_proj = pd.DataFrame(projections['projections'])
                        
                        st.dataframe(
                            df_proj.style.format({
                                'ca_projete': '{:,.0f}',
                                'rn_projete': '{:,.0f}',
                                'marge_nette_projetee': '{:.2f}%'
                            }),
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        # Afficher l'historique
                        if 'historique' in projections:
                            st.markdown("### 📜 Historique")
                            df_hist = pd.DataFrame(projections['historique'])
                            
                            st.dataframe(
                                df_hist.style.format({
                                    'ca': '{:,.0f}',
                                    'resultat_net': '{:,.0f}'
                                }),
                                use_container_width=True,
                                hide_index=True
                            )
                    elif 'erreur' in projections:
                        st.warning(f"⚠️ {projections['erreur']}")
                
                with tab4:
                    st.subheader(f"📄 Données Brutes - {nom_complet_entreprise}")
                    
                    col_brut1, col_brut2 = st.columns(2)
                    
                    with col_brut1:
                        if data.get('bilan'):
                            st.markdown("### 📋 Bilan")
                            df_bilan = pd.DataFrame([
                                {"Poste": k.replace('_', ' ').title(), "Valeur": f"{v:,.0f}"}
                                for k, v in data['bilan'].items()
                            ])
                            st.dataframe(df_bilan, use_container_width=True, hide_index=True)
                    
                    with col_brut2:
                        if data.get('compte_resultat'):
                            st.markdown("### 💹 Compte de Résultat")
                            df_cr = pd.DataFrame([
                                {"Poste": k.replace('_', ' ').title(), "Valeur": f"{v:,.0f}"}
                                for k, v in data['compte_resultat'].items()
                            ])
                            st.dataframe(df_cr, use_container_width=True, hide_index=True)
                    
                    if data.get('flux_tresorerie'):
                        st.markdown("### 💸 Flux de Trésorerie")
                        df_ft = pd.DataFrame([
                            {"Poste": k.replace('_', ' ').title(), "Valeur": f"{v:,.0f}"}
                            for k, v in data['flux_tresorerie'].items()
                        ])
                        st.dataframe(df_ft, use_container_width=True, hide_index=True)

# ======================
# SECTION ADMIN (DÉVELOPPEUR)
# ======================
def developer_section():
    """Section administration complète"""
    st.title("⚙️ Section Administration")
    
    if 'dev_authenticated' not in st.session_state:
        st.session_state.dev_authenticated = False
    
    if not st.session_state.dev_authenticated:
        st.markdown("### 🔐 Authentification Requise")
        password = st.text_input("Mot de passe administrateur", type="password")
        
        if st.button("🔓 Se connecter", use_container_width=True):
            if password == DEVELOPER_PASSWORD:
                st.session_state.dev_authenticated = True
                st.success("✅ Connexion réussie !")
                st.rerun()
            else:
                st.error("❌ Mot de passe incorrect")
        return
    
    st.success("✅ Mode Administrateur Activé")
    
    # Onglets d'administration
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Données Financières",
        "🏢 Noms Entreprises",
        "🏷️ Gestion Secteurs",
        "⚙️ Paramètres"
    ])
    
    with tab1:
        st.header("📊 Gestion des Données Financières")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("➕ Ajouter/Modifier")
            
            symbole = st.text_input("Symbole BRVM", placeholder="Ex: SNTS", key="dev_symbole").upper()
            annee = st.number_input("Année", min_value=2000, max_value=2030, value=datetime.now().year-1, key="dev_annee")
            
            with st.expander("📋 Bilan", expanded=True):
                col_b1, col_b2 = st.columns(2)
                
                with col_b1:
                    actif_total = st.number_input("Actif Total", value=0.0, format="%.2f", key="bilan_actif_total")
                    actif_courant = st.number_input("Actif Courant", value=0.0, format="%.2f", key="bilan_actif_courant")
                    stocks = st.number_input("Stocks", value=0.0, format="%.2f", key="bilan_stocks")
                    creances = st.number_input("Créances", value=0.0, format="%.2f", key="bilan_creances")
                    tresorerie = st.number_input("Trésorerie", value=0.0, format="%.2f", key="bilan_tresorerie")
                
                with col_b2:
                    capitaux_propres = st.number_input("Capitaux Propres", value=0.0, format="%.2f", key="bilan_capitaux_propres")
                    dettes_totales = st.number_input("Dettes Totales", value=0.0, format="%.2f", key="bilan_dettes_totales")
                    passif_courant = st.number_input("Passif Courant", value=0.0, format="%.2f", key="bilan_passif_courant")
                    cours_action = st.number_input("Cours de l'Action", value=0.0, format="%.2f", key="bilan_cours_action")
                    nb_actions = st.number_input("Nombre d'Actions", value=0.0, format="%.2f", key="bilan_nb_actions")
            
            with st.expander("💹 Compte de Résultat"):
                chiffre_affaires = st.number_input("Chiffre d'Affaires", value=0.0, format="%.2f", key="cr_chiffre_affaires")
                resultat_exploitation = st.number_input("Résultat d'Exploitation", value=0.0, format="%.2f", key="cr_resultat_exploitation")
                resultat_net = st.number_input("Résultat Net", value=0.0, format="%.2f", key="cr_resultat_net")
                charges_financieres = st.number_input("Charges Financières", value=0.0, format="%.2f", key="cr_charges_financieres")
                benefice_par_action = st.number_input("Bénéfice par Action", value=0.0, format="%.2f", key="cr_benefice_par_action")
            
            with st.expander("💸 Flux de Trésorerie"):
                flux_exploitation = st.number_input("Flux d'Exploitation", value=0.0, format="%.2f", key="ft_flux_exploitation")
                flux_investissement = st.number_input("Flux d'Investissement", value=0.0, format="%.2f", key="ft_flux_investissement")
flux_financement = st.number_input("Flux de Financement", value=0.0, format="%.2f", key="ft_flux_financement")
            
            # Bouton de sauvegarde
            if st.button("💾 Sauvegarder", use_container_width=True, type="primary"):
                # Construction du dictionnaire de données
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
                
                if save_financial_data(symbole, annee, data_dict):
                    st.success("✅ Données sauvegardées avec succès !")
                    st.rerun()
                else:
                    st.error("❌ Erreur lors de la sauvegarde")
        
        with col2:
            st.subheader("🗑️ Supprimer")
            
            # Récupérer toutes les données disponibles
            financial_data = init_storage()
            if financial_data:
                # Créer une liste des symboles uniques
                symboles = sorted(set([data['symbole'] for data in financial_data.values() 
                                     if isinstance(data, dict)]))
                
                if symboles:
                    symbole_delete = st.selectbox("Sélectionner le symbole", 
                                                 ["-- Choisir --"] + symboles,
                                                 key="delete_symbole")
                    
                    if symbole_delete != "-- Choisir --":
                        # Récupérer les années disponibles pour ce symbole
                        annees = sorted([data['annee'] for key, data in financial_data.items() 
                                        if isinstance(data, dict) and data['symbole'] == symbole_delete])
                        
                        if annees:
                            annee_delete = st.selectbox("Sélectionner l'année", 
                                                       annees,
                                                       key="delete_annee")
                            
                            if st.button("🗑️ Supprimer", use_container_width=True, 
                                        type="secondary"):
                                if delete_financial_data(symbole_delete, annee_delete):
                                    st.success(f"✅ Données {symbole_delete} - {annee_delete} supprimées !")
                                    st.rerun()
                                else:
                                    st.error("❌ Erreur lors de la suppression")
                        else:
                            st.warning("Aucune année disponible pour ce symbole")
                else:
                    st.info("Aucune donnée financière disponible")
            else:
                st.info("Aucune donnée financière disponible")
    
    with tab2:
        st.header("🏢 Gestion des Noms d'Entreprises")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("➕ Ajouter/Modifier")
            
            symbole_nom = st.text_input("Symbole", placeholder="Ex: SNTS", 
                                       key="nom_symbole").upper()
            nom_complet = st.text_input("Nom complet de l'entreprise", 
                                       placeholder="Ex: SONATEL",
                                       key="nom_complet")
            
            if st.button("💾 Enregistrer le nom", use_container_width=True):
                if save_symbol_mapping(symbole_nom, nom_complet):
                    st.success(f"✅ Nom enregistré : {symbole_nom} → {nom_complet}")
                    st.rerun()
                else:
                    st.error("❌ Erreur lors de l'enregistrement")
        
        with col2:
            st.subheader("🗑️ Supprimer")
            
            symbol_mapping = st.session_state.get('symbol_mapping', {})
            if symbol_mapping:
                symboles_list = list(symbol_mapping.keys())
                symbole_delete = st.selectbox("Sélectionner le symbole à supprimer",
                                             ["-- Choisir --"] + symboles_list,
                                             key="delete_symbol_mapping")
                
                if symbole_delete != "-- Choisir --":
                    st.warning(f"Supprimer : {symbole_delete} - {symbol_mapping[symbole_delete]}")
                    
                    if st.button("🗑️ Supprimer ce mapping", use_container_width=True,
                                type="secondary"):
                        if delete_symbol_mapping(symbole_delete):
                            st.success(f"✅ Mapping {symbole_delete} supprimé !")
                            st.rerun()
                        else:
                            st.error("❌ Erreur lors de la suppression")
            else:
                st.info("Aucun mapping de symbole disponible")
    
    with tab3:
        st.header("🏷️ Gestion des Secteurs")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("➕ Créer/Modifier un Secteur")
            
            # Récupérer les entreprises disponibles
            financial_data = init_storage()
            if financial_data:
                entreprises = sorted(set([data['symbole'] for data in financial_data.values() 
                                        if isinstance(data, dict)]))
                
                # Ajouter les noms complets pour l'affichage
                entreprises_display = []
                for symbole in entreprises:
                    nom = get_company_name(symbole)
                    if nom != symbole:
                        entreprises_display.append(f"{symbole} - {nom}")
                    else:
                        entreprises_display.append(symbole)
                
                secteur_name = st.text_input("Nom du secteur", 
                                            placeholder="Ex: Télécommunications",
                                            key="secteur_name")
                
                # Zone de drag & drop simulée avec multiselect
                st.markdown("<div class='sector-dropzone'>", unsafe_allow_html=True)
                st.markdown("**Sélectionnez les entreprises du secteur**")
                entreprises_selected = st.multiselect(
                    "Entreprises",
                    options=entreprises_display,
                    key="secteur_entreprises",
                    label_visibility="collapsed"
                )
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Convertir les sélections en symboles
                entreprises_symboles = []
                for item in entreprises_selected:
                    symbole = item.split(" - ")[0] if " - " in item else item
                    entreprises_symboles.append(symbole)
                
                if st.button("💾 Sauvegarder le secteur", use_container_width=True):
                    if secteur_name and entreprises_symboles:
                        if save_sector_mapping(secteur_name, entreprises_symboles):
                            st.success(f"✅ Secteur '{secteur_name}' sauvegardé avec {len(entreprises_symboles)} entreprises")
                            st.rerun()
                        else:
                            st.error("❌ Erreur lors de la sauvegarde")
                    else:
                        st.warning("⚠️ Veuillez saisir un nom de secteur et sélectionner au moins une entreprise")
            else:
                st.info("Veuillez d'abord ajouter des données financières")
        
        with col2:
            st.subheader("🗑️ Gérer les Secteurs Existants")
            
            sector_mapping = st.session_state.get('sector_mapping', {})
            if sector_mapping:
                secteurs = list(sector_mapping.keys())
                secteur_delete = st.selectbox("Sélectionner un secteur",
                                             ["-- Choisir --"] + secteurs,
                                             key="delete_secteur")
                
                if secteur_delete != "-- Choisir --":
                    entreprises_secteur = sector_mapping[secteur_delete]
                    st.info(f"**{secteur_delete}** - {len(entreprises_secteur)} entreprise(s)")
                    
                    # Afficher les entreprises sous forme de tags
                    st.markdown("**Entreprises :**")
                    cols = st.columns(3)
                    for i, symbole in enumerate(entreprises_secteur):
                        with cols[i % 3]:
                            st.markdown(f"<div class='company-tag'>{symbole}</div>", 
                                       unsafe_allow_html=True)
                    
                    if st.button("🗑️ Supprimer ce secteur", use_container_width=True,
                                type="secondary"):
                        if delete_sector(secteur_delete):
                            st.success(f"✅ Secteur '{secteur_delete}' supprimé !")
                            st.rerun()
                        else:
                            st.error("❌ Erreur lors de la suppression")
            else:
                st.info("Aucun secteur défini")
    
    with tab4:
        st.header("⚙️ Paramètres Système")
        
        st.subheader("📊 Statistiques de la Base de Données")
        
        # Connexion à Supabase pour les statistiques
        supabase = init_supabase()
        if supabase:
            try:
                # Compter les enregistrements dans chaque table
                tables = ["financial_data", "symbol_mapping", "sector_mapping"]
                stats = {}
                
                for table in tables:
                    try:
                        response = supabase.table(table).select("*", count="exact").execute()
                        stats[table] = response.count or 0
                    except:
                        stats[table] = 0
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📈 Données Financières", f"{stats.get('financial_data', 0)}")
                with col2:
                    st.metric("🏢 Mappings Symboles", f"{stats.get('symbol_mapping', 0)}")
                with col3:
                    st.metric("🏷️ Secteurs Définis", f"{stats.get('sector_mapping', 0)}")
                
            except Exception as e:
                st.error(f"Erreur lors de la récupération des statistiques: {str(e)}")
        
        st.markdown("---")
        
        st.subheader("🔧 Maintenance")
        
        col_m1, col_m2 = st.columns(2)
        
        with col_m1:
            if st.button("🔄 Recharger les Données", use_container_width=True):
                # Recharger toutes les données depuis Supabase
                if 'financial_data' in st.session_state:
                    del st.session_state.financial_data
                if 'symbol_mapping' in st.session_state:
                    del st.session_state.symbol_mapping
                if 'sector_mapping' in st.session_state:
                    del st.session_state.sector_mapping
                
                init_storage()
                st.success("✅ Données rechargées avec succès !")
                st.rerun()
        
        with col_m2:
            if st.button("🚪 Déconnexion Admin", use_container_width=True, type="secondary"):
                st.session_state.dev_authenticated = False
                st.success("✅ Déconnecté de la section admin")
                st.rerun()
        
        st.markdown("---")
        
        st.subheader("📝 Informations")
        
        st.info("""
        **Capital Project - Version Professionnelle**
        
        Version: 1.0.0
        Dernière mise à jour: 2024
        Développé pour l'analyse fondamentale BRVM
        
        Pour toute question ou support, contactez l'équipe de développement.
        """)

# ============================
# APPLICATION PRINCIPALE
# ============================

def main():
    """Application principale"""
    
    # Charger le CSS personnalisé
    load_custom_css()
    
    # Initialiser le stockage
    init_storage()
    
    # Navigation
    render_navigation()
    
    # Gestion des pages
    current_page = st.session_state.get('page', 'accueil')
    
    if current_page == 'accueil':
        page_accueil()
    elif current_page == 'cours':
        page_cours()
    elif current_page == 'analyse':
        page_analyse()
    elif current_page == 'dev':
        developer_section()
    
    # Footer professionnel
    st.markdown("""
    <div class='custom-footer'>
    <p>Capital Project - Analyse BRVM Pro © 2024 | Version Professionnelle</p>
    <p>Données fournies à titre indicatif | Investissement soumis à risque</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
