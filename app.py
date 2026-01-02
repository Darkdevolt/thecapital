# app.py - Point d'entrée principal
import streamlit as st
from datetime import datetime

# Configuration de la page AVANT tout import
st.set_page_config(
    page_title="Analyse BRVM Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Imports des modules APRÈS la configuration
from components.navigation import render_navigation

# Initialiser la session state
if 'page' not in st.session_state:
    st.session_state.page = 'accueil'

# Interface principale
def main():
    # Barre de navigation
    render_navigation()
    
    # Import dynamique des pages pour éviter les problèmes de chargement
    if st.session_state.page == 'accueil':
        from pages.accueil import page_accueil
        page_accueil()
    elif st.session_state.page == 'cours':
        from pages.cours import page_cours
        page_cours()
    elif st.session_state.page == 'analyse':
        from pages.analyse import page_analyse
        page_analyse()
    elif st.session_state.page == 'dev':
        from pages.developpeur import page_developpeur
        page_developpeur()
    
    # Pied de page
    st.markdown("---")
    st.caption(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')} | Analyse BRVM Pro v1.0")

if __name__ == "__main__":
    main()
