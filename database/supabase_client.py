# database/supabase_client.py
import streamlit as st
from supabase import create_client
from config.settings import SUPABASE_URL, SUPABASE_KEY

def init_supabase():
    """Initialiser la connexion à Supabase"""
    if 'supabase' not in st.session_state:
        try:
            st.session_state.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            # Test de connexion
            test_response = st.session_state.supabase.table("financial_data").select("*", count="exact").limit(1).execute()
            return st.session_state.supabase
        except Exception as e:
            st.error(f"Erreur de connexion Supabase: {str(e)}")
            return None
    return st.session_state.supabase
