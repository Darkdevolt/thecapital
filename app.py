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

# Configuration Supabase
SUPABASE_URL = "https://otsiwiwlnowxeolbbgvm.supabase.co"
SUPABASE_KEY = "sb_publishable_MhaI5b-kMmb5liIMOJ4P3Q_xGTsJAFJ"

def init_supabase():
    """Initialiser la connexion à Supabase"""
    if 'supabase' not in st.session_state:
        try:
            st.session_state.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            # Test de connexion
            test_response = st.session_state.supabase.table("financial_data").select("*", count="exact").limit(1).execute()
            st.success("✅ Connexion Supabase établie")
        except Exception as e:
            st.error(f"❌ Erreur de connexion Supabase: {str(e)}")
            return None
    return st.session_state.supabase

def load_all_financial_data():
    """Charger toutes les données financières depuis Supabase"""
    supabase = init_supabase()
    if not supabase:
        return {}
    
    try:
        # Récupérer toutes les données
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
        # Préparer l'enregistrement
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
    
    # EBITDA = Résultat d'exploitation + Amortissements
    ebitda = compte_resultat.get('resultat_exploitation', 0)
    
    # EBIT = Résultat d'exploitation
    ebit = compte_resultat.get('resultat_exploitation', 0)
    
    # Free Cash Flow
    fcf = flux_tresorerie.get('flux_exploitation', 0) + flux_tresorerie.get('flux_investissement', 0)
    
    # Working Capital (Fonds de roulement)
    working_capital = bilan.get('actif_courant', 0) - bilan.get('passif_courant', 0)
    
    # Enterprise Value approximé
    market_cap = bilan.get('cours_action', 0) * bilan.get('nb_actions', 0)
    enterprise_value = market_cap + bilan.get('dettes_totales', 0) - bilan.get('tresorerie', 0)
    
    # ========== RATIOS DE RENTABILITÉ CORRIGÉS ==========
    
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
    
    # ========== RATIOS DE LIQUIDITÉ CORRIGÉS ==========
    
    if bilan.get('actif_courant') and bilan.get('passif_courant') and bilan.get('passif_courant') > 0:
        ratios['ratio_liquidite_generale'] = bilan['actif_courant'] / bilan['passif_courant']
    
    # Ratio de liquidité réduite (quick ratio) : exclut les stocks
    if bilan.get('actif_courant') and bilan.get('stocks') is not None and bilan.get('passif_courant'):
        actif_liquide = bilan['actif_courant'] - bilan.get('stocks', 0)
        if bilan['passif_courant'] > 0:
            ratios['ratio_liquidite_reduite'] = actif_liquide / bilan['passif_courant']
    
    if bilan.get('tresorerie') and bilan.get('passif_courant') and bilan.get('passif_courant') > 0:
        ratios['ratio_liquidite_immediate'] = bilan['tresorerie'] / bilan['passif_courant']
    
    # ========== RATIOS D'ENDETTEMENT CORRIGÉS ==========
    
    if bilan.get('dettes_totales') and bilan.get('capitaux_propres') and bilan.get('capitaux_propres') > 0:
        ratios['ratio_endettement'] = (bilan['dettes_totales'] / bilan['capitaux_propres']) * 100
    
    if bilan.get('dettes_totales') and bilan.get('actif_total') and bilan.get('actif_total') > 0:
        ratios['taux_endettement'] = (bilan['dettes_totales'] / bilan['actif_total']) * 100
    
    # Solvabilité
    if bilan.get('capitaux_propres') and bilan.get('actif_total') and bilan.get('actif_total') > 0:
        ratios['ratio_solvabilite'] = (bilan['capitaux_propres'] / bilan['actif_total']) * 100
    
    # Debt to EBITDA (crucial pour évaluer capacité de remboursement)
    if bilan.get('dettes_totales') and ebitda > 0:
        ratios['debt_to_ebitda'] = bilan['dettes_totales'] / ebitda
    
    # Couverture des intérêts
    if ebit and compte_resultat.get('charges_financieres') and abs(compte_resultat.get('charges_financieres', 0)) > 0:
        ratios['couverture_interets'] = ebit / abs(compte_resultat['charges_financieres'])
    
    # ========== RATIOS D'EFFICACITÉ ==========
    
    if compte_resultat.get('chiffre_affaires') and bilan.get('actif_total') and bilan.get('actif_total') > 0:
        ratios['rotation_actifs'] = compte_resultat['chiffre_affaires'] / bilan['actif_total']
    
    if compte_resultat.get('chiffre_affaires') and bilan.get('stocks') and bilan.get('stocks') > 0:
        ratios['rotation_stocks'] = compte_resultat['chiffre_affaires'] / bilan['stocks']
    
    # Délai de recouvrement (en jours)
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
    
    # EV/EBITDA (multiple de valorisation clé)
    if enterprise_value and ebitda > 0:
        ratios['ev_ebitda'] = enterprise_value / ebitda
    
    # EV/Sales
    if enterprise_value and compte_resultat.get('chiffre_affaires') and compte_resultat.get('chiffre_affaires') > 0:
        ratios['ev_sales'] = enterprise_value / compte_resultat['chiffre_affaires']
    
    # ========== RATIOS DE FLUX DE TRÉSORERIE ==========
    
    if flux_tresorerie.get('flux_exploitation') and compte_resultat.get('resultat_net') and compte_resultat.get('resultat_net') != 0:
        ratios['qualite_benefices'] = flux_tresorerie['flux_exploitation'] / compte_resultat['resultat_net']
    
    if fcf and market_cap > 0:
        ratios['fcf_yield'] = (fcf / market_cap) * 100
    
    # Ratio de couverture des dettes par FCF
    if fcf and bilan.get('dettes_totales') and bilan.get('dettes_totales') > 0:
        ratios['fcf_to_debt'] = fcf / bilan['dettes_totales']
    
    # ========== DONNÉES INTERMÉDIAIRES UTILES ==========
    ratios['ebitda'] = ebitda
    ratios['ebit'] = ebit
    ratios['fcf'] = fcf
    ratios['working_capital'] = working_capital
    ratios['enterprise_value'] = enterprise_value
    ratios['market_cap'] = market_cap
    
    return ratios

def calculate_valuation_multiples(symbole, annee, ratios_entreprise, financial_data):
    """
    Valorisation par multiples avec comparaison sectorielle (MÉDIANE)
    """
    
    # Récupérer toutes les entreprises du même secteur
    secteur_multiples = {
        'per': [],
        'price_to_book': [],
        'ev_ebitda': [],
        'ev_sales': []
    }
    
    # Parcourir toutes les données financières
    for key, data in financial_data.items():
        if key == f"{symbole}_{annee}":
            continue  # Exclure l'entreprise elle-même
        
        ratios = data.get('ratios', {})
        
        # Collecter les multiples valides
        if ratios.get('per') and 0 < ratios['per'] < 100:  # Filtrer valeurs aberrantes
            secteur_multiples['per'].append(ratios['per'])
        
        if ratios.get('price_to_book') and 0 < ratios['price_to_book'] < 20:
            secteur_multiples['price_to_book'].append(ratios['price_to_book'])
        
        if ratios.get('ev_ebitda') and 0 < ratios['ev_ebitda'] < 50:
            secteur_multiples['ev_ebitda'].append(ratios['ev_ebitda'])
        
        if ratios.get('ev_sales') and 0 < ratios['ev_sales'] < 10:
            secteur_multiples['ev_sales'].append(ratios['ev_sales'])
    
    # Calculer les MÉDIANES (plus robuste que moyenne)
    medianes = {}
    for key, values in secteur_multiples.items():
        if len(values) >= 2:  # Minimum 2 comparables
            medianes[f"{key}_median"] = np.median(values)
    
    # VALORISATIONS BASÉES SUR LES MÉDIANES
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
        
        # Convertir EV en valeur des capitaux propres
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
    
    # DÉCISION D'INVESTISSEMENT
    valorisations['medianes_secteur'] = medianes
    
    # Calculer potentiel moyen (moyenne des écarts)
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
    """
    Projections financières pondérées : 40% TCAM + 60% Régression Linéaire
    """
    
    # Récupérer l'historique
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
    
    # Trier par année
    historique = sorted(historique, key=lambda x: x['annee'])
    
    annees = np.array([h['annee'] for h in historique]).reshape(-1, 1)
    ca_values = np.array([h['ca'] for h in historique])
    rn_values = np.array([h['resultat_net'] for h in historique])
    
    # ========== 1. TCAM (Taux de Croissance Annuel Moyen) ==========
    
    def calcul_tcam(valeur_debut, valeur_fin, nb_annees):
        if valeur_debut <= 0:
            return 0
        return (pow(valeur_fin / valeur_debut, 1/nb_annees) - 1) * 100
    
    tcam_ca = calcul_tcam(ca_values[0], ca_values[-1], len(ca_values) - 1)
    tcam_rn = calcul_tcam(abs(rn_values[0]), abs(rn_values[-1]), len(rn_values) - 1) if rn_values[0] != 0 else 0
    
    # ========== 2. RÉGRESSION LINÉAIRE ==========
    
    model_ca = LinearRegression()
    model_ca.fit(annees, ca_values)
    
    model_rn = LinearRegression()
    model_rn.fit(annees, rn_values)
    
    # Qualité du modèle (R²)
    r2_ca = model_ca.score(annees, ca_values)
    r2_rn = model_rn.score(annees, rn_values)
    
    # ========== 3. PROJECTIONS PONDÉRÉES ==========
    
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
        
        # PONDÉRATION : 40% TCAM + 60% Régression
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

# ===========================
# SCRAPING BRVM - COURS UNIQUEMENT
# ===========================
@st.cache_data(ttl=300)
def scrape_brvm_cours():
    """
    Récupère UNIQUEMENT les cours depuis BRVM
    URL principale sans distinction de secteur
    """
    url = "https://www.brvm.org/fr/cours-actions/0"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        # Désactivation warnings SSL
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        
        if response.status_code != 200:
            st.error(f"❌ Erreur HTTP {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Trouver le tableau
        table = soup.find('table')
        
        if not table:
            st.error("❌ Aucun tableau trouvé")
            return None
        
        # Extraction des en-têtes
        headers_list = [th.get_text(strip=True) for th in table.find_all('th')]
        
        # Extraction des lignes
        data = []
        for row in table.find_all('tr')[1:]:  # Skip header
            cells = row.find_all('td')
            if cells and len(cells) >= 2:
                row_data = [cell.get_text(strip=True) for cell in cells]
                data.append(row_data)
        
        if not data:
            st.error("❌ Aucune donnée extraite")
            return None
        
        # Créer DataFrame
        df = pd.DataFrame(data, columns=headers_list[:len(data[0])])
        df = clean_dataframe(df)
        
        return df
    
    except Exception as e:
        st.error(f"❌ Erreur : {str(e)}")
        return None


# ===========================
# SCRAPING SECTEURS BRVM
# ===========================
@st.cache_data(ttl=3600)
@st.cache_data(ttl=300)
def scrape_brvm_cours():
    """
    Récupère les cours depuis BRVM - Version robuste
    """
    url = "https://www.brvm.org/fr/cours-actions/0"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Désactivation warnings SSL
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Requête avec retry
        session = requests.Session()
        session.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))
        
        response = session.get(url, headers=headers, timeout=20, verify=False)
        response.raise_for_status()
        
        # Parser HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Debugging : afficher la structure
        tables = soup.find_all('table')
        
        if not tables:
            st.error(f"❌ Aucun tableau trouvé. Status: {response.status_code}")
            st.info(f"Contenu récupéré : {len(response.content)} octets")
            return None
        
        # Prendre le premier tableau contenant des données
        table = None
        for t in tables:
            rows = t.find_all('tr')
            if len(rows) > 1:  # Au moins header + 1 ligne
                table = t
                break
        
        if not table:
            st.error("❌ Aucun tableau valide trouvé")
            return None
        
        # Extraction des données
        rows = table.find_all('tr')
        
        # En-têtes
        headers_row = rows[0]
        headers_list = [th.get_text(strip=True) for th in headers_row.find_all(['th', 'td'])]
        
        # Données
        data = []
        for row in rows[1:]:
            cells = row.find_all(['td', 'th'])
            if cells:
                row_data = [cell.get_text(strip=True) for cell in cells]
                if len(row_data) >= 2:  # Au moins Symbole + Nom
                    data.append(row_data)
        
        if not data:
            st.error("❌ Aucune donnée extraite du tableau")
            return None
        
        # Créer DataFrame
        # Ajuster le nombre de colonnes
        max_cols = max(len(row) for row in data)
        if len(headers_list) < max_cols:
            headers_list.extend([f'Col_{i}' for i in range(len(headers_list), max_cols)])
        
        df = pd.DataFrame(data, columns=headers_list[:max_cols])
        
        # Nettoyage
        df = clean_dataframe(df)
        
        st.success(f"✅ {len(df)} titres chargés depuis BRVM")
        return df
    
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Erreur de connexion : {str(e)}")
        return None
    except Exception as e:
        st.error(f"❌ Erreur scraping : {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return None

# ===========================
# NAVIGATION STYLÉE
# ===========================
def render_navigation():
    """
    Barre de navigation stylée en haut de page
    """
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
        .nav-links {
            display: flex;
            justify-content: center;
            gap: 1rem;
            flex-wrap: wrap;
        }
        .nav-button {
            background-color: rgba(255, 255, 255, 0.2);
            color: white;
            padding: 0.6rem 1.5rem;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 500;
            transition: all 0.3s ease;
            border: 2px solid transparent;
            cursor: pointer;
        }
        .nav-button:hover {
            background-color: rgba(255, 255, 255, 0.3);
            border-color: white;
            transform: translateY(-2px);
        }
        .nav-button.active {
            background-color: white;
            color: #1e3c72;
            border-color: white;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div class="nav-container">
            <div class="nav-title">📊 Analyse BRVM Pro</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Boutons de navigation
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        btn_accueil = st.button("🏠 Accueil", use_container_width=True, type="primary" if st.session_state.get('page', 'accueil') == 'accueil' else "secondary")
        if btn_accueil:
            st.session_state.page = 'accueil'
            st.rerun()
    
    with col2:
        btn_cours = st.button("💹 Cours", use_container_width=True, type="primary" if st.session_state.get('page', 'accueil') == 'cours' else "secondary")
        if btn_cours:
            st.session_state.page = 'cours'
            st.rerun()
    
    with col3:
        btn_secteurs = st.button("🏢 Secteurs", use_container_width=True, type="primary" if st.session_state.get('page', 'accueil') == 'secteurs' else "secondary")
        if btn_secteurs:
            st.session_state.page = 'secteurs'
            st.rerun()
    
    with col4:
        btn_analyse = st.button("📈 Analyse", use_container_width=True, type="primary" if st.session_state.get('page', 'accueil') == 'analyse' else "secondary")
        if btn_analyse:
            st.session_state.page = 'analyse'
            st.rerun()
    
    with col5:
        btn_dev = st.button("⚙️ Développeur", use_container_width=True, type="primary" if st.session_state.get('page', 'accueil') == 'dev' else "secondary")
        if btn_dev:
            st.session_state.page = 'dev'
            st.rerun()
    
    st.markdown("---")

# ===========================
# PAGE ACCUEIL
# ===========================
def page_accueil():
    st.title("🏠 Accueil - Analyse BRVM Pro")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 📊 Bienvenue sur Analyse BRVM Pro
        
        **Votre outil complet d'analyse de la Bourse Régionale des Valeurs Mobilières**
        
        #### Fonctionnalités principales :
        - 💹 **Cours en temps réel** : Tous les titres BRVM
        - 🏢 **Analyse par secteur** : 7 secteurs économiques
        - 📈 **Analyse fondamentale** : Ratios, scores, valorisation
        - 🔮 **Projections** : Scénarios futurs basés sur l'historique
        - ⚡ **Alertes** : Détection automatique des risques
        """)
    
    with col2:
        st.markdown("""
        ### 🎯 Comment utiliser l'application ?
        
        1. **Cours** : Consultez les cours actuels de tous les titres
        2. **Secteurs** : Analysez les performances par secteur
        3. **Analyse** : Sélectionnez un titre pour analyse approfondie
        4. **Développeur** : Saisissez des données financières
        """)
        
        st.info("💡 **Astuce** : Les données sont mises à jour toutes les 5 minutes")
    
    # Statistiques rapides
    st.markdown("---")
    st.subheader("📊 Statistiques du jour")
    
    with st.spinner("Chargement..."):
        df = scrape_brvm_cours()
        
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
    st.title("💹 Cours des Actions BRVM")
    
    col_refresh, col_info = st.columns([1, 3])
    
    with col_refresh:
        if st.button("🔄 Actualiser", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    with col_info:
        st.info("📡 Données en direct depuis BRVM - Actualisation toutes les 5 minutes")
    
    with st.spinner("📊 Chargement des cours..."):
        df = scrape_brvm_cours()
    
    if df is not None:
        # Statistiques
        st.subheader("📊 Vue d'ensemble")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total titres", len(df))
        
        with col2:
            if 'Variation (%)' in df.columns:
                hausse = len(df[df['Variation (%)'] > 0])
                st.metric("En hausse", hausse, delta=f"+{hausse}")
        
        with col3:
            if 'Variation (%)' in df.columns:
                baisse = len(df[df['Variation (%)'] < 0])
                st.metric("En baisse", baisse, delta=f"-{baisse}")
        
        with col4:
            if 'Variation (%)' in df.columns:
                stable = len(df[df['Variation (%)'] == 0])
                st.metric("Stables", stable)
        
        # Tableau des cours
        st.markdown("---")
        st.subheader("📈 Tableau des cours")
        
        def color_variation(val):
            if isinstance(val, (int, float)):
                if val > 0:
                    return 'color: green; font-weight: bold'
                elif val < 0:
                    return 'color: red; font-weight: bold'
            return ''
        
        if 'Variation (%)' in df.columns:
            styled_df = df.style.map(color_variation, subset=['Variation (%)'])
            st.dataframe(styled_df, use_container_width=True, height=500)
        else:
            st.dataframe(df, use_container_width=True, height=500)
        
        # Top/Flop
        if 'Variation (%)' in df.columns:
            st.markdown("---")
            col_top, col_flop = st.columns(2)
            
            with col_top:
                st.subheader("🔥 Top 5 Hausses")
                top5 = df.nlargest(5, 'Variation (%)')
                st.dataframe(top5[['Symbole', 'Nom', 'Variation (%)']].style.map(
                    color_variation, subset=['Variation (%)']),
                    use_container_width=True,
                    hide_index=True
                )
            
            with col_flop:
                st.subheader("📉 Top 5 Baisses")
                flop5 = df.nsmallest(5, 'Variation (%)')
                st.dataframe(flop5[['Symbole', 'Nom', 'Variation (%)']].style.map(
                    color_variation, subset=['Variation (%)']),
                    use_container_width=True,
                    hide_index=True
                )
        
        # Export
        st.markdown("---")
        csv = df.to_csv(index=False, sep=';', decimal=',')
        st.download_button(
            label="📥 Télécharger en CSV",
            data=csv,
            file_name=f"brvm_cours_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
    else:
        st.error("❌ Impossible de charger les données")


# ===========================
# PAGE SECTEURS
# ===========================
def page_secteurs():
    st.title("🏢 Analyse par Secteur")
    
    col_refresh, col_info = st.columns([1, 3])
    
    with col_refresh:
        if st.button("🔄 Actualiser", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    with col_info:
        st.info("📊 Classification sectorielle officielle BRVM")
    
    with st.spinner("📊 Chargement des secteurs..."):
        df = scrape_brvm_secteurs()
    
    if df is not None:
        # Statistiques par secteur
        st.subheader("📊 Répartition par secteur")
        
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
        
        # Filtre par secteur
        st.markdown("---")
        st.subheader("🔍 Filtrer par secteur")
        
        if 'Secteur' in df.columns:
            secteurs = ['Tous'] + sorted(df['Secteur'].unique().tolist())
            secteur_selected = st.selectbox("Choisissez un secteur", secteurs)
            
            if secteur_selected != 'Tous':
                df_filtre = df[df['Secteur'] == secteur_selected]
            else:
                df_filtre = df
        else:
            df_filtre = df
        
        # Affichage
        st.dataframe(df_filtre, use_container_width=True, height=400)
        
        # Performance moyenne par secteur
        if 'Secteur' in df.columns and 'Variation (%)' in df.columns:
            st.markdown("---")
            st.subheader("📈 Performance moyenne par secteur")
            
            perf = df.groupby('Secteur')['Variation (%)'].agg(['mean', 'count']).reset_index()
            perf.columns = ['Secteur', 'Variation Moyenne (%)', 'Nombre']
            perf = perf.sort_values('Variation Moyenne (%)', ascending=False)
            
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
        st.error("❌ Impossible de charger les données secteurs")


# ===========================
# PAGE ANALYSE
# ===========================
def page_analyse():
    st.title("📈 Analyse Fondamentale")
    
    st.info("💡 Sélectionnez un titre pour voir son analyse complète")
    
    financial_data = init_storage()
    
    if financial_data:
        symboles = sorted(set([data['symbole'] for data in financial_data.values() if isinstance(data, dict)]))
        
        if symboles:
            symbole_selected = st.selectbox("Choisissez un titre", [''] + symboles)
            
            if symbole_selected:
                # Votre code d'analyse existant (ratios, piotroski, etc.)
                st.success(f"Analyse de {symbole_selected}")
                # ... (code existant pour l'analyse)
        else:
            st.warning("Aucune donnée financière disponible")
    else:
        st.warning("Aucune donnée financière disponible")


# ===========================
# FONCTION DE FUSION
# ===========================
def get_brvm_data_with_sectors():
    """
    Récupère directement les données avec secteurs depuis BRVM
    Plus besoin de fusion car tout vient de la même source
    """
    # Option 1 : Utiliser directement les données par secteur
    df_secteurs = scrape_secteurs_brvm()
    
    if df_secteurs is not None:
        return df_secteurs
    
    # Fallback : Si les secteurs échouent, récupérer juste les cours
    st.warning("⚠️ Récupération par secteur échouée, chargement des cours généraux...")
    df_brvm = scrape_brvm_data()
    
    if df_brvm is not None:
        # Ajouter une colonne secteur par défaut
        df_brvm['Secteur'] = 'Non classé'
        return df_brvm
    
    return None
    
    # Récupération des secteurs
    df_secteurs = scrape_secteurs_brvm()
    
    if df_secteurs is None:
        st.warning("⚠️ Secteurs non disponibles - Affichage des cours uniquement")
        return df_brvm
    
    # Fusion sur le symbole
    if 'Symbole' in df_brvm.columns and 'Symbole' in df_secteurs.columns:
        # Sélection des colonnes pertinentes des secteurs
        colonnes_secteurs = ['Symbole']
        if 'Secteur' in df_secteurs.columns:
            colonnes_secteurs.append('Secteur')
        if 'Société' in df_secteurs.columns:
            colonnes_secteurs.append('Société')
        
        df_secteurs_clean = df_secteurs[colonnes_secteurs]
        
        # Fusion left pour garder toutes les données BRVM
        df_combined = df_brvm.merge(df_secteurs_clean, on='Symbole', how='left')
        
        # Remplir les secteurs manquants
        if 'Secteur' in df_combined.columns:
            df_combined['Secteur'].fillna('Non classé', inplace=True)
        
        st.info(f"ℹ️ {len(df_combined)} titres avec secteurs fusionnés")
        return df_combined
    
    return df_brvm
def clean_dataframe(df):
    """Nettoyer et formater le DataFrame"""
    df = df.copy()
    if df.empty:
        return df
    
    df.columns = [col.strip() for col in df.columns]
    
    # Identifier les colonnes numériques
    numeric_columns = []
    for col in df.columns:
        if any(keyword in col for keyword in ['Cours', 'Volume', 'Variation', 'Capitalisation']):
            numeric_columns.append(col)
    
    # Nettoyer les valeurs numériques
    for col in numeric_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.')
            df[col] = df[col].str.replace(' ', '')
            df[col] = df[col].str.replace('FCFA', '')
            df[col] = df[col].str.replace('F', '')
            df[col] = df[col].str.replace('CFA', '')
            df[col] = df[col].str.replace('%', '')
            df[col] = df[col].str.replace('€', '')
            df[col] = df[col].str.replace('$', '')
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    if 'Symbole' in df.columns:
        df = df.sort_values('Symbole').reset_index(drop=True)
    
    return df

# ===========================
# SECTION DÉVELOPPEUR
# ===========================

def developer_section():
    """Section réservée au développeur pour gérer les données financières"""
    st.title("🔐 Section Développeur - Gestion des Données Financières")
    
    # Authentification
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
    
    # Interface de gestion des données
    st.success("✅ Connecté en tant que développeur")
    
    # Charger les données BRVM pour récupérer les cours
    col_refresh1, col_refresh2 = st.columns([3, 1])
    with col_refresh1:
        st.info("💡 Les cours sont automatiquement récupérés depuis BRVM")
    with col_refresh2:
        if st.button("🔄 Actualiser les cours", use_container_width=True):
            st.cache_data.clear()
            st.success("Cours actualisés!")
            st.rerun()
    
    with st.spinner("Chargement des cours BRVM..."):
        df_brvm = scrape_brvm_data()
    
    # Initialiser le stockage
    financial_data = init_storage()
    
    # Sélection du symbole
    col1, col2 = st.columns([3, 1])
    with col1:
        symbole = st.text_input("Symbole de l'action (ex: SNTS, SGBC, BICC)", key="symbole_input").upper()
    with col2:
        annee = st.number_input("Année", min_value=2015, max_value=2030, value=2024)
    
    if symbole:
        # Vérifier si le symbole existe dans les données BRVM
        symbole_existe = False
        cours_brvm = 0
        nom_societe = ""
        variation = 0
        
        if df_brvm is not None and 'Symbole' in df_brvm.columns:
            if symbole in df_brvm['Symbole'].values:
                symbole_existe = True
                ligne = df_brvm[df_brvm['Symbole'] == symbole].iloc[0]
                
                # Récupérer le nom de la société si disponible
                if 'Nom' in df_brvm.columns:
                    nom_societe = ligne['Nom']
                
                # Chercher le cours de clôture
                for col in df_brvm.columns:
                    if 'Cours' in col and ('Clôture' in col or 'Cloture' in col):
                        try:
                            cours_brvm = float(ligne[col])
                            break
                        except:
                            continue
                
                # Si pas trouvé, chercher n'importe quelle colonne avec "Cours"
                if cours_brvm == 0:
                    for col in df_brvm.columns:
                        if 'Cours' in col:
                            try:
                                cours_brvm = float(ligne[col])
                                break
                            except:
                                continue
                
                # Chercher la variation si disponible
                if 'Variation (%)' in df_brvm.columns:
                    try:
                        variation = float(ligne['Variation (%)'])
                    except:
                        variation = 0
        
        st.subheader(f"📊 Données financières pour {symbole} - {annee}")
        
        if symbole_existe and nom_societe:
            if variation > 0:
                st.success(f"✅ {nom_societe} - Cours: {cours_brvm:,.0f} FCFA (+{variation}%)")
            elif variation < 0:
                st.warning(f"⚠️ {nom_societe} - Cours: {cours_brvm:,.0f} FCFA ({variation}%)")
            else:
                st.info(f"ℹ️ {nom_societe} - Cours: {cours_brvm:,.0f} FCFA")
        elif symbole_existe:
            st.info(f"ℹ️ Symbole {symbole} trouvé - Cours: {cours_brvm:,.0f} FCFA")
        else:
            st.warning(f"⚠️ Symbole {symbole} non trouvé dans les données BRVM")
        
        # Créer les onglets pour les différents états financiers
        tab1, tab2, tab3, tab4 = st.tabs(["📈 Bilan", "💰 Compte de Résultat", "💵 Flux de Trésorerie", "📊 Ratios Calculés"])
        
        # Clé unique pour ce symbole et cette année
        data_key = f"{symbole}_{annee}"
        
        # Récupérer les données existantes
        existing_data = financial_data.get(data_key, {
            'bilan': {},
            'compte_resultat': {},
            'flux_tresorerie': {},
            'ratios': {},
            'last_update': None
        })
        
        with tab1:
            st.markdown("### 🏦 BILAN")
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.markdown("**ACTIF**")
                actif_immobilise = st.number_input("Actif Immobilisé (FCFA)", 
                                                  value=float(existing_data.get('bilan', {}).get('actif_immobilise', 0)), 
                                                  step=1000000.0, 
                                                  format="%.0f",
                                                  key=f"actif_immo_{data_key}")
                actif_courant = st.number_input("Actif Courant (FCFA)", 
                                               value=float(existing_data.get('bilan', {}).get('actif_courant', 0)), 
                                               step=1000000.0,
                                               format="%.0f",
                                               key=f"actif_courant_{data_key}")
                stocks = st.number_input("Stocks (FCFA)", 
                                        value=float(existing_data.get('bilan', {}).get('stocks', 0)), 
                                        step=1000000.0,
                                        format="%.0f",
                                        key=f"stocks_{data_key}")
                creances = st.number_input("Créances (FCFA)", 
                                          value=float(existing_data.get('bilan', {}).get('creances', 0)), 
                                          step=1000000.0,
                                          format="%.0f",
                                          key=f"creances_{data_key}")
                tresorerie = st.number_input("Trésorerie et équivalents (FCFA)", 
                                            value=float(existing_data.get('bilan', {}).get('tresorerie', 0)), 
                                            step=1000000.0,
                                            format="%.0f",
                                            key=f"tresorerie_{data_key}")
                
                actif_total = actif_immobilise + actif_courant
                st.metric("**ACTIF TOTAL**", f"{actif_total:,.0f} FCFA")
            
            with col_b:
                st.markdown("**PASSIF**")
                capitaux_propres = st.number_input("Capitaux Propres (FCFA)", 
                                                  value=float(existing_data.get('bilan', {}).get('capitaux_propres', 0)), 
                                                  step=1000000.0,
                                                  format="%.0f",
                                                  key=f"cap_propres_{data_key}")
                dettes_long_terme = st.number_input("Dettes Long Terme (FCFA)", 
                                                   value=float(existing_data.get('bilan', {}).get('dettes_long_terme', 0)), 
                                                   step=1000000.0,
                                                   format="%.0f",
                                                   key=f"dettes_lt_{data_key}")
                passif_courant = st.number_input("Passif Courant (FCFA)", 
                                                value=float(existing_data.get('bilan', {}).get('passif_courant', 0)), 
                                                step=1000000.0,
                                                format="%.0f",
                                                key=f"passif_courant_{data_key}")
                
                dettes_totales = dettes_long_terme + passif_courant
                passif_total = capitaux_propres + dettes_totales
                
                st.metric("**PASSIF TOTAL**", f"{passif_total:,.0f} FCFA")
                
                # Vérification de l'équilibre
                if abs(actif_total - passif_total) > 1:
                    st.error(f"⚠️ Bilan non équilibré ! Différence: {actif_total - passif_total:,.0f} FCFA")
                else:
                    st.success("✅ Bilan équilibré")
            
            # Informations complémentaires
            st.markdown("**Informations Marché**")
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                # Cours automatique ou manuel
                if symbole_existe and cours_brvm > 0:
                    cours_action = st.number_input(
                        f"Cours de {symbole} (FCFA)", 
                        value=float(cours_brvm), 
                        step=100.0, 
                        format="%.0f",
                        key=f"cours_{data_key}",
                        help=f"Cours actuel sur BRVM: {cours_brvm:,.0f} FCFA"
                    )
                    st.caption(f"📈 Cours BRVM: {cours_brvm:,.0f} FCFA")
                else:
                    cours_action = st.number_input(
                        f"Cours de {symbole} (FCFA)", 
                        value=float(existing_data.get('bilan', {}).get('cours_action', 0)), 
                        step=100.0,
                        format="%.0f",
                        key=f"cours_{data_key}",
                        help="Symbole non trouvé - saisie manuelle requise"
                    )
            
            with col_m2:
                nb_actions = st.number_input("Nombre d'actions", 
                                            value=int(existing_data.get('bilan', {}).get('nb_actions', 0)), 
                                            step=1000,
                                            key=f"nb_actions_{data_key}")
            
            with col_m3:
                if nb_actions > 0 and capitaux_propres > 0:
                    cap_propres_par_action = capitaux_propres / nb_actions
                    st.metric("Cap. Propres / Action", f"{cap_propres_par_action:,.0f} FCFA")
                else:
                    cap_propres_par_action = 0
            
            # Sauvegarder les données du bilan
            bilan_data = {
                'actif_immobilise': float(actif_immobilise),
                'actif_courant': float(actif_courant),
                'stocks': float(stocks),
                'creances': float(creances),
                'tresorerie': float(tresorerie),
                'actif_total': float(actif_total),
                'capitaux_propres': float(capitaux_propres),
                'dettes_long_terme': float(dettes_long_terme),
                'passif_courant': float(passif_courant),
                'dettes_totales': float(dettes_totales),
                'passif_total': float(passif_total),
                'cours_action': float(cours_action),
                'nb_actions': int(nb_actions),
                'capitaux_propres_par_action': float(cap_propres_par_action),
                'cours_source': 'auto' if (symbole_existe and cours_brvm > 0) else 'manual'
            }
        
        with tab2:
            st.markdown("### 💰 COMPTE DE RÉSULTAT")
            
            chiffre_affaires = st.number_input("Chiffre d'Affaires (FCFA)", 
                                              value=float(existing_data.get('compte_resultat', {}).get('chiffre_affaires', 0)), 
                                              step=1000000.0,
                                              format="%.0f",
                                              key=f"ca_{data_key}")
            charges_exploitation = st.number_input("Charges d'Exploitation (FCFA)", 
                                                  value=float(existing_data.get('compte_resultat', {}).get('charges_exploitation', 0)), 
                                                  step=1000000.0,
                                                  format="%.0f",
                                                  key=f"charges_exp_{data_key}")
            
            resultat_exploitation = chiffre_affaires - charges_exploitation
            st.metric("Résultat d'Exploitation", f"{resultat_exploitation:,.0f} FCFA")
            
            charges_financieres = st.number_input("Charges Financières (FCFA)", 
                                                 value=float(existing_data.get('compte_resultat', {}).get('charges_financieres', 0)), 
                                                 step=100000.0,
                                                 format="%.0f",
                                                 key=f"charges_fin_{data_key}")
            produits_financiers = st.number_input("Produits Financiers (FCFA)", 
                                                 value=float(existing_data.get('compte_resultat', {}).get('produits_financiers', 0)), 
                                                 step=100000.0,
                                                 format="%.0f",
                                                 key=f"prod_fin_{data_key}")
            
            resultat_financier = produits_financiers - charges_financieres
            st.metric("Résultat Financier", f"{resultat_financier:,.0f} FCFA")
            
            resultat_avant_impot = resultat_exploitation + resultat_financier
            st.metric("Résultat Avant Impôt", f"{resultat_avant_impot:,.0f} FCFA")
            
            impots = st.number_input("Impôts sur les sociétés (FCFA)", 
                                    value=float(existing_data.get('compte_resultat', {}).get('impots', 0)), 
                                    step=100000.0,
                                    format="%.0f",
                                    key=f"impots_{data_key}")
            
            resultat_net = resultat_avant_impot - impots
            st.metric("**RÉSULTAT NET**", f"{resultat_net:,.0f} FCFA", delta=None)
            
            # Calcul par action
            if nb_actions > 0:
                benefice_par_action = resultat_net / nb_actions
                st.metric("Bénéfice par Action (BPA)", f"{benefice_par_action:,.2f} FCFA")
            else:
                benefice_par_action = 0
            
            # Sauvegarder les données du compte de résultat
            compte_resultat_data = {
                'chiffre_affaires': float(chiffre_affaires),
                'charges_exploitation': float(charges_exploitation),
                'resultat_exploitation': float(resultat_exploitation),
                'charges_financieres': float(charges_financieres),
                'produits_financiers': float(produits_financiers),
                'resultat_financier': float(resultat_financier),
                'resultat_avant_impot': float(resultat_avant_impot),
                'impots': float(impots),
                'resultat_net': float(resultat_net),
                'benefice_par_action': float(benefice_par_action)
            }
        
        with tab3:
            st.markdown("### 💵 TABLEAU DES FLUX DE TRÉSORERIE")
            
            st.markdown("**Flux de Trésorerie d'Exploitation**")
            flux_exploitation = st.number_input("Flux d'Exploitation (FCFA)", 
                                               value=float(existing_data.get('flux_tresorerie', {}).get('flux_exploitation', 0)), 
                                               step=1000000.0,
                                               format="%.0f",
                                               key=f"flux_exp_{data_key}")
            
            st.markdown("**Flux de Trésorerie d'Investissement**")
            flux_investissement = st.number_input("Flux d'Investissement (FCFA)", 
                                                 value=float(existing_data.get('flux_tresorerie', {}).get('flux_investissement', 0)), 
                                                 step=1000000.0,
                                                 format="%.0f",
                                                 key=f"flux_inv_{data_key}")
            
            st.markdown("**Flux de Trésorerie de Financement**")
            flux_financement = st.number_input("Flux de Financement (FCFA)", 
                                              value=float(existing_data.get('flux_tresorerie', {}).get('flux_financement', 0)), 
                                              step=1000000.0,
                                              format="%.0f",
                                              key=f"flux_fin_{data_key}")
            
            variation_tresorerie = flux_exploitation + flux_investissement + flux_financement
            st.metric("**Variation de Trésorerie**", f"{variation_tresorerie:,.0f} FCFA")
            
            # Sauvegarder les données des flux de trésorerie
            flux_tresorerie_data = {
                'flux_exploitation': float(flux_exploitation),
                'flux_investissement': float(flux_investissement),
                'flux_financement': float(flux_financement),
                'variation_tresorerie': float(variation_tresorerie)
            }
        
        with tab4:
            st.markdown("### 📊 RATIOS FINANCIERS CALCULÉS AUTOMATIQUEMENT")
            
            # Calculer les ratios
            ratios = calculate_enhanced_financial_ratios(bilan_data, compte_resultat_data, flux_tresorerie_data)
            
            if ratios:
                col_r1, col_r2, col_r3 = st.columns(3)
                
                with col_r1:
                    st.markdown("**📈 RENTABILITÉ**")
                    if 'marge_nette' in ratios:
                        st.metric("Marge Nette", f"{ratios['marge_nette']:.2f}%")
                    if 'marge_ebit' in ratios:
                        st.metric("Marge EBIT", f"{ratios['marge_ebit']:.2f}%")
                    if 'marge_ebitda' in ratios:
                        st.metric("Marge EBITDA", f"{ratios['marge_ebitda']:.2f}%")
                    if 'roe' in ratios:
                        st.metric("ROE", f"{ratios['roe']:.2f}%")
                    if 'roa' in ratios:
                        st.metric("ROA", f"{ratios['roa']:.2f}%")
                
                with col_r2:
                    st.markdown("**💧 LIQUIDITÉ**")
                    if 'ratio_liquidite_generale' in ratios:
                        st.metric("Ratio de Liquidité Générale", f"{ratios['ratio_liquidite_generale']:.2f}")
                    if 'ratio_liquidite_reduite' in ratios:
                        st.metric("Ratio de Liquidité Réduite", f"{ratios['ratio_liquidite_reduite']:.2f}")
                    if 'ratio_liquidite_immediate' in ratios:
                        st.metric("Ratio de Liquidité Immédiate", f"{ratios['ratio_liquidite_immediate']:.2f}")
                    
                    st.markdown("**💳 ENDETTEMENT**")
                    if 'ratio_endettement' in ratios:
                        st.metric("Ratio d'Endettement", f"{ratios['ratio_endettement']:.2f}%")
                    if 'taux_endettement' in ratios:
                        st.metric("Taux d'Endettement", f"{ratios['taux_endettement']:.2f}%")
                    if 'debt_to_ebitda' in ratios:
                        st.metric("Debt to EBITDA", f"{ratios['debt_to_ebitda']:.2f}")
                
                with col_r3:
                    st.markdown("**⚡ EFFICACITÉ**")
                    if 'rotation_actifs' in ratios:
                        st.metric("Rotation des Actifs", f"{ratios['rotation_actifs']:.2f}")
                    if 'rotation_stocks' in ratios:
                        st.metric("Rotation des Stocks", f"{ratios['rotation_stocks']:.2f}")
                    if 'delai_recouvrement' in ratios:
                        st.metric("Délai de Recouvrement", f"{ratios['delai_recouvrement']:.0f} jours")
                    
                    st.markdown("**📊 MARCHÉ**")
                    if 'per' in ratios:
                        st.metric("PER", f"{ratios['per']:.2f}")
                    if 'price_to_book' in ratios:
                        st.metric("Price to Book", f"{ratios['price_to_book']:.2f}")
                    if 'ev_ebitda' in ratios:
                        st.metric("EV/EBITDA", f"{ratios['ev_ebitda']:.2f}")
                
                # Interprétation des ratios
                st.markdown("---")
                st.markdown("### 💡 Interprétation Automatique")
                
                interpretations = []
                
                if 'roe' in ratios:
                    if ratios['roe'] > 15:
                        interpretations.append("✅ ROE excellent (>15%) - Entreprise très rentable pour les actionnaires")
                    elif ratios['roe'] > 10:
                        interpretations.append("👍 ROE bon (10-15%) - Rentabilité correcte")
                    else:
                        interpretations.append("⚠️ ROE faible (<10%) - Rentabilité à améliorer")
                
                if 'ratio_liquidite_generale' in ratios:
                    if ratios['ratio_liquidite_generale'] > 2:
                        interpretations.append("✅ Excellente liquidité (>2) - Capacité élevée à honorer les dettes court terme")
                    elif ratios['ratio_liquidite_generale'] > 1:
                        interpretations.append("👍 Bonne liquidité (1-2) - Capacité correcte")
                    else:
                        interpretations.append("⚠️ Liquidité faible (<1) - Risque de solvabilité")
                
                if 'ratio_endettement' in ratios:
                    if ratios['ratio_endettement'] < 50:
                        interpretations.append("✅ Faible endettement (<50%) - Structure financière saine")
                    elif ratios['ratio_endettement'] < 100:
                        interpretations.append("👍 Endettement modéré (50-100%) - Structure acceptable")
                    else:
                        interpretations.append("⚠️ Fort endettement (>100%) - Risque financier élevé")
                
                if 'debt_to_ebitda' in ratios:
                    if ratios['debt_to_ebitda'] < 3:
                        interpretations.append("✅ Dette/EBITDA excellent (<3) - Capacité de remboursement forte")
                    elif ratios['debt_to_ebitda'] < 5:
                        interpretations.append("👍 Dette/EBITDA acceptable (3-5)")
                    else:
                        interpretations.append("⚠️ Dette/EBITDA élevé (>5) - Risque de surendettement")
                
                if 'ev_ebitda' in ratios:
                    if ratios['ev_ebitda'] < 8:
                        interpretations.append("✅ Multiple EV/EBITDA attractif (<8) - Action potentiellement sous-évaluée")
                    elif ratios['ev_ebitda'] < 12:
                        interpretations.append("👍 Multiple EV/EBITDA modéré (8-12)")
                    else:
                        interpretations.append("⚠️ Multiple EV/EBITDA élevé (>12) - Action potentiellement surévaluée")
                
                for interp in interpretations:
                    st.info(interp)
            else:
                st.warning("Remplissez les données financières pour voir les ratios calculés")
        
        # Bouton de sauvegarde global
        st.markdown("---")
        col_save1, col_save2, col_save3 = st.columns([1, 1, 1])
        
        with col_save1:
            if st.button("💾 Sauvegarder les Données", type="primary", use_container_width=True):
                # Préparer les données pour Supabase
                data_to_save = {
                    'bilan': bilan_data,
                    'compte_resultat': compte_resultat_data,
                    'flux_tresorerie': flux_tresorerie_data,
                    'ratios': ratios
                }
                
                # Sauvegarder dans Supabase
                if save_financial_data(symbole, annee, data_to_save):
                    st.success(f"✅ Données sauvegardées dans le cloud pour {symbole} - {annee}")
                    # Recharger les données
                    st.session_state.financial_data = load_all_financial_data()
                    st.rerun()
        
        with col_save2:
            if st.button("🗑️ Supprimer ces Données", use_container_width=True):
                if delete_financial_data(symbole, annee):
                    st.success(f"Données supprimées du cloud pour {symbole} - {annee}")
                    # Recharger les données
                    st.session_state.financial_data = load_all_financial_data()
                    st.rerun()
        
        with col_save3:
            if st.button("🔄 Actualiser depuis le Cloud", use_container_width=True):
                st.session_state.financial_data = load_all_financial_data()
                st.success("Données actualisées depuis Supabase")
                st.rerun()
        
        # Afficher toutes les données sauvegardées
        st.markdown("---")
        st.subheader("📚 Données Financières Sauvegardées (Cloud)")
        
        financial_data = init_storage()
        if financial_data:
            saved_data = []
            for key, data in financial_data.items():
                if isinstance(data, dict):
                    saved_data.append({
                        'Symbole': data.get('symbole', 'N/A'),
                        'Année': data.get('annee', 'N/A'),
                        'Dernière MAJ': data.get('last_update', 'N/A')[:19] if data.get('last_update') else 'N/A'
                    })
            
            if saved_data:
                df_saved = pd.DataFrame(saved_data)
                st.dataframe(df_saved, use_container_width=True)
                st.caption(f"Total: {len(saved_data)} enregistrements dans Supabase")
        else:
            st.info("Aucune donnée financière sauvegardée dans le cloud")

def display_brvm_data():
    st.sidebar.header("⚙️ Paramètres")
    
    col_refresh1, col_refresh2 = st.sidebar.columns(2)
    with col_refresh1:
        if st.button("🔄 Actualiser", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    with col_refresh2:
        mode_affichage = st.radio("Mode", ["Avec secteurs", "Cours seuls"], 
                                  label_visibility="collapsed")
    
    with st.spinner("📊 Récupération des données BRVM..."):
        if mode_affichage == "Avec secteurs":
            df = get_brvm_data_with_sectors()
        else:
            df = scrape_brvm_data()
            if df is not None:
                df['Secteur'] = 'Tous'
    
    if df is not None:
        st.subheader("📊 Statistiques du marché")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Nombre total de titres", len(df))
        
        with col2:
            if 'Variation (%)' in df.columns:
                hausse = len(df[df['Variation (%)'] > 0])
                st.metric("En hausse", hausse, f"+{hausse}")
        
        with col3:
            if 'Variation (%)' in df.columns:
                baisse = len(df[df['Variation (%)'] < 0])
                st.metric("En baisse", baisse, f"-{baisse}")
        
        with col4:
            if 'Variation (%)' in df.columns:
                stable = len(df[df['Variation (%)'] == 0])
                st.metric("Stables", stable)
        
        # Répartition par secteur
        if 'Secteur' in df.columns and mode_affichage == "Avec secteurs":
            st.markdown("---")
            st.subheader("📈 Répartition par secteur")
            
            secteur_counts = df['Secteur'].value_counts()
            
            col_sec1, col_sec2 = st.columns([2, 1])
            
            with col_sec1:
                # Graphique en barres
                import plotly.express as px
                fig = px.bar(
                    x=secteur_counts.index,
                    y=secteur_counts.values,
                    labels={'x': 'Secteur', 'y': 'Nombre de sociétés'},
                    title='Nombre de sociétés par secteur',
                    color=secteur_counts.values,
                    color_continuous_scale='Viridis'
                )
                fig.update_layout(showlegend=False, height=300)
                st.plotly_chart(fig, use_container_width=True)
            
            with col_sec2:
                st.markdown("**Distribution :**")
                for secteur, count in secteur_counts.items():
                    st.metric(secteur, count)
        
        # Filtre par secteur
        st.markdown("---")
        st.subheader("🔍 Filtrage par secteur")
        
        if 'Secteur' in df.columns:
            secteurs = ['Tous les secteurs'] + sorted(df['Secteur'].dropna().unique().tolist())
            
            col_filtre1, col_filtre2 = st.columns([3, 1])
            
            with col_filtre1:
                secteur_selectionne = st.selectbox("Choisissez un secteur", secteurs)
            
            with col_filtre2:
                if secteur_selectionne != 'Tous les secteurs':
                    df_filtre = df[df['Secteur'] == secteur_selectionne]
                    st.metric("Titres affichés", len(df_filtre))
                else:
                    df_filtre = df
                    st.metric("Titres affichés", len(df_filtre))
            
            if secteur_selectionne != 'Tous les secteurs':
                st.info(f"📌 Secteur : **{secteur_selectionne}** ({len(df_filtre)} sociétés)")
        else:
            df_filtre = df
        
        # Affichage du tableau
        st.subheader("📊 Cours des Actions")
        
        def color_variation(val):
            if isinstance(val, (int, float)):
                if val > 0:
                    return 'color: green; font-weight: bold'
                elif val < 0:
                    return 'color: red; font-weight: bold'
            return ''
        
        if 'Variation (%)' in df_filtre.columns:
            styled_df = df_filtre.style.map(color_variation, subset=['Variation (%)'])
            st.dataframe(styled_df, use_container_width=True, height=400)
        else:
            st.dataframe(df_filtre, use_container_width=True, height=400)
        
        # Analyse des performances par secteur
        if 'Secteur' in df_filtre.columns and 'Variation (%)' in df_filtre.columns and len(df_filtre['Secteur'].unique()) > 1:
            st.markdown("---")
            st.subheader("📊 Performance moyenne par secteur")
            
            perf_secteur = df_filtre.groupby('Secteur')['Variation (%)'].agg(['mean', 'count']).reset_index()
            perf_secteur.columns = ['Secteur', 'Variation Moyenne (%)', 'Nombre de titres']
            perf_secteur = perf_secteur.sort_values('Variation Moyenne (%)', ascending=False)
            
            col_perf1, col_perf2 = st.columns([2, 1])
            
            with col_perf1:
                fig_perf = px.bar(
                    perf_secteur,
                    x='Secteur',
                    y='Variation Moyenne (%)',
                    title='Performance moyenne par secteur',
                    color='Variation Moyenne (%)',
                    color_continuous_scale=['red', 'yellow', 'green'],
                    color_continuous_midpoint=0
                )
                fig_perf.update_layout(height=300)
                st.plotly_chart(fig_perf, use_container_width=True)
            
            with col_perf2:
                st.dataframe(
                    perf_secteur.style.format({
                        'Variation Moyenne (%)': '{:.2f}%',
                        'Nombre de titres': '{:.0f}'
                    }),
                    use_container_width=True,
                    hide_index=True
                )
        
        # Export CSV
        st.markdown("---")
        st.subheader("💾 Export des données")
        
        csv = df_filtre.to_csv(index=False, sep=';', decimal=',')
        st.download_button(
            label="📥 Télécharger en CSV",
            data=csv,
            file_name=f"brvm_cours_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
        
        # Section Analyse Fondamentale
        st.markdown("---")
        st.subheader("📊 Analyse Fondamentale par Titre")
        
        if 'Symbole' in df_filtre.columns:
            symboles_list = [''] + df_filtre['Symbole'].dropna().unique().tolist()
            symbole_selected = st.selectbox("Sélectionnez un titre pour voir son analyse fondamentale", symboles_list)
            
            if symbole_selected:
                # Charger les données financières
                financial_data = init_storage()
                
                # Trouver les données pour ce symbole
                symbole_data = {}
                for key, data in financial_data.items():
                    if data.get('symbole') == symbole_selected:
                        symbole_data[data['annee']] = data
                
                if symbole_data:
                    st.success(f"✅ Données financières disponibles pour {symbole_selected}")
                    
                    # Afficher les années disponibles
                    annees = sorted(symbole_data.keys())
                    annee_selectionnee = st.selectbox("Sélectionnez l'année", annees, index=len(annees)-1)
                    
                    if annee_selectionnee:
                        data = symbole_data[annee_selectionnee]
                        
                        # Afficher les ratios
                        st.markdown(f"### 📊 Ratios pour {symbole_selected} - {annee_selectionnee}")
                        
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
                            
                            # Valorisation par multiples
                            st.markdown("### 💹 Valorisation par Multiples")
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
                            
                            # Projections financières
                            st.markdown("### 📈 Projections Financières")
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
                    st.warning(f"ℹ️ Aucune donnée financière sauvegardée pour {symbole_selected}")
                    st.info("Utilisez la section Développeur pour saisir les données financières de cette entreprise")
        
        # Export CSV
        st.markdown("---")
        st.subheader("💾 Export des données")
        
        csv = df_filtre.to_csv(index=False, sep=';', decimal=',')
        st.download_button(
            label="📥 Télécharger en CSV",
            data=csv,
            file_name=f"brvm_cours_{secteur_selectionne.replace(' ', '_') if 'secteur_selectionne' in locals() else 'tous'}.csv",
            mime="text/csv"
        )
    
    else:
        st.warning("⚠️ Impossible de récupérer les données BRVM")
        st.info("Vérifiez votre connexion internet ou réessayez plus tard")

# ===========================
# INTERFACE PRINCIPALE
# ===========================

def main():
    # Initialisation session state
    if 'page' not in st.session_state:
        st.session_state.page = 'accueil'
    
    # Navigation
    render_navigation()
    
    # Routing des pages
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
    
    # Footer
    st.markdown("---")
    st.caption(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')} | 🔗 Source : BRVM")


if __name__ == "__main__":
    main()
