"""
Module utilitaire pour Analyse BRVM Pro

Ce module contient :
- Scraping des données BRVM
- Calculs financiers et ratios
- Fonctions helpers diverses
"""

from .scraping import scrape_brvm, format_brvm_dataframe
from .calculations import (
    calculate_enhanced_financial_ratios,
    calculate_valuation_multiples,
    calculate_financial_projections
)
from .helpers import (
    format_currency,
    format_percentage,
    format_ratio,
    format_date,
    format_datetime,
    get_symbol_display_name,
    extract_symbole_from_display,
    get_available_symbols,
    get_years_for_symbol,
    create_financial_options,
    safe_divide,
    get_financial_summary
)

__all__ = [
    # Scraping
    'scrape_brvm',
    'format_brvm_dataframe',
    
    # Calculs
    'calculate_enhanced_financial_ratios',
    'calculate_valuation_multiples',
    'calculate_financial_projections',
    
    # Helpers
    'format_currency',
    'format_percentage',
    'format_ratio',
    'format_date',
    'format_datetime',
    'get_symbol_display_name',
    'extract_symbole_from_display',
    'get_available_symbols',
    'get_years_for_symbol',
    'create_financial_options',
    'safe_divide',
    'get_financial_summary'
]
