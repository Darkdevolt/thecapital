"""
Configuration centralisée pour l'application Analyse BRVM Pro
"""
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class SupabaseConfig:
    """Configuration Supabase"""
    url: str
    key: str
    
    @classmethod
    def from_env(cls):
        """Charger la configuration depuis les variables d'environnement ou secrets Streamlit"""
        try:
            import streamlit as st
            # Essayer de charger depuis les secrets Streamlit
            url = st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL", ""))
            key = st.secrets.get("SUPABASE_KEY", os.getenv("SUPABASE_KEY", ""))
        except:
            # Fallback sur les variables d'environnement
            url = os.getenv("SUPABASE_URL", "")
            key = os.getenv("SUPABASE_KEY", "")
        
        return cls(url=url, key=key)

@dataclass
class AppConfig:
    """Configuration générale de l'application"""
    # Informations de l'application
    APP_TITLE: str = "Analyse BRVM Pro"
    APP_VERSION: str = "1.0.0"
    PAGE_ICON: str = "📊"
    LAYOUT: str = "wide"
    
    # Mot de passe développeur
    DEVELOPER_PASSWORD: str = "dev_brvm_2024"
    
    # URL de scraping
    SCRAPING_URL: str = "https://www.sikafinance.com/marches/aaz"
    SCRAPING_TIMEOUT: int = 15
    
    # Cache TTL (Time To Live) en secondes
    CACHE_TTL: int = 300  # 5 minutes
    
    # Projections financières
    DEFAULT_PROJECTION_YEARS: int = 3
    PROJECTION_TCAM_WEIGHT: float = 0.4
    PROJECTION_REGRESSION_WEIGHT: float = 0.6
    
    # Limites pour les ratios
    MAX_PER: float = 100
    MAX_PRICE_TO_BOOK: float = 20
    MAX_EV_EBITDA: float = 50
    MAX_EV_SALES: float = 10
    
    # Seuils de recommandation
    RECOMMENDATION_STRONG_BUY: float = 20.0  # > 20%
    RECOMMENDATION_BUY: float = 10.0         # > 10%
    RECOMMENDATION_HOLD_MIN: float = -10.0   # > -10%
    RECOMMENDATION_SELL: float = -20.0       # > -20%
    
    # Tables Supabase
    TABLE_FINANCIAL_DATA: str = "financial_data"
    TABLE_SYMBOL_MAPPING: str = "symbol_mapping"
    
    @classmethod
    def load(cls):
        """Charger la configuration"""
        return cls()

@dataclass
class RecommendationThresholds:
    """Seuils pour les recommandations d'investissement"""
    strong_buy: float = 20.0
    buy: float = 10.0
    hold_min: float = -10.0
    sell: float = -20.0
    
    def get_recommendation(self, potential: float) -> tuple[str, str]:
        """
        Obtenir la recommandation et la justification basées sur le potentiel
        
        Args:
            potential: Potentiel de hausse/baisse en %
            
        Returns:
            tuple (recommandation, justification)
        """
        if potential > self.strong_buy:
            return "ACHAT FORT", f"Sous-évalué de {potential:.1f}% par rapport aux pairs"
        elif potential > self.buy:
            return "ACHAT", f"Potentiel de hausse de {potential:.1f}%"
        elif potential > self.hold_min:
            return "CONSERVER", "Valorisation proche de la juste valeur"
        elif potential > self.sell:
            return "VENTE", f"Surévalué de {abs(potential):.1f}%"
        else:
            return "VENTE FORTE", f"Fortement surévalué de {abs(potential):.1f}%"

@dataclass
class DisplayConfig:
    """Configuration de l'affichage"""
    # Émojis pour la navigation
    HOME_ICON: str = "🏠"
    COURSE_ICON: str = "📈"
    ANALYSIS_ICON: str = "🔍"
    DEV_ICON: str = "⚙️"
    
    # Couleurs (pour les styles CSS personnalisés)
    PRIMARY_COLOR: str = "#1e3c72"
    SECONDARY_COLOR: str = "#2a5298"
    SUCCESS_COLOR: str = "#28a745"
    WARNING_COLOR: str = "#ffc107"
    DANGER_COLOR: str = "#dc3545"
    
    # Format de dates
    DATE_FORMAT: str = "%d/%m/%Y"
    DATETIME_FORMAT: str = "%d/%m/%Y %H:%M"
    
    # Formats numériques
    CURRENCY_FORMAT: str = "{:,.0f}"
    PERCENTAGE_FORMAT: str = "{:.2f}%"
    RATIO_FORMAT: str = "{:.2f}"

# Instances globales de configuration
app_config = AppConfig.load()
supabase_config = SupabaseConfig.from_env()
recommendation_thresholds = RecommendationThresholds()
display_config = DisplayConfig()

# Export des configurations
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
