import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import urllib3

# Désactiver les warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="BRVM Cours Actions", page_icon="📈", layout="wide")

st.title("📈 Cours des Actions BRVM")
st.markdown("*Bourse Régionale des Valeurs Mobilières via Sikafinance*")

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

# Interface principale
col1, col2, col3 = st.columns([1, 1, 4])
with col1:
    if st.button("🔄 Rafraîchir", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

with col2:
    st.info(f"⏰ {datetime.now().strftime('%H:%M:%S')}")

st.markdown("---")

# Scraper et afficher les données
with st.spinner("Chargement des données de la BRVM..."):
    df_indices, df_actions = scrape_brvm()

if df_indices is not None or df_actions is not None:
    st.success("✅ Données chargées avec succès depuis Sikafinance")
    
    # Onglets pour séparer indices et actions
    tab1, tab2 = st.tabs(["📊 Actions Cotées", "📈 Indices BRVM"])
    
    with tab1:
        if df_actions is not None and not df_actions.empty:
            # Statistiques des actions
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Nombre d'actions", len(df_actions))
            with col2:
                st.metric("Dernière mise à jour", datetime.now().strftime('%d/%m/%Y'))
            with col3:
                st.metric("Source", "Sikafinance")
            
            st.markdown("---")
            
            # Filtre de recherche
            search = st.text_input("🔍 Rechercher une action", placeholder="Entrez le nom ou le symbole...")
            
            if search:
                mask = df_actions.astype(str).apply(lambda x: x.str.contains(search, case=False, na=False)).any(axis=1)
                filtered_df = df_actions[mask]
                st.info(f"🔎 {len(filtered_df)} résultat(s) trouvé(s)")
            else:
                filtered_df = df_actions
            
            # Afficher le tableau des actions
            st.dataframe(
                filtered_df,
                use_container_width=True,
                height=500,
                hide_index=True
            )
            
            # Bouton de téléchargement
            csv_actions = filtered_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 Télécharger les actions en CSV",
                data=csv_actions,
                file_name=f"brvm_actions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("⚠️ Aucune donnée d'action disponible")
    
    with tab2:
        if df_indices is not None and not df_indices.empty:
            st.subheader("Indices du marché BRVM")
            
            # Afficher le tableau des indices
            st.dataframe(
                df_indices,
                use_container_width=True,
                height=500,
                hide_index=True
            )
            
            # Bouton de téléchargement
            csv_indices = df_indices.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 Télécharger les indices en CSV",
                data=csv_indices,
                file_name=f"brvm_indices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("⚠️ Aucune donnée d'indice disponible")

else:
    st.error("❌ Impossible de charger les données. Veuillez réessayer plus tard.")
    st.info("💡 Le site source peut être temporairement indisponible.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <small>Données provenant de <a href='https://www.sikafinance.com/marches/aaz' target='_blank'>Sikafinance.com</a> | 
    Mise à jour automatique toutes les 5 minutes</small>
</div>
""", unsafe_allow_html=True)
