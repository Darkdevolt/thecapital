# pages/analyse.py
import streamlit as st
import pandas as pd
from database.operations import init_storage
from utils.calculations import calculate_enhanced_financial_ratios, calculate_valuation_multiples, calculate_financial_projections

def page_analyse():
    st.title("🔍 Analyse Fondamentale")
    
    financial_data = init_storage()
    
    if not financial_data:
        st.warning("Aucune donnée financière disponible.")
        st.info("Rendez-vous dans la section Développeur pour saisir des données financières.")
        return
    
    symboles = sorted(set([data['symbole'] for data in financial_data.values() if isinstance(data, dict)]))
    
    if not symboles:
        st.warning("Aucune entreprise trouvée dans les données.")
        return
    
    # Utiliser le mapping pour afficher des noms lisibles
    mapping = st.session_state.get('symbol_mapping', {})
    
    # Créer les options avec format: "SNTS - Sonatel S.A." si mapping existe
    options = []
    for symbole in symboles:
        nom_complet = mapping.get(symbole, symbole)
        options.append(f"{symbole} - {nom_complet}")
    
    # Sélection de l'entreprise
    selected_option = st.selectbox("Choisissez une entreprise", [''] + options)
    
    if selected_option:
        # Extraire le symbole de l'option sélectionnée
        symbole_selected = selected_option.split(" - ")[0]
        
        # Récupérer les données de cette entreprise
        symbole_data = {}
        for key, data in financial_data.items():
            if data.get('symbole') == symbole_selected:
                symbole_data[data['annee']] = data
        
        if symbole_data:
            # Afficher le nom complet si disponible
            nom_complet = mapping.get(symbole_selected, symbole_selected)
            st.success(f"📊 Données disponibles pour {nom_complet}")
            
            # Sélection de l'année
            annees = sorted(symbole_data.keys())
            annee_selectionnee = st.selectbox("Sélectionnez l'année", annees, index=len(annees)-1)
            
            if annee_selectionnee:
                data = symbole_data[annee_selectionnee]
                
                # Onglets pour l'analyse
                tab1, tab2, tab3, tab4 = st.tabs(["📋 Ratios Financiers", "💰 Valorisation", "📈 Projections", "📊 Données Brutes"])
                
                with tab1:
                    st.subheader(f"Ratios Financiers - {annee_selectionnee}")
                    
                    if 'ratios' in data:
                        ratios = data['ratios']
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.markdown("**📊 Rentabilité**")
                            if 'roe' in ratios:
                                st.metric("ROE (Rentabilité des Capitaux Propres)", f"{ratios['roe']:.2f}%")
                            if 'roa' in ratios:
                                st.metric("ROA (Rentabilité de l'Actif)", f"{ratios['roa']:.2f}%")
                            if 'marge_nette' in ratios:
                                st.metric("Marge Nette", f"{ratios['marge_nette']:.2f}%")
                        
                        with col2:
                            st.markdown("**💧 Liquidité**")
                            if 'ratio_liquidite_generale' in ratios:
                                st.metric("Liquidité Générale", f"{ratios['ratio_liquidite_generale']:.2f}")
                            if 'ratio_liquidite_reduite' in ratios:
                                st.metric("Liquidité Réduite", f"{ratios['ratio_liquidite_reduite']:.2f}")
                            if 'ratio_liquidite_immediate' in ratios:
                                st.metric("Liquidité Immédiate", f"{ratios['ratio_liquidite_immediate']:.2f}")
                        
                        with col3:
                            st.markdown("**🏦 Endettement**")
                            if 'ratio_endettement' in ratios:
                                st.metric("Ratio d'Endettement", f"{ratios['ratio_endettement']:.2f}%")
                            if 'debt_to_ebitda' in ratios:
                                st.metric("Dette/EBITDA", f"{ratios['debt_to_ebitda']:.2f}")
                            if 'couverture_interets' in ratios:
                                st.metric("Couverture des Intérêts", f"{ratios['couverture_interets']:.2f}x")
                
                with tab2:
                    st.subheader("Valorisation par Multiples")
                    
                    valorisations = calculate_valuation_multiples(
                        symbole_selected,
                        annee_selectionnee,
                        {**data['bilan'], **data['compte_resultat'], **data.get('ratios', {})},
                        financial_data
                    )
                    
                    if 'recommandation' in valorisations:
                        col_rec1, col_rec2 = st.columns([1, 3])
                        
                        with col_rec1:
                            if "ACHAT FORT" in valorisations['recommandation']:
                                st.success(f"## {valorisations['recommandation']}")
                            elif "ACHAT" in valorisations['recommandation']:
                                st.success(f"## {valorisations['recommandation']}")
                            elif "VENTE" in valorisations['recommandation']:
                                st.error(f"## {valorisations['recommandation']}")
                            elif "VENTE FORTE" in valorisations['recommandation']:
                                st.error(f"## {valorisations['recommandation']}")
                            else:
                                st.warning(f"## {valorisations['recommandation']}")
                        
                        with col_rec2:
                            st.info(f"**Justification :** {valorisations.get('justification', '')}")
                    
                    # Afficher les multiples de valorisation
                    if 'medianes_secteur' in valorisations:
                        st.markdown("### Multiples Sectoriels (Médiane)")
                        medianes = valorisations['medianes_secteur']
                        
                        if medianes:
                            df_medianes = pd.DataFrame(list(medianes.items()), columns=['Multiple', 'Valeur'])
                            st.dataframe(df_medianes, use_container_width=True)
                
                with tab3:
                    st.subheader("Projections Financières")
                    
                    projections = calculate_financial_projections(symbole_selected, financial_data)
                    
                    if 'projections' in projections:
                        st.markdown(f"**Méthode :** {projections.get('methode', '')}")
                        st.markdown(f"**TCAM du CA :** {projections.get('tcam_ca', 0):.2f}%")
                        st.markdown(f"**TCAM du Résultat Net :** {projections.get('tcam_rn', 0):.2f}%")
                        
                        df_proj = pd.DataFrame(projections['projections'])
                        st.dataframe(df_proj.style.format({
                            'ca_projete': '{:,.0f}',
                            'rn_projete': '{:,.0f}',
                            'marge_nette_projetee': '{:.2f}%'
                        }), use_container_width=True)
                    elif 'erreur' in projections:
                        st.warning(projections['erreur'])
                
                with tab4:
                    st.subheader("Données Brutes")
                    
                    col_brut1, col_brut2 = st.columns(2)
                    
                    with col_brut1:
                        if data.get('bilan'):
                            st.markdown("**Bilan**")
                            df_bilan = pd.DataFrame(list(data['bilan'].items()), columns=['Poste', 'Valeur'])
                            st.dataframe(df_bilan, use_container_width=True)
                    
                    with col_brut2:
                        if data.get('compte_resultat'):
                            st.markdown("**Compte de résultat**")
                            df_cr = pd.DataFrame(list(data['compte_resultat'].items()), columns=['Poste', 'Valeur'])
                            st.dataframe(df_cr, use_container_width=True)
