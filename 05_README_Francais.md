<p align="center">
  <b>🌍 Language / Langue:</b><br>
  <a href="/simondeqin/Bio-data-workflow-automation/blob/main/05_README_Francais.md">🇫🇷 Français</a> |
  <a href="/simondeqin/Bio-data-workflow-automation/blob/main/05_README_English.md">🇬🇧 English</a>
</p>

---

# 🧩 Bio-data-workflow-automation  
_Un pipeline complet et évolutif pour enrichir et classifier automatiquement un catalogue Bio._


# 🧩 Bio-data-workflow-automation  
_Un pipeline complet et évolutif pour enrichir et classifier automatiquement un catalogue Bio._

---

## **1. Contexte et résultats**

### **1.1 Contexte**
Ce projet a été réalisé lors de mon stage chez **GOOD**, une agence de services numériques pour les fabricants et distributeurs du secteur **Bio**.  
Je travaillais sur la base **BioAnalytics**, qui centralise les ventes en caisse issues d’un panel de magasins partenaires et sert de support aux analyses de marché fournies aux clients.

### **1.2 Importance et problème**
La base BioAnalytics est un outil essentiel d’**intelligence business**, mais sa qualité doit être continuellement contrôlée.  
Les principales difficultés rencontrées :

- erreurs de **classification** pouvant fausser les résultats ;  
- **remplissage manuel** lent et répétitif ;  
- nécessité d’une **mise à jour fréquente** ;  
- **sources variées** (magasins, catalogues, sites web) rendant la consolidation complexe.  

👉 D’où la création d’un pipeline automatisé pour fiabiliser et accélérer ces traitements.

### **1.3 Résultats et valeurs apportées**
Le pipeline automatise la **normalisation**, la **complétion** et la **classification** des produits de la base BioAnalytics, améliorant nettement la rapidité et la fiabilité du traitement.

- **Efficacité accrue** : le travail d’une journée est ramené à **30 min–1 h**, grâce à des scripts modulaires facilement réutilisables.  
- **Moins d’erreurs humaines** : l’algorithme détecte les incohérences des données existantes et permet d’ajuster le ratio entre précision et taux de remplissage selon les besoins.  
- **Qualité renforcée** : formats standardisés, mises à jour régulières et **KPI de contrôle** assurent la cohérence et la fiabilité de la base.

---

## **2. Structure du projet**
```
├── src/
│ ├── main.py # Script principal
│ ├── ml_qualification.py # Modèles ML pour classification
│ ├── extract_contenu.py # Extraction du contenant
│ ├── api_openfoodfacts.py # Complétion via API OpenFoodFacts
│ ├── google_api_search.py # Complétion via API Google
│
├── data/
│ ├── Dataset_filtre_pour_entrainement_ML.xlsx # Jeu d’entraînement
│ └── Demo_brut_V2.xlsx # Exemple d’entrée
│
├── models/
│ ├── classification_models.pkl
│ └── label_encoders.pkl
│
├── outputs/
│ ├── Demo_classifié_final.xlsx
│ └── Statistiques_Remplissage.xlsx
│
├── README_Francais.md              # Version française du README
├── README_English.md               # Version anglaise du README
│
├── requirements.txt
└── .gitignore
```
---

## **3. Composantes et déroulement**

Le script **main.py** orchestre toutes les étapes du pipeline, du nettoyage des données à la génération du fichier final.

- **Étape 0 – Entraînement du modèle ML (optionnel)**  
  Entraîne un modèle de classification sur un jeu de données existant, puis sauvegarde les modèles (.pkl) pour réutilisation automatique.

- **Étape 1 – Complétion via OpenFoodFacts**  
  Recherche les produits manquants dans la base publique OpenFoodFacts pour remplir les colonnes *Désignation* et *Marque*.

- **Étape 2 – Extraction du contenant (Regex)**  
  Détecte le format du produit (ex. “6x250 g”, “500 ml”) et calcule une valeur standardisée pour la colonne *Contenant*.

- **Étape 3 – Classification automatique (ML)**  
  Prédit les catégories (*Famille*, *Sous-famille*, *Segment*) selon la désignation du produit, en respectant la hiérarchie entre ces niveaux.

- **Étape 4 – Recherche via API Google**  
  Complète la *Marque* ou la *Désignation* manquante en analysant les premières pages web trouvées.

- **Étape 5 – Export et rapport final**  
  Génère un fichier Excel enrichi et un rapport de taux de remplissage avant/après traitement.

---

## **4. Input et output**

- **Input** : fichier Excel brut (exemple : `data/Demo_brut_V2.xlsx`)  
- **Output** : fichier Excel enrichi (exemple : `outputs/Demo_classifié_final.xlsx`)  

### **Exemple d’enrichissement**

#### Avant traitement
| EAN           | Désignation              | Marque   | Famille | Sous-famille | Segment | Contenant |
|---------------|--------------------------|----------|---------|--------------|----------|-----------|
| 8721082004091 | POP CORN CARAMEL BIO 75G | NON CREE | 9999    | (vide)       | (vide)  | (vide)    |

#### Après traitement
| EAN           | Désignation (après)       | Marque (après)                             | Famille (prédit) | Sous-famille (prédit) | Segment (prédit) | Contenant (calculé) |
|---------------|---------------------------|--------------------------------------------|------------------|-----------------------|------------------|---------------------|
| 8721082004091 | Pop Corn Caramel Bio 75 g | Rempli automatiquement (API OpenFoodFacts / Google) | Épicerie salée   | Farines / Aides pâtisseries | Aide pâtisserie   | 0,075 kg           |

> **Remarques :**
> - *Désignation* : normalisée automatiquement.  
> - *Marque* : complétée via OpenFoodFacts ou recherche Google.  
> - *Famille / Sous-famille / Segment* : prédits par le modèle ML hiérarchique.  
> - *Contenant* : calculé à partir du format du produit (ex. “75G”).

---

## **5. Limites et améliorations**

### **Limites actuelles**

Trois principaux points freinent encore la performance du pipeline :

- **Dépendance aux sources externes** : la qualité et la couverture des bases publiques varient selon les catégories de produits. Les limitations d’usage des services gratuits (comme Google) ralentissent les traitements à grande échelle.  
- **Qualité des données d’entraînement** : les modèles actuels produisent souvent des résultats plus précis que la base d’origine, mais leurs performances restent limitées par la qualité initiale des données. Tant que les sources contiennent des erreurs ou des informations incomplètes, la progression reste plafonnée.  
- **Usage des modèles de langage (LLM)** : bien qu’ils n’aient pas été intégrés directement au pipeline, des outils comme *ChatGPT* ont joué un rôle important dans l’analyse, la vérification et l’automatisation partielle des tâches. Leur potentiel reste élevé, mais leur intégration complète est freinée par les contraintes actuelles du secteur de l’IA — coûts élevés, forte consommation d’énergie et infrastructures encore limitées.

### **Pistes d’amélioration**

Des progrès restent possibles à court terme, avec un budget et des ressources raisonnables :

- **Améliorer l’accès aux données** : utiliser des sources plus fiables ou étendre les droits d’accès à des services payants pour garantir une meilleure couverture et des résultats plus rapides.  
- **Renforcer l’apprentissage automatique** : enrichir le jeu de données avec des exemples plus variés et améliorer la logique de vérification automatique pour fiabiliser encore les classifications.  
- **Mieux exploiter les LLMs** : adopter des solutions professionnelles ou des interfaces API plus économiques, permettant d’intégrer ces outils de manière plus fluide dans le pipeline et d’accroître le niveau d’automatisation.

---

📘 *Dernière mise à jour : octobre 2025*  
Auteur : **Yuchen LU**
