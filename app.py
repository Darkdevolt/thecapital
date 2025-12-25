import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import warnings
import json
from datetime import datetime
from supabase import create_client
warnings.filterwarnings('ignore')

# Configuration
st.set_page_config(page_title="Analyse BRVM", layout="wide")

# Mot de passe développeur
DEVELOPER_PASSWORD = "dev_brvm_2024"

# ===========================
# CONFIGURATION SUPABASE
# ===========================

# Configuration Supabase - UTILISEZ VOS CLÉS ICI
SUPABASE_URL = "https://otsiwiwlnowxeolbbgvm.supabase.co"
SUPABASE_KEY = "sb_publishable_MhaI5b-kMmb5liIMOJ4P3Q_xGTsJAFJ"

def init_supabase():
    """Initialiser la connexion à Supabase"""
    if 'supabase' not in st.session_state:
        try:
            st.session_state.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            # Test de connexion
            test_response = st.session_state.supabase.table("financial_data").select("*", count="exact").limit(1).execute()
            print(f"✅ Connexion Supabase établie")
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
        
        print(f"✅ {len(financial_data)} enregistrements chargés depuis Supabase")
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

def calculate_financial_ratios(bilan, compte_resultat, flux_tresorerie):
    """Calculer automatiquement les ratios financiers"""
    ratios = {}
    
    try:
        # RATIOS DE RENTABILITÉ
        if compte_resultat.get('resultat_net') and compte_resultat.get('chiffre_affaires'):
            ratios['marge_nette'] = (compte_resultat['resultat_net'] / compte_resultat['chiffre_affaires']) * 100
        
        if compte_resultat.get('resultat_exploitation') and compte_resultat.get('chiffre_affaires'):
            ratios['marge_exploitation'] = (compte_resultat['resultat_exploitation'] / compte_resultat['chiffre_affaires']) * 100
        
        if compte_resultat.get('resultat_net') and bilan.get('capitaux_propres'):
            ratios['roe'] = (compte_resultat['resultat_net'] / bilan['capitaux_propres']) * 100
        
        if compte_resultat.get('resultat_net') and bilan.get('actif_total'):
            ratios['roa'] = (compte_resultat['resultat_net'] / bilan['actif_total']) * 100
        
        # RATIOS DE LIQUIDITÉ
        if bilan.get('actif_courant') and bilan.get('passif_courant'):
            ratios['ratio_liquidite_generale'] = bilan['actif_courant'] / bilan['passif_courant']
        
        if bilan.get('tresorerie') and bilan.get('passif_courant'):
            ratios['ratio_liquidite_immediate'] = bilan['tresorerie'] / bilan['passif_courant']
        
        # RATIOS D'ENDETTEMENT
        if bilan.get('dettes_totales') and bilan.get('capitaux_propres'):
            ratios['ratio_endettement'] = (bilan['dettes_totales'] / bilan['capitaux_propres']) * 100
        
        if bilan.get('dettes_totales') and bilan.get('actif_total'):
            ratios['taux_endettement'] = (bilan['dettes_totales'] / bilan['actif_total']) * 100
        
        # RATIOS D'EFFICACITÉ
        if compte_resultat.get('chiffre_affaires') and bilan.get('actif_total'):
            ratios['rotation_actifs'] = compte_resultat['chiffre_affaires'] / bilan['actif_total']
        
        if compte_resultat.get('chiffre_affaires') and bilan.get('stocks') and bilan.get('stocks') > 0:
            ratios['rotation_stocks'] = compte_resultat['chiffre_affaires'] / bilan['stocks']
        
        # RATIOS DE MARCHÉ
        if bilan.get('cours_action') and compte_resultat.get('benefice_par_action') and compte_resultat.get('benefice_par_action') > 0:
            ratios['per'] = bilan['cours_action'] / compte_resultat['benefice_par_action']
        
        if bilan.get('cours_action') and bilan.get('capitaux_propres_par_action') and bilan.get('capitaux_propres_par_action') > 0:
            ratios['price_to_book'] = bilan['cours_action'] / bilan['capitaux_propres_par_action']
        
        # RATIOS DE FLUX DE TRÉSORERIE
        if flux_tresorerie.get('flux_exploitation') and compte_resultat.get('resultat_net') and compte_resultat.get('resultat_net') != 0:
            ratios['qualite_benefices'] = flux_tresorerie['flux_exploitation'] / compte_resultat['resultat_net']
        
        if flux_tresorerie.get('flux_exploitation') and bilan.get('passif_courant') and bilan.get('passif_courant') > 0:
            ratios['couverture_dettes_courtes'] = flux_tresorerie['flux_exploitation'] / bilan['passif_courant']
        
    except Exception as e:
        st.error(f"Erreur lors du calcul des ratios: {str(e)}")
    
    return ratios

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
    
    # Initialiser le stockage
    financial_data = init_storage()
    
    # Section de gestion des données
    col1, col2 = st.columns([3, 1])
    with col1:
        symbole = st.text_input("Symbole de l'action (ex: SNTS, SGBC, BICC)", key="symbole_input").upper()
    with col2:
        annee = st.number_input("Année", min_value=2015, max_value=2030, value=2024)
    
    if symbole:
        st.subheader(f"📊 Données financières pour {symbole} - {annee}")
        
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
                actif_immobilise = st.number_input("Actif Immobilisé (FCFA)", value=float(existing_data.get('bilan', {}).get('actif_immobilise', 0)), step=1000000.0, key=f"actif_immo_{data_key}")
                actif_courant = st.number_input("Actif Courant (FCFA)", value=float(existing_data.get('bilan', {}).get('actif_courant', 0)), step=1000000.0, key=f"actif_courant_{data_key}")
                stocks = st.number_input("Stocks (FCFA)", value=float(existing_data.get('bilan', {}).get('stocks', 0)), step=1000000.0, key=f"stocks_{data_key}")
                creances = st.number_input("Créances (FCFA)", value=float(existing_data.get('bilan', {}).get('creances', 0)), step=1000000.0, key=f"creances_{data_key}")
                tresorerie = st.number_input("Trésorerie et équivalents (FCFA)", value=float(existing_data.get('bilan', {}).get('tresorerie', 0)), step=1000000.0, key=f"tresorerie_{data_key}")
                
                actif_total = actif_immobilise + actif_courant
                st.metric("**ACTIF TOTAL**", f"{actif_total:,.0f} FCFA")
            
            with col_b:
                st.markdown("**PASSIF**")
                capitaux_propres = st.number_input("Capitaux Propres (FCFA)", value=float(existing_data.get('bilan', {}).get('capitaux_propres', 0)), step=1000000.0, key=f"cap_propres_{data_key}")
                dettes_long_terme = st.number_input("Dettes Long Terme (FCFA)", value=float(existing_data.get('bilan', {}).get('dettes_long_terme', 0)), step=1000000.0, key=f"dettes_lt_{data_key}")
                passif_courant = st.number_input("Passif Courant (FCFA)", value=float(existing_data.get('bilan', {}).get('passif_courant', 0)), step=1000000.0, key=f"passif_courant_{data_key}")
                
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
                cours_action = st.number_input("Cours de l'action (FCFA)", value=float(existing_data.get('bilan', {}).get('cours_action', 0)), step=100.0, key=f"cours_{data_key}")
            with col_m2:
                nb_actions = st.number_input("Nombre d'actions", value=int(existing_data.get('bilan', {}).get('nb_actions', 0)), step=1000, key=f"nb_actions_{data_key}")
            with col_m3:
                if nb_actions > 0 and capitaux_propres > 0:
                    cap_propres_par_action = capitaux_propres / nb_actions
                    st.metric("Cap. Propres / Action", f"{cap_propres_par_action:,.0f} FCFA")
                else:
                    cap_propres_par_action = 0
            
            # Sauvegarder les données du bilan
            bilan_data = {
                'actif_immobilise': actif_immobilise,
                'actif_courant': actif_courant,
                'stocks': stocks,
                'creances': creances,
                'tresorerie': tresorerie,
                'actif_total': actif_total,
                'capitaux_propres': capitaux_propres,
                'dettes_long_terme': dettes_long_terme,
                'passif_courant': passif_courant,
                'dettes_totales': dettes_totales,
                'passif_total': passif_total,
                'cours_action': cours_action,
                'nb_actions': nb_actions,
                'capitaux_propres_par_action': cap_propres_par_action
            }
        
        with tab2:
            st.markdown("### 💰 COMPTE DE RÉSULTAT")
            
            chiffre_affaires = st.number_input("Chiffre d'Affaires (FCFA)", value=float(existing_data.get('compte_resultat', {}).get('chiffre_affaires', 0)), step=1000000.0, key=f"ca_{data_key}")
            charges_exploitation = st.number_input("Charges d'Exploitation (FCFA)", value=float(existing_data.get('compte_resultat', {}).get('charges_exploitation', 0)), step=1000000.0, key=f"charges_exp_{data_key}")
            
            resultat_exploitation = chiffre_affaires - charges_exploitation
            st.metric("Résultat d'Exploitation", f"{resultat_exploitation:,.0f} FCFA")
            
            charges_financieres = st.number_input("Charges Financières (FCFA)", value=float(existing_data.get('compte_resultat', {}).get('charges_financieres', 0)), step=100000.0, key=f"charges_fin_{data_key}")
            produits_financiers = st.number_input("Produits Financiers (FCFA)", value=float(existing_data.get('compte_resultat', {}).get('produits_financiers', 0)), step=100000.0, key=f"prod_fin_{data_key}")
            
            resultat_financier = produits_financiers - charges_financieres
            st.metric("Résultat Financier", f"{resultat_financier:,.0f} FCFA")
            
            resultat_avant_impot = resultat_exploitation + resultat_financier
            st.metric("Résultat Avant Impôt", f"{resultat_avant_impot:,.0f} FCFA")
            
            impots = st.number_input("Impôts sur les sociétés (FCFA)", value=float(existing_data.get('compte_resultat', {}).get('impots', 0)), step=100000.0, key=f"impots_{data_key}")
            
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
                'chiffre_affaires': chiffre_affaires,
                'charges_exploitation': charges_exploitation,
                'resultat_exploitation': resultat_exploitation,
                'charges_financieres': charges_financieres,
                'produits_financiers': produits_financiers,
                'resultat_financier': resultat_financier,
                'resultat_avant_impot': resultat_avant_impot,
                'impots': impots,
                'resultat_net': resultat_net,
                'benefice_par_action': benefice_par_action
            }
        
        with tab3:
            st.markdown("### 💵 TABLEAU DES FLUX DE TRÉSORERIE")
            
            st.markdown("**Flux de Trésorerie d'Exploitation**")
            flux_exploitation = st.number_input("Flux d'Exploitation (FCFA)", value=float(existing_data.get('flux_tresorerie', {}).get('flux_exploitation', 0)), step=1000000.0, key=f"flux_exp_{data_key}")
            
            st.markdown("**Flux de Trésorerie d'Investissement**")
            flux_investissement = st.number_input("Flux d'Investissement (FCFA)", value=float(existing_data.get('flux_tresorerie', {}).get('flux_investissement', 0)), step=1000000.0, key=f"flux_inv_{data_key}")
            
            st.markdown("**Flux de Trésorerie de Financement**")
            flux_financement = st.number_input("Flux de Financement (FCFA)", value=float(existing_data.get('flux_tresorerie', {}).get('flux_financement', 0)), step=1000000.0, key=f"flux_fin_{data_key}")
            
            variation_tresorerie = flux_exploitation + flux_investissement + flux_financement
            st.metric("**Variation de Trésorerie**", f"{variation_tresorerie:,.0f} FCFA")
            
            # Sauvegarder les données des flux de trésorerie
            flux_tresorerie_data = {
                'flux_exploitation': flux_exploitation,
                'flux_investissement': flux_investissement,
                'flux_financement': flux_financement,
                'variation_tresorerie': variation_tresorerie
            }
        
        with tab4:
            st.markdown("### 📊 RATIOS FINANCIERS CALCULÉS AUTOMATIQUEMENT")
            
            # Calculer les ratios
            ratios = calculate_financial_ratios(bilan_data, compte_resultat_data, flux_tresorerie_data)
            
            if ratios:
                col_r1, col_r2, col_r3 = st.columns(3)
                
                with col_r1:
                    st.markdown("**📈 RENTABILITÉ**")
                    if 'marge_nette' in ratios:
                        st.metric("Marge Nette", f"{ratios['marge_nette']:.2f}%")
                    if 'marge_exploitation' in ratios:
                        st.metric("Marge d'Exploitation", f"{ratios['marge_exploitation']:.2f}%")
                    if 'roe' in ratios:
                        st.metric("ROE", f"{ratios['roe']:.2f}%")
                    if 'roa' in ratios:
                        st.metric("ROA", f"{ratios['roa']:.2f}%")
                
                with col_r2:
                    st.markdown("**💧 LIQUIDITÉ**")
                    if 'ratio_liquidite_generale' in ratios:
                        st.metric("Ratio de Liquidité Générale", f"{ratios['ratio_liquidite_generale']:.2f}")
                    if 'ratio_liquidite_immediate' in ratios:
                        st.metric("Ratio de Liquidité Immédiate", f"{ratios['ratio_liquidite_immediate']:.2f}")
                    
                    st.markdown("**💳 ENDETTEMENT**")
                    if 'ratio_endettement' in ratios:
                        st.metric("Ratio d'Endettement", f"{ratios['ratio_endettement']:.2f}%")
                    if 'taux_endettement' in ratios:
                        st.metric("Taux d'Endettement", f"{ratios['taux_endettement']:.2f}%")
                
                with col_r3:
                    st.markdown("**⚡ EFFICACITÉ**")
                    if 'rotation_actifs' in ratios:
                        st.metric("Rotation des Actifs", f"{ratios['rotation_actifs']:.2f}")
                    if 'rotation_stocks' in ratios:
                        st.metric("Rotation des Stocks", f"{ratios['rotation_stocks']:.2f}")
                    
                    st.markdown("**📊 MARCHÉ**")
                    if 'per' in ratios:
                        st.metric("PER", f"{ratios['per']:.2f}")
                    if 'price_to_book' in ratios:
                        st.metric("Price to Book", f"{ratios['price_to_book']:.2f}")
                
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
                    'symbole': symbole,
                    'annee': annee,
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

# ===========================
# FONCTIONS DE SCRAPING BRVM
# ===========================

@st.cache_data(ttl=300)
def scrape_brvm_data():
    """Fonction pour scraper les données du site BRVM"""
    url = "https://www.brvm.org/fr/cours-actions/0"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        table = None
        for t in soup.find_all('table'):
            headers_list = [th.get_text(strip=True) for th in t.find_all('th')]
            if 'Symbole' in headers_list and 'Nom' in headers_list:
                table = t
                break
        
        if not table:
            tables = soup.find_all('table')
            if tables:
                table = tables[0]
        
        if not table:
            return None
        
        headers_list = [th.get_text(strip=True) for th in table.find_all('th')]
        
        if not headers_list:
            headers_list = ['Symbole', 'Nom', 'Volume', 'Cours veille (FCFA)', 
                      'Cours Ouverture (FCFA)', 'Cours Clôture (FCFA)', 'Variation (%)']
        
        data = []
        for row in table.find_all('tr'):
            cells = row.find_all(['td', 'th'])
            if cells and cells[0].name == 'td':
                row_data = [cell.get_text(strip=True) for cell in cells]
                
                if len(row_data) >= 6:
                    if len(row_data) < len(headers_list):
                        row_data.extend([''] * (len(headers_list) - len(row_data)))
                    elif len(row_data) > len(headers_list):
                        row_data = row_data[:len(headers_list)]
                    
                    data.append(row_data)
        
        if not data:
            return None
        
        df = pd.DataFrame(data, columns=headers_list)
        df_clean = clean_dataframe(df)
        
        return df_clean
        
    except Exception as e:
        return None

def clean_dataframe(df):
    """Nettoyer et formater le DataFrame"""
    df = df.copy()
    df.columns = [col.strip() for col in df.columns]
    
    numeric_columns = []
    for col in df.columns:
        if any(keyword in col for keyword in ['Cours', 'Volume', 'Variation']):
            numeric_columns.append(col)
    
    for col in numeric_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.')
            df[col] = df[col].str.replace(' ', '')
            if 'Variation' in col:
                df[col] = df[col].str.replace('%', '')
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    if 'Symbole' in df.columns:
        df = df.sort_values('Symbole').reset_index(drop=True)
    
    return df

def display_brvm_data():
    """Afficher les données BRVM avec analyse fondamentale"""
    
    st.sidebar.header("⚙️ Paramètres")
    
    if st.sidebar.button("🔄 Actualiser les données"):
        st.cache_data.clear()
        st.rerun()
    
    with st.spinner("Récupération des données BRVM..."):
        df = scrape_brvm_data()
    
    if df is not None:
        st.subheader("📈 Statistiques du marché")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Nombre de titres", len(df))
        
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
        
        st.subheader("📋 Cours des Actions")
        
        def color_variation(val):
            if isinstance(val, (int, float)):
                if val > 0:
                    return 'color: green; font-weight: bold'
                elif val < 0:
                    return 'color: red; font-weight: bold'
            return ''
        
        if 'Variation (%)' in df.columns:
            styled_df = df.style.map(color_variation, subset=['Variation (%)'])
            st.dataframe(styled_df, use_container_width=True, height=400)
        else:
            st.dataframe(df, use_container_width=True, height=400)
        
        # Section Analyse Fondamentale
        st.markdown("---")
        st.subheader("📊 Analyse Fondamentale par Titre")
        
        if 'Symbole' in df.columns:
            symboles_list = [''] + df['Symbole'].dropna().unique().tolist()
            symbole_selected = st.selectbox("Sélectionnez un titre pour voir son analyse fondamentale", symboles_list)
            
            if symbole_selected:
                # Charger les données depuis Supabase
                financial_data = init_storage()
                
                financial_records = []
                for key, data in financial_data.items():
                    if isinstance(data, dict) and data.get('symbole') == symbole_selected:
                        financial_records.append(data)
                
                if financial_records:
                    # Trier par année
                    financial_records = sorted(financial_records, key=lambda x: x.get('annee', 0), reverse=True)
                    
                    st.success(f"✅ {len(financial_records)} année(s) de données disponibles pour {symbole_selected}")
                    
                    # Afficher chaque année
                    for record in financial_records:
                        annee = record.get('annee', 'N/A')
                        
                        with st.expander(f"📅 Année {annee} - Dernière MAJ: {record.get('last_update', 'N/A')[:19] if record.get('last_update') else 'N/A'}"):
                            
                            tab_a, tab_b, tab_c, tab_d = st.tabs(["Bilan", "Compte de Résultat", "Flux de Trésorerie", "Ratios"])
                            
                            with tab_a:
                                bilan = record.get('bilan', {})
                                if bilan:
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        st.markdown("**ACTIF**")
                                        st.write(f"Actif Immobilisé: {bilan.get('actif_immobilise', 0):,.0f} FCFA")
                                        st.write(f"Actif Courant: {bilan.get('actif_courant', 0):,.0f} FCFA")
                                        st.write(f"Stocks: {bilan.get('stocks', 0):,.0f} FCFA")
                                        st.write(f"Créances: {bilan.get('creances', 0):,.0f} FCFA")
                                        st.write(f"Trésorerie: {bilan.get('tresorerie', 0):,.0f} FCFA")
                                        st.metric("**Total Actif**", f"{bilan.get('actif_total', 0):,.0f} FCFA")
                                    
                                    with col2:
                                        st.markdown("**PASSIF**")
                                        st.write(f"Capitaux Propres: {bilan.get('capitaux_propres', 0):,.0f} FCFA")
                                        st.write(f"Dettes Long Terme: {bilan.get('dettes_long_terme', 0):,.0f} FCFA")
                                        st.write(f"Passif Courant: {bilan.get('passif_courant', 0):,.0f} FCFA")
                                        st.metric("**Total Passif**", f"{bilan.get('passif_total', 0):,.0f} FCFA")
                                else:
                                    st.info("Aucune donnée de bilan")
                            
                            with tab_b:
                                cr = record.get('compte_resultat', {})
                                if cr:
                                    st.write(f"Chiffre d'Affaires: **{cr.get('chiffre_affaires', 0):,.0f} FCFA**")
                                    st.write(f"Charges d'Exploitation: {cr.get('charges_exploitation', 0):,.0f} FCFA")
                                    st.write(f"Résultat d'Exploitation: {cr.get('resultat_exploitation', 0):,.0f} FCFA")
                                    st.write(f"Charges Financières: {cr.get('charges_financieres', 0):,.0f} FCFA")
                                    st.write(f"Produits Financiers: {cr.get('produits_financiers', 0):,.0f} FCFA")
                                    st.write(f"Impôts: {cr.get('impots', 0):,.0f} FCFA")
                                    st.metric("**Résultat Net**", f"{cr.get('resultat_net', 0):,.0f} FCFA")
                                    if cr.get('benefice_par_action', 0) > 0:
                                        st.metric("BPA", f"{cr.get('benefice_par_action', 0):,.2f} FCFA")
                                else:
                                    st.info("Aucune donnée de compte de résultat")
                            
                            with tab_c:
                                ft = record.get('flux_tresorerie', {})
                                if ft:
                                    st.write(f"Flux d'Exploitation: {ft.get('flux_exploitation', 0):,.0f} FCFA")
                                    st.write(f"Flux d'Investissement: {ft.get('flux_investissement', 0):,.0f} FCFA")
                                    st.write(f"Flux de Financement: {ft.get('flux_financement', 0):,.0f} FCFA")
                                    st.metric("**Variation Trésorerie**", f"{ft.get('variation_tresorerie', 0):,.0f} FCFA")
                                else:
                                    st.info("Aucune donnée de flux de trésorerie")
                            
                            with tab_d:
                                ratios = record.get('ratios', {})
                                if ratios:
                                    col1, col2, col3 = st.columns(3)
                                    
                                    with col1:
                                        st.markdown("**Rentabilité**")
                                        if 'marge_nette' in ratios:
                                            st.metric("Marge Nette", f"{ratios['marge_nette']:.2f}%")
                                        if 'roe' in ratios:
                                            st.metric("ROE", f"{ratios['roe']:.2f}%")
                                        if 'roa' in ratios:
                                            st.metric("ROA", f"{ratios['roa']:.2f}%")
                                    
                                    with col2:
                                        st.markdown("**Liquidité**")
                                        if 'ratio_liquidite_generale' in ratios:
                                            st.metric("Liquidité Générale", f"{ratios['ratio_liquidite_generale']:.2f}")
                                        if 'ratio_endettement' in ratios:
                                            st.metric("Endettement", f"{ratios['ratio_endettement']:.2f}%")
                                    
                                    with col3:
                                        st.markdown("**Marché**")
                                        if 'per' in ratios:
                                            st.metric("PER", f"{ratios['per']:.2f}")
                                        if 'price_to_book' in ratios:
                                            st.metric("P/B", f"{ratios['price_to_book']:.2f}")
                                else:
                                    st.info("Aucun ratio calculé")
                else:
                    st.warning(f"⚠️ Aucune donnée financière disponible pour {symbole_selected}")
                    st.info("💡 Le développeur doit ajouter les données via la section développeur")
        
        # Export CSV
        st.markdown("---")
        st.subheader("💾 Export des données")
        csv = df.to_csv(index=False, sep=';', decimal=',')
        st.download_button(
            label="📥 Télécharger les cours en CSV",
            data=csv,
            file_name="brvm_cours.csv",
            mime="text/csv"
        )
    
    else:
        st.warning("⚠️ Impossible de récupérer les données BRVM")
        st.info("Vérifiez votre connexion internet ou réessayez plus tard")

# ===========================
# INTERFACE PRINCIPALE
# ===========================

def main():
    st.title("📊 Analyse des titres BRVM avec Stockage Cloud")
    
    # Menu de navigation
    page = st.sidebar.radio(
        "Navigation",
        ["🏠 Accueil & Cours", "🔐 Section Développeur", "ℹ️ À propos"]
    )
    
    if page == "🏠 Accueil & Cours":
        st.markdown("""
        ### Application d'analyse BRVM avec Stockage Cloud
        
        **Nouveau :** Toutes les données financières sont maintenant stockées dans le cloud (Supabase) et accessibles depuis n'importe où !
        
        Cette application vous permet de :
        - 📈 Consulter les cours en temps réel
        - 📊 Analyser les données fondamentales des sociétés cotées
        - 💾 Stocker et partager les analyses financières
        - 💹 Suivre les variations et performances
        """)
        
        # Afficher les statistiques du cloud
        financial_data = init_storage()
        if financial_data:
            st.sidebar.info(f"📦 {len(financial_data)} analyses stockées dans le cloud")
        
        display_brvm_data()
        
        st.markdown("---")
        st.caption("Source : BRVM - https://www.brvm.org | Données stockées dans Supabase | " + datetime.now().strftime("%d/%m/%Y %H:%M"))
    
    elif page == "🔐 Section Développeur":
        developer_section()
    
    elif page == "ℹ️ À propos":
        st.header("À propos de cette application")
        st.markdown("""
        ### Fonctionnalités principales
        
        1. **Scraping des données BRVM** : Récupération automatique des cours
        2. **Analyse fondamentale** : Calcul des ratios financiers
        3. **Stockage cloud** : Persistance des données via Supabase
        4. **Interface développeur** : Gestion des données financières
        
        ### Configuration technique
        
        - **Framework** : Streamlit
        - **Base de données** : Supabase (PostgreSQL)
        - **Stockage** : 500 Mo gratuit
        - **Déploiement** : Streamlit Cloud / GitHub
        
        ### Instructions de déploiement
        
        1. Créez un fichier `requirements.txt` :
        ```
        streamlit
        pandas
        requests
        beautifulsoup4
        supabase
        ```
        
        2. Déployez sur Streamlit Cloud en connectant votre GitHub
        3. Ajoutez vos secrets Supabase dans les paramètres
        """)

if __name__ == "__main__":
    main()
