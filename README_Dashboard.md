-# 📊 Tableau de Bord - Courbes Descriptives

## Vue d'ensemble

Le nouveau tableau de bord intégré dans le module d'accueil affiche des courbes descriptives des états évolutifs des productions et des recettes de votre coopérative.

## 🚀 Fonctionnalités

### 📈 Métriques de Résumé
- **Total des livraisons** : Nombre total de livraisons enregistrées
- **Production totale** : Quantité totale produite (en kg)
- **Recettes totales** : Montant total des recettes (FCFA)
- **Bénéfice net** : Différence entre recettes et dépenses
- **Cultures actives** : Nombre de cultures différentes
- **Production moyenne** : Quantité moyenne par livraison
- **Total des dépenses** : Montant total des dépenses
- **Quantité vendue** : Quantité totale vendue

### 📊 Graphiques d'Évolution de la Production
1. **Évolution de la Production par Culture** : Courbe montrant l'évolution mensuelle de la production pour chaque culture
2. **Nombre de Livraisons par Mois** : Graphique en barres du nombre de livraisons mensuelles
3. **Quantité Moyenne par Livraison** : Graphique de dispersion montrant la quantité moyenne par livraison
4. **Répartition de la Production par Culture** : Graphique en secteurs de la répartition totale

### 💰 Graphiques d'Évolution des Recettes
1. **Évolution des Recettes Totales** : Courbe d'évolution des recettes par culture
2. **Recettes vs Dépenses** : Comparaison entre recettes et dépenses par période
3. **Évolution du Bénéfice Net** : Graphique en barres du bénéfice net par culture
4. **Répartition des Recettes par Culture** : Graphique en secteurs des recettes

### 🔍 Analyse Comparative
- **Corrélation Production-Recettes** : Graphique de dispersion montrant la relation entre production et recettes
- **Coefficient de corrélation** : Indicateur statistique de la corrélation

## 🛠️ Installation des Dépendances

### Méthode Automatique
Exécutez le script d'installation :
```bash
python install_dashboard_deps.py
```

### Méthode Manuelle
Installez les dépendances requises :
```bash
pip install plotly numpy
```

## 📱 Modes d'Affichage

### Mode Avancé (avec Plotly)
- Graphiques interactifs avec zoom, survol et filtrage
- Graphiques en secteurs, courbes et barres avancés
- Graphiques de corrélation avec taille variable des points

### Mode Simplifié (sans Plotly)
- Graphiques Streamlit natifs (line_chart, bar_chart)
- Tableaux de données pour l'analyse comparative
- Toutes les métriques de résumé disponibles

## 🎯 Utilisation

1. **Accès** : Le tableau de bord s'affiche automatiquement dans l'onglet "🏡Accueil"
2. **Navigation** : Utilisez les onglets pour basculer entre "Production" et "Recettes"
3. **Interactivité** : Survolez les graphiques pour voir les détails (mode avancé)
4. **Mise à jour** : Les données sont mises à jour automatiquement à chaque visite

## 📊 Sources de Données

### Production
- Table `productions` : données de livraisons par culture
- Filtrage automatique des données erronées (statut != 'erreur')
- Agrégation par mois et par culture

### Recettes
- Table `transactions` : recettes et dépenses par culture
- Table `ventes` : chiffre d'affaires des ventes
- Calcul automatique du bénéfice net

## 🎨 Personnalisation

### Styles CSS
Le tableau de bord utilise des styles CSS personnalisés pour :
- Conteneurs avec arrière-plan dégradé
- Cartes de métriques avec ombres
- Titre stylisé avec effet de texte
- Conteneurs de graphiques avec bordures arrondies

### Couleurs
- **Vert** (#4CAF50) : Production et éléments positifs
- **Bleu** (#1976D2) : Titres et éléments principaux
- **Rouge** : Dépenses et éléments négatifs
- **Dégradés** : Arrière-plans et conteneurs

## 🔧 Dépannage

### Problème : "Plotly n'est pas installé"
**Solution** : Exécutez `python install_dashboard_deps.py` ou `pip install plotly numpy`

### Problème : "Aucune donnée disponible"
**Solution** : 
1. Vérifiez que des données de production sont enregistrées
2. Vérifiez que des transactions sont saisies
3. Assurez-vous que les cultures sont configurées

### Problème : Graphiques ne s'affichent pas
**Solution** :
1. Vérifiez la connexion à la base de données
2. Rechargez la page
3. Vérifiez les logs d'erreur dans la console

## 📈 Évolutions Futures

- Filtres par période personnalisables
- Export des graphiques en PDF/PNG
- Alertes automatiques sur les tendances
- Prévisions basées sur l'historique
- Comparaisons inter-coopératives

## 🤝 Support

Pour toute question ou problème :
1. Vérifiez ce README
2. Consultez les logs d'erreur
3. Vérifiez l'installation des dépendances
4. Contactez l'administrateur système

---

*Tableau de bord développé pour optimiser la gestion et le suivi des coopératives d'hévéa* 🌿