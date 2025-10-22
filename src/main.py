# main.py

import pandas as pd
import time
import os
import numpy as np
import unicodedata

# Import modules from the current directory
import api_openfoodfacts
import google_api_search
import extract_contenu
import ml_qualification
from categories_dict import famille_dict, sous_famille_dict, segment_dict


# === File Configuration ===
INPUT_FILE = "../Fichiers_importés/Demo_brut_V2.xlsx"
TRAINING_DATA_FILE = "../Fichiers_importés/Dataset_filtre_pour_entrainement_ML.xlsx"

# ========================

def count_empty_values(df, columns):
    """
    Compte les valeurs vides pour les colonnes spécifiées, avec règles par colonne :
    - Désignation : vide, NaN, 'inconnu'
    - Marque : vide, NaN, 'non cree' (toutes variantes/accents)
    - Famille / Sous-famille / Segment : vide, NaN, 'divers', '9999'
    - Toujours : '', 'nan', 'none', 'null', '?'
    (comparaisons insensibles aux accents/majuscules/minuscules)
    """
    def _norm(s):
        s = str(s).strip().lower()
        # enlever accents
        s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
        return s

    def _is_empty(colname, value):
        if pd.isna(value):
            return True
        v = _norm(value)
        if v in {"", "nan", "none", "null", "?"}:
            return True

        col = _norm(colname)
        if col == "designation":
            return v in {"inconnu"}
        if col == "marque":
            # couvre: "non créé", "non créé", "non cree", etc. (accents enlevés)
            return v in {"non cree", "non creee"}
        if col in {"famille", "sous-famille", "sous famille", "segment"}:
            if v in {"divers", "9999", "divers famille"}:
                return True
            # si la cellule est un entier 9999 ou une chaîne "9999"
            try:
                return int(v) == 9999
            except Exception:
                pass
        return False

    stats = {}
    for col in columns:
        if col in df.columns:
            empty_mask = df[col].apply(lambda x: _is_empty(col, x))
            empty_count = int(empty_mask.sum())
            total_rows = int(len(df))
            stats[col] = {
                'total_rows': total_rows,
                'empty_count': empty_count,
                'filled_count': int(total_rows - empty_count),
                'empty_percentage': round(empty_count / total_rows * 100, 2) if total_rows else 0.0,
                'filled_percentage': round((total_rows - empty_count) / total_rows * 100, 2) if total_rows else 0.0,
            }
        else:
            stats[col] = {
                'total_rows': len(df),
                'empty_count': 'Colonne non trouvée',
                'filled_count': 'Colonne non trouvée',
                'empty_percentage': 'N/A',
                'filled_percentage': 'N/A'
            }
    return stats

def create_filling_rate_report(df_initial, df_final):
    """
    Crée un rapport simplifié des taux de remplissage avant et après traitement.
    
    Args:
        df_initial (pd.DataFrame): DataFrame initial (début du pipeline)
        df_final (pd.DataFrame): DataFrame après toutes les étapes
        
    Returns:
        pd.DataFrame: DataFrame avec les statistiques de remplissage
    """
    # Colonnes d'intérêt à analyser
    target_columns = ['Désignation', 'Marque', 'Contenant', 'Famille', 'Sous-famille', 'Segment']
    
    # Statistiques avant et après
    stats_initial = count_empty_values(df_initial, target_columns)
    stats_final = count_empty_values(df_final, target_columns)
    
    # Créer le rapport
    report_data = []
    
    for col in target_columns:
        if col in stats_initial and col in stats_final:
            initial_empty = stats_initial[col]['empty_count']
            final_empty = stats_final[col]['empty_count']
            total_rows = stats_initial[col]['total_rows']
            
            if isinstance(initial_empty, int) and isinstance(final_empty, int):
                filled_by_pipeline = initial_empty - final_empty
                improvement_rate = (filled_by_pipeline / initial_empty * 100) if initial_empty > 0 else 0
            else:
                filled_by_pipeline = 'N/A'
                improvement_rate = 'N/A'
            
            report_data.append({
                'Colonne': col,
                'Avant_Vides': initial_empty,
                'Après_Vides': final_empty,
                'Amélioration_%': round(improvement_rate, 2) if isinstance(improvement_rate, (int, float)) else improvement_rate,
                'Remplis_Par_Pipeline': filled_by_pipeline,
                'Total_Lignes': total_rows
            })
    
    # Créer le DataFrame du rapport
    report_df = pd.DataFrame(report_data)
    
    return report_df

def normalize_categories(df):
    """
    Normalizes column names and converts numeric category codes to text names,
    handling missing values during the conversion.
    
    Args:
        df (pd.DataFrame): The input DataFrame.
        
    Returns:
        pd.DataFrame: The DataFrame with normalized columns and categories.
    """
    # 1. Normalisation des noms de colonnes
    column_mapping = {
        'famille': 'Famille', 
        'sous famille': 'Sous-famille', 
        'sous-famille': 'Sous-famille',
        'segment': 'Segment',
        'désignation': 'Désignation',
        'marque': 'Marque',
        'contenant': 'Contenant',
        'ean': 'EAN',
        'codebarre': 'EAN'
    }
    
    # Normaliser d'abord les noms de colonnes
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', ' ')
    
    # Appliquer le mapping
    df.columns = [column_mapping.get(col, col.title()) for col in df.columns]
    
    print(f"Colonnes après normalisation: {list(df.columns)}")

    # 2. Inversion des dictionnaires pour la conversion
    famille_inv = {v: k for k, v in famille_dict.items()}
    sous_famille_inv = {v: k for k, v in sous_famille_dict.items()}
    segment_inv = {v: k for k, v in segment_dict.items()}
    
    # 3. Conversion des codes numériques en noms textuels
    for col, inv_dict in [('Famille', famille_inv), ('Sous-famille', sous_famille_inv), ('Segment', segment_inv)]:
        if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
            print(f"Conversion des codes numériques de la colonne '{col}' en noms textuels...")
            
            # Create a mask for NaN values
            is_nan_mask = df[col].isna()
            
            # Fill NaNs with a temporary value before converting to int, then map
            df[col] = df[col].fillna(-1).astype(int).map(inv_dict)
            
            # Replace the temporary value back with NaN
            df.loc[is_nan_mask, col] = np.nan
    
    return df

def run_pipeline():
    """
    Exécute le pipeline d'enrichissement de données.
    """
    start_time = time.time()
    print("Début du pipeline d'enrichissement de données...")

    if not os.path.exists(INPUT_FILE):
        print(f"Erreur: Le fichier d'entrée '{INPUT_FILE}' est introuvable.")
        return

    # === Étape 0: Préparation des modèles ML ===
    print("\nÉtape 0: Entraînement des modèles de Machine Learning (si nécessaire)...")
    if os.path.exists(TRAINING_DATA_FILE) and (not os.path.exists('classification_models.pkl') or not os.path.exists('label_encoders.pkl')):
        try:
            df_train = pd.read_excel(TRAINING_DATA_FILE)
            ml_qualification.train_classification_models(df_train)
            print("Modèles de classification entraînés et sauvegardés.")
        except ImportError:
            print("Échec de l'entraînement: 'sentence-transformers' non installé. Ignoré.")
    else:
        print("Fichier d'entraînement non trouvé ou modèles existants. Saut de l'entraînement.")

    try:
        df = pd.read_excel(INPUT_FILE)
        print(f"\nFichier d'entrée chargé: {len(df)} lignes.")
    except Exception as e:
        print(f"Erreur lors du chargement: {e}")
        return

    # === Étape de normalisation des colonnes et des catégories ===
    print("\nNormalisation des noms de colonnes et des catégories...")
    df = normalize_categories(df.copy())
    print("Normalisation terminée.")
    
    # Sauvegarde du DataFrame initial pour les statistiques
    df_initial = df.copy()
    
    # === Étape 1: Remplissage via l'API OpenFoodFacts ===
    print("\nÉtape 1/4: Remplissage 'Désignation' et 'Marque' via OpenFoodFacts...")
    df, stats_api = api_openfoodfacts.fill_with_openfoodfacts_api(df)
    print(f"Remplissage API terminé. Statut: {stats_api}")

    # === Étape 2: Extraction du 'Contenant' par Regex ===
    print("\nÉtape 2/4: Extraction du 'Contenant' via Regex...")
    df, stats_contenu = extract_contenu.fill_contenu_column(df)
    print(f"Extraction du contenant terminée. Statut: {stats_contenu}")

    # === Étape 3: Prédiction des catégories par ML ===
    print("\nÉtape 3/4: Prédiction des catégories par ML...")
    df, stats_ml = ml_qualification.predict_classification(df)
    print(f"Prédiction ML terminée. Statut: {stats_ml}")

    # === Étape 4: Remplissage via API Google ===
    print("\nÉtape 4/4: Remplissage 'Marque' via Google API...")
    df, stats_web = google_api_search.fill_with_google_api(df)
    print(f"API Google terminé. Statut: {stats_web}")

    # === Export du fichier final ===
    try:
        df.to_excel("../Fichiers_exportés/Demo_classifié_final.xlsx", index=False)
        end_time = time.time()
        print("\nPipeline terminé avec succès!")
        print(f"Fichier final exporté: 'Demo_classifié_final.xlsx'")
        print(f"Durée totale: {end_time - start_time:.2f} secondes.")
    except Exception as e:
        print(f"Erreur lors de l'exportation du fichier final: {e}")
        return

    # === Génération du rapport de statistiques final ===
    print("\nGénération du rapport statistiques final...")
    try:
        stats_report_final = create_filling_rate_report(df_initial, df)
        
        stats_report_final.to_excel("../Fichiers_exportés/Statistiques_Remplissage.xlsx", index=False)
        print("Rapport statistiques généré: 'Statistiques_Remplissage.xlsx'")
        
        # Affichage d'un résumé dans la console
        print("\nRÉSUMÉ DES TAUX DE REMPLISSAGE:")
        target_cols = ['Désignation', 'Marque', 'Contenant', 'Famille', 'Sous-famille', 'Segment']
        
        for col in target_cols:
            if col in df.columns:
                initial_empty = count_empty_values(df_initial, [col])[col]['empty_count']
                final_empty = count_empty_values(df, [col])[col]['empty_count']
                
                if isinstance(initial_empty, int) and isinstance(final_empty, int):
                    filled = initial_empty - final_empty
                    improvement_rate = (filled / initial_empty * 100) if initial_empty > 0 else 0
                    print(f"   {col}: {filled}/{initial_empty} remplis ({improvement_rate:.1f}% d'amélioration)")
                else:
                    print(f"   {col}: Données non disponibles")
        
        print(f"\nPipeline terminé en {end_time - start_time:.2f}s")
        
    except Exception as e:
        print(f"Erreur lors de la génération des statistiques finales: {e}")

if __name__ == "__main__":
    run_pipeline()