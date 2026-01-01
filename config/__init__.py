"""
Module de configuration pour Analyse BRVM Pro

Ce module centralise toute la configuration de l'application :
- Configuration Supabase
- Configuration de l'application
- Seuils de recommandation
- Configuration de l'affichage
"""

from .settings import (
    AppConfig,
    SupabaseConfig,
    RecommendationThresholds,
    DisplayConfig,
    app_config,
    supabase_config,
    recommendation_thresholds,
    display_config
)

__all__ = [
    'AppConfig',
    'SupabaseConfig',
    'RecommendationThresholds',
    'DisplayConfig',
    'app_config',
    'supabase_config',
    'recommendation_thresholds',
    'display_config'
]
