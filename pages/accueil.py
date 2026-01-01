# pages/accueil.py
import streamlit as st
from datetime import datetime
from database.operations import init_storage

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
        
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        
        with col_stat1:
            st.metric("Entreprises", len(entreprises))
        
        with col_stat2:
            st.metric("Données financières", total_donnees)
        
        with col_stat3:
            if 'symbol_mapping' in st.session_state:
                st.metric("Noms configurés", len(st.session_state.symbol_mapping))
    else:
        st.info("Aucune donnée financière disponible. Rendez-vous dans la section Développeur pour configurer.")
