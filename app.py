import streamlit as st
import pandas as pd
import requests
from io import StringIO
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="BRVM Stocks", layout="wide")
st.title("📊 Données BRVM")

@st.cache_data(ttl=600)
def get_brvm_data():
    try:
        # URL alternative si le site principal échoue
        urls = [
            "https://www.brvm.org/fr/cours-actions/0",
            "http://www.brvm.org/fr/cours-actions/0"  # HTTP au lieu de HTTPS
        ]
        
        for url in urls:
            try:
                # Essayer sans vérification SSL
                response = requests.get(
                    url, 
                    timeout=15, 
                    verify=False,
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                
                if response.status_code == 200:
                    # Essayer pandas read_html d'abord
                    try:
                        dfs = pd.read_html(StringIO(response.text))
                        if dfs:
                            df = dfs[0]
                            st.success(f"Données récupérées depuis {url}")
                            return df
                    except:
                        pass
                    
                    # Méthode manuelle si pandas échoue
                    import re
                    lines = response.text.split('\n')
                    data_lines = []
                    
                    for line in lines:
                        if any(symbol in line for symbol in ['BICB', 'BOAB', 'ORAC', 'SGBC']):
                            # Nettoyer la ligne
                            clean_line = re.sub(r'<[^>]+>', ' ', line)
                            clean_line = re.sub(r'\s+', ' ', clean_line).strip()
                            if clean_line:
                                data_lines.append(clean_line)
                    
                    if data_lines:
                        # Créer un DataFrame simple
                        df = pd.DataFrame([line.split()[:7] for line in data_lines if len(line.split()) >= 6])
                        return df
                        
            except:
                continue
        
        # Données de secours (fallback)
        st.warning("Utilisation des données de secours")
        return create_fallback_data()
        
    except Exception as e:
        st.error(f"Erreur : {e}")
        return create_fallback_data()

def create_fallback_data():
    """Créer des données factices pour tester l'interface"""
    import random
    symbols = ['BICB', 'BICC', 'BOAB', 'BOAC', 'ORAC', 'SGBC', 'SNTS', 'UNLC']
    data = []
    
    for symbol in symbols:
        price = random.randint(1000, 50000)
        change = random.uniform(-5, 5)
        data.append({
            'Symbole': symbol,
            'Nom': f'Company {symbol}',
            'Volume': random.randint(100, 10000),
            'Cours Clôture (FCFA)': price,
            'Variation (%)': round(change, 2)
        })
    
    return pd.DataFrame(data)

# Interface
df = get_brvm_data()

if df is not None:
    st.dataframe(df, use_container_width=True)
    
    # Boutons d'action
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 Actualiser"):
            st.cache_data.clear()
            st.rerun()
    with col2:
        st.download_button(
            "📥 Télécharger CSV",
            df.to_csv(index=False),
            "brvm_data.csv"
        )
    with col3:
        st.metric("Nombre de titres", len(df))
else:
    st.error("Impossible de récupérer les données")
