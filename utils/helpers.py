# utils/helpers.py
import warnings
import urllib3
from datetime import datetime

# Désactiver les warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore')

def format_currency(value):
    """Formater un nombre en devise"""
    if value == 0:
        return "0"
    elif abs(value) >= 1_000_000_000:
        return f"{value/1_000_000_000:,.1f}Md"
    elif abs(value) >= 1_000_000:
        return f"{value/1_000_000:,.1f}M"
    elif abs(value) >= 1_000:
        return f"{value/1_000:,.1f}K"
    else:
        return f"{value:,.0f}"

def format_percentage(value):
    """Formater un pourcentage"""
    if value is None:
        return "N/A"
    return f"{value:.2f}%"

def get_current_datetime():
    """Obtenir la date et heure actuelles formatées"""
    return datetime.now().strftime('%d/%m/%Y %H:%M')

def format_timestamp(timestamp):
    """Formater un timestamp ISO en format lisible"""
    if not timestamp:
        return "N/A"
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime('%d/%m/%Y %H:%M')
    except:
        return timestamp
