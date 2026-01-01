# pages/developpeur.py
import streamlit as st
import pandas as pd
from datetime import datetime
from config.settings import DEVELOPER_PASSWORD
from database.operations import init_storage, load_symbol_mapping, save_symbol_mapping, delete_symbol_mapping, save_financial_data, delete_financial_data, load_all_financial_data
from utils.calculations import calculate_enhanced_financial_ratios

def page_developpeur():
    """Section réservée au développeur pour gérer les données"""
    st.title("⚙️ Section Développeur")
    
    if 'dev_authenticated' not in st.session_state:
        st.session_state.dev_authenticated = False
    
    if not st.session_state.dev_authenticated:
        password = st.text_input("Mot de passe développeur", type="password")
        if st.button("Se connecter"):
            if password == DEVELOPER_PASSWORD:
                st.session_state.dev_authenticated = True
                st.rerun()
            else:
                st.error("Mot de passe incorrect")
        return
    
    st.success("✅ Connecté en tant que développeur")
    
    # Onglets développeur
    tab1, tab2, tab3 = st.tabs([
        "📊 Données Financières",
        "🔤 Noms des Entreprises",
        "⚙️ Paramètres"
    ])
    
    with tab1:
        st.header("Gestion des Données Financières")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Ajouter/Modifier des données")
            symbole = st.text_input("Symbole BRVM (ex: SNTS)", key="dev_symbole")
            annee = st.number_input("Année", min_value=2000, max_value=2030, value=2023, key="dev_annee")
            
            with st.expander("Bilan"):
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    actif_total = st.number_input("Actif Total", value=0.0, key="bilan_actif_total")
                    actif_courant = st.number_input("Actif Courant", value=0.0, key="bilan_actif_courant")
                    stocks = st.number_input("Stocks", value=0.0, key="bilan_stocks")
                    creances = st.number_input("Créances", value=0.0, key="bilan_creances")
                    tresorerie = st.number_input("Trésorerie", value=0.0, key="bilan_tresorerie")
                
                with col_b2:
                    capitaux_propres = st.number_input("Capitaux Propres", value=0.0, key="bilan_capitaux_propres")
                    dettes_totales = st.number_input("Dettes Totales", value=0.0, key="bilan_dettes_totales")
                    passif_courant = st.number_input("Passif Courant", value=0.0, key="bilan_passif_courant")
                    cours_action = st.number_input("Cours Action", value=0.0, key="bilan_cours_action")
                    nb_actions = st.number_input("Nombre d'Actions", value=0.0, key="bilan_nb_actions")
            
            with st.expander("Compte de Résultat"):
                chiffre_affaires = st.number_input("Chiffre d'Affaires", value=0.0, key="cr_chiffre_affaires")
                resultat_exploitation = st.number_input("Résultat Exploitation", value=0.0, key="cr_resultat_exploitation")
                resultat_net = st.number_input("Résultat Net", value=0.0, key="cr_resultat_net")
                charges_financieres = st.number_input("Charges Financières", value=0.0, key="cr_charges_financieres")
                benefice_par_action = st.number_input("Bénéfice par Action", value=0.0, key="cr_benefice_par_action")
            
            with st.expander("Flux de Trésorerie"):
                flux_exploitation = st.number_input("Flux d'Exploitation", value=0.0, key="ft_flux_exploitation")
                flux_investissement = st.number_input("Flux d'Investissement", value=0.0, key="ft_flux_investissement")
                flux_financement = st.number_input("Flux de Financement", value=0.0, key="ft_flux_financement")
            
            if st.button("💾 Sauvegarder les Données", type="primary", use_container_width=True):
                if symbole and annee:
                    data_dict = {
                        'bilan': {
                            'actif_total': actif_total,
                            'actif_courant': actif_courant,
                            'stocks': stocks,
                            'creances': creances,
                            'tresorerie': tresorerie,
                            'capitaux_propres': capitaux_propres,
                            'dettes_totales': dettes_totales,
                            'passif_courant': passif_courant,
                            'cours_action': cours_action,
                            'nb_actions': nb_actions
                        },
                        'compte_resultat': {
                            'chiffre_affaires': chiffre_affaires,
                            'resultat_exploitation': resultat_exploitation,
                            'resultat_net': resultat_net,
                            'charges_financieres': charges_financieres,
                            'benefice_par_action': benefice_par_action
                        },
                        'flux_tresorerie': {
                            'flux_exploitation': flux_exploitation,
                            'flux_investissement': flux_investissement,
                            'flux_financement': flux_financement
                        }
                    }
                    
                    # Calculer les ratios
                    ratios = calculate_enhanced_financial_ratios(
                        data_dict['bilan'],
                        data_dict['compte_resultat'],
                        data_dict['flux_tresorerie']
                    )
                    data_dict['ratios'] = ratios
                    
                    if save_financial_data(symbole, annee, data_dict):
                        st.success(f"✅ Données sauvegardées pour {symbole} - {annee}")
                        st.session_state.financial_data = load_all_financial_data()
                        st.rerun()
                    else:
                        st.error("❌ Erreur lors de la sauvegarde")
                else:
                    st.error("⚠️ Veuillez remplir le symbole et l'année")
        
        with col2:
            st.subheader("Supprimer des données")
            
            financial_data = init_storage()
            if financial_data:
                options = []
                for key, data in financial_data.items():
                    if isinstance(data, dict):
                        symbole = data.get('symbole', '')
                        annee = data.get('annee', '')
                        nom_complet = st.session_state.get('symbol_mapping', {}).get(symbole, symbole)
                        options.append(f"{symbole} - {nom_complet} ({annee})")
                
                if options:
                    selected = st.selectbox("Sélectionnez les données à supprimer", options)
                    
                    if selected and st.button("🗑️ Supprimer", type="secondary", use_container_width=True):
                        # Extraire symbole et année
                        parts = selected.split(" (")
                        symbole = parts[0].split(" - ")[0]
                        annee = parts[1].replace(")", "")
                        
                        if delete_financial_data(symbole, int(annee)):
                            st.success(f"✅ Données supprimées pour {symbole} - {annee}")
                            st.session_state.financial_data = load_all_financial_data()
                            st.rerun()
                        else:
                            st.error("❌ Erreur lors de la suppression")
                else:
                    st.info("📭 Aucune donnée à supprimer")
    
    with tab2:
        st.header("Noms des Entreprises")
        st.info("""
        Associez un nom complet à chaque symbole BRVM pour améliorer l'interface.
        Exemple: 
        - Symbole: "SNTS" → Nom: "Sonatel S.A."
        - Symbole: "SHEC" → Nom: "Vivo Energy Côte d'Ivoire"
        """)
        
        # Afficher les mappings existants
        symbol_mapping = load_symbol_mapping()
        st.session_state.symbol_mapping = symbol_mapping
        
        if symbol_mapping:
            st.subheader("Noms configurés")
            df_mapping = pd.DataFrame(
                [(k, v) for k, v in symbol_mapping.items()],
                columns=["Symbole BRVM", "Nom Complet"]
            )
            st.dataframe(df_mapping, use_container_width=True)
        
        # Ajouter/Modifier un mapping
        st.subheader("Ajouter/Modifier un nom")
        
        # Charger les symboles existants dans les données financières
        financial_data = init_storage()
        symboles_existants = sorted(set([data['symbole'] for data in financial_data.values() if isinstance(data, dict)]))
        
        col_map1, col_map2 = st.columns(2)
        
        with col_map1:
            if symboles_existants:
                symbole = st.selectbox("Symbole BRVM", [''] + symboles_existants)
            else:
                symbole = st.text_input("Symbole BRVM", placeholder="Ex: SNTS")
        
        with col_map2:
            nom_complet = st.text_input("Nom complet de l'entreprise", 
                                       placeholder="Ex: Sonatel S.A.")
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("💾 Sauvegarder", type="primary", use_container_width=True):
                if symbole and nom_complet:
                    if save_symbol_mapping(symbole, nom_complet):
                        st.success(f"✅ Nom sauvegardé: {symbole} → {nom_complet}")
                        st.session_state.symbol_mapping = load_symbol_mapping()
                        st.rerun()
                    else:
                        st.error("❌ Erreur lors de la sauvegarde")
                else:
                    st.error("⚠️ Veuillez remplir tous les champs")
        
        with col_btn2:
            if symbol_mapping and symbole in symbol_mapping:
                if st.button("🗑️ Supprimer", type="secondary", use_container_width=True):
                    if delete_symbol_mapping(symbole):
                        st.success(f"✅ Nom supprimé pour {symbole}")
                        st.session_state.symbol_mapping = load_symbol_mapping()
                        st.rerun()
                    else:
                        st.error("❌ Erreur lors de la suppression")
    
    with tab3:
        st.header("Paramètres")
        
        st.subheader("Configuration Supabase")
        from config.settings import SUPABASE_URL
        st.info(f"URL: {SUPABASE_URL}")
        
        from database.supabase_client import init_supabase
        if st.button("🔗 Tester la connexion Supabase", use_container_width=True):
            supabase = init_supabase()
            if supabase:
                st.success("✅ Connexion Supabase active")
            else:
                st.error("❌ Erreur de connexion Supabase")
        
        st.subheader("Gestion du cache")
        if st.button("🧹 Vider le cache", type="secondary", use_container_width=True):
            st.cache_data.clear()
            st.success("✅ Cache vidé")
        
        st.subheader("Déconnexion")
        if st.button("🚪 Se déconnecter", type="secondary", use_container_width=True):
            st.session_state.dev_authenticated = False
            st.rerun()
