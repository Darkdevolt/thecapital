# config/settings.py
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://otsiwiwlnowxeolbbgvm.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "sb_publishable_MhaI5b-kMmb5liIMOJ4P3Q_xGTsJAFJ")

# Configuration Application
DEVELOPER_PASSWORD = os.getenv("DEVELOPER_PASSWORD", "dev_brvm_2024")
APP_TITLE = "Analyse BRVM Pro"
APP_VERSION = "1.0"
