"""
Module de gestion de la base de données Supabase
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
    'init_supabase',
    'load_all_financial_data',
    'save_financial_data',
    'delete_financial_data',
    'get_financial_data_by_symbol',
    'load_symbol_mapping',
    'save_symbol_mapping',
    'delete_symbol_mapping',
    'init_storage',
    'refresh_storage'
]
