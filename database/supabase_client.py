"""
Client Supabase pour l'application Analyse BRVM Pro
Gère la connexion et l'initialisation de Supabase
"""
import streamlit as st
from supabase import create_client, Client
from typing import Optional
from config import supabase_config


class SupabaseClient:
    """Singleton pour gérer la connexion Supabase"""
    
    _instance: Optional[Client] = None
    _initialized: bool = False
    
    @classmethod
    def get_client(cls) -> Optional[Client]:
        """
        Obtenir l'instance du client Supabase (Singleton)
        
        Returns:
            Client Supabase ou None si erreur
        """
        if cls._instance is None:
            cls._instance = cls._initialize_client()
        return cls._instance
    
    @classmethod
    def _initialize_client(cls) -> Optional[Client]:
        """
        Initialiser la connexion à Supabase
        
        Returns:
            Client Supabase ou None si erreur
        """
        try:
            if not supabase_config.url or not supabase_config.key:
                st.error("⚠️ Configuration Supabase manquante. Vérifiez vos secrets.")
                return None
            
            client = create_client(supabase_config.url, supabase_config.key)
            
            # Test de connexion
            if not cls._initialized:
                test_response = client.table("financial_data").select("*", count="exact").limit(1).execute()
                cls._initialized = True
                
            return client
            
        except Exception as e:
            st.error(f"❌ Erreur de connexion Supabase: {str(e)}")
            return None
    
    @classmethod
    def test_connection(cls) -> bool:
        """
        Tester la connexion à Supabase
        
        Returns:
            True si la connexion fonctionne, False sinon
        """
        try:
            client = cls.get_client()
            if not client:
                return False
            
            # Test simple de lecture
            client.table("financial_data").select("*", count="exact").limit(1).execute()
            return True
            
        except Exception as e:
            st.error(f"❌ Test de connexion échoué: {str(e)}")
            return False
    
    @classmethod
    def reset_connection(cls):
        """Réinitialiser la connexion (utile pour le debugging)"""
        cls._instance = None
        cls._initialized = False


def init_supabase() -> Optional[Client]:
    """
    Fonction helper pour initialiser Supabase (compatible avec l'ancien code)
    
    Returns:
        Client Supabase ou None
    """
    if 'supabase' not in st.session_state:
        st.session_state.supabase = SupabaseClient.get_client()
    return st.session_state.supabase


# Export
__all__ = ['SupabaseClient', 'init_supabase']
