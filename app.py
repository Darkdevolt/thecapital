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

# ===========================
# CONFIGURATION
# ===========================

# Configuration Streamlit
st.set_page_config(page_title="Analyse BRVM", layout="wide")

# Mot de passe développeur
DEVELOPER_PASSWORD = "dev_brvm_2024"

# Configuration Supabase
SUPABASE_URL = "https://otsiwiwlnowxeolbbgvm.supabase.co"
SUPABASE_KEY = "sb_publishable_MhaI5b-kMmb5liIMOJ4P3Q_xGTsJAFJ"

# Configuration des secteurs Rich Bourse
SECTEURS_RICHBOURSE = {
    'Consommation discrétionnaire': 'https://www.richbourse.com/common/variation/index/veille/hausse_baisse/consommation-discretionnaire',
    'Consommation de base': 'https://www.richbourse.com/common/variation/index/veille/hausse_baisse/consommation-de-base',
    'Énergie': 'https://www.richbourse.com/common/variation/index/veille/hausse_baisse/energie',
    'Industriels': 'https://www.richbourse.com/common/variation/index/veille/hausse_baisse/industriels',
    'Services financiers': 'https://www.richbourse.com/common/variation/index/veille/hausse_baisse/services-financiers',
    'Services publics': 'https://www.richbourse.com/common/variation/index/veille/hausse_baisse/services-publics'
}

# ===========================
# INITIALISATION SUPABASE
# ===========================

def init_supabase():
    """Initialiser la connexion à Supabase"""
    if 'supabase' not in st.session_state:
        try:
            st.session_state.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            # Test de connexion
            test_response = st.session_state.supabase.table("financial_data").select("*", count="exact").limit(1).execute()
            if not hasattr(st, '_supabase_success_shown'):
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

# ===========================
# FONCTIONS DE GESTION SUPABASE
# ===========================

def load_symbol_mapping():
    """Charger le mapping des symboles depuis Supabase"""
    supabase = init_supabase()
    if not supabase:
        return {}
    
    try:
        response = supabase.table("symbol_mapping").select("*").execute()
        mapping = {}
        for record in response.data:
            mapping[record['symbole']] = {
                'nom': record.get('nom_complet', record['symbole']),
                'secteur': record.get('secteur', 'Non classifié')
            }
        return mapping
    except Exception as e:
        st.error(f"Erreur de chargement du mapping: {str(e)}")
        return {}

def save_symbol_mapping(symbole, nom_complet, secteur=None):
    """Sauvegarder un mapping dans Supabase"""
    supabase = init_supabase()
    if not supabase:
        return False
    
    try:
        record = {
            'symbole': symbole,
            'nom_complet': nom_complet,
            'secteur': secteur if secteur else 'Non classifié',
            'last_update': datetime.now().isoformat()
        }
        
        # Vérifier si l'entrée existe déjà
        existing = supabase.table("symbol_mapping")\
            .select("*")\
            .eq("symbole", symbole)\
            .execute()
        
        if existing.data:
            # Mise à jour
            response = supabase.table("symbol_mapping")\
                .update(record)\
                .eq("symbole", symbole)\
                .execute()
        else:
            # Insertion
            response = supabase.table("symbol_mapping").insert(record).execute()
        
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
        response = supabase.table("symbol_mapping")\
            .delete()\
            .eq("symbole", symbole)\
            .execute()
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

# ===========================
# FONCTIONS DE SCRAPING DES SECTEURS RICHBOURSE
# ===========================

@st.cache_data(ttl=3600)
def scrape_secteur_richbourse(url_secteur, nom_secteur):
    """
    Scrape les symboles et noms d'actions d'un secteur depuis Rich Bourse
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        response = requests.get(url_secteur, headers=headers, verify=False, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Trouver le tableau principal des actions
        table = soup.find('table')
        if not table:
            return []
        
        actions = []
        tbody = table.find('tbody')
        
        if tbody:
            for row in tbody.find_all('tr'):
                cols = row.find_all('td')
                
                if len(cols) >= 3:
                    symbole = cols[0].get_text(strip=True)
                    nom_complet = cols[1].get_text(strip=True)
                    
                    if symbole and nom_complet and symbole != 'TOTAL':
                        actions.append({
                            'symbole': symbole,
                            'nom': nom_complet,
                            'secteur': nom_secteur
                        })
        
        return actions
    
    except Exception as e:
        st.error(f"Erreur scraping secteur {nom_secteur}: {str(e)}")
        return []

@st.cache_data(ttl=3600)
def scrape_tous_secteurs_richbourse():
    """Scrape tous les secteurs Rich Bourse"""
    mapping_secteurs = {}
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_secteurs = len(SECTEURS_RICHBOURSE)
    
    for idx, (nom_secteur, url) in enumerate(SECTEURS_RICHBOURSE.items()):
        status_text.text(f"Scraping du secteur: {nom_secteur}...")
        
        actions = scrape_secteur_richbourse(url, nom_secteur)
        
        for action in actions:
            mapping_secteurs[action['symbole']] = {
                'nom': action['nom'],
                'secteur': action['secteur']
            }
        
        progress_bar.progress((idx + 1) / total_secteurs)
    
    progress_bar.empty()
    status_text.empty()
    
    return mapping_secteurs

def get_secteur_by_symbole(symbole, mapping_secteurs):
    """Retourne le secteur d'un symbole donné"""
    if symbole in mapping_secteurs:
        return mapping_secteurs[symbole]['secteur']
    return "Non classifié"

def get_nom_by_symbole(symbole, mapping_secteurs):
    """Retourne le nom complet d'un symbole donné"""
    if symbole in mapping_secteurs:
        return mapping_secteurs[symbole]['nom']
    return symbole

def save_secteur_mapping(symbole, nom, secteur):
    """Sauvegarder le mapping secteur dans Supabase"""
    return save_symbol_mapping(symbole, nom, secteur)

def save_all_secteurs_to_supabase(mapping_secteurs):
    """Sauvegarder tous les secteurs scrapés dans Supabase"""
    supabase = init_supabase()
    if not supabase:
        return 0, len(mapping_secteurs)
    
    success_count = 0
    error_count = 0
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total = len(mapping_secteurs)
    
    for idx, (symbole, info) in enumerate(mapping_secteurs.items()):
        status_text.text(f"Sauvegarde: {symbole} - {info['nom']}...")
        
        if save_secteur_mapping(symbole, info['nom'], info['secteur']):
            success_count += 1
        else:
            error_count += 1
        
        progress_bar.progress((idx + 1) / total)
    
    progress_bar.empty()
    status_text.empty()
    
    return success_count, error_count

def load_secteurs_from_supabase():
    """Charger les secteurs depuis Supabase"""
    return load_symbol_mapping()

def get_actions_by_secteur(secteur, financial_data, mapping_secteurs):
    """Retourne toutes les actions d'un secteur donné"""
    actions_secteur = []
    
    for symbole, info in mapping_secteurs.items():
        if info.get('secteur') == secteur:
            actions_secteur.append(symbole)
    
    return actions_secteur

def get_stats_secteurs(financial_data, mapping_secteurs):
    """Calcule les statistiques par secteur"""
    stats = {}
    
    for symbole, info in mapping_secteurs.items():
        secteur = info.get('secteur', 'Non classifié')
        
        if secteur not in stats:
            stats[secteur] = {
                'nb_entreprises': 0,
                'entreprises': []
            }
        
        stats[secteur]['nb_entreprises'] += 1
        stats[secteur]['entreprises'].append(symbole)
    
    # Convertir en DataFrame
    df_stats = pd.DataFrame([
        {
            'Secteur': secteur,
            'Nombre d\'entreprises': data['nb_entreprises'],
            'Entreprises': ', '.join(data['entreprises'][:5]) + ('...' if len(data['entreprises']) > 5 else '')
        }
        for secteur, data in stats.items()
    ])
    
    return df_stats.sort_values('Nombre d\'entreprises', ascending=False)

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
        btn_analyse = st.button("🔍 Analyse", use_container_width=True,
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

# ===========================
# PAGES DE L'APPLICATION
# ===========================
def page_accueil():
    st.title("🏠 Accueil - Analyse BRVM Pro")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### Bienvenue sur Analyse BRVM Pro
        
        **Votre outil d'analyse fondamentale pour la Bourse Régionale des Valeurs Mobilières**
        
        #### Fonctionnalités :
        - **📈 Cours en direct** : Données de marché depuis Sika Finance
        - **🔍 Analyse fondamentale** : Ratios financiers et valorisation
        - **📊 Projections** : Scénarios futurs basés sur l'historique
        - **⚖️ Comparaisons sectorielles** : Multiples de valorisation
        - **🏭 Classification sectorielle** : Import automatique depuis Rich Bourse
        """)
    
    with col2:
        st.markdown("""
        ### Comment utiliser ?
        
        1. **⚙️ Développeur** : Configurez les entreprises et les données
        2. **🔍 Analyse** : Sélectionnez un titre pour analyse détaillée
        3. **📈 Cours** : Suivez les cotations en temps réel
        """)
        st.info("💡 **Conseil** : Commencez par configurer vos entreprises dans la section Développeur")
    
    st.markdown("---")
    st.subheader("📊 Statistiques")
    
    financial_data = init_storage()
    if financial_data:
        entreprises = set([data['symbole'] for data in financial_data.values() if isinstance(data, dict)])
        total_donnees = len(financial_data)
        
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        
        with col_stat1:
            st.metric("Entreprises", len(entreprises))
        
        with col_stat2:
            st.metric("Données financières", total_donnees)
        
        with col_stat3:
            if 'symbol_mapping' in st.session_state:
                st.metric("Noms configurés", len(st.session_state.symbol_mapping))
        
        with col_stat4:
            if 'symbol_mapping' in st.session_state:
                secteurs = set([info.get('secteur', 'Non classifié') for info in st.session_state.symbol_mapping.values()])
                st.metric("Secteurs", len(secteurs))
    else:
        st.info("Aucune donnée financière disponible. Rendez-vous dans la section Développeur pour configurer.")

def page_cours():
    st.title("📈 Cours des Actions BRVM")
    
    # Scraper et afficher les données
    with st.spinner("Chargement des données de la BRVM..."):
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
                    st.metric("Dernière mise à jour", datetime.now().strftime('%d/%m/%Y'))
                with col3:
                    st.metric("Source", "Sikafinance")
                
                st.markdown("---")
                
                # Filtre de recherche
                search = st.text_input("🔍 Rechercher une action", placeholder="Entrez le nom ou le symbole...")
                
                if search:
                    mask = df_actions.astype(str).apply(lambda x: x.str.contains(search, case=False, na=False)).any(axis=1)
                    filtered_df = df_actions[mask]
                    st.info(f"🔎 {len(filtered_df)} résultat(s) trouvé(s)")
                else:
                    filtered_df = df_actions
                
                # Afficher le tableau des actions
                st.dataframe(
                    filtered_df,
                    use_container_width=True,
                    height=500,
                    hide_index=True
                )
                
                # Bouton de téléchargement
                csv_actions = filtered_df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 Télécharger les actions en CSV",
                    data=csv_actions,
                    file_name=f"brvm_actions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("⚠️ Aucune donnée d'action disponible")
        
        with tab2:
            if df_indices is not None and not df_indices.empty:
                st.subheader("Indices du marché BRVM")
                
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
                    label="📥 Télécharger les indices en CSV",
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
    st.title("🔍 Analyse Fondamentale")
    
    financial_data = init_storage()
    
    if not financial_data:
        st.warning("Aucune donnée financière disponible.")
        st.info("Rendez-vous dans la section Développeur pour saisir des données financières.")
        return
    
    symboles = sorted(set([data['symbole'] for data in financial_data.values() if isinstance(data, dict)]))
    
    if not symboles:
        st.warning("Aucune entreprise trouvée dans les données.")
        return
    
    # Utiliser le mapping pour afficher des noms lisibles
    mapping = st.session_state.get('symbol_mapping', {})
    
    # Créer les options avec format: "SNTS - Sonatel S.A. [Services publics]"
    options = []
    for symbole in symboles:
        if symbole in mapping:
            nom = mapping[symbole].get('nom', symbole)
            secteur = mapping[symbole].get('secteur', 'Non classifié')
            options.append(f"{symbole} - {nom} [{secteur}]")
        else:
            options.append(f"{symbole}")
    
    # Sélection de l'entreprise
    selected_option = st.selectbox("Choisissez une entreprise", [''] + options)
    
    if selected_option:
        # Extraire le symbole de l'option sélectionnée
        symbole_selected = selected_option.split(" - ")[0].split(" [")[0]
        
        # Récupérer les données de cette entreprise
        symbole_data = {}
        for key, data in financial_data.items():
            if data.get('symbole') == symbole_selected:
                symbole_data[data['annee']] = data
        
        if symbole_data:
            # Afficher le nom complet et secteur si disponible
            if symbole_selected in mapping:
                nom_complet = mapping[symbole_selected].get('nom', symbole_selected)
                secteur = mapping[symbole_selected].get('secteur', 'Non classifié')
                st.success(f"📊 {nom_complet} | 🏭 Secteur: {secteur}")
            else:
                st.success(f"📊 Données disponibles pour {symbole_selected}")
            
            # Sélection de l'année
            annees = sorted(symbole_data.keys())
            annee_selectionnee = st.selectbox("Sélectionnez l'année", annees, index=len(annees)-1)
            
            if annee_selectionnee:
                data = symbole_data[annee_selectionnee]
                
                # Onglets pour l'analyse
                tab1, tab2, tab3, tab4 = st.tabs(["📋 Ratios Financiers", "💰 Valorisation", "📈 Projections", "📊 Données Brutes"])
                
                with tab1:
                    st.subheader(f"Ratios Financiers - {annee_selectionnee}")
                    
                    if 'ratios' in data:
                        ratios = data['ratios']
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.markdown("**📊 Rentabilité**")
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
                    st.subheader("Valorisation par Multiples")
                    
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
                        st.markdown("### Multiples Sectoriels (Médiane)")
                        medianes = valorisations['medianes_secteur']
                        
                        if medianes:
                            df_medianes = pd.DataFrame(list(medianes.items()), columns=['Multiple', 'Valeur'])
                            st.dataframe(df_medianes, use_container_width=True)
                
                with tab3:
                    st.subheader("Projections Financières")
                    
                    projections = calculate_financial_projections(symbole_selected, financial_data)
                    
                    if 'projections' in projections:
                        st.markdown(f"**Méthode :** {projections.get('methode', '')}")
                        st.markdown(f"**TCAM du CA :** {projections.get('tcam_ca', 0):.2f}%")
                        st.markdown(f"**TCAM du Résultat Net :** {projections.get('tcam_rn', 0):.2f}%")
                        
                        df_proj = pd.DataFrame(projections['projections'])
                        st.dataframe(df_proj.style.format({
                            'ca_projete': '{:,.0f}',
                            'rn_projete': '{:,.0f}',
                            'marge_nette_projetee': '{:.2f}%'
                        }), use_container_width=True)
                    elif 'erreur' in projections:
                        st.warning(projections['erreur'])
                
                with tab4:
                    st.subheader("Données Brutes")
                    
                    col_brut1, col_brut2 = st.columns(2)
                    
                    with col_brut1:
                        if data.get('bilan'):
                            st.markdown("**Bilan**")
                            df_bilan = pd.DataFrame(list(data['bilan'].items()), columns=['Poste', 'Valeur'])
                            st.dataframe(df_bilan, use_container_width=True)
                    
                    with col_brut2:
                        if data.get('compte_resultat'):
                            st.markdown("**Compte de résultat**")
                            df_cr = pd.DataFrame(list(data['compte_resultat'].items()), columns=['Poste', 'Valeur'])
                            st.dataframe(df_cr, use_container_width=True)

def developer_section():
    """Section réservée au développeur pour gérer les données"""
    st.title("⚙️ Section Développeur")
    
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
    
    st.success("✅ Connecté en tant que développeur")
    
    # Onglets développeur
    tab1, tab2, tab3 = st.tabs([
        "📊 Données Financières",
        "🔤 Noms et Secteurs",
        "⚙️ Paramètres"
    ])
    
    with tab1:
        st.header("Gestion des Données Financières")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Ajouter/Modifier des données")
            symbole = st.text_input("Symbole BRVM (ex: SNTS)", key="dev_symbole")
            annee = st.number_input("Année", min_value=2000, max_value=2030, value=2023, key="dev_annee")
            
            with st.expander("Bilan"):
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
            
            with st.expander("Compte de Résultat"):
                chiffre_affaires = st.number_input("Chiffre d'Affaires", value=0.0, key="cr_chiffre_affaires")
                resultat_exploitation = st.number_input("Résultat Exploitation", value=0.0, key="cr_resultat_exploitation")
                resultat_net = st.number_input("Résultat Net", value=0.0, key="cr_resultat_net")
                charges_financieres = st.number_input("Charges Financières", value=0.0, key="cr_charges_financieres")
                benefice_par_action = st.number_input("Bénéfice par Action", value=0.0, key="cr_benefice_par_action")
            
            with st.expander("Flux de Trésorerie"):
                flux_exploitation = st.number_input("Flux d'Exploitation", value=0.0, key="ft_flux_exploitation")
                flux_investissement = st.number_input("Flux d'Investissement", value=0.0, key="ft_flux_investissement")
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
                        data_dict['bilan'],
                        data_dict['compte_resultat'],
                        data_dict['flux_tresorerie']
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
            st.subheader("Supprimer des données")
            
            financial_data = init_storage()
            if financial_data:
                options = []
                for key, data in financial_data.items():
                    if isinstance(data, dict):
                        symbole_item = data.get('symbole', '')
                        annee_item = data.get('annee', '')
                        mapping = st.session_state.get('symbol_mapping', {})
                        if symbole_item in mapping:
                            nom_complet = mapping[symbole_item].get('nom', symbole_item)
                        else:
                            nom_complet = symbole_item
                        options.append(f"{symbole_item} - {nom_complet} ({annee_item})")
                
                if options:
                    selected = st.selectbox("Sélectionnez les données à supprimer", options)
                    
                    if selected and st.button("🗑️ Supprimer", type="secondary", use_container_width=True):
                        # Extraire symbole et année
                        parts = selected.split(" (")
                        symbole_del = parts[0].split(" - ")[0]
                        annee_del = parts[1].replace(")", "")
                        
                        if delete_financial_data(symbole_del, int(annee_del)):
                            st.success(f"✅ Données supprimées pour {symbole_del} - {annee_del}")
                            st.session_state.financial_data = load_all_financial_data()
                            st.rerun()
                        else:
                            st.error("❌ Erreur lors de la suppression")
                else:
                    st.info("📭 Aucune donnée à supprimer")
    
    with tab2:
        st.header("Noms et Secteurs des Entreprises")
        
        # Sous-onglets pour séparer scraping et gestion manuelle
        subtab1, subtab2, subtab3 = st.tabs([
            "🔄 Import Automatique (Rich Bourse)", 
            "✏️ Gestion Manuelle",
            "📊 Vue d'ensemble"
        ])
        
        # ============= SOUS-ONGLET 1: IMPORT AUTOMATIQUE =============
        with subtab1:
            st.subheader("Import automatique depuis Rich Bourse")
            
            st.info("""
            🎯 **Fonctionnalité automatique** : Récupère automatiquement les noms complets et les secteurs 
            de toutes les entreprises BRVM depuis le site Rich Bourse.
            
            **Avantages** :
            - ✅ Import en masse de tous les secteurs
            - ✅ Données officielles et à jour
            - ✅ Noms complets automatiques
            - ✅ Classification sectorielle précise
            """)
            
            col_scrape1, col_scrape2 = st.columns(2)
            
            with col_scrape1:
                if st.button("🔄 Scanner Rich Bourse", type="primary", use_container_width=True):
                    with st.spinner("Scraping en cours..."):
                        mapping_secteurs = scrape_tous_secteurs_richbourse()
                        
                        if mapping_secteurs:
                            st.session_state['mapping_secteurs_temp'] = mapping_secteurs
                            st.success(f"✅ {len(mapping_secteurs)} entreprises trouvées!")
                            
                            # Afficher un aperçu
                            st.markdown("### 📋 Aperçu des données récupérées")
                            df_preview = pd.DataFrame([
                                {
                                    'Symbole': symbole,
                                    'Nom complet': info['nom'],
                                    'Secteur': info['secteur']
                                }
                                for symbole, info in list(mapping_secteurs.items())[:10]
                            ])
                            st.dataframe(df_preview, use_container_width=True)
                            
                            if len(mapping_secteurs) > 10:
                                st.caption(f"... et {len(mapping_secteurs) - 10} autres entreprises")
                        else:
                            st.error("❌ Aucune donnée récupérée")
            
            with col_scrape2:
                if 'mapping_secteurs_temp' in st.session_state:
                    if st.button("💾 Sauvegarder dans Supabase", type="secondary", use_container_width=True):
                        mapping = st.session_state['mapping_secteurs_temp']
                        
                        with st.spinner("Sauvegarde en cours..."):
                            success, errors = save_all_secteurs_to_supabase(mapping)
                        
                        if errors == 0:
                            st.success(f"✅ Toutes les données sauvegardées ({success} entreprises)")
                            # Recharger le mapping
                            st.session_state.symbol_mapping = load_symbol_mapping()
                            del st.session_state['mapping_secteurs_temp']
                            st.rerun()
                        else:
                            st.warning(f"⚠️ {success} réussies, {errors} erreurs")
            
            # Statistiques par secteur
            if 'mapping_secteurs_temp' in st.session_state:
                st.markdown("---")
                st.subheader("📊 Répartition par secteur")
                
                mapping = st.session_state['mapping_secteurs_temp']
                secteurs_count = {}
                
                for info in mapping.values():
                    secteur = info['secteur']
                    secteurs_count[secteur] = secteurs_count.get(secteur, 0) + 1
                
                df_secteurs = pd.DataFrame([
                    {'Secteur': k, 'Nombre d\'entreprises': v}
                    for k, v in secteurs_count.items()
                ]).sort_values
