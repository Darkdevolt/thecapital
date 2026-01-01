"""
Module de scraping des données BRVM depuis Sikafinance
"""
import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import urllib3
from typing import Tuple, Optional
from config import app_config

# Désactiver les warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@st.cache_data(ttl=app_config.CACHE_TTL)
def scrape_brvm() -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """
    Scraper les données de cours des actions depuis Sikafinance
    
    Returns:
        Tuple (df_indices, df_actions) ou (None, None) si erreur
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        
        # Requête avec vérification SSL désactivée
        response = requests.get(
            app_config.SCRAPING_URL,
            headers=headers,
            verify=False,
            timeout=app_config.SCRAPING_TIMEOUT
        )
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Trouver toutes les tables
        tables = soup.find_all('table')
        
        if len(tables) < 2:
            return None, None
        
        # Première table : Les indices
        df_indices = _parse_table(tables[0])
        
        # Deuxième table : Les actions
        df_actions = _parse_table(tables[1])
        
        return df_indices, df_actions
    
    except requests.exceptions.Timeout:
        st.error(f"⏱️ Timeout lors du scraping (>{app_config.SCRAPING_TIMEOUT}s)")
        return None, None
    
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Erreur réseau lors du scraping: {str(e)}")
        return None, None
    
    except Exception as e:
        st.error(f"❌ Erreur lors du scraping: {str(e)}")
        return None, None


def _parse_table(table) -> Optional[pd.DataFrame]:
    """
    Parser une table HTML en DataFrame
    
    Args:
        table: Objet BeautifulSoup table
        
    Returns:
        DataFrame ou None
    """
    try:
        headers = []
        data = []
        
        # Extraire les en-têtes
        thead = table.find('thead')
        if thead:
            for th in thead.find_all('th'):
                headers.append(th.get_text(strip=True))
        else:
            # Si pas de thead, prendre la première ligne comme en-tête
            first_row = table.find('tr')
            if first_row:
                for th in first_row.find_all(['th', 'td']):
                    headers.append(th.get_text(strip=True))
        
        # Extraire les données
        tbody = table.find('tbody')
        if tbody:
            for row in tbody.find_all('tr'):
                cols = row.find_all('td')
                if cols and len(cols) > 0:
                    row_data = [col.get_text(strip=True) for col in cols]
                    data.append(row_data)
        
        # Créer le DataFrame
        if headers and data:
            return pd.DataFrame(data, columns=headers)
        
        return None
        
    except Exception as e:
        st.error(f"❌ Erreur de parsing de table: {str(e)}")
        return None


def format_brvm_dataframe(df: pd.DataFrame, df_type: str = "actions") -> pd.DataFrame:
    """
    Formater un DataFrame BRVM pour un meilleur affichage
    
    Args:
        df: DataFrame à formater
        df_type: Type de données ("actions" ou "indices")
        
    Returns:
        DataFrame formaté
    """
    if df is None or df.empty:
        return df
    
    try:
        # Conversion des colonnes numériques si possible
        for col in df.columns:
            # Essayer de convertir en numérique (gère les séparateurs de milliers)
            try:
                df[col] = pd.to_numeric(
                    df[col].str.replace(' ', '').str.replace(',', '.'),
                    errors='ignore'
                )
            except:
                pass
        
        return df
        
    except Exception as e:
        st.warning(f"⚠️ Impossible de formater le DataFrame: {str(e)}")
        return df


# Export
__all__ = ['scrape_brvm', 'format_brvm_dataframe']
