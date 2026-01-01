# app.py - Nouveau point d'entrée principal
import streamlit as st
from datetime import datetime

# Import des modules
from components.navigation import render_navigation
from pages.accueil import page_accueil
from pages.cours import page_cours
from pages.analyse import page_analyse
from pages.developpeur import page_developpeur

# Configuration de la page
st.set_page_config(
    page_title="Analyse BRVM Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialiser la session state
if 'page' not in st.session_state:
    st.session_state.page = 'accueil'

# Interface principale
def main():
    # Barre de navigation
    render_navigation()
    
    # Router vers la page appropriée
    if st.session_state.page == 'accueil':
        page_accueil()
    elif st.session_state.page == 'cours':
        page_cours()
    elif st.session_state.page == 'analyse':
        page_analyse()
    elif st.session_state.page == 'dev':
        page_developpeur()
    
    # Pied de page
    st.markdown("---")
    st.caption(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')} | Analyse BRVM Pro v1.0")

if __name__ == "__main__":
    main()
