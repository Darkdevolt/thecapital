# database/operations.py
import streamlit as st
from datetime import datetime
from database.supabase_client import init_supabase

def load_symbol_mapping():
    """Charger le mapping des symboles depuis Supabase"""
    supabase = init_supabase()
    if not supabase:
        return {}
    
    try:
        response = supabase.table("symbol_mapping").select("*").execute()
        mapping = {}
        for record in response.data:
            mapping[record['symbole']] = record['nom_complet']
        return mapping
    except Exception as e:
        st.error(f"Erreur de chargement du mapping: {str(e)}")
        return {}

def save_symbol_mapping(symbole, nom_complet):
    """Sauvegarder un mapping dans Supabase"""
    supabase = init_supabase()
    if not supabase:
        return False
    
    try:
        record = {
            'symbole': symbole,
            'nom_complet': nom_complet,
            'last_update': datetime.now().isoformat()
        }
        
        # Vérifier si l'entrée existe déjà
        existing = supabase.table("symbol_mapping")\
            .select("*")\
            .eq("symbole", symbole)\
            .execute()
        
        if existing.data:
            # Mise à jour
            response = supabase.table("symbol_mapping")\
                .update(record)\
                .eq("symbole", symbole)\
                .execute()
        else:
            # Insertion
            response = supabase.table("symbol_mapping").insert(record).execute()
        
        return True
    except Exception as e:
        st.error(f"Erreur de sauvegarde du mapping: {str(e)}")
        return False

def delete_symbol_mapping(symbole):
    """Supprimer un mapping de Supabase"""
    supabase = init_supabase()
    if not supabase:
        return False
    
    try:
        response = supabase.table("symbol_mapping")\
            .delete()\
            .eq("symbole", symbole)\
            .execute()
        return True
    except Exception as e:
        st.error(f"Erreur de suppression du mapping: {str(e)}")
        return False

def load_all_financial_data():
    """Charger toutes les données financières depuis Supabase"""
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
        st.error(f"Erreur de chargement depuis Supabase: {str(e)}")
        return {}

def save_financial_data(symbole, annee, data_dict):
    """Sauvegarder les données dans Supabase"""
    supabase = init_supabase()
    if not supabase:
        return False
    
    try:
        record = {
            'symbole': symbole,
            'annee': annee,
            'data': data_dict,
            'last_update': datetime.now().isoformat()
        }
        
        # Vérifier si l'entrée existe déjà
        existing = supabase.table("financial_data")\
            .select("*")\
            .eq("symbole", symbole)\
            .eq("annee", annee)\
            .execute()
        
        if existing.data:
            # Mise à jour
            response = supabase.table("financial_data")\
                .update(record)\
                .eq("symbole", symbole)\
                .eq("annee", annee)\
                .execute()
        else:
            # Insertion
            response = supabase.table("financial_data").insert(record).execute()
        
        return True
    except Exception as e:
        st.error(f"Erreur de sauvegarde dans Supabase: {str(e)}")
        return False

def delete_financial_data(symbole, annee):
    """Supprimer des données de Supabase"""
    supabase = init_supabase()
    if not supabase:
        return False
    
    try:
        response = supabase.table("financial_data")\
            .delete()\
            .eq("symbole", symbole)\
            .eq("annee", annee)\
            .execute()
        return True
    except Exception as e:
        st.error(f"Erreur de suppression: {str(e)}")
        return False

def init_storage():
    """Initialiser le stockage avec Supabase"""
    if 'financial_data' not in st.session_state:
        st.session_state.financial_data = load_all_financial_data()
    if 'symbol_mapping' not in st.session_state:
        st.session_state.symbol_mapping = load_symbol_mapping()
    return st.session_state.financial_data
