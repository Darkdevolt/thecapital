# components/navigation.py
import streamlit as st

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
