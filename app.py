import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import urllib3
import warnings

# Désactiver les avertissements SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore')

# Fonction pour récupérer les données
@st.cache_data(ttl=3600)
def scrape_brvm_data():
    url = "https://www.brvm.org/fr/cours-actions/0"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Ajouter verify=False pour ignorer la vérification SSL
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        response.raise_for_status()
        
        # Vérifier le contenu
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Recherche du tableau - plusieurs méthodes
            table = soup.find('table', {'class': None})  # Table sans classe
            if not table:
                tables = soup.find_all('table')
                if tables:
                    table = tables[0]  # Prendre le premier tableau
            
            if not table:
                # Essayer une autre méthode
                table = soup.select_one('table')
            
            if not table:
                st.error("Tableau non trouvé sur la page.")
                # Afficher un aperçu du HTML pour déboguer
                with st.expander("Aperçu du HTML"):
                    st.text(soup.prettify()[:2000])
                return None
            
            # Extraction des en-têtes
            headers = []
            for th in table.find_all('th'):
                headers.append(th.text.strip())
            
            # Si pas d'en-têtes, créer des en-têtes par défaut
            if not headers:
                headers = ['Symbole', 'Nom', 'Volume', 'Cours veille (FCFA)', 
                          'Cours Ouverture (FCFA)', 'Cours Clôture (FCFA)', 'Variation (%)']
            
            # Extraction des lignes
            data = []
            for row in table.find_all('tr'):
                cols = row.find_all('td')
                if cols:
                    row_data = [col.text.strip() for col in cols]
                    if len(row_data) == len(headers):
                        data.append(row_data)
            
            if not data:
                # Essayer une autre méthode d'extraction
                for row in table.find_all('tr')[1:]:
                    cols = row.find_all('td')
                    if cols:
                        row_data = [col.text.strip() for col in cols]
                        data.append(row_data)
            
            # Création du DataFrame
            if data:
                df = pd.DataFrame(data, columns=headers)
                
                # Nettoyage des données
                for col in df.columns:
                    if 'Variation' in col:
                        df[col] = df[col].str.replace(',', '.').str.replace('%', '').astype(float)
                    elif 'Cours' in col or 'Volume' in col:
                        df[col] = df[col].str.replace(' ', '').str.replace(',', '.').astype(float)
                
                return df
            else:
                st.error("Aucune donnée extraite du tableau.")
                return None
                
        else:
            st.error(f"Erreur HTTP {response.status_code}")
            return None
            
    except requests.exceptions.SSLError as e:
        # Réessayer sans SSL
        try:
            response = requests.get(url, headers=headers, timeout=15, verify=False)
            return scrape_brvm_data()  # Appel récursif
        except:
            st.error(f"Erreur SSL persistante : {e}")
            return None
            
    except Exception as e:
        st.error(f"Erreur lors du scraping : {str(e)}")
        return None
