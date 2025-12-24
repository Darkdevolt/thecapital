import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Configuration de la page
st.set_page_config(
    page_title="Analyse des titres BRVM",
    page_icon="📈",
    layout="wide"
)

# Titre de l'application
st.title("📊 Analyse des titres cotés à la BRVM")
st.markdown("""  
Cette application extrait en temps réel les données des actions depuis le [site officiel de la BRVM](https://www.brvm.org/fr/cours-actions/0).
""")

# Fonction pour récupérer les données
@st.cache_data(ttl=3600)  # Cache pendant 1 heure
def scrape_brvm_data():
    url = "https://www.brvm.org/fr/cours-actions/0"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Recherche du tableau
        table = soup.find('table')
        
        if not table:
            st.error("Tableau non trouvé sur la page.")
            return None
        
        # Extraction des en-têtes
        headers = []
        for th in table.find_all('th'):
            headers.append(th.text.strip())
        
        # Extraction des lignes de données
        data = []
        for row in table.find_all('tr')[1:]:  # Ignorer l'en-tête
            cols = row.find_all('td')
            if len(cols) == len(headers):
                row_data = [col.text.strip() for col in cols]
                data.append(row_data)
        
        # Création du DataFrame
        df = pd.DataFrame(data, columns=headers)
        
        # Nettoyage des données
        if 'Variation (%)' in df.columns:
            df['Variation (%)'] = df['Variation (%)'].str.replace(',', '.').astype(float)
        
        # Colonnes numériques
        numeric_columns = ['Volume', 'Cours veille (FCFA)', 'Cours Ouverture (FCFA)', 'Cours Clôture (FCFA)']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].str.replace(' ', '').astype(float)
        
        return df
    
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur de connexion : {e}")
        return None
    except Exception as e:
        st.error(f"Erreur lors du scraping : {e}")
        return None

# Interface principale
def main():
    # Sidebar pour les filtres
    with st.sidebar:
        st.header("🔧 Filtres")
        st.markdown("Filtrez les données selon vos critères.")
        
        # Option de tri
        sort_by = st.selectbox(
            "Trier par :",
            ["Symbole", "Variation (%)", "Volume", "Cours Clôture (FCFA)"]
        )
        
        # Filtre par variation
        variation_filter = st.selectbox(
            "Filtrer par variation :",
            ["Toutes", "Hausse (≥ 0%)", "Baisse (< 0%)", "Stable (= 0%)"]
        )
    
    # Bouton pour actualiser les données
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔄 Actualiser les données", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    # Récupération des données
    with st.spinner("Récupération des données en cours..."):
        df = scrape_brvm_data()
    
    if df is not None and not df.empty:
        # Application des filtres
        if variation_filter == "Hausse (≥ 0%)":
            df = df[df['Variation (%)'] >= 0]
        elif variation_filter == "Baisse (< 0%)":
            df = df[df['Variation (%)'] < 0]
        elif variation_filter == "Stable (= 0%)":
            df = df[df['Variation (%)'] == 0]
        
        # Tri des données
        if sort_by == "Variation (%)":
            df = df.sort_values(by=sort_by, ascending=False)
        else:
            df = df.sort_values(by=sort_by)
        
        # Affichage des métriques clés
        st.subheader("📈 Aperçu du marché")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Nombre de titres", len(df))
        
        with col2:
            hausse = len(df[df['Variation (%)'] > 0])
            st.metric("En hausse", hausse)
        
        with col3:
            baisse = len(df[df['Variation (%)'] < 0])
            st.metric("En baisse", baisse)
        
        with col4:
            stable = len(df[df['Variation (%)'] == 0])
            st.metric("Stables", stable)
        
        # Affichage du tableau
        st.subheader("📋 Tableau des cours")
        
        # Personnalisation du style
        def color_variation(val):
            if val > 0:
                return 'color: green'
            elif val < 0:
                return 'color: red'
            else:
                return 'color: gray'
        
        styled_df = df.style.map(color_variation, subset=['Variation (%)'])
        
        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True,
            height=600
        )
        
        # Téléchargement des données
        st.subheader("💾 Export des données")
        
        csv = df.to_csv(index=False, sep=';', decimal=',')
        st.download_button(
            label="📥 Télécharger en CSV",
            data=csv,
            file_name=f"brvm_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
        # Affichage des données brutes
        with st.expander("🔍 Afficher les données brutes"):
            st.write(df)
    
    else:
        st.error("Impossible de récupérer les données. Veuillez réessayer plus tard.")

if __name__ == "__main__":
    main()
