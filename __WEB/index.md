# 🛠️ FG-ToolWatcher

Bienvenue dans la documentation technique de **FG-ToolWatcher**, l'outil d'agrégation et de surveillance des prix pour le secteur de l'outillage.

## 📌 Présentation
Ce projet permet de surveiller les tarifs de différents fournisseurs (Lecot, Clabots, Klium, etc.), de normaliser les données et de boucher les trous d'information (EAN/MPN) grâce à un système d'indexation croisée intelligent.

## 🚀 Fonctionnalités Clés
* **Scraping Multi-sources** : Récupération de données via loaders spécifiques.
* **Data Cleaning** : Normalisation des prix et validation des marques via `ProductDataParser`.
* **DB Indexing** : Synchronisation mondiale des identifiants `EAN` <-> `MPN` par marque.
* **Interface Graphique** : Visualisation et gestion via une GUI dédiée.

## 🛠️ Structure du Projet
- **CORE/** : Logique métier, loaders et moteurs de recherche.
- **GUI/** : Interface utilisateur.
- **__WEB/** : Cette documentation.
- **USER/DATA/** : Stockage des bases de données CSV.

---
*Dernière mise à jour : 20 février 2026*