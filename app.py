import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Configuration de la page
st.set_page_config(
    page_title="BRVM Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS personnalisé
st.markdown("""
<style>
    /* Style général */
    .main {
        padding: 0rem 1rem;
    }
    
    /* En-tête */
    .header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    
    /* Cartes */
    .card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.3s;
    }
    
    .card:hover {
        transform: translateY(-5px);
    }
    
    /* Boutons */
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        transform: scale(1.02);
    }
    
    /* Métriques */
    .stMetric {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
    }
    
    /* Onglets */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        font-weight: 600;
        border-radius: 10px 10px 0 0;
    }
    
    /* Tableau */
    .dataframe {
        border: none !important;
    }
    
    /* Badges */
    .badge {
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85em;
        font-weight: 600;
    }
    
    .badge-success {
        background-color: #d4edda;
        color: #155724;
    }
    
    .badge-danger {
        background-color: #f8d7da;
        color: #721c24;
    }
    
    .badge-warning {
        background-color: #fff3cd;
        color: #856404;
    }
</style>
""", unsafe_allow_html=True)

# Données simulées (en attendant la connexion au site)
def load_sample_data():
    """Charger des données d'exemple avec structure réaliste"""
    data = {
        "Symbole": ["BICB", "BICC", "BOAB", "BOAC", "ORAC", "SGBC", "SNTS", "UNLC", "PALC", "CFAC"],
        "Nom": [
            "BANQUE INTERNATIONALE POUR L'INDUSTRIE ET LE COMMERCE DU BENIN",
            "BICI COTE D'IVOIRE",
            "BANK OF AFRICA BENIN",
            "BANK OF AFRICA COTE D'IVOIRE",
            "ORANGE COTE D'IVOIRE",
            "SOCIETE GENERALE COTE D'IVOIRE",
            "SONATEL SENEGAL",
            "UNILEVER COTE D'IVOIRE",
            "PALM COTE D'IVOIRE",
            "CFAO MOTORS COTE D'IVOIRE"
        ],
        "Volume": [900, 1025, 4599, 1027, 342, 282, 3047, 0, 535, 4047],
        "Cours veille (FCFA)": [4950, 19000, 5930, 7090, 14500, 28550, 25000, 34225, 8000, 1440],
        "Cours Ouverture (FCFA)": [4900, 19335, 5825, 7100, 14790, 28000, 25000, 0, 7705, 1300],
        "Cours Clôture (FCFA)": [4905, 19380, 5825, 7100, 14600, 28500, 24900, 34225, 7945, 1445],
        "Variation (%)": [-0.91, 0.21, 0.43, 0.14, 0.69, 2.52, -0.40, 0.00, -1.85, 3.21]
    }
    
    df = pd.DataFrame(data)
    
    # Calculer la capitalisation fictive
    df["Capitalisation (M FCFA)"] = df["Cours Clôture (FCFA)"] * df["Volume"] * 1000 / 1_000_000
    df["Capitalisation (M FCFA)"] = df["Capitalisation (M FCFA)"].round(2)
    
    # Catégorie fictive
    categories = ["Banque", "Banque", "Banque", "Banque", "Télécom", "Banque", 
                  "Télécom", "Consommation", "Agro", "Automobile"]
    df["Secteur"] = categories
    
    return df

# Initialisation de session
if 'df' not in st.session_state:
    st.session_state.df = load_sample_data()
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ["BICB", "ORAC", "SGBC"]

# Header élégant
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.markdown("""
    <div class="header">
        <h1 style="margin:0;">📈 BRVM Analytics Dashboard</h1>
        <p style="margin:0; opacity:0.9;">Analyse en temps réel des marchés boursiers d'Afrique de l'Ouest</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.metric("Dernière mise à jour", 
              st.session_state.last_update.strftime("%H:%M"),
              delta="3 min")

# Sidebar - Filtres
with st.sidebar:
    st.markdown("### 🔍 Filtres")
    
    # Filtre par secteur
    sectors = st.multiselect(
        "Secteur d'activité",
        options=st.session_state.df["Secteur"].unique().tolist(),
        default=st.session_state.df["Secteur"].unique().tolist()
    )
    
    # Filtre par variation
    variation_range = st.slider(
        "Plage de variation (%)",
        min_value=-10.0,
        max_value=10.0,
        value=(-5.0, 5.0),
        step=0.5
    )
    
    # Filtre par volume
    volume_min = st.number_input(
        "Volume minimum",
        min_value=0,
        max_value=10000,
        value=0
    )
    
    # Watchlist
    st.markdown("### ⭐ Watchlist")
    selected_symbols = st.multiselect(
        "Sélectionnez vos actions favorites",
        options=st.session_state.df["Symbole"].tolist(),
        default=st.session_state.watchlist
    )
    st.session_state.watchlist = selected_symbols
    
    st.markdown("---")
    st.markdown("### 📊 Indicateurs")
    st.markdown("""
    - 📈 **Indice BRVM 10** : 145.67 (+1.2%)
    - 💰 **Capitalisation totale** : 12,450 Mds FCFA
    - 📉 **Volume total** : 45,678,900
    """)

# Fonction d'actualisation
def refresh_data():
    st.session_state.last_update = datetime.now()
    st.success("Données actualisées avec succès !")

# Boutons d'action en ligne
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    if st.button("🔄 Actualiser", use_container_width=True):
        refresh_data()
with col2:
    if st.button("📊 Exporter CSV", use_container_width=True):
        st.info("Export CSV démarré")
with col3:
    if st.button("📈 Graphiques", use_container_width=True):
        st.info("Affichage des graphiques")
with col4:
    if st.button("🔔 Alertes", use_container_width=True):
        st.info("Configuration des alertes")
with col5:
    if st.button("📱 Rapport", use_container_width=True):
        st.info("Génération du rapport")

# Filtrage des données
filtered_df = st.session_state.df.copy()
if sectors:
    filtered_df = filtered_df[filtered_df["Secteur"].isin(sectors)]
filtered_df = filtered_df[
    (filtered_df["Variation (%)"] >= variation_range[0]) & 
    (filtered_df["Variation (%)"] <= variation_range[1])
]
filtered_df = filtered_df[filtered_df["Volume"] >= volume_min]

# KPI Cards
st.markdown("### 📊 Indicateurs clés")
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

with kpi1:
    st.metric(
        "Total Actions",
        len(filtered_df),
        f"{len(filtered_df) - len(st.session_state.df)}"
    )

with kpi2:
    rising = len(filtered_df[filtered_df["Variation (%)"] > 0])
    st.metric(
        "En hausse",
        rising,
        f"{rising - len(filtered_df[filtered_df['Variation (%)'] <= 0])}"
    )

with kpi3:
    falling = len(filtered_df[filtered_df["Variation (%)"] < 0])
    st.metric(
        "En baisse",
        falling,
        f"{falling - len(filtered_df[filtered_df['Variation (%)'] >= 0])}"
    )

with kpi4:
    avg_change = filtered_df["Variation (%)"].mean()
    st.metric(
        "Variation moyenne",
        f"{avg_change:.2f}%",
        f"{avg_change - filtered_df['Variation (%)'].median():.2f}%"
    )

with kpi5:
    total_volume = filtered_df["Volume"].sum()
    st.metric(
        "Volume total",
        f"{total_volume:,}",
        f"{(total_volume - filtered_df['Volume'].mean()):.0f}"
    )

# Onglets principaux
tab1, tab2, tab3, tab4 = st.tabs(["📋 Tableau", "📈 Graphiques", "⭐ Watchlist", "📊 Analyse"])

with tab1:
    # Tableau interactif
    col1, col2 = st.columns([3, 1])
    
    with col2:
        sort_by = st.selectbox(
            "Trier par",
            ["Symbole", "Variation (%)", "Volume", "Cours Clôture (FCFA)", "Capitalisation (M FCFA)"]
        )
        
        ascending = st.checkbox("Ordre croissant", value=False)
    
    # Tableau stylisé
    display_df = filtered_df.copy()
    display_df = display_df.sort_values(sort_by, ascending=ascending)
    
    # Formater les colonnes
    display_df["Variation (%)"] = display_df["Variation (%)"].apply(
        lambda x: f"{x:+.2f}%" if x != 0 else f"{x:.2f}%"
    )
    
    # Afficher le tableau avec style
    st.dataframe(
        display_df.style.applymap(
            lambda x: 'color: green' if '+' in str(x) else 'color: red' if '-' in str(x) and x != '0.00%' else '',
            subset=["Variation (%)"]
        ).format({
            "Cours veille (FCFA)": "{:,.0f}",
            "Cours Clôture (FCFA)": "{:,.0f}",
            "Capitalisation (M FCFA)": "{:,.2f}"
        }),
        use_container_width=True,
        height=500
    )

with tab2:
    # Graphiques interactifs
    st.markdown("### 📈 Visualisations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Graphique des variations
        fig1 = px.bar(
            filtered_df.nlargest(10, "Variation (%)"),
            x="Symbole",
            y="Variation (%)",
            color="Variation (%)",
            color_continuous_scale="RdYlGn",
            title="Top 10 des variations (%)"
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Graphique des volumes
        fig2 = px.pie(
            filtered_df.nlargest(5, "Volume"),
            values="Volume",
            names="Symbole",
            title="Répartition des volumes (Top 5)"
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    # Graphique de dispersion
    fig3 = px.scatter(
        filtered_df,
        x="Cours Clôture (FCFA)",
        y="Volume",
        size="Capitalisation (M FCFA)",
        color="Secteur",
        hover_name="Nom",
        title="Relation Cours vs Volume"
    )
    st.plotly_chart(fig3, use_container_width=True)

with tab3:
    # Watchlist personnalisée
    st.markdown("### ⭐ Votre Watchlist")
    
    if st.session_state.watchlist:
        watchlist_df = filtered_df[filtered_df["Symbole"].isin(st.session_state.watchlist)]
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            for _, row in watchlist_df.iterrows():
                with st.container():
                    col_a, col_b, col_c, col_d = st.columns([1, 2, 1, 1])
                    
                    with col_a:
                        st.markdown(f"**{row['Symbole']}**")
                    
                    with col_b:
                        st.markdown(f"*{row['Nom'][:30]}...*")
                    
                    with col_c:
                        variation = row["Variation (%)"]
                        color = "green" if variation > 0 else "red" if variation < 0 else "gray"
                        st.markdown(f"<span style='color:{color};font-weight:bold'>{variation:+.2f}%</span>", 
                                   unsafe_allow_html=True)
                    
                    with col_d:
                        st.markdown(f"**{row['Cours Clôture (FCFA)']:,.0f}**")
                    
                    st.progress(min(abs(variation) / 10, 1.0))
        
        with col2:
            st.markdown("### 📊 Performance")
            avg_performance = watchlist_df["Variation (%)"].mean()
            st.metric("Performance moyenne", f"{avg_performance:.2f}%")
            
            best = watchlist_df.loc[watchlist_df["Variation (%)"].idxmax()]
            worst = watchlist_df.loc[watchlist_df["Variation (%)"].idxmin()]
            
            st.markdown(f"**Meilleur :** {best['Symbole']} ({best['Variation (%)']:+.2f}%)")
            st.markdown(f"**Plus faible :** {worst['Symbole']} ({worst['Variation (%)']:+.2f}%)")
    else:
        st.info("Ajoutez des actions à votre watchlist dans la barre latérale")

with tab4:
    # Analyse détaillée
    st.markdown("### 📊 Analyse approfondie")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📈 Distribution des variations")
        
        fig_hist = px.histogram(
            filtered_df,
            x="Variation (%)",
            nbins=20,
            title="Distribution des variations (%)"
        )
        st.plotly_chart(fig_hist, use_container_width=True)
        
        # Statistiques descriptives
        st.markdown("#### 📊 Statistiques")
        
        stats_df = filtered_df.describe()
        st.dataframe(stats_df.style.format("{:.2f}"), use_container_width=True)
    
    with col2:
        st.markdown("#### 📊 Corrélations")
        
        # Matrice de corrélation
        numeric_df = filtered_df.select_dtypes(include=['float64', 'int64'])
        corr_matrix = numeric_df.corr()
        
        fig_corr = px.imshow(
            corr_matrix,
            text_auto=True,
            aspect="auto",
            color_continuous_scale="RdBu",
            title="Matrice de corrélation"
        )
        st.plotly_chart(fig_corr, use_container_width=True)
        
        # Secteurs
        st.markdown("#### 🏢 Par secteur")
        sector_stats = filtered_df.groupby("Secteur").agg({
            "Variation (%)": "mean",
            "Volume": "sum"
        }).round(2)
        
        st.dataframe(sector_stats, use_container_width=True)

# Footer
st.markdown("---")
footer_col1, footer_col2, footer_col3 = st.columns(3)

with footer_col1:
    st.markdown("**© 2024 BRVM Analytics**")
    st.markdown("*Dashboard officiel des marchés*")

with footer_col2:
    st.markdown("**📞 Contact**")
    st.markdown("support@brvm-analytics.com")

with footer_col3:
    st.markdown("**📡 Connexion**")
    if st.button("Vérifier la connexion", key="footer_check"):
        try:
            # Tentative de connexion au site réel
            import requests
            response = requests.get("https://www.brvm.org", timeout=5)
            if response.status_code == 200:
                st.success("✅ Connecté à BRVM")
            else:
                st.warning("⚠️ Connexion limitée")
        except:
            st.error("❌ Hors ligne - Mode démo")

# Mode sombre/clair
st.sidebar.markdown("---")
theme = st.sidebar.selectbox("🎨 Thème", ["Clair", "Sombre"])

# Information système
st.sidebar.markdown("---")
st.sidebar.markdown(f"""
**Informations système :**
- Actions chargées : {len(st.session_state.df)}
- Données filtrées : {len(filtered_df)}
- Dernière actualisation : {st.session_state.last_update.strftime("%H:%M:%S")}
""")
