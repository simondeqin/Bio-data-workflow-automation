# api_openfoodfacts.py

import pandas as pd
import requests
import time
import numpy as np

def fill_with_openfoodfacts_api(df, designation_col='Désignation', marque_col='Marque', ean_col='EAN'):
    """
    Fills 'Désignation' and 'Marque' columns using the OpenFoodFacts API.
    
    Args:
        df (pd.DataFrame): The input DataFrame.
        designation_col (str): The name of the designation column.
        marque_col (str): The name of the brand column.
        ean_col (str): The name of the EAN column.
        
    Returns:
        pd.DataFrame: The modified DataFrame.
        dict: A dictionary with the fill statistics.
    """
    stats = {
        'total_rows': len(df),
        'designation_filled': 0,
        'marque_filled': 0,
        'api_calls': 0
    }
    
    df[designation_col] = df[designation_col].astype(str).str.strip().str.lower().replace(['nan', 'none'], 'inconnu')
    df[marque_col] = df[marque_col].astype(str).str.strip().str.lower().replace(['nan', 'none'], 'non cree')
    
    mask_designation = df[designation_col] == "inconnu"
    mask_marque = df[marque_col] == "non cree"
    mask_total = mask_designation | mask_marque
    
    df_api_subset = df[mask_total].copy()
    
    if df_api_subset.empty:
        print("No rows found to fill with OpenFoodFacts API.")
        return df, stats

    def get_info(ean):
        nonlocal stats
        url = f"https://world.openfoodfacts.org/api/v0/product/{ean}.json"
        try:
            response = requests.get(url, timeout=5)
            stats['api_calls'] += 1
            data = response.json()
            if data.get('status') == 1:
                product = data['product']
                return pd.Series({
                    'product_name_api': product.get('product_name', ''),
                    'brand_api': product.get('brands', '')
                })
        except Exception:
            return pd.Series({'product_name_api': '', 'brand_api': ''})
        return pd.Series({'product_name_api': '', 'brand_api': ''})
    
    df_api_subset[['product_name_api', 'brand_api']] = df_api_subset[ean_col].astype(str).apply(get_info)
    
    for idx in df_api_subset.index:
        # Update Designation
        if mask_designation.loc[idx] and pd.notna(df_api_subset.loc[idx, 'product_name_api']) and df_api_subset.loc[idx, 'product_name_api'].strip() != "":
            df.loc[idx, designation_col] = df_api_subset.loc[idx, 'product_name_api']
            stats['designation_filled'] += 1
        
        # Update Marque
        if mask_marque.loc[idx] and pd.notna(df_api_subset.loc[idx, 'brand_api']) and df_api_subset.loc[idx, 'brand_api'].strip() != "":
            df.loc[idx, marque_col] = df_api_subset.loc[idx, 'brand_api']
            stats['marque_filled'] += 1
            
    # Normalize back to title case for cleaner output
    df[designation_col] = df[designation_col].astype(str).str.title()
    df[marque_col] = df[marque_col].astype(str).str.title()
    
    return df, stats