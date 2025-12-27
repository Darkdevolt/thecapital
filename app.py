import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import warnings
import json
from datetime import datetime
from supabase import create_client
import numpy as np
from sklearn.linear_model import LinearRegression
import plotly.graph_objects as go
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Analyse BRVM Pro", layout="wide")

DEVELOPER_PASSWORD = "dev_brvm_2024"
SUPABASE_URL = "https://otsiwiwlnowxeolbbgvm.supabase.co"
SUPABASE_KEY = "sb_publishable_MhaI5b-kMmb5liIMOJ4P3Q_xGTsJAFJ"

# ===========================
# SUPABASE
# ===========================

def init_supabase():
    if 'supabase' not in st.session_state:
        try:
            st.session_state.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            st.session_state.supabase.table("financial_data").select("*", count="exact").limit(1).execute()
        except Exception as e:
            st.error(f"❌ Erreur Supabase: {str(e)}")
            return None
    return st.session_state.supabase

def load_all_financial_data():
    supabase = init_supabase()
    if not supabase:
        return {}
    try:
        response = supabase.table("financial_data").select("*").execute()
        financial_data = {}
        for record in response.data:
            key = f"{record['symbole']}_{record['annee']}"
            financial_data[key] = {
                'symbole': record['symbole'],
                'annee': record['annee'],
                'bilan': record['data'].get('bilan', {}),
                'compte_resultat': record['data'].get('compte_resultat', {}),
                'flux_tresorerie': record['data'].get('flux_tresorerie', {}),
                'ratios': record['data'].get('ratios', {}),
                'last_update': record.get('last_update', None)
            }
        return financial_data
    except Exception as e:
        st.error(f"Erreur chargement: {str(e)}")
        return {}

def save_financial_data(symbole, annee, data_dict):
    supabase = init_supabase()
    if not supabase:
        return False
    try:
        record = {'symbole': symbole, 'annee': annee, 'data': data_dict, 'last_update': datetime.now().isoformat()}
        existing = supabase.table("financial_data").select("*").eq("symbole", symbole).eq("annee", annee).execute()
        if existing.data:
            supabase.table("financial_data").update(record).eq("symbole", symbole).eq("annee", annee).execute()
        else:
            supabase.table("financial_data").insert(record).execute()
        return True
    except Exception as e:
        st.error(f"Erreur sauvegarde: {str(e)}")
        return False

def delete_financial_data(symbole, annee):
    supabase = init_supabase()
    if not supabase:
        return False
    try:
        supabase.table("financial_data").delete().eq("symbole", symbole).eq("annee", annee).execute()
        return True
    except Exception as e:
        st.error(f"Erreur suppression: {str(e)}")
        return False

def init_storage():
    if 'financial_data' not in st.session_state:
        st.session_state.financial_data = load_all_financial_data()
    return st.session_state.financial_data

# ===========================
# UTILITAIRES
# ===========================

def safe_ratio(numerator, denominator, default=None):
    try:
        if denominator and denominator != 0 and not np.isnan(denominator):
            result = numerator / denominator
            if np.isnan(result) or np.isinf(result):
                return default
            return result
        return default
    except (TypeError, ZeroDivisionError):
        return default

def validate_financial_data(bilan, compte_resultat):
    errors = []
    warnings_list = []
    
    if abs(bilan.get('actif_total', 0) - bilan.get('passif_total', 0)) > 1000:
        errors.append(f"❌ Bilan non équilibré : {bilan.get('actif_total', 0) - bilan.get('passif_total', 0):,.0f} FCFA")
    
    if compte_resultat.get('resultat_net', 0) > compte_resultat.get('chiffre_affaires', 0):
        warnings_list.append("⚠️ Résultat net > CA : vérifier")
    
    if bilan.get('actif_total', 0) < 0:
        errors.append("❌ Actif total négatif")
    
    if bilan.get('capitaux_propres', 0) < 0:
        warnings_list.append("⚠️ Capitaux propres négatifs")
    
    return errors, warnings_list

# ===========================
# RATIOS FINANCIERS AMÉLIORÉS
# ===========================

def calculate_enhanced_financial_ratios(bilan, compte_resultat, flux_tresorerie):
    ratios = {}
    
    # Dotations amortissements (estimation si non fourni)
    dotations_amortissements = compte_resultat.get('dotations_amortissements', 0)
    if dotations_amortissements == 0:
        dotations_amortissements = bilan.get('actif_immobilise', 0) * 0.10
    
    # EBITDA CORRIGÉ
    ebitda = compte_resultat.get('resultat_exploitation', 0) + dotations_amortissements
    ebit = compte_resultat.get('resultat_exploitation', 0)
    
    # Taux d'imposition
    taux_imposition = safe_ratio(compte_resultat.get('impots', 0), 
                                 compte_resultat.get('resultat_avant_impot', 0), 0.25)
    if taux_imposition is None:
        taux_imposition = 0.25
    
    # NOPAT et Capital investi
    nopat = ebit * (1 - taux_imposition)
    capital_investi = (bilan.get('capitaux_propres', 0) + 
                      bilan.get('dettes_totales', 0) - 
                      bilan.get('tresorerie', 0))
    
    # FCF et Working Capital
    fcf = flux_tresorerie.get('flux_exploitation', 0) + flux_tresorerie.get('flux_investissement', 0)
    working_capital = bilan.get('actif_courant', 0) - bilan.get('passif_courant', 0)
    
    # Enterprise Value
    market_cap = bilan.get('cours_action', 0) * bilan.get('nb_actions', 0)
    enterprise_value = market_cap + bilan.get('dettes_totales', 0) - bilan.get('tresorerie', 0)
    
    # RENTABILITÉ
    marge_nette = safe_ratio(compte_resultat.get('resultat_net', 0), compte_resultat.get('chiffre_affaires', 0))
    if marge_nette is not None:
        ratios['marge_nette'] = marge_nette * 100
    
    marge_ebit = safe_ratio(ebit, compte_resultat.get('chiffre_affaires', 0))
    if marge_ebit is not None:
        ratios['marge_ebit'] = marge_ebit * 100
    
    marge_ebitda = safe_ratio(ebitda, compte_resultat.get('chiffre_affaires', 0))
    if marge_ebitda is not None:
        ratios['marge_ebitda'] = marge_ebitda * 100
    
    roe = safe_ratio(compte_resultat.get('resultat_net', 0), bilan.get('capitaux_propres', 0))
    if roe is not None:
        ratios['roe'] = roe * 100
    
    roa = safe_ratio(compte_resultat.get('resultat_net', 0), bilan.get('actif_total', 0))
    if roa is not None:
        ratios['roa'] = roa * 100
    
    # ROIC CORRIGÉ
    roic = safe_ratio(nopat, capital_investi)
    if roic is not None:
        ratios['roic'] = roic * 100
    
    # LIQUIDITÉ
    ratio_liquidite_generale = safe_ratio(bilan.get('actif_courant', 0), bilan.get('passif_courant', 0))
    if ratio_liquidite_generale is not None:
        ratios['ratio_liquidite_generale'] = ratio_liquidite_generale
    
    actif_liquide = bilan.get('actif_courant', 0) - bilan.get('stocks', 0)
    ratio_liquidite_reduite = safe_ratio(actif_liquide, bilan.get('passif_courant', 0))
    if ratio_liquidite_reduite is not None:
        ratios['ratio_liquidite_reduite'] = ratio_liquidite_reduite
    
    ratio_liquidite_immediate = safe_ratio(bilan.get('tresorerie', 0), bilan.get('passif_courant', 0))
    if ratio_liquidite_immediate is not None:
        ratios['ratio_liquidite_immediate'] = ratio_liquidite_immediate
    
    # ENDETTEMENT
    ratio_endettement = safe_ratio(bilan.get('dettes_totales', 0), bilan.get('capitaux_propres', 0))
    if ratio_endettement is not None:
        ratios['ratio_endettement'] = ratio_endettement * 100
    
    taux_endettement = safe_ratio(bilan.get('dettes_totales', 0), bilan.get('actif_total', 0))
    if taux_endettement is not None:
        ratios['taux_endettement'] = taux_endettement * 100
    
    ratio_solvabilite = safe_ratio(bilan.get('capitaux_propres', 0), bilan.get('actif_total', 0))
    if ratio_solvabilite is not None:
        ratios['ratio_solvabilite'] = ratio_solvabilite * 100
    
    debt_to_ebitda = safe_ratio(bilan.get('dettes_totales', 0), ebitda)
    if debt_to_ebitda is not None:
        ratios['debt_to_ebitda'] = debt_to_ebitda
    
    couverture_interets = safe_ratio(ebit, abs(compte_resultat.get('charges_financieres', 0)))
    if couverture_interets is not None:
        ratios['couverture_interets'] = couverture_interets
    
    # EFFICACITÉ
    rotation_actifs = safe_ratio(compte_resultat.get('chiffre_affaires', 0), bilan.get('actif_total', 0))
    if rotation_actifs is not None:
        ratios['rotation_actifs'] = rotation_actifs
    
    rotation_stocks = safe_ratio(compte_resultat.get('chiffre_affaires', 0), bilan.get('stocks', 0))
    if rotation_stocks is not None:
        ratios['rotation_stocks'] = rotation_stocks
    
    delai_recouvrement = safe_ratio(bilan.get('creances', 0), compte_resultat.get('chiffre_affaires', 0))
    if delai_recouvrement is not None:
        ratios['delai_recouvrement'] = delai_recouvrement * 365
    
    # MARCHÉ
    bpa = compte_resultat.get('benefice_par_action', 0)
    if bpa == 0 and bilan.get('nb_actions', 0) > 0:
        bpa = compte_resultat.get('resultat_net', 0) / bilan.get('nb_actions', 0)
    
    if bpa != 0:
        ratios['benefice_par_action'] = bpa
        per = safe_ratio(bilan.get('cours_action', 0), bpa)
        if per is not None and per > 0:
            ratios['per'] = per
    
    if bilan.get('nb_actions', 0) > 0:
        cpa = bilan.get('capitaux_propres', 0) / bilan.get('nb_actions', 0)
        price_to_book = safe_ratio(bilan.get('cours_action', 0), cpa)
        if price_to_book is not None:
            ratios['price_to_book'] = price_to_book
    
    ev_ebitda = safe_ratio(enterprise_value, ebitda)
    if ev_ebitda is not None and ev_ebitda > 0:
        ratios['ev_ebitda'] = ev_ebitda
    
    ev_sales = safe_ratio(enterprise_value, compte_resultat.get('chiffre_affaires', 0))
    if ev_sales is not None:
        ratios['ev_sales'] = ev_sales
    
    # FLUX DE TRÉSORERIE
    qualite_benefices = safe_ratio(flux_tresorerie.get('flux_exploitation', 0), compte_resultat.get('resultat_net', 0))
    if qualite_benefices is not None:
        ratios['qualite_benefices'] = qualite_benefices
    
    fcf_yield = safe_ratio(fcf, market_cap)
    if fcf_yield is not None:
        ratios['fcf_yield'] = fcf_yield * 100
    
    fcf_to_debt = safe_ratio(fcf, bilan.get('dettes_totales', 0))
    if fcf_to_debt is not None:
        ratios['fcf_to_debt'] = fcf_to_debt
    
    # Z-SCORE D'ALTMAN
    if bilan.get('actif_total', 0) > 0:
        X1 = working_capital / bilan['actif_total']
        X2 = safe_ratio(compte_resultat.get('resultat_net', 0), bilan['actif_total'], 0)
        X3 = safe_ratio(ebit, bilan['actif_total'], 0)
        X4 = safe_ratio(market_cap, bilan.get('passif_total', 0), 0)
        X5 = safe_ratio(compte_resultat.get('chiffre_affaires', 0), bilan['actif_total'], 0)
        
        z_score = 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 1.0*X5
        ratios['altman_z_score'] = z_score
        
        if z_score > 2.99:
            ratios['altman_interpretation'] = "Sûr"
        elif z_score > 1.81:
            ratios['altman_interpretation'] = "Zone grise"
        else:
            ratios['altman_interpretation'] = "Risque de faillite"
    
    # DONNÉES INTERMÉDIAIRES
    ratios['ebitda'] = ebitda
    ratios['ebit'] = ebit
    ratios['nopat'] = nopat
    ratios['fcf'] = fcf
    ratios['working_capital'] = working_capital
    ratios['enterprise_value'] = enterprise_value
    ratios['market_cap'] = market_cap
    ratios['capital_investi'] = capital_investi
    
    return ratios

def calculate_piotroski_score(symbole, annee, financial_data):
    score = 0
    details = []
    
    current_key = f"{symbole}_{annee}"
    if current_key not in financial_data:
        return None, []
    
    current = financial_data[current_key]
    prev_key = f"{symbole}_{annee-1}"
    has_prev = prev_key in financial_data
    prev = financial_data.get(prev_key)
    
    # RENTABILITÉ (4 points)
    if current['compte_resultat'].get('resultat_net', 0) > 0:
        score += 1
        details.append("✅ Résultat net positif (+1)")
    else:
        details.append("❌ Résultat net négatif (0)")
    
    if current['flux_tresorerie'].get('flux_exploitation', 0) > 0:
        score += 1
        details.append("✅ Flux exploitation positifs (+1)")
    else:
        details.append("❌ Flux exploitation négatifs (0)")
    
    flux_exp = current['flux_tresorerie'].get('flux_exploitation', 0)
    res_net = current['compte_resultat'].get('resultat_net', 1)
    if flux_exp > res_net:
        score += 1
        details.append("✅ Qualité bénéfices élevée (+1)")
    else:
        details.append("❌ Qualité bénéfices faible (0)")
    
    if has_prev:
        roa_current = current['ratios'].get('roa', 0)
        roa_prev = prev['ratios'].get('roa', 0)
        if roa_current > roa_prev:
            score += 1
            details.append(f"✅ ROA amélioration ({roa_prev:.2f}% → {roa_current:.2f}%) (+1)")
        else:
            details.append("❌ ROA en baisse (0)")
    
    # LEVIER (3 points)
    if has_prev:
        dette_current = current['bilan'].get('dettes_totales', 0)
        dette_prev = prev['bilan'].get('dettes_totales', 0)
        if dette_current < dette_prev:
            score += 1
            details.append("✅ Réduction dette (+1)")
        else:
            details.append("❌ Dette augmentée (0)")
        
        liq_current = current['ratios'].get('ratio_liquidite_generale', 0)
        liq_prev = prev['ratios'].get('ratio_liquidite_generale', 0)
        if liq_current > liq_prev:
            score += 1
            details.append("✅ Liquidité améliorée (+1)")
        else:
            details.append("❌ Liquidité baisse (0)")
        
        actions_current = current['bilan'].get('nb_actions', 0)
        actions_prev = prev['bilan'].get('nb_actions', 0)
        if actions_current <= actions_prev:
            score += 1
            details.append("✅ Pas d'émission actions (+1)")
        else:
            details.append("❌ Dilution actions (0)")
    
    # EFFICACITÉ (2 points)
    if has_prev:
        marge_current = current['ratios'].get('marge_ebitda', 0)
        marge_prev = prev['ratios'].get('marge_ebitda', 0)
        if marge_current > marge_prev:
            score += 1
            details.append("✅ Marge améliorée (+1)")
        else:
            details.append("❌ Marge baisse (0)")
        
        rot_current = current['ratios'].get('rotation_actifs', 0)
        rot_prev = prev['ratios'].get('rotation_actifs', 0)
        if rot_current > rot_prev:
            score += 1
            details.append("✅ Rotation actifs améliorée (+1)")
        else:
            details.append("❌ Rotation actifs baisse (0)")
    
    return score, details

def detecter_alertes(ratios, bilan):
    alertes = []
    
    # CRITIQUES
    if ratios.get('ratio_liquidite_generale', 2) < 1:
        alertes.append({
            'niveau': '🔴 CRITIQUE',
            'message': 'Risque liquidité imminent - Ratio < 1',
            'valeur': ratios.get('ratio_liquidite_generale', 0)
        })
    
    if ratios.get('debt_to_ebitda', 0) > 5:
        alertes.append({
            'niveau': '🔴 CRITIQUE',
            'message': 'Endettement excessif - Dette/EBITDA > 5',
            'valeur': ratios.get('debt_to_ebitda', 0)
        })
    
    if bilan.get('capitaux_propres', 0) < 0:
        alertes.append({
            'niveau': '🔴 CRITIQUE',
            'message': 'Capitaux propres négatifs - Insolvabilité',
            'valeur': bilan.get('capitaux_propres', 0)
        })
    
    if ratios.get('altman_z_score', 3) < 1.81:
        alertes.append({
            'niveau': '🔴 CRITIQUE',
            'message': f"Z-Score: {ratios.get('altman_interpretation', 'Risque élevé')}",
            'valeur': ratios.get('altman_z_score', 0)
        })
    
    # IMPORTANTS
    if ratios.get('roe', 0) < 5:
        alertes.append({
            'niveau': '🟠 IMPORTANT',
            'message': 'Rentabilité très faible - ROE < 5%',
            'valeur': ratios.get('roe', 0)
        })
    
    if ratios.get('couverture_interets', 0) < 2:
        alertes.append({
            'niveau': '🟠 IMPORTANT',
            'message': 'Difficulté couvrir intérêts - Ratio < 2',
            'valeur': ratios.get('couverture_interets', 0)
        })
    
    # ATTENTION
    if ratios.get('ratio_liquidite_generale', 2) < 1.5:
        alertes.append({
            'niveau': '🟡 ATTENTION',
            'message': 'Liquidité limite - Ratio 1-1.5',
            'valeur': ratios.get('ratio_liquidite_generale', 0)
        })
    
    return alertes

def calculate_valuation_multiples(symbole, annee, ratios_entreprise, financial_data):
    secteur_multiples = {'per': [], 'price_to_book': [], 'ev_ebitda': [], 'ev_sales': []}
    
    for key, data in financial_data.items():
        if key == f"{symbole}_{annee}":
            continue
        
        ratios = data.get('ratios', {})
        
        # FILTRES STRICTS
        if ratios.get('per') and 5 < ratios['per'] < 30:
            secteur_multiples['per'].append(ratios['per'])
        
        if ratios.get('price_to_book') and 0.5 < ratios['price_to_book'] < 10:
            secteur_multiples['price_to_book'].append(ratios['price_to_book'])
        
        if ratios.get('ev_ebitda') and 3 < ratios['ev_ebitda'] < 20:
            secteur_multiples['ev_ebitda'].append(ratios['ev_ebitda'])
        
        if ratios.get('ev_sales') and 0.5 < ratios['ev_sales'] < 5:
            secteur_multiples['ev_sales'].append(ratios['ev_sales'])
    
    medianes = {}
    for key, values in secteur_multiples.items():
        if len(values) >= 2:
            medianes[f"{key}_median"] = np.median(values)
    
    valorisations = {}
    
    # P/E
    if 'per_median' in medianes:
        bpa = ratios_entreprise.get('benefice_par_action', 0)
        if bpa and bpa > 0:
            juste_valeur_per = medianes['per_median'] * bpa
            valorisations['juste_valeur_per'] = juste_valeur_per
            cours_actuel = ratios_entreprise.get('cours_action', 0)
            if cours_actuel > 0:
                valorisations['ecart_per'] = ((juste_valeur_per - cours_actuel) / cours_actuel) * 100
    
    # P/B
    if 'price_to_book_median' in medianes:
        cpa = ratios_entreprise.get('capitaux_propres_par_action', 0)
        if cpa and cpa > 0:
            juste_valeur_pb = medianes['price_to_book_median'] * cpa
            valorisations['juste_valeur_pb'] = juste_valeur_pb
            cours_actuel = ratios_entreprise.get('cours_action', 0)
            if cours_actuel > 0:
                valorisations['ecart_pb'] = ((juste_valeur_pb - cours_actuel) / cours_actuel) * 100
    
    # EV/EBITDA
    if 'ev_ebitda_median' in medianes and ratios_entreprise.get('ebitda'):
        ev_juste = medianes['ev_ebitda_median'] * ratios_entreprise['ebitda']
        dettes = ratios_entreprise.get('dettes_totales', 0)
        tresorerie = ratios_entreprise.get('tresorerie', 0)
        juste_valeur_ev = ev_juste - dettes + tresorerie
        nb_actions = ratios_entreprise.get('nb_actions', 0)
        if nb_actions > 0:
            juste_valeur_ev_par_action = juste_valeur_ev / nb_actions
            valorisations['juste_valeur_ev_ebitda'] = juste_valeur_ev_par_action
            cours_actuel = ratios_entreprise.get('cours_action', 0)
            if cours_actuel > 0:
                valorisations['ecart_ev_ebitda'] = ((juste_valeur_ev_par_action - cours_actuel) / cours_actuel) * 100
    
    valorisations['medianes_secteur'] = medianes
    
    ecarts = [v for k, v in valorisations.items() if k.startswith('ecart_')]
    if ecarts:
        valorisations['potentiel_moyen'] = np.mean(ecarts)
        valorisations['potentiel_median'] = np.median(ecarts)
        potentiel = valorisations['potentiel_median']
        
        if potentiel > 20:
            valorisations['recommandation'] = "ACHAT FORT"
            valorisations['justification'] = f"Sous-évalué de {potentiel:.1f}%"
        elif potentiel > 10:
            valorisations['recommandation'] = "ACHAT"
            valorisations['justification'] = f"Potentiel {potentiel:.1f}%"
        elif potentiel > -10:
            valorisations['recommandation'] = "CONSERVER"
            valorisations['justification'] = "Valorisation juste"
        elif potentiel > -20:
            valorisations['recommandation'] = "VENTE"
            valorisations['justification'] = f"Surévalué de {abs(potentiel):.1f}%"
        else:
            valorisations['recommandation'] = "VENTE FORTE"
            valorisations['justification'] = f"Fortement surévalué {abs(potentiel):.1f}%"
    
    return valorisations

def calculate_financial_projections(symbole, financial_data, annees_projection=3):
    historique = []
    for key, data in financial_data.items():
        if data.get('symbole') == symbole:
            annee = data.get('annee')
            ca = data.get('compte_resultat', {}).get('chiffre_affaires', 0)
            rn = data.get('compte_resultat', {}).get('resultat_net', 0)
            if ca > 0 and rn != 0:
                historique.append({'annee': int(annee), 'ca': ca, 'resultat_net': rn})
    
    if len(historique) < 2:
        return {"erreur": "Historique insuffisant (min 2 ans)"}
    
    historique = sorted(historique, key=lambda x: x['annee'])
    annees = np.array([h['annee'] for h in historique]).reshape(-1, 1)
    ca_values = np.array([h['ca'] for h in historique])
    rn_values = np.array([h['resultat_net'] for h in historique])
    
    # TCAM
    def calcul_tcam(val_debut, val_fin, nb_annees):
        if val_debut <= 0:
            return 0
        return (pow(val_fin / val_debut, 1/nb_annees) - 1) * 100
    
    tcam_ca = calcul_tcam(ca_values[0], ca_values[-1], len(ca_values) - 1)
    tcam_rn = calcul_tcam(abs(rn_values[0]), abs(rn_values[-1]), len(rn_values) - 1) if rn_values[0] != 0 else 0
    
    # RÉGRESSION
    model_ca = LinearRegression()
    model_ca.fit(annees, ca_values)
    r2_ca = model_ca.score(annees, ca_values)
    
    model_rn = LinearRegression()
    model_rn.fit(annees, rn_values)
    r2_rn = model_rn.score(annees, rn_values)
    
    # PROJECTIONS avec pondération par R²
    projections = []
    # PARTIE 2/3 - À ajouter après calculate_financial_projections

    derniere_annee = historique[-1]['annee']
    dernier_ca = historique[-1]['ca']
    dernier_rn = historique[-1]['resultat_net']
    
    # Pondération dynamique basée sur R²
    poids_tcam = 0.3
    poids_reg_ca = 0.7 * r2_ca
    poids_reg_rn = 0.7 * r2_rn
    
    poids_total_ca = poids_tcam + poids_reg_ca
    poids_total_rn = poids_tcam + poids_reg_rn
    
    for i in range(1, annees_projection + 1):
        annee_future = derniere_annee + i
        
        ca_tcam = dernier_ca * pow(1 + tcam_ca/100, i)
        rn_tcam = dernier_rn * pow(1 + tcam_rn/100, i)
        
        ca_reg = model_ca.predict([[annee_future]])[0]
        rn_reg = model_rn.predict([[annee_future]])[0]
        
        ca_projete = (poids_tcam * ca_tcam + poids_reg_ca * ca_reg) / poids_total_ca
        rn_projete = (poids_tcam * rn_tcam + poids_reg_rn * rn_reg) / poids_total_rn
        
        projections.append({
            'annee': int(annee_future),
            'ca_projete': float(ca_projete),
            'rn_projete': float(rn_projete),
            'ca_optimiste': float(ca_projete * 1.15),
            'ca_pessimiste': float(ca_projete * 0.85),
            'marge_nette_projetee': float((rn_projete / ca_projete * 100) if ca_projete > 0 else 0)
        })
    
    return {
        'historique': historique,
        'tcam_ca': float(tcam_ca),
        'tcam_rn': float(tcam_rn),
        'r2_ca': float(r2_ca),
        'r2_rn': float(r2_rn),
        'projections': projections,
        'methode': f'Pondération dynamique (TCAM {poids_tcam*100:.0f}% + Régression {poids_reg_ca*100:.0f}%)'
    }

# ===========================
# SCRAPING BRVM
# ===========================

@st.cache_data(ttl=300)
def scrape_brvm_data():
    sectors = [
        ("https://www.brvm.org/fr/cours-actions/0", "Tous les titres"),
        ("https://www.brvm.org/fr/cours-actions/194", "Consommation de Base"),
        ("https://www.brvm.org/fr/cours-actions/195", "Consommation Cyclique"),
        ("https://www.brvm.org/fr/cours-actions/196", "Financier"),
        ("https://www.brvm.org/fr/cours-actions/197", "Industriel"),
        ("https://www.brvm.org/fr/cours-actions/198", "Services Publics"),
        ("https://www.brvm.org/fr/cours-actions/199", "Technologie"),
        ("https://www.brvm.org/fr/cours-actions/200", "Autres")
    ]
    
    all_data = []
    
    for url, secteur in sectors:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            
            response = requests.get(url, headers=headers, timeout=15, verify=False)
            
            if response.status_code != 200:
                continue
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            table = None
            for t in soup.find_all('table'):
                headers_list = [th.get_text(strip=True) for th in t.find_all('th')]
                if 'Symbole' in headers_list and 'Nom' in headers_list:
                    table = t
                    break
            
            if not table:
                tables = soup.find_all('table')
                if tables:
                    table = tables[0]
            
            if not table:
                continue
            
            headers_list = [th.get_text(strip=True) for th in table.find_all('th')]
            
            if not headers_list:
                headers_list = ['Symbole', 'Nom', 'Volume', 'Cours veille (FCFA)', 
                              'Cours Ouverture (FCFA)', 'Cours Clôture (FCFA)', 'Variation (%)']
            
            data = []
            for row in table.find_all('tr'):
                cells = row.find_all(['td', 'th'])
                if cells and cells[0].name == 'td':
                    row_data = [cell.get_text(strip=True) for cell in cells]
                    
                    if len(row_data) >= 6:
                        if len(row_data) < len(headers_list):
                            row_data.extend([''] * (len(headers_list) - len(row_data)))
                        elif len(row_data) > len(headers_list):
                            row_data = row_data[:len(headers_list)]
                        
                        row_data.append(secteur)
                        data.append(row_data)
            
            if data:
                df_sector = pd.DataFrame(data, columns=headers_list + ['Secteur'])
                df_sector = clean_dataframe(df_sector)
                all_data.append(df_sector)
                
        except Exception as e:
            continue
    
    if all_data:
        df_combined = pd.concat(all_data, ignore_index=True)
        if 'Symbole' in df_combined.columns:
            df_combined = df_combined.drop_duplicates(subset='Symbole', keep='first')
        return df_combined
    else:
        st.error("❌ Aucune donnée récupérée")
        return None

def clean_dataframe(df):
    df = df.copy()
    if df.empty:
        return df
    
    df.columns = [col.strip() for col in df.columns]
    
    numeric_columns = []
    for col in df.columns:
        if any(keyword in col for keyword in ['Cours', 'Volume', 'Variation', 'Capitalisation']):
            numeric_columns.append(col)
    
    for col in numeric_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.')
            df[col] = df[col].str.replace(' ', '')
            df[col] = df[col].str.replace('FCFA', '')
            df[col] = df[col].str.replace('F', '')
            df[col] = df[col].str.replace('CFA', '')
            df[col] = df[col].str.replace('%', '')
            df[col] = df[col].str.replace('€', '')
            df[col] = df[col].str.replace('$', '')
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    if 'Symbole' in df.columns:
        df = df.sort_values('Symbole').reset_index(drop=True)
    
    return df

# ===========================
# SECTION DÉVELOPPEUR
# ===========================

def developer_section():
    st.title("🔐 Section Développeur - Gestion des Données Financières")
    
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
    
    col_refresh1, col_refresh2 = st.columns([3, 1])
    with col_refresh1:
        st.info("💡 Les cours sont automatiquement récupérés depuis BRVM")
    with col_refresh2:
        if st.button("🔄 Actualiser les cours", use_container_width=True):
            st.cache_data.clear()
            st.success("Cours actualisés!")
            st.rerun()
    
    with st.spinner("Chargement des cours BRVM..."):
        df_brvm = scrape_brvm_data()
    
    financial_data = init_storage()
    
    col1, col2 = st.columns([3, 1])
    with col1:
        symbole = st.text_input("Symbole de l'action (ex: SNTS, SGBC, BICC)", key="symbole_input").upper()
    with col2:
        annee = st.number_input("Année", min_value=2015, max_value=2030, value=2024)
    
    if symbole:
        symbole_existe = False
        cours_brvm = 0
        nom_societe = ""
        variation = 0
        
        if df_brvm is not None and 'Symbole' in df_brvm.columns:
            if symbole in df_brvm['Symbole'].values:
                symbole_existe = True
                ligne = df_brvm[df_brvm['Symbole'] == symbole].iloc[0]
                
                if 'Nom' in df_brvm.columns:
                    nom_societe = ligne['Nom']
                
                for col in df_brvm.columns:
                    if 'Cours' in col and ('Clôture' in col or 'Cloture' in col):
                        try:
                            cours_brvm = float(ligne[col])
                            break
                        except:
                            continue
                
                if cours_brvm == 0:
                    for col in df_brvm.columns:
                        if 'Cours' in col:
                            try:
                                cours_brvm = float(ligne[col])
                                break
                            except:
                                continue
                
                if 'Variation (%)' in df_brvm.columns:
                    try:
                        variation = float(ligne['Variation (%)'])
                    except:
                        variation = 0
        
        st.subheader(f"📊 Données financières pour {symbole} - {annee}")
        
        if symbole_existe and nom_societe:
            if variation > 0:
                st.success(f"✅ {nom_societe} - Cours: {cours_brvm:,.0f} FCFA (+{variation}%)")
            elif variation < 0:
                st.warning(f"⚠️ {nom_societe} - Cours: {cours_brvm:,.0f} FCFA ({variation}%)")
            else:
                st.info(f"ℹ️ {nom_societe} - Cours: {cours_brvm:,.0f} FCFA")
        elif symbole_existe:
            st.info(f"ℹ️ Symbole {symbole} trouvé - Cours: {cours_brvm:,.0f} FCFA")
        else:
            st.warning(f"⚠️ Symbole {symbole} non trouvé dans les données BRVM")
        
        tab1, tab2, tab3, tab4 = st.tabs(["📈 Bilan", "💰 Compte de Résultat", "💵 Flux de Trésorerie", "📊 Ratios Calculés"])
        
        data_key = f"{symbole}_{annee}"
        
        existing_data = financial_data.get(data_key, {
            'bilan': {},
            'compte_resultat': {},
            'flux_tresorerie': {},
            'ratios': {},
            'last_update': None
        })
        
        with tab1:
            st.markdown("### 🏦 BILAN")
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.markdown("**ACTIF**")
                actif_immobilise = st.number_input("Actif Immobilisé (FCFA)", 
                                                  value=float(existing_data.get('bilan', {}).get('actif_immobilise', 0)), 
                                                  step=1000000.0, 
                                                  format="%.0f",
                                                  key=f"actif_immo_{data_key}")
                actif_courant = st.number_input("Actif Courant (FCFA)", 
                                               value=float(existing_data.get('bilan', {}).get('actif_courant', 0)), 
                                               step=1000000.0,
                                               format="%.0f",
                                               key=f"actif_courant_{data_key}")
                stocks = st.number_input("Stocks (FCFA)", 
                                        value=float(existing_data.get('bilan', {}).get('stocks', 0)), 
                                        step=1000000.0,
                                        format="%.0f",
                                        key=f"stocks_{data_key}")
                creances = st.number_input("Créances (FCFA)", 
                                          value=float(existing_data.get('bilan', {}).get('creances', 0)), 
                                          step=1000000.0,
                                          format="%.0f",
                                          key=f"creances_{data_key}")
                tresorerie = st.number_input("Trésorerie et équivalents (FCFA)", 
                                            value=float(existing_data.get('bilan', {}).get('tresorerie', 0)), 
                                            step=1000000.0,
                                            format="%.0f",
                                            key=f"tresorerie_{data_key}")
                
                actif_total = actif_immobilise + actif_courant
                st.metric("**ACTIF TOTAL**", f"{actif_total:,.0f} FCFA")
            
            with col_b:
                st.markdown("**PASSIF**")
                capitaux_propres = st.number_input("Capitaux Propres (FCFA)", 
                                                  value=float(existing_data.get('bilan', {}).get('capitaux_propres', 0)), 
                                                  step=1000000.0,
                                                  format="%.0f",
                                                  key=f"cap_propres_{data_key}")
                dettes_long_terme = st.number_input("Dettes Long Terme (FCFA)", 
                                                   value=float(existing_data.get('bilan', {}).get('dettes_long_terme', 0)), 
                                                   step=1000000.0,
                                                   format="%.0f",
                                                   key=f"dettes_lt_{data_key}")
                passif_courant = st.number_input("Passif Courant (FCFA)", 
                                                value=float(existing_data.get('bilan', {}).get('passif_courant', 0)), 
                                                step=1000000.0,
                                                format="%.0f",
                                                key=f"passif_courant_{data_key}")
                
                dettes_totales = dettes_long_terme + passif_courant
                passif_total = capitaux_propres + dettes_totales
                
                st.metric("**PASSIF TOTAL**", f"{passif_total:,.0f} FCFA")
                
                if abs(actif_total - passif_total) > 1:
                    st.error(f"⚠️ Bilan non équilibré ! Différence: {actif_total - passif_total:,.0f} FCFA")
                else:
                    st.success("✅ Bilan équilibré")
            
            st.markdown("**Informations Marché**")
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                if symbole_existe and cours_brvm > 0:
                    cours_action = st.number_input(
                        f"Cours de {symbole} (FCFA)", 
                        value=float(cours_brvm), 
                        step=100.0, 
                        format="%.0f",
                        key=f"cours_{data_key}",
                        help=f"Cours actuel sur BRVM: {cours_brvm:,.0f} FCFA"
                    )
                    st.caption(f"📈 Cours BRVM: {cours_brvm:,.0f} FCFA")
                else:
                    cours_action = st.number_input(
                        f"Cours de {symbole} (FCFA)", 
                        value=float(existing_data.get('bilan', {}).get('cours_action', 0)), 
                        step=100.0,
                        format="%.0f",
                        key=f"cours_{data_key}",
                        help="Symbole non trouvé - saisie manuelle requise"
                    )
            
            with col_m2:
                nb_actions = st.number_input("Nombre d'actions", 
                                            value=int(existing_data.get('bilan', {}).get('nb_actions', 0)), 
                                            step=1000,
                                            key=f"nb_actions_{data_key}")
            
            with col_m3:
                if nb_actions > 0 and capitaux_propres > 0:
                    cap_propres_par_action = capitaux_propres / nb_actions
                    st.metric("Cap. Propres / Action", f"{cap_propres_par_action:,.0f} FCFA")
                else:
                    cap_propres_par_action = 0
            
            bilan_data = {
                'actif_immobilise': float(actif_immobilise),
                'actif_courant': float(actif_courant),
                'stocks': float(stocks),
                'creances': float(creances),
                'tresorerie': float(tresorerie),
                'actif_total': float(actif_total),
                'capitaux_propres': float(capitaux_propres),
                'dettes_long_terme': float(dettes_long_terme),
                'passif_courant': float(passif_courant),
                'dettes_totales': float(dettes_totales),
                'passif_total': float(passif_total),
                'cours_action': float(cours_action),
                'nb_actions': int(nb_actions),
                'capitaux_propres_par_action': float(cap_propres_par_action),
                'cours_source': 'auto' if (symbole_existe and cours_brvm > 0) else 'manual'
            }
        
        with tab2:
            st.markdown("### 💰 COMPTE DE RÉSULTAT")
            
            chiffre_affaires = st.number_input("Chiffre d'Affaires (FCFA)", 
                                              value=float(existing_data.get('compte_resultat', {}).get('chiffre_affaires', 0)), 
                                              step=1000000.0,
                                              format="%.0f",
                                              key=f"ca_{data_key}")
            charges_exploitation = st.number_input("Charges d'Exploitation (FCFA)", 
                                                  value=float(existing_data.get('compte_resultat', {}).get('charges_exploitation', 0)), 
                                                  step=1000000.0,
                                                  format="%.0f",
                                                  key=f"charges_exp_{data_key}")
            
            # Nouvelle entrée pour les dotations aux amortissements
            dotations_amortissements = st.number_input("Dotations aux Amortissements (FCFA)", 
                                                      value=float(existing_data.get('compte_resultat', {}).get('dotations_amortissements', 0)), 
                                                      step=100000.0,
                                                      format="%.0f",
                                                      key=f"dotations_amort_{data_key}",
                                                      help="Requis pour calcul correct de l'EBITDA")
            
            resultat_exploitation = chiffre_affaires - charges_exploitation
            st.metric("Résultat d'Exploitation", f"{resultat_exploitation:,.0f} FCFA")
            
            charges_financieres = st.number_input("Charges Financières (FCFA)", 
                                                 value=float(existing_data.get('compte_resultat', {}).get('charges_financieres', 0)), 
                                                 step=100000.0,
                                                 format="%.0f",
                                                 key=f"charges_fin_{data_key}")
            produits_financiers = st.number_input("Produits Financiers (FCFA)", 
                                                 value=float(existing_data.get('compte_resultat', {}).get('produits_financiers', 0)), 
                                                 step=100000.0,
                                                 format="%.0f",
                                                 key=f"prod_fin_{data_key}")
            
            resultat_financier = produits_financiers - charges_financieres
            st.metric("Résultat Financier", f"{resultat_financier:,.0f} FCFA")
            
            resultat_avant_impot = resultat_exploitation + resultat_financier
            st.metric("Résultat Avant Impôt", f"{resultat_avant_impot:,.0f} FCFA")
            
            impots = st.number_input("Impôts sur les sociétés (FCFA)", 
                                    value=float(existing_data.get('compte_resultat', {}).get('impots', 0)), 
                                    step=100000.0,
                                    format="%.0f",
                                    key=f"impots_{data_key}")
            
            resultat_net = resultat_avant_impot - impots
            st.metric("**RÉSULTAT NET**", f"{resultat_net:,.0f} FCFA", delta=None)
            
            if nb_actions > 0:
                benefice_par_action = resultat_net / nb_actions
                st.metric("Bénéfice par Action (BPA)", f"{benefice_par_action:,.2f} FCFA")
            else:
                benefice_par_action = 0
            
            compte_resultat_data = {
                'chiffre_affaires': float(chiffre_affaires),
                'charges_exploitation': float(charges_exploitation),
                'dotations_amortissements': float(dotations_amortissements),
                'resultat_exploitation': float(resultat_exploitation),
                'charges_financieres': float(charges_financieres),
                'produits_financiers': float(produits_financiers),
                'resultat_financier': float(resultat_financier),
                'resultat_avant_impot': float(resultat_avant_impot),
                'impots': float(impots),
                'resultat_net': float(resultat_net),
                'benefice_par_action': float(benefice_par_action)
            }
        
        with tab3:
            st.markdown("### 💵 TABLEAU DES FLUX DE TRÉSORERIE")
            
            st.markdown("**Flux de Trésorerie d'Exploitation**")
            flux_exploitation = st.number_input("Flux d'Exploitation (FCFA)", 
                                               value=float(existing_data.get('flux_tresorerie', {}).get('flux_exploitation', 0)), 
                                               step=1000000.0,
                                               format="%.0f",
                                               key=f"flux_exp_{data_key}")
            
            st.markdown("**Flux de Trésorerie d'Investissement**")
            flux_investissement = st.number_input("Flux d'Investissement (FCFA)", 
                                                 value=float(existing_data.get('flux_tresorerie', {}).get('flux_investissement', 0)), 
                                                 step=1000000.0,
                                                 format="%.0f",
                                                 key=f"flux_inv_{data_key}")
            
            st.markdown("**Flux de Trésorerie de Financement**")
            flux_financement = st.number_input("Flux de Financement (FCFA)", 
                                              value=float(existing_data.get('flux_tresorerie', {}).get('flux_financement', 0)), 
                                              step=1000000.0,
                                              format="%.0f",
                                              key=f"flux_fin_{data_key}")
            
            variation_tresorerie = flux_exploitation + flux_investissement + flux_financement
            st.metric("**Variation de Trésorerie**", f"{variation_tresorerie:,.0f} FCFA")
            
            flux_tresorerie_data = {
                'flux_exploitation': float(flux_exploitation),
                'flux_investissement': float(flux_investissement),
                'flux_financement': float(flux_financement),
                'variation_tresorerie': float(variation_tresorerie)
            }
        
        with tab4:
            st.markdown("### 📊 RATIOS FINANCIERS CALCULÉS")
            
            ratios = calculate_enhanced_financial_ratios(bilan_data, compte_resultat_data, flux_tresorerie_data)
            
            # Validation
            errors, warnings_list = validate_financial_data(bilan_data, compte_resultat_data)
            
            if errors:
                for error in errors:
                    st.error(error)
            
            if warnings_list:
                for warning in warnings_list:
                    st.warning(warning)
            
            if ratios:
                col_r1, col_r2, col_r3 = st.columns(3)
                
                with col_r1:
                    st.markdown("**📈 RENTABILITÉ**")
                    if 'marge_nette' in ratios:
                        st.metric("Marge Nette", f"{ratios['marge_nette']:.2f}%")
                    if 'marge_ebitda' in ratios:
                        st.metric("Marge EBITDA", f"{ratios['marge_ebitda']:.2f}%")
                    if 'roe' in ratios:
                        st.metric("ROE", f"{ratios['roe']:.2f}%")
                    if 'roic' in ratios:
                        st.metric("ROIC", f"{ratios['roic']:.2f}%")
                
                with col_r2:
                    st.markdown("**💧 LIQUIDITÉ & DETTE**")
                    if 'ratio_liquidite_generale' in ratios:
                        st.metric("Liquidité Générale", f"{ratios['ratio_liquidite_generale']:.2f}")
                    if 'debt_to_ebitda' in ratios:
                        st.metric("Dette/EBITDA", f"{ratios['debt_to_ebitda']:.2f}")
                    if 'couverture_interets' in ratios:
                        st.metric("Couverture Intérêts", f"{ratios['couverture_interets']:.2f}")
                
                with col_r3:
                    st.markdown("**📊 MARCHÉ**")
                    if 'per' in ratios:
                        st.metric("PER", f"{ratios['per']:.2f}")
                    if 'price_to_book' in ratios:
                        st.metric("Price to Book", f"{ratios['price_to_book']:.2f}")
                    if 'ev_ebitda' in ratios:
                        st.metric("EV/EBITDA", f"{ratios['ev_ebitda']:.2f}")
                
                # Z-Score d'Altman
                if 'altman_z_score' in ratios:
                    st.markdown("---")
                    st.markdown("### 🎯 Z-Score d'Altman (Prédiction Faillite)")
                    col_z1, col_z2 = st.columns([1, 2])
                    with col_z1:
                        st.metric("Z-Score", f"{ratios['altman_z_score']:.2f}")
                    with col_z2:
                        interp = ratios.get('altman_interpretation', '')
                        if interp == "Sûr":
                            st.success(f"✅ **{interp}** - Risque de faillite très faible")
                        elif interp == "Zone grise":
                            st.warning(f"⚠️ **{interp}** - Surveillance nécessaire")
                        else:
                            st.error(f"🔴 **{interp}** - Attention maximale requise")
                
                # Alertes
                alertes = detecter_alertes(ratios, bilan_data)
                if alertes:
                    st.markdown("---")
                    st.markdown("### 🚨 Alertes Financières")
                    for alerte in alertes:
                        if '🔴' in alerte['niveau']:
                            st.error(f"{alerte['niveau']}: {alerte['message']}")
                        elif '🟠' in alerte['niveau']:
                            st.warning(f"{alerte['niveau']}: {alerte['message']}")
                        else:
                            st.info(f"{alerte['niveau']}: {alerte['message']}")
            else:
                st.warning("Remplissez les données pour voir les ratios")
        
        # SAUVEGARDE
        st.markdown("---")
        col_save1, col_save2, col_save3 = st.columns([1, 1, 1])
        
        with col_save1:
            if st.button("💾 Sauvegarder", type="primary", use_container_width=True):
# PARTIE 3/3 - FINALE - À ajouter après la Partie 2

                data_to_save = {
                    'bilan': bilan_data,
                    'compte_resultat': compte_resultat_data,
                    'flux_tresorerie': flux_tresorerie_data,
                    'ratios': ratios
                }
                
                if save_financial_data(symbole, annee, data_to_save):
                    st.success(f"✅ Données sauvegardées pour {symbole} - {annee}")
                    st.session_state.financial_data = load_all_financial_data()
                    st.rerun()
        
        with col_save2:
            if st.button("🗑️ Supprimer", use_container_width=True):
                if delete_financial_data(symbole, annee):
                    st.success(f"Données supprimées pour {symbole} - {annee}")
                    st.session_state.financial_data = load_all_financial_data()
                    st.rerun()
        
        with col_save3:
            if st.button("🔄 Actualiser", use_container_width=True):
                st.session_state.financial_data = load_all_financial_data()
                st.success("Données actualisées")
                st.rerun()
        
        # Données sauvegardées
        st.markdown("---")
        st.subheader("📚 Données Sauvegardées (Cloud)")
        
        financial_data = init_storage()
        if financial_data:
            saved_data = []
            for key, data in financial_data.items():
                if isinstance(data, dict):
                    saved_data.append({
                        'Symbole': data.get('symbole', 'N/A'),
                        'Année': data.get('annee', 'N/A'),
                        'Dernière MAJ': data.get('last_update', 'N/A')[:19] if data.get('last_update') else 'N/A'
                    })
            
            if saved_data:
                df_saved = pd.DataFrame(saved_data)
                st.dataframe(df_saved, use_container_width=True)
                st.caption(f"Total: {len(saved_data)} enregistrements")
        else:
            st.info("Aucune donnée sauvegardée")

# ===========================
# AFFICHAGE DONNÉES BRVM
# ===========================

def display_brvm_data():
    st.sidebar.header("⚙️ Paramètres")
    
    if st.sidebar.button("🔄 Actualiser les données"):
        st.cache_data.clear()
        st.rerun()
    
    with st.spinner("Récupération des données BRVM..."):
        df = scrape_brvm_data()
    
    if df is not None:
        st.subheader("📈 Statistiques du marché")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Nombre total de titres", len(df))
        
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
        
        # Filtre par secteur
        st.markdown("---")
        st.subheader("🔍 Filtrage par secteur")
        
        if 'Secteur' in df.columns:
            secteurs = ['Tous les secteurs'] + sorted(df['Secteur'].dropna().unique().tolist())
            secteur_selectionne = st.selectbox("Choisissez un secteur", secteurs)
            
            if secteur_selectionne != 'Tous les secteurs':
                df_filtre = df[df['Secteur'] == secteur_selectionne]
                st.info(f"📊 {secteur_selectionne}: {len(df_filtre)} titres")
            else:
                df_filtre = df
        else:
            df_filtre = df
            st.warning("Information secteurs non disponible")
        
        # Affichage
        st.subheader("📋 Cours des Actions")
        
        def color_variation(val):
            if isinstance(val, (int, float)):
                if val > 0:
                    return 'color: green; font-weight: bold'
                elif val < 0:
                    return 'color: red; font-weight: bold'
            return ''
        
        if 'Variation (%)' in df_filtre.columns:
            styled_df = df_filtre.style.map(color_variation, subset=['Variation (%)'])
            st.dataframe(styled_df, use_container_width=True, height=400)
        else:
            st.dataframe(df_filtre, use_container_width=True, height=400)
        
        # Analyse Fondamentale
        st.markdown("---")
        st.subheader("📊 Analyse Fondamentale par Titre")
        
        if 'Symbole' in df_filtre.columns:
            symboles_list = [''] + df_filtre['Symbole'].dropna().unique().tolist()
            symbole_selected = st.selectbox("Sélectionnez un titre", symboles_list)
            
            if symbole_selected:
                financial_data = init_storage()
                
                symbole_data = {}
                for key, data in financial_data.items():
                    if data.get('symbole') == symbole_selected:
                        symbole_data[data['annee']] = data
                
                if symbole_data:
                    st.success(f"✅ Données financières disponibles pour {symbole_selected}")
                    
                    annees = sorted(symbole_data.keys())
                    annee_selectionnee = st.selectbox("Sélectionnez l'année", annees, index=len(annees)-1)
                    
                    if annee_selectionnee:
                        data = symbole_data[annee_selectionnee]
                        
                        # RATIOS
                        st.markdown(f"### 📊 Ratios pour {symbole_selected} - {annee_selectionnee}")
                        
                        if 'ratios' in data:
                            ratios = data['ratios']
                            
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.markdown("**Rentabilité**")
                                if 'roe' in ratios:
                                    st.metric("ROE", f"{ratios['roe']:.2f}%")
                                if 'roic' in ratios:
                                    st.metric("ROIC", f"{ratios['roic']:.2f}%")
                                if 'marge_nette' in ratios:
                                    st.metric("Marge Nette", f"{ratios['marge_nette']:.2f}%")
                            
                            with col2:
                                st.markdown("**Liquidité & Dette**")
                                if 'ratio_liquidite_generale' in ratios:
                                    st.metric("Liquidité Générale", f"{ratios['ratio_liquidite_generale']:.2f}")
                                if 'debt_to_ebitda' in ratios:
                                    st.metric("Dette/EBITDA", f"{ratios['debt_to_ebitda']:.2f}")
                            
                            with col3:
                                st.markdown("**Marché**")
                                if 'per' in ratios:
                                    st.metric("PER", f"{ratios['per']:.2f}")
                                if 'ev_ebitda' in ratios:
                                    st.metric("EV/EBITDA", f"{ratios['ev_ebitda']:.2f}")
                            
                            # F-Score de Piotroski
                            st.markdown("---")
                            st.markdown("### 🎯 F-Score de Piotroski")
                            
                            score, details = calculate_piotroski_score(symbole_selected, annee_selectionnee, financial_data)
                            
                            if score is not None:
                                col_p1, col_p2 = st.columns([1, 3])
                                
                                with col_p1:
                                    st.metric("Score", f"{score}/9")
                                    if score >= 7:
                                        st.success("✅ Excellent")
                                    elif score >= 5:
                                        st.warning("⚠️ Moyen")
                                    else:
                                        st.error("🔴 Faible")
                                
                                with col_p2:
                                    st.markdown("**Détails du score:**")
                                    for detail in details[:5]:
                                        st.caption(detail)
                                    
                                    if len(details) > 5:
                                        with st.expander("Voir tous les critères"):
                                            for detail in details[5:]:
                                                st.caption(detail)
                            else:
                                st.info("Score non disponible (nécessite données année précédente)")
                            
                            # Alertes
                            st.markdown("---")
                            st.markdown("### 🚨 Alertes Financières")
                            
                            alertes = detecter_alertes(ratios, data['bilan'])
                            
                            if alertes:
                                for alerte in alertes[:3]:
                                    if '🔴' in alerte['niveau']:
                                        st.error(f"{alerte['niveau']}: {alerte['message']}")
                                    elif '🟠' in alerte['niveau']:
                                        st.warning(f"{alerte['niveau']}: {alerte['message']}")
                                    else:
                                        st.info(f"{alerte['niveau']}: {alerte['message']}")
                                
                                if len(alertes) > 3:
                                    with st.expander(f"Voir toutes les alertes ({len(alertes)})"):
                                        for alerte in alertes[3:]:
                                            st.caption(f"{alerte['niveau']}: {alerte['message']}")
                            else:
                                st.success("✅ Aucune alerte détectée - Situation financière saine")
                            
                            # Valorisation
                            st.markdown("---")
                            st.markdown("### 💹 Valorisation par Multiples")
                            
                            ratios_complets = {**data['bilan'], **data['compte_resultat'], **ratios}
                            valorisations = calculate_valuation_multiples(
                                symbole_selected, 
                                annee_selectionnee, 
                                ratios_complets,
                                financial_data
                            )
                            
                            if 'recommandation' in valorisations:
                                col_rec1, col_rec2 = st.columns([1, 2])
                                with col_rec1:
                                    if "ACHAT" in valorisations['recommandation']:
                                        st.success(f"**{valorisations['recommandation']}**")
                                    elif "VENTE" in valorisations['recommandation']:
                                        st.error(f"**{valorisations['recommandation']}**")
                                    else:
                                        st.warning(f"**{valorisations['recommandation']}**")
                                
                                with col_rec2:
                                    st.info(f"*{valorisations.get('justification', '')}*")
                                
                                # Détails valorisation
                                if st.checkbox("Voir les détails de valorisation"):
                                    col_v1, col_v2, col_v3 = st.columns(3)
                                    
                                    with col_v1:
                                        if 'juste_valeur_per' in valorisations:
                                            st.metric("Valeur juste (P/E)", 
                                                     f"{valorisations['juste_valeur_per']:,.0f} FCFA",
                                                     f"{valorisations.get('ecart_per', 0):.1f}%")
                                    
                                    with col_v2:
                                        if 'juste_valeur_pb' in valorisations:
                                            st.metric("Valeur juste (P/B)", 
                                                     f"{valorisations['juste_valeur_pb']:,.0f} FCFA",
                                                     f"{valorisations.get('ecart_pb', 0):.1f}%")
                                    
                                    with col_v3:
                                        if 'juste_valeur_ev_ebitda' in valorisations:
                                            st.metric("Valeur juste (EV/EBITDA)", 
                                                     f"{valorisations['juste_valeur_ev_ebitda']:,.0f} FCFA",
                                                     f"{valorisations.get('ecart_ev_ebitda', 0):.1f}%")
                            
                            # Projections
                            st.markdown("---")
                            st.markdown("### 📈 Projections Financières")
                            
                            projections = calculate_financial_projections(symbole_selected, financial_data)
                            
                            if 'projections' in projections:
                                df_proj = pd.DataFrame(projections['projections'])
                                
                                # Graphique
                                fig = go.Figure()
                                
                                # Historique
                                hist_annees = [h['annee'] for h in projections['historique']]
                                hist_ca = [h['ca'] for h in projections['historique']]
                                
                                fig.add_trace(go.Scatter(
                                    x=hist_annees,
                                    y=hist_ca,
                                    name='CA Historique',
                                    line=dict(color='blue', width=3),
                                    mode='lines+markers'
                                ))
                                
                                # Projections
                                fig.add_trace(go.Scatter(
                                    x=df_proj['annee'],
                                    y=df_proj['ca_projete'],
                                    name='CA Projeté',
                                    line=dict(color='green', width=3, dash='dash'),
                                    mode='lines+markers'
                                ))
                                
                                # Scénarios
                                fig.add_trace(go.Scatter(
                                    x=df_proj['annee'],
                                    y=df_proj['ca_optimiste'],
                                    name='Scénario Optimiste',
                                    line=dict(color='lightgreen', width=1, dash='dot'),
                                    mode='lines'
                                ))
                                
                                fig.add_trace(go.Scatter(
                                    x=df_proj['annee'],
                                    y=df_proj['ca_pessimiste'],
                                    name='Scénario Pessimiste',
                                    line=dict(color='orange', width=1, dash='dot'),
                                    mode='lines'
                                ))
                                
                                fig.update_layout(
                                    title=f"Projections CA - {symbole_selected}",
                                    xaxis_title="Année",
                                    yaxis_title="Chiffre d'Affaires (FCFA)",
                                    hovermode='x unified',
                                    height=400
                                )
                                
                                st.plotly_chart(fig, use_container_width=True)
                                
                                # Tableau
                                st.dataframe(df_proj.style.format({
                                    'ca_projete': '{:,.0f}',
                                    'rn_projete': '{:,.0f}',
                                    'ca_optimiste': '{:,.0f}',
                                    'ca_pessimiste': '{:,.0f}',
                                    'marge_nette_projetee': '{:.2f}%'
                                }), use_container_width=True)
                                
                                st.caption(f"Méthode: {projections.get('methode', '')}")
                                st.caption(f"TCAM CA: {projections.get('tcam_ca', 0):.2f}% | Fiabilité R²: {projections.get('r2_ca', 0):.2%}")
                            else:
                                st.warning(projections.get('erreur', 'Erreur de projection'))
                
                else:
                    st.warning(f"ℹ️ Aucune donnée pour {symbole_selected}")
                    st.info("Utilisez la Section Développeur pour saisir les données")
        
        # Export CSV
        st.markdown("---")
        st.subheader("💾 Export des données")
        
        csv = df_filtre.to_csv(index=False, sep=';', decimal=',')
        st.download_button(
            label="📥 Télécharger en CSV",
            data=csv,
            file_name=f"brvm_cours_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    else:
        st.warning("⚠️ Impossible de récupérer les données BRVM")
        st.info("Vérifiez votre connexion internet")

# ===========================
# INTERFACE PRINCIPALE
# ===========================

def main():
    st.title("📊 Analyse BRVM Pro - Édition Complète")
    st.caption("Analyse fondamentale avancée avec ratios corrigés, Z-Score d'Altman, F-Score de Piotroski")
    
    page = st.sidebar.radio(
        "Navigation",
        ["🏠 Accueil & Cours", "🔐 Section Développeur", "📚 Guide d'Utilisation", "ℹ️ À propos"]
    )
    
    if page == "🏠 Accueil & Cours":
        st.markdown("""
        ### Application d'analyse BRVM avec Stockage Cloud
        
        **✨ Nouveautés de cette version :**
        - ✅ **EBITDA corrigé** : Calcul exact avec amortissements
        - ✅ **ROIC corrigé** : Formule académique NOPAT/Capital investi
        - ✅ **Z-Score d'Altman** : Prédiction risque de faillite
        - ✅ **F-Score de Piotroski** : Qualité financière sur 9 points
        - ✅ **Système d'alertes** : Détection automatique des problèmes
        - ✅ **Projections avancées** : Scénarios optimiste/pessimiste/réaliste
        - ✅ **Valorisation stricte** : Filtres robustes (PER 5-30, EV/EBITDA 3-20)
        """)
        
        financial_data = init_storage()
        if financial_data:
            st.sidebar.success(f"📦 {len(financial_data)} analyses en cloud")
        
        display_brvm_data()
        
        st.markdown("---")
        st.caption(f"Source : BRVM | Cloud : Supabase | {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    elif page == "🔐 Section Développeur":
        developer_section()
    
    elif page == "📚 Guide d'Utilisation":
        st.header("📚 Guide d'Utilisation")
        
        with st.expander("🔍 Comment analyser une action ?", expanded=True):
            st.markdown("""
            **Étapes simples :**
            
            1. **Page Accueil** : Consultez les cours BRVM en temps réel
            2. **Sélectionner un titre** : Dans le menu déroulant "Analyse Fondamentale"
            3. **Consulter les ratios** : ROE, PER, Dette/EBITDA, etc.
            4. **Vérifier le F-Score** : Note sur 9 (7-9 = Excellent, 5-6 = Moyen, 0-4 = Faible)
            5. **Lire les alertes** : Signaux d'alerte automatiques
            6. **Voir la recommandation** : ACHAT / CONSERVER / VENTE
            """)
        
        with st.expander("📊 Comprendre les ratios clés"):
            st.markdown("""
            **Rentabilité :**
            - **ROE** : Rentabilité des capitaux propres (>15% = Excellent)
            - **ROIC** : Rentabilité du capital investi (>12% = Bon)
            - **Marge EBITDA** : Rentabilité opérationnelle (>20% = Très bon)
            
            **Liquidité :**
            - **Ratio de liquidité** : Capacité à payer dettes court terme (>1.5 = Sûr)
            - **Dette/EBITDA** : Années pour rembourser la dette (<3 = Bon)
            
            **Valorisation :**
            - **PER** : Prix / Bénéfice (10-20 = Normal pour BRVM)
            - **EV/EBITDA** : Multiple de valorisation (5-12 = Raisonnable)
            
            **Qualité :**
            - **Z-Score d'Altman** : >2.99 = Sûr, 1.81-2.99 = Zone grise, <1.81 = Risque
            - **F-Score de Piotroski** : 7-9 = Excellent, 5-6 = Moyen, 0-4 = Éviter
            """)
        
        with st.expander("🔐 Section Développeur - Saisir des données"):
            st.markdown("""
            **Mot de passe :** `dev_brvm_2024`
            
            **Données à saisir :**
            1. **Bilan** : Actif, Passif, Dettes, Capitaux propres
            2. **Compte de résultat** : CA, Charges, Résultat net, **Amortissements**
            3. **Flux de trésorerie** : Exploitation, Investissement, Financement
            
            ⚠️ **Important** : Les amortissements sont requis pour un calcul correct de l'EBITDA !
            
            Les cours sont **automatiquement récupérés** depuis BRVM.
            """)
        
        with st.expander("📈 Interpréter les projections"):
            st.markdown("""
            Les projections utilisent une **pondération dynamique** :
            - 30% TCAM (Taux de Croissance Annuel Moyen)
            - 70% Régression linéaire (pondéré par R²)
            
            **3 scénarios :**
            - 🟢 **Optimiste** : +15% sur projection
            - 🔵 **Réaliste** : Projection pondérée
            - 🟠 **Pessimiste** : -15% sur projection
            
            **Fiabilité** : R² proche de 1.00 = Projection très fiable
            """)
    
    elif page == "ℹ️ À propos":
        st.header("ℹ️ À propos")
        st.markdown("""
        ### 🎯 Analyse BRVM Pro v2.0
        
        **Application d'analyse fondamentale avancée pour la Bourse Régionale des Valeurs Mobilières**
        
        ### 🚀 Fonctionnalités
        
        ✅ **Scraping en temps réel** : Cours BRVM actualisés  
        ✅ **Ratios corrigés** : EBITDA, ROIC selon formules académiques  
        ✅ **Analyse de qualité** : Z-Score d'Altman, F-Score de Piotroski  
        ✅ **Valorisation stricte** : Multiples sectoriels avec filtres robustes  
        ✅ **Projections avancées** : Scénarios multiples avec pondération dynamique  
        ✅ **Système d'alertes** : Détection automatique 3 niveaux  
        ✅ **Cloud Supabase** : Données persistantes et partagées  
        
        ### 🛠️ Technologies
        
        - **Framework** : Streamlit
        - **Scraping** : BeautifulSoup4, Requests
        - **Analyse** : NumPy, Pandas, Scikit-learn
        - **Visualisation** : Plotly
        - **Base de données** : Supabase (PostgreSQL)
        
        ### 📝 Améliorations v2.0
        
        **Corrections critiques :**
        - EBITDA = Résultat exploitation + Amortissements
        - ROIC = NOPAT / Capital investi
        - Validation des données (bilan équilibré)
        - Gestion erreurs avec safe_ratio()
        
        **Nouveaux indicateurs :**
        - Z-Score d'Altman (prédiction faillite)
        - F-Score de Piotroski (qualité sur 9 points)
        - Système d'alertes (Critique/Important/Attention)
        
        **Valorisation améliorée :**
        - Filtres stricts : PER 5-30, EV/EBITDA 3-20
        - Utilisation de la médiane (plus robuste)
        - Scénarios de projection
        
        ### 📞 Contact & Support
        
        Pour toute question ou suggestion d'amélioration, utilisez le bouton de feedback Streamlit.
        
        ---
        
        **Version** : 2.0 (Décembre 2024)  
        **Licence** : Usage personnel et éducatif
        """)
        
        st.info("💡 **Astuce** : Utilisez le mode sombre pour une meilleure expérience (⚙️ → Settings → Theme)")

if __name__ == "__main__":
    main()
