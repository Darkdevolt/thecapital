import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import warnings
warnings.filterwarnings('ignore')

# Configuration
st.set_page_config(page_title="Analyse BRVM", layout="wide")
st.title("📊 Analyse des titres BRVM")

@st.cache_data(ttl=300)  # Cache 5 minutes
def scrape_brvm_data():
    """
    Fonction pour scraper les données du site BRVM
    basée sur la structure HTML observée
    """
    url = "https://www.brvm.org/fr/cours-actions/0"
    
    try:
        # Headers pour simuler un navigateur
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        # Désactiver la vérification SSL pour Streamlit Cloud
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        
        if response.status_code != 200:
            st.error(f"Erreur HTTP {response.status_code}")
            return None
        
        # Parser le HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # DEBUG: Afficher la structure pour comprendre
        with st.expander("🔍 Voir la structure HTML (débogage)"):
            st.code(str(soup)[:5000], language='html')
        
        # Recherche du tableau principal
        # Méthode 1: Chercher par les en-têtes spécifiques
        table = None
        for t in soup.find_all('table'):
            # Vérifier si ce tableau contient les bonnes colonnes
            headers = [th.get_text(strip=True) for th in t.find_all('th')]
            if 'Symbole' in headers and 'Nom' in headers:
                table = t
                break
        
        # Méthode 2: Prendre le premier tableau si la méthode 1 échoue
        if not table:
            tables = soup.find_all('table')
            if tables:
                table = tables[0]  # Prendre le premier tableau
                st.warning("Utilisation du premier tableau trouvé (structure différente)")
        
        if not table:
            st.error("Aucun tableau trouvé sur la page")
            return None
        
        # Extraction des en-têtes
        headers = []
        for th in table.find_all('th'):
            headers.append(th.get_text(strip=True))
        
        # Si pas d'en-têtes, utiliser les en-têtes par défaut
        if not headers:
            headers = ['Symbole', 'Nom', 'Volume', 'Cours veille (FCFA)', 
                      'Cours Ouverture (FCFA)', 'Cours Clôture (FCFA)', 'Variation (%)']
        
        # Extraction des données
        data = []
        for row in table.find_all('tr'):
            cells = row.find_all(['td', 'th'])
            if cells and cells[0].name == 'td':  # Ignorer la ligne d'en-tête
                row_data = [cell.get_text(strip=True) for cell in cells]
                
                # Vérifier que la ligne a le bon nombre de colonnes
                if len(row_data) >= 6:  # Au moins les colonnes principales
                    # Compléter si moins de colonnes que d'en-têtes
                    if len(row_data) < len(headers):
                        row_data.extend([''] * (len(headers) - len(row_data)))
                    elif len(row_data) > len(headers):
                        row_data = row_data[:len(headers)]
                    
                    data.append(row_data)
        
        if not data:
            st.error("Aucune donnée extraite du tableau")
            return None
        
        # Création du DataFrame
        df = pd.DataFrame(data, columns=headers)
        
        # Nettoyage des données
        df_clean = clean_dataframe(df)
        
        return df_clean
        
    except Exception as e:
        st.error(f"Erreur lors du scraping : {str(e)}")
        return None

def clean_dataframe(df):
    """Nettoyer et formater le DataFrame"""
    df = df.copy()
    
    # Nettoyer les noms de colonnes
    df.columns = [col.strip() for col in df.columns]
    
    # Colonnes à convertir en numérique
    numeric_columns = []
    for col in df.columns:
        if any(keyword in col for keyword in ['Cours', 'Volume', 'Variation']):
            numeric_columns.append(col)
    
    # Conversion des valeurs numériques
    for col in numeric_columns:
        if col in df.columns:
            # Remplacer les virgules par des points pour les décimales
            df[col] = df[col].astype(str).str.replace(',', '.')
            # Supprimer les espaces dans les nombres
            df[col] = df[col].str.replace(' ', '')
            # Supprimer les % pour la colonne Variation
            if 'Variation' in col:
                df[col] = df[col].str.replace('%', '')
            # Convertir en numérique
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Trier par Symbole
    if 'Symbole' in df.columns:
        df = df.sort_values('Symbole').reset_index(drop=True)
    
    return df

def display_brvm_data():
    """Afficher les données BRVM avec interface utilisateur"""
    
    st.sidebar.header("⚙️ Paramètres")
    
    # Bouton d'actualisation
    if st.sidebar.button("🔄 Actualiser les données"):
        st.cache_data.clear()
        st.rerun()
    
    # Options d'affichage
    show_raw = st.sidebar.checkbox("Afficher les données brutes", False)
    sort_by = st.sidebar.selectbox(
        "Trier par",
        ["Symbole", "Variation (%)", "Volume", "Cours Clôture (FCFA)"]
    )
    
    # Récupération des données
    with st.spinner("Récupération des données BRVM..."):
        df = scrape_brvm_data()
    
    if df is not None:
        # Statistiques rapides
        st.subheader("📈 Statistiques du marché")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total = len(df)
            st.metric("Nombre de titres", total)
        
        with col2:
            if 'Variation (%)' in df.columns:
                hausse = len(df[df['Variation (%)'] > 0])
                st.metric("En hausse", hausse, f"+{hausse}")
        
        with col3:
            if 'Variation (%)' in df.columns:
                baisse = len(df[df['Variation (%)'] < 0])
                st.metric("En baisse", baisse, f"-{baisse}")
        
        with col4:
            if 'Variation (%)' in df.columns:
                stable = len(df[df['Variation (%)'] == 0])
                st.metric("Stables", stable)
        
        # Tri des données
        if sort_by in df.columns:
            if sort_by == 'Variation (%)':
                df_display = df.sort_values(sort_by, ascending=False)
            else:
                df_display = df.sort_values(sort_by)
        else:
            df_display = df
        
        # Affichage du tableau
        st.subheader("📋 Données des actions")
        
        # Mise en forme des variations
        def color_variation(val):
            if isinstance(val, (int, float)):
                if val > 0:
                    return 'color: green; font-weight: bold'
                elif val < 0:
                    return 'color: red; font-weight: bold'
            return ''
        
        # Appliquer le style si la colonne existe
        if 'Variation (%)' in df_display.columns:
            styled_df = df_display.style.map(color_variation, subset=['Variation (%)'])
            st.dataframe(styled_df, use_container_width=True, height=400)
        else:
            st.dataframe(df_display, use_container_width=True, height=400)
        
        # Données brutes pour débogage
        if show_raw:
            st.subheader("📄 Données brutes extraites")
            st.write("Structure du DataFrame :", df.shape)
            st.write(df)
        
        # Téléchargement
        st.subheader("💾 Export des données")
        
        csv = df.to_csv(index=False, sep=';', decimal=',')
        st.download_button(
            label="📥 Télécharger en CSV",
            data=csv,
            file_name="brvm_data.csv",
            mime="text/csv"
        )
        
        # Informations sur les colonnes
        with st.expander("ℹ️ Informations sur les colonnes"):
            st.markdown("""
            - **Symbole** : Code de l'action
            - **Nom** : Nom de l'entreprise
            - **Volume** : Nombre d'actions échangées
            - **Cours veille** : Cours de la veille (FCFA)
            - **Cours Ouverture** : Cours à l'ouverture (FCFA)
            - **Cours Clôture** : Cours à la clôture (FCFA)
            - **Variation (%)** : Pourcentage de variation
            """)
    
    else:
        # Mode démo avec données statiques
        st.warning("⚠️ Mode démonstration - Données statiques")
        
        # Données d'exemple basées sur le HTML fourni
        demo_data = {
            'Symbole': ['BICB', 'BICC', 'BOAB', 'ORAC', 'SGBC', 'SNTS'],
            'Nom': ['BANQUE INTERNATIONALE POUR L\'INDUSTRIE ET LE COMMERCE DU BENIN',
                   'BICI COTE D\'IVOIRE', 'BANK OF AFRICA BENIN', 
                   'ORANGE COTE D\'IVOIRE', 'SOCIETE GENERALE COTE D\'IVOIRE',
                   'SONATEL SENEGAL'],
            'Volume': [900, 1025, 4599, 342, 282, 3047],
            'Cours veille (FCFA)': [4950, 19000, 5930, 14500, 28550, 25000],
            'Cours Clôture (FCFA)': [4905, 19380, 5825, 14600, 28500, 24900],
            'Variation (%)': [-0.91, 0.21, 0.43, 0.69, 2.52, -0.40]
        }
        
        df_demo = pd.DataFrame(demo_data)
        st.dataframe(df_demo, use_container_width=True)
        
        st.info("""
        **Note** : L'application n'a pas pu se connecter au site BRVM.
        Les données affichées sont à titre d'exemple.
        
        Prochaines étapes :
        1. Vérifiez que le site https://www.brvm.org est accessible
        2. La structure HTML peut avoir changé
        3. Contactez le support si le problème persiste
        """)

# Interface principale
def main():
    st.markdown("""
    ### Application d'analyse des actions BRVM
    
    Cette application extrait les données boursières de la Bourse Régionale des Valeurs Mobilières (BRVM).
    
    **Fonctionnalités** :
    - Extraction en temps réel des cours des actions
    - Affichage des variations
    - Filtrage et tri des données
    - Export au format CSV
    """)
    
    # Affichage des données
    display_brvm_data()
    
    # Footer
    st.markdown("---")
    st.caption("Source : BRVM - https://www.brvm.org | Dernière mise à jour : " + pd.Timestamp.now().strftime("%d/%m/%Y %H:%M"))

if __name__ == "__main__":
    main()
