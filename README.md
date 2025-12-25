# 📊 BRVM Analyzer - Plateforme d'Analyse Financière

Application Streamlit pour l'analyse des titres de la Bourse Régionale des Valeurs Mobilières (BRVM).

## 🎯 Fonctionnalités

### Pour les Investisseurs
- ✅ Consultation des cours en temps réel
- ✅ Statistiques de marché (titres en hausse/baisse/stables)
- ✅ Analyse fondamentale complète par titre
- ✅ Visualisation des ratios financiers
- ✅ Export des données en CSV

### Pour le Développeur
- ✅ Section sécurisée pour la gestion des données financières
- ✅ Ajout/modification du Bilan
- ✅ Ajout/modification du Compte de Résultat
- ✅ Ajout/modification du Tableau des Flux de Trésorerie
- ✅ Calcul automatique de 15+ ratios financiers
- ✅ Interprétation automatique des ratios
- ✅ Stockage persistant des données

## 🚀 Installation

### Prérequis
- Python 3.8+
- pip

### Installation locale

```bash
# Cloner le repository
git clone https://github.com/votre-username/brvm-analyzer.git
cd brvm-analyzer

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
streamlit run app.py
```

## 🔐 Accès Développeur

La section développeur est protégée par mot de passe. Pour y accéder :
1. Naviguer vers "🔐 Section Développeur" dans le menu
2. Entrer le mot de passe (par défaut: `dev_brvm_2024`)
3. **⚠️ IMPORTANT** : Changez ce mot de passe dans le fichier `app.py` ligne 14

## 📊 Ratios Calculés Automatiquement

### Rentabilité
- Marge Nette
- Marge d'Exploitation  
- ROE (Return on Equity)
- ROA (Return on Assets)

### Liquidité
- Ratio de Liquidité Générale
- Ratio de Liquidité Immédiate

### Endettement
- Ratio d'Endettement
- Taux d'Endettement

### Efficacité
- Rotation des Actifs
- Rotation des Stocks

### Marché
- PER (Price Earnings Ratio)
- Price to Book Ratio

### Flux de Trésorerie
- Qualité des Bénéfices
- Couverture des Dettes Court Terme

## 📁 Structure du Projet

```
brvm-analyzer/
├── app.py                  # Application principale
├── requirements.txt        # Dépendances Python
├── .streamlit/
│   └── config.toml        # Configuration Streamlit
├── README.md              # Documentation
└── .gitignore            # Fichiers à ignorer
```

## 🌐 Déploiement sur Streamlit Cloud

1. Pusher le code sur GitHub
2. Se connecter sur [streamlit.io/cloud](https://streamlit.io/cloud)
3. Créer une nouvelle app et sélectionner le repository
4. L'app sera déployée automatiquement

## 💡 Utilisation

### Ajouter des données financières

1. Accéder à la section développeur
2. Entrer le symbole de l'action (ex: SNTS, SGBC, BICC)
3. Sélectionner l'année
4. Remplir les données dans les onglets :
   - **Bilan** : Actif, Passif, Capitaux Propres
   - **Compte de Résultat** : CA, Charges, Résultat Net
   - **Flux de Trésorerie** : Flux d'exploitation, d'investissement, de financement
5. Cliquer sur "💾 Sauvegarder les Données"

Les ratios sont calculés automatiquement dès que vous remplissez les données !

### Consulter l'analyse d'un titre

1. Sur la page d'accueil
2. Descendre à "📊 Analyse Fondamentale par Titre"
3. Sélectionner le symbole
4. Voir toutes les années de données disponibles

## 🔒 Sécurité

- Mot de passe développeur à changer en production
- Session state pour la persistance temporaire
- Prévu pour intégration avec base de données cloud

## 📈 Roadmap Future

- [ ] Base de données PostgreSQL/Supabase
- [ ] Graphiques historiques
- [ ] Analyse technique (RSI, MACD, etc.)
- [ ] Alertes email/SMS
- [ ] API REST
- [ ] Système d'abonnement premium
- [ ] Prédictions ML

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
- Ouvrir une issue pour signaler un bug
- Proposer de nouvelles fonctionnalités
- Soumettre une pull request

## 📝 Licence

Ce projet est sous licence MIT.

## 📧 Contact

Pour toute question ou suggestion, contactez-nous.

## ⚠️ Disclaimer

Cette application est fournie à des fins éducatives et informatives uniquement. Elle ne constitue pas un conseil en investissement. Faites toujours vos propres recherches avant d'investir.

---

**Fait avec ❤️ pour la communauté BRVM**# thecapital
