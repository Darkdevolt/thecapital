"""
Module de gestion de la base de données Supabase
Ce module gère :
- La connexion à Supabase
- Les opérations CRUD sur les données financières
- Les opérations CRUD sur les mappings symboles
- Le stockage en session_state
"""
from .supabase_client import init_supabase
from .operations import (
    load_all_financial_data,
    save_financial_data,
    delete_financial_data,
    get_financial_data_by_symbol,
    load_symbol_mapping,
    save_symbol_mapping,
    delete_symbol_mapping,
    init_storage,
    refresh_storage
)

__all__ = [
    # Client
    'init_supabase',
    
    # Données financières
    'load_all_financial_data',
    'save_financial_data',
    'delete_financial_data',
    'get_financial_data_by_symbol',
    
    # Mappings symboles
    'load_symbol_mapping',
    'save_symbol_mapping',
    'delete_symbol_mapping',
    
    # Stockage
    'init_storage',
    'refresh_storage'
]
