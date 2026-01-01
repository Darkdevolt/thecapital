# pages/cours.py
import streamlit as st
import pandas as pd
from datetime import datetime
from utils.scraping import scrape_brvm

def page_cours():
    st.title("📈 Cours des Actions BRVM")
    
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
