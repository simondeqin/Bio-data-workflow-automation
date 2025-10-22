# ml_qualification.py

import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sentence_transformers import SentenceTransformer

def get_st_model():
    """Returns the SentenceTransformer model if installed, otherwise None."""
    try:
        from sentence_transformers import SentenceTransformer
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        return SentenceTransformer(model_name)
    except ImportError:
        print("Warning: 'sentence-transformers' library is not installed. ML models will not work.")
        return None

def train_classification_models(df, text_col='Désignation', label_cols=['Famille', 'Sous-famille', 'Segment']):
    """
    Trains and saves machine learning models for hierarchical product classification.
    
    Args:
        df (pd.DataFrame): The input DataFrame.
        text_col (str): The name of the text column for features.
        label_cols (list): A list of column names for the labels (e.g., ['Famille', 'Sous-famille', 'Segment']).
    
    Returns:
        tuple: A tuple of trained models and their corresponding label encoders.
    """
    df = df.dropna(subset=[text_col] + label_cols).copy()
    
    encoders = {col: LabelEncoder() for col in label_cols}
    for col in label_cols:
        df[f'{col}_encoded'] = encoders[col].fit_transform(df[col].astype(str).str.strip())
        
    X_text = df[text_col].tolist()
    
    st_model = get_st_model()
    if st_model is None:
        return None, None
        
    X_emb = st_model.encode(X_text, show_progress_bar=False, normalize_embeddings=True)
    
    models = {}
    for col in label_cols:
        y = df[f'{col}_encoded'].values
        clf = LogisticRegression(multi_class='multinomial', solver='lbfgs', max_iter=1000, n_jobs=-1)
        clf.fit(X_emb, y)
        models[col] = clf
        
    joblib.dump(models, 'classification_models.pkl')
    joblib.dump(encoders, 'label_encoders.pkl')
    
    print("Models and encoders saved to 'classification_models.pkl' and 'label_encoders.pkl'")
    
    return models, encoders

def evaluate_models(df, text_col='Désignation', label_cols=['Famille', 'Sous-famille', 'Segment']):
    """
    Splits data, trains models, and prints accuracy scores. This function is for evaluation purposes.
    
    Args:
        df (pd.DataFrame): The training DataFrame.
        text_col (str): The name of the text column for features.
        label_cols (list): A list of column names for the labels.
    """
    df_eval = df.dropna(subset=[text_col] + label_cols).copy()
    
    encoders = {col: LabelEncoder() for col in label_cols}
    for col in label_cols:
        df_eval[f'{col}_encoded'] = encoders[col].fit_transform(df_eval[col].astype(str).str.strip())
        
    X_text = df_eval[text_col].tolist()
    
    st_model = get_st_model()
    if st_model is None:
        return
        
    X_emb = st_model.encode(X_text, show_progress_bar=False, normalize_embeddings=True)
    
    # Split the data into training and test sets (80/20)
    X_train, X_test, y_f_train, y_f_test, y_sf_train, y_sf_test, y_seg_train, y_seg_test = train_test_split(
        X_emb, 
        df_eval['Famille_encoded'].values, 
        df_eval['Sous-famille_encoded'].values, 
        df_eval['Segment_encoded'].values, 
        test_size=0.2, 
        random_state=42, 
        stratify=df_eval['Famille_encoded'].values
    )

    models = {}
    print("\nTraining and evaluating models:")
    for i, (col, y_train, y_test) in enumerate(zip(label_cols, [y_f_train, y_sf_train, y_seg_train], [y_f_test, y_sf_test, y_seg_test]), 1):
        print(f"  - Model for '{col}'...")
        clf = LogisticRegression(multi_class='multinomial', solver='lbfgs', max_iter=1000, n_jobs=-1)
        clf.fit(X_train, y_train)
        y_pred = clf.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        print(f"  ✅ Accuracy for '{col}': {accuracy:.4f}")
        models[col] = clf
    
def predict_classification(df, text_col='Désignation', label_cols=['Famille', 'Sous-famille', 'Segment']):
    stats = {
        'status': 'Non exécuté',
        'famille_filled': 0,
        'sous_famille_filled': 0,
        'segment_filled': 0
    }
    
    try:
        models = joblib.load('classification_models.pkl')
        encoders = joblib.load('label_encoders.pkl')
        stats['status'] = 'Succès'
    except FileNotFoundError:
        print("❌ Erreur: Modèles non trouvés. Saut de l'étape de prédiction.")
        return df, stats
        
    st_model = get_st_model()
    if st_model is None:
        stats['status'] = 'Échec (dépendances manquantes)'
        return df, stats

    for col in label_cols:
        df[col] = df[col].astype(str).str.strip().str.lower()
        df[col] = df[col].replace(['nan', 'none'], 'divers famille')
    
    mask_to_predict = df['Famille'] == 'divers famille'
    df_to_predict = df[mask_to_predict].copy()
    
    if df_to_predict.empty:
        print("Aucune ligne à prédire pour la classification.")
        return df, stats
        
    X_text = df_to_predict[text_col].tolist()
    X_emb = st_model.encode(X_text, show_progress_bar=False, normalize_embeddings=True)

    predictions = {}
    for col, model in models.items():
        predicted_encoded = model.predict(X_emb)
        predictions[f'{col}_predicted'] = encoders[col].inverse_transform(predicted_encoded)
        
    df_predictions = pd.DataFrame(predictions, index=df_to_predict.index)
    
    for col in label_cols:
        df.loc[df_predictions.index, col] = df_predictions[f'{col}_predicted']
        filled_count = (df.loc[df_predictions.index, col].astype(str).str.lower() != 'divers famille').sum()
        key = col.lower().replace("-", "_")   # ex: "Sous-famille" -> "sous_famille"
        stats[f"{key}_filled"] = int(filled_count)
        
    # Normalize back to title case for cleaner output
    for col in label_cols:
        df[col] = df[col].astype(str).str.title()
    
    return df, stats