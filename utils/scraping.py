# utils/scraping.py
import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import urllib3
from datetime import datetime

# Désactiver les warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

@st.cache_data(ttl=300)
def scrape_brvm():
    """Scrape les données de cours des actions depuis Sikafinance"""
    url = "https://www.sikafinance.com/marches/aaz"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        
        # Requête avec vérification SSL désactivée
        response = requests.get(url, headers=headers, verify=False, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Trouver toutes les tables
        tables = soup.find_all('table')
        
        if len(tables) < 2:
            return None, None
        
        # Première table : Les indices
        indices_table = tables[0]
        indices_data = []
        indices_headers = []
        
        # Extraire les en-têtes des indices
        thead = indices_table.find('thead')
        if thead:
            for th in thead.find_all('th'):
                indices_headers.append(th.get_text(strip=True))
        else:
            # Si pas de thead, prendre la première ligne comme en-tête
            first_row = indices_table.find('tr')
            if first_row:
                for th in first_row.find_all(['th', 'td']):
                    indices_headers.append(th.get_text(strip=True))
        
        # Extraire les données des indices
        tbody = indices_table.find('tbody')
        if tbody:
            for row in tbody.find_all('tr'):
                cols = row.find_all('td')
                if cols and len(cols) > 0:
                    row_data = [col.get_text(strip=True) for col in cols]
                    indices_data.append(row_data)
        
        # Deuxième table : Les actions
        actions_table = tables[1]
        actions_data = []
        actions_headers = []
        
        # Extraire les en-têtes des actions
        thead = actions_table.find('thead')
        if thead:
            for th in thead.find_all('th'):
                actions_headers.append(th.get_text(strip=True))
        else:
            # Si pas de thead, prendre la première ligne comme en-tête
            first_row = actions_table.find('tr')
            if first_row:
                for th in first_row.find_all(['th', 'td']):
                    actions_headers.append(th.get_text(strip=True))
        
        # Extraire les données des actions
        tbody = actions_table.find('tbody')
        if tbody:
            for row in tbody.find_all('tr'):
                cols = row.find_all('td')
                if cols and len(cols) > 0:
                    row_data = [col.get_text(strip=True) for col in cols]
                    actions_data.append(row_data)
        
        # Créer les DataFrames
        df_indices = None
        df_actions = None
        
        if indices_headers and indices_data:
            df_indices = pd.DataFrame(indices_data, columns=indices_headers)
        
        if actions_headers and actions_data:
            df_actions = pd.DataFrame(actions_data, columns=actions_headers)
        
        return df_indices, df_actions
    
    except Exception as e:
        st.error(f"Erreur lors du scraping: {str(e)}")
        return None, None
