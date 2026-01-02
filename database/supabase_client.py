# database/supabase_client.py - MODE LOCAL
import streamlit as st
from config.settings import SUPABASE_URL, SUPABASE_KEY

def init_supabase():
    """Version locale sans Supabase"""
    
    # Mode local - utilise session_state pour stocker les données
    if 'local_storage' not in st.session_state:
        st.session_state.local_storage = {
            'symbol_mapping': {},
            'financial_data': {}
        }
    
    st.warning("⚠️ Mode LOCAL activé - Les données ne sont pas sauvegardées en ligne")
    st.info("Pour utiliser Supabase : créez les tables SQL et configurez les clés API")
    
    # Retourne un objet mock qui simule Supabase
    class MockSupabase:
        def __init__(self):
            self.data = st.session_state.local_storage
            
        def table(self, table_name):
            return MockTable(table_name, self.data)
    
    class MockTable:
        def __init__(self, name, data):
            self.name = name
            self.data = data
            
        def select(self, *args, **kwargs):
            return MockQuery(self.name, self.data)
    
    class MockQuery:
        def __init__(self, table_name, data):
            self.table_name = table_name
            self.data = data
            
        def execute(self):
            # Simule une réponse
            if self.table_name == 'symbol_mapping':
                return type('Response', (), {'data': [
                    {'symbole': k, 'nom_complet': v} 
                    for k, v in self.data['symbol_mapping'].items()
                ]})()
            return type('Response', (), {'data': []})()
    
    return MockSupabase()
