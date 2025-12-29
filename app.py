import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="BRVM Cours Actions", page_icon="📈", layout="wide")

st.title("📈 Cours des Actions BRVM")
st.markdown("*Bourse Régionale des Valeurs Mobilières*")

@st.cache_data(ttl=300)
def scrape_brvm():
    """Scrape les données de cours des actions depuis BRVM"""
    url = "https://www.brvm.org/fr/cours-actions/0"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Trouver le tableau des cours
        table = soup.find('table')
        
        if not table:
            return None
        
        # Extraire les en-têtes
        headers = []
        thead = table.find('thead')
        if thead:
            for th in thead.find_all('th'):
                headers.append(th.get_text(strip=True))
        
        # Extraire les données
        data = []
        tbody = table.find('tbody')
        if tbody:
            for row in tbody.find_all('tr'):
                cols = row.find_all('td')
                if cols:
                    row_data = [col.get_text(strip=True) for col in cols]
                    data.append(row_data)
        
        if not headers or not data:
            return None
        
        # Créer le DataFrame
        df = pd.DataFrame(data, columns=headers)
        
        return df
    
    except Exception as e:
        st.error(f"Erreur lors du scraping: {str(e)}")
        return None

# Bouton de rafraîchissement
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
    df = scrape_brvm()

if df is not None and not df.empty:
    st.success(f"✅ {len(df)} actions chargées avec succès")
    
    # Afficher les statistiques
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Nombre d'actions", len(df))
    with col2:
        st.metric("Dernière mise à jour", datetime.now().strftime('%d/%m/%Y'))
    with col3:
        st.metric("Source", "BRVM.org")
    
    st.markdown("---")
    
    # Filtre de recherche
    search = st.text_input("🔍 Rechercher une action", placeholder="Entrez le nom ou le symbole...")
    
    if search:
        # Filtrer sur toutes les colonnes
        mask = df.astype(str).apply(lambda x: x.str.contains(search, case=False, na=False)).any(axis=1)
        filtered_df = df[mask]
        st.info(f"🔎 {len(filtered_df)} résultat(s) trouvé(s)")
    else:
        filtered_df = df
    
    # Afficher le tableau
    st.dataframe(
        filtered_df,
        use_container_width=True,
        height=600,
        hide_index=True
    )
    
    # Bouton de téléchargement
    csv = filtered_df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 Télécharger en CSV",
        data=csv,
        file_name=f"brvm_cours_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )
    
else:
    st.error("❌ Impossible de charger les données. Veuillez réessayer plus tard.")
    st.info("💡 Le site BRVM peut être temporairement indisponible ou la structure de la page a changé.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <small>Données provenant de <a href='https://www.brvm.org' target='_blank'>BRVM.org</a> | 
    Mise à jour automatique toutes les 5 minutes</small>
</div>
""", unsafe_allow_html=True)
