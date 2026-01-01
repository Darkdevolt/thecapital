# utils/calculations.py
import numpy as np
from sklearn.linear_model import LinearRegression

def calculate_enhanced_financial_ratios(bilan, compte_resultat, flux_tresorerie):
    """Version améliorée avec tous les ratios standards"""
    ratios = {}
    
    # ========== CALCULS INTERMÉDIAIRES CRITIQUES ==========
    ebitda = compte_resultat.get('resultat_exploitation', 0)
    ebit = compte_resultat.get('resultat_exploitation', 0)
    fcf = flux_tresorerie.get('flux_exploitation', 0) + flux_tresorerie.get('flux_investissement', 0)
    working_capital = bilan.get('actif_courant', 0) - bilan.get('passif_courant', 0)
    
    market_cap = bilan.get('cours_action', 0) * bilan.get('nb_actions', 0)
    enterprise_value = market_cap + bilan.get('dettes_totales', 0) - bilan.get('tresorerie', 0)
    
    # ========== RATIOS DE RENTABILITÉ ==========
    if compte_resultat.get('resultat_net') and compte_resultat.get('chiffre_affaires'):
        ratios['marge_nette'] = (compte_resultat['resultat_net'] / compte_resultat['chiffre_affaires']) * 100
    
    if ebit and compte_resultat.get('chiffre_affaires'):
        ratios['marge_ebit'] = (ebit / compte_resultat['chiffre_affaires']) * 100
    
    if ebitda and compte_resultat.get('chiffre_affaires'):
        ratios['marge_ebitda'] = (ebitda / compte_resultat['chiffre_affaires']) * 100
    
    if compte_resultat.get('resultat_net') and bilan.get('capitaux_propres'):
        ratios['roe'] = (compte_resultat['resultat_net'] / bilan['capitaux_propres']) * 100
    
    if compte_resultat.get('resultat_net') and bilan.get('actif_total'):
        ratios['roa'] = (compte_resultat['resultat_net'] / bilan['actif_total']) * 100
    
    if ebit and bilan.get('actif_total'):
        roic_denom = bilan['actif_total'] - bilan.get('passif_courant', 0)
        if roic_denom > 0:
            ratios['roic'] = (ebit * 0.75 / roic_denom) * 100
    
    # ========== RATIOS DE LIQUIDITÉ ==========
    if bilan.get('actif_courant') and bilan.get('passif_courant') and bilan.get('passif_courant') > 0:
        ratios['ratio_liquidite_generale'] = bilan['actif_courant'] / bilan['passif_courant']
    
    if bilan.get('actif_courant') and bilan.get('stocks') is not None and bilan.get('passif_courant'):
        actif_liquide = bilan['actif_courant'] - bilan.get('stocks', 0)
        if bilan['passif_courant'] > 0:
            ratios['ratio_liquidite_reduite'] = actif_liquide / bilan['passif_courant']
    
    if bilan.get('tresorerie') and bilan.get('passif_courant') and bilan.get('passif_courant') > 0:
        ratios['ratio_liquidite_immediate'] = bilan['tresorerie'] / bilan['passif_courant']
    
    # ========== RATIOS D'ENDETTEMENT ==========
    if bilan.get('dettes_totales') and bilan.get('capitaux_propres') and bilan.get('capitaux_propres') > 0:
        ratios['ratio_endettement'] = (bilan['dettes_totales'] / bilan['capitaux_propres']) * 100
    
    if bilan.get('dettes_totales') and bilan.get('actif_total') and bilan.get('actif_total') > 0:
        ratios['taux_endettement'] = (bilan['dettes_totales'] / bilan['actif_total']) * 100
    
    if bilan.get('capitaux_propres') and bilan.get('actif_total') and bilan.get('actif_total') > 0:
        ratios['ratio_solvabilite'] = (bilan['capitaux_propres'] / bilan['actif_total']) * 100
    
    if bilan.get('dettes_totales') and ebitda > 0:
        ratios['debt_to_ebitda'] = bilan['dettes_totales'] / ebitda
    
    if ebit and compte_resultat.get('charges_financieres') and abs(compte_resultat.get('charges_financieres', 0)) > 0:
        ratios['couverture_interets'] = ebit / abs(compte_resultat['charges_financieres'])
    
    # ========== RATIOS D'EFFICACITÉ ==========
    if compte_resultat.get('chiffre_affaires') and bilan.get('actif_total') and bilan.get('actif_total') > 0:
        ratios['rotation_actifs'] = compte_resultat['chiffre_affaires'] / bilan['actif_total']
    
    if compte_resultat.get('chiffre_affaires') and bilan.get('stocks') and bilan.get('stocks') > 0:
        ratios['rotation_stocks'] = compte_resultat['chiffre_affaires'] / bilan['stocks']
    
    if compte_resultat.get('chiffre_affaires') and bilan.get('creances') and compte_resultat.get('chiffre_affaires') > 0:
        ratios['delai_recouvrement'] = (bilan['creances'] / compte_resultat['chiffre_affaires']) * 365
    
    # ========== RATIOS DE MARCHÉ ==========
    if bilan.get('cours_action') and compte_resultat.get('benefice_par_action') and compte_resultat.get('benefice_par_action') > 0:
        ratios['per'] = bilan['cours_action'] / compte_resultat['benefice_par_action']
    elif bilan.get('cours_action') and compte_resultat.get('resultat_net') and bilan.get('nb_actions') and bilan.get('nb_actions') > 0:
        bpa = compte_resultat['resultat_net'] / bilan['nb_actions']
        if bpa > 0:
            ratios['per'] = bilan['cours_action'] / bpa
            ratios['benefice_par_action'] = bpa
    
    if bilan.get('cours_action') and bilan.get('capitaux_propres_par_action') and bilan.get('capitaux_propres_par_action') > 0:
        ratios['price_to_book'] = bilan['cours_action'] / bilan['capitaux_propres_par_action']
    
    if enterprise_value and ebitda > 0:
        ratios['ev_ebitda'] = enterprise_value / ebitda
    
    if enterprise_value and compte_resultat.get('chiffre_affaires') and compte_resultat.get('chiffre_affaires') > 0:
        ratios['ev_sales'] = enterprise_value / compte_resultat['chiffre_affaires']
    
    # ========== RATIOS DE FLUX DE TRÉSORERIE ==========
    if flux_tresorerie.get('flux_exploitation') and compte_resultat.get('resultat_net') and compte_resultat.get('resultat_net') != 0:
        ratios['qualite_benefices'] = flux_tresorerie['flux_exploitation'] / compte_resultat['resultat_net']
    
    if fcf and market_cap > 0:
        ratios['fcf_yield'] = (fcf / market_cap) * 100
    
    if fcf and bilan.get('dettes_totales') and bilan.get('dettes_totales') > 0:
        ratios['fcf_to_debt'] = fcf / bilan['dettes_totales']
    
    # ========== DONNÉES INTERMÉDIAIRES ==========
    ratios['ebitda'] = ebitda
    ratios['ebit'] = ebit
    ratios['fcf'] = fcf
    ratios['working_capital'] = working_capital
    ratios['enterprise_value'] = enterprise_value
    ratios['market_cap'] = market_cap
    
    return ratios

def calculate_valuation_multiples(symbole, annee, ratios_entreprise, financial_data):
    """Valorisation par multiples avec comparaison sectorielle (MÉDIANE)"""
    secteur_multiples = {
        'per': [],
        'price_to_book': [],
        'ev_ebitda': [],
        'ev_sales': []
    }
    
    # Parcourir toutes les données financières
    for key, data in financial_data.items():
        if key == f"{symbole}_{annee}":
            continue
        
        ratios = data.get('ratios', {})
        
        if ratios.get('per') and 0 < ratios['per'] < 100:
            secteur_multiples['per'].append(ratios['per'])
        if ratios.get('price_to_book') and 0 < ratios['price_to_book'] < 20:
            secteur_multiples['price_to_book'].append(ratios['price_to_book'])
        if ratios.get('ev_ebitda') and 0 < ratios['ev_ebitda'] < 50:
            secteur_multiples['ev_ebitda'].append(ratios['ev_ebitda'])
        if ratios.get('ev_sales') and 0 < ratios['ev_sales'] < 10:
            secteur_multiples['ev_sales'].append(ratios['ev_sales'])
    
    # Calculer les MÉDIANES
    medianes = {}
    for key, values in secteur_multiples.items():
        if len(values) >= 2:
            medianes[f"{key}_median"] = np.median(values)
    
    valorisations = {}
    
    # 1. Valorisation par P/E médian
    if 'per_median' in medianes:
        bpa = ratios_entreprise.get('benefice_par_action')
        if not bpa and ratios_entreprise.get('resultat_net') and ratios_entreprise.get('nb_actions'):
            bpa = ratios_entreprise['resultat_net'] / ratios_entreprise['nb_actions']
        
        if bpa:
            juste_valeur_per = medianes['per_median'] * bpa
            valorisations['juste_valeur_per'] = juste_valeur_per
            cours_actuel = ratios_entreprise.get('cours_action', 0)
            if cours_actuel > 0:
                valorisations['ecart_per'] = ((juste_valeur_per - cours_actuel) / cours_actuel) * 100
    
    # 2. Valorisation par P/B médian
    if 'price_to_book_median' in medianes:
        if ratios_entreprise.get('capitaux_propres_par_action'):
            cpa = ratios_entreprise['capitaux_propres_par_action']
        elif ratios_entreprise.get('capitaux_propres') and ratios_entreprise.get('nb_actions'):
            cpa = ratios_entreprise['capitaux_propres'] / ratios_entreprise['nb_actions']
        else:
            cpa = None
        
        if cpa:
            juste_valeur_pb = medianes['price_to_book_median'] * cpa
            valorisations['juste_valeur_pb'] = juste_valeur_pb
            cours_actuel = ratios_entreprise.get('cours_action', 0)
            if cours_actuel > 0:
                valorisations['ecart_pb'] = ((juste_valeur_pb - cours_actuel) / cours_actuel) * 100
    
    # 3. Valorisation par EV/EBITDA médian
    if 'ev_ebitda_median' in medianes and ratios_entreprise.get('ebitda'):
        enterprise_value_juste = medianes['ev_ebitda_median'] * ratios_entreprise['ebitda']
        dettes = ratios_entreprise.get('dettes_totales', 0)
        tresorerie = ratios_entreprise.get('tresorerie', 0)
        juste_valeur_ev = enterprise_value_juste - dettes + tresorerie
        nb_actions = ratios_entreprise.get('nb_actions', 0)
        
        if nb_actions > 0:
            juste_valeur_ev_par_action = juste_valeur_ev / nb_actions
            valorisations['juste_valeur_ev_ebitda'] = juste_valeur_ev_par_action
            cours_actuel = ratios_entreprise.get('cours_action', 0)
            if cours_actuel > 0:
                valorisations['ecart_ev_ebitda'] = ((juste_valeur_ev_par_action - cours_actuel) / cours_actuel) * 100
    
    valorisations['medianes_secteur'] = medianes
    
    # Calculer potentiel moyen
    ecarts = [v for k, v in valorisations.items() if k.startswith('ecart_')]
    if ecarts:
        valorisations['potentiel_moyen'] = np.mean(ecarts)
        valorisations['potentiel_median'] = np.median(ecarts)
        
        # RECOMMANDATION
        potentiel = valorisations['potentiel_median']
        if potentiel > 20:
            valorisations['recommandation'] = "ACHAT FORT"
            valorisations['justification'] = f"Sous-évalué de {potentiel:.1f}% par rapport aux pairs"
        elif potentiel > 10:
            valorisations['recommandation'] = "ACHAT"
            valorisations['justification'] = f"Potentiel de hausse de {potentiel:.1f}%"
        elif potentiel > -10:
            valorisations['recommandation'] = "CONSERVER"
            valorisations['justification'] = "Valorisation proche de la juste valeur"
        elif potentiel > -20:
            valorisations['recommandation'] = "VENTE"
            valorisations['justification'] = f"Surévalué de {abs(potentiel):.1f}%"
        else:
            valorisations['recommandation'] = "VENTE FORTE"
            valorisations['justification'] = f"Fortement surévalué de {abs(potentiel):.1f}%"
    
    return valorisations

def calculate_financial_projections(symbole, financial_data, annees_projection=3):
    """Projections financières pondérées : 40% TCAM + 60% Régression Linéaire"""
    historique = []
    for key, data in financial_data.items():
        if data.get('symbole') == symbole:
            annee = data.get('annee')
            ca = data.get('compte_resultat', {}).get('chiffre_affaires', 0)
            rn = data.get('compte_resultat', {}).get('resultat_net', 0)
            if ca > 0 and rn != 0:
                historique.append({
                    'annee': int(annee),
                    'ca': ca,
                    'resultat_net': rn
                })
    
    if len(historique) < 2:
        return {"erreur": "Historique insuffisant (minimum 2 ans)"}
    
    historique = sorted(historique, key=lambda x: x['annee'])
    annees = np.array([h['annee'] for h in historique]).reshape(-1, 1)
    ca_values = np.array([h['ca'] for h in historique])
    rn_values = np.array([h['resultat_net'] for h in historique])
    
    # TCAM
    def calcul_tcam(valeur_debut, valeur_fin, nb_annees):
        if valeur_debut <= 0:
            return 0
        return (pow(valeur_fin / valeur_debut, 1/nb_annees) - 1) * 100
    
    tcam_ca = calcul_tcam(ca_values[0], ca_values[-1], len(ca_values) - 1)
    tcam_rn = calcul_tcam(abs(rn_values[0]), abs(rn_values[-1]), len(rn_values) - 1) if rn_values[0] != 0 else 0
    
    # RÉGRESSION LINÉAIRE
    model_ca = LinearRegression()
    model_ca.fit(annees, ca_values)
    
    model_rn = LinearRegression()
    model_rn.fit(annees, rn_values)
    
    r2_ca = model_ca.score(annees, ca_values)
    r2_rn = model_rn.score(annees, rn_values)
    
    # PROJECTIONS
    projections = []
    derniere_annee = historique[-1]['annee']
    dernier_ca = historique[-1]['ca']
    dernier_rn = historique[-1]['resultat_net']
    
    for i in range(1, annees_projection + 1):
        annee_future = derniere_annee + i
        
        ca_tcam = dernier_ca * pow(1 + tcam_ca/100, i)
        rn_tcam = dernier_rn * pow(1 + tcam_rn/100, i)
        
        ca_reg = model_ca.predict([[annee_future]])[0]
        rn_reg = model_rn.predict([[annee_future]])[0]
        ca_projete = 0.4 * ca_tcam + 0.6 * ca_reg
        rn_projete = 0.4 * rn_tcam + 0.6 * rn_reg
        
        projections.append({
            'annee': int(annee_future),
            'ca_projete': float(ca_projete),
            'rn_projete': float(rn_projete),
            'marge_nette_projetee': float((rn_projete / ca_projete * 100) if ca_projete > 0 else 0)
        })
    
    return {
        'historique': historique,
        'tcam_ca': float(tcam_ca),
        'tcam_rn': float(tcam_rn),
        'r2_ca': float(r2_ca),
        'r2_rn': float(r2_rn),
        'projections': projections,
        'methode': '40% TCAM + 60% Régression Linéaire'
    }
