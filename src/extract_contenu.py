# extract_contenu.py

import pandas as pd
import re
import numpy as np
import unicodedata

# --- conversion unitaire -> kg (approximer 1 L = 1 kg) ---
def _to_kg(val: float, unit: str) -> float | None:
    unit = unit.lower()
    if unit in ("g", "gr"):
        return val / 1000.0
    if unit == "kg":
        return val
    if unit == "ml":
        return val / 1000.0
    if unit == "cl":
        return (val * 10) / 1000.0      # 1 cl = 10 ml
    if unit == "dl":
        return (val * 100) / 1000.0     # 1 dl = 100 ml
    if unit == "l":
        return val
    return None

def extract_contenu(designation):
    """
    Extrait le contenu total en kg à partir d'une désignation produit.
    Gère: g/gr, kg, ml/cl/dl/l ; décimales avec VIRGULE ou POINT ; formats 3x20g et 20g x3.
    Retourne float (kg) ou None si non déductible.
    """
    if pd.isna(designation) or not isinstance(designation, str):
        return None

    s = unicodedata.normalize("NFKC", designation).lower()
    s = s.replace("×", "x")
    s = s.replace(",", ".")                 # décimales FR -> EN
    s = re.sub(r"\s+", " ", s).strip()      # espaces normalisés

    # Motifs
    units = r"(?:kg|g|gr|ml|l|cl|dl)\b"

    # 1) q x val unit   ex: "3 x 20 g", "2x0.5 l"
    pat_qx = re.compile(rf"(?P<q>\d+)\s*x\s*(?P<val>\d+(?:\.\d+)?)\s*(?P<u>{units})", re.I)

    # 2) val unit x q   ex: "20 g x 3", "0.5 l x2"
    pat_xq = re.compile(rf"(?P<val>\d+(?:\.\d+)?)\s*(?P<u>{units})\s*x\s*(?P<q>\d+)", re.I)

    # 3) simple         ex: "75 g", "0.5 l"
    pat_one = re.compile(rf"(?<!\d)(?P<val>\d+(?:\.\d+)?)\s*(?P<u>{units})", re.I)

    # Essai 1 : q x val unit
    m = pat_qx.search(s)
    if m:
        q = float(m.group("q"))
        val = float(m.group("val"))
        u = m.group("u").lower()
        if u == "gr": u = "g"
        kg = _to_kg(val, u)
        return round(q * kg, 3) if kg is not None else None

    # Essai 2 : val unit x q
    m = pat_xq.search(s)
    if m:
        q = float(m.group("q"))
        val = float(m.group("val"))
        u = m.group("u").lower()
        if u == "gr": u = "g"
        kg = _to_kg(val, u)
        return round(q * kg, 3) if kg is not None else None

    # Essai 3 : simple
    m = pat_one.search(s)
    if m:
        val = float(m.group("val"))
        u = m.group("u").lower()
        if u == "gr": u = "g"
        kg = _to_kg(val, u)
        return round(kg, 3) if kg is not None else None

    return None

def fill_contenu_column(df, designation_col='Désignation', contenant_col='Contenant'):
    """
    Remplit 'Contenant' en kg UNIQUEMENT si la cellule est vide/NaN.
    """
    stats = {'total_rows': len(df), 'contenants_filled': 0}

    if contenant_col not in df.columns:
        df[contenant_col] = pd.Series(dtype='object')

    mask_to_fill = df[contenant_col].isna() | (df[contenant_col].astype(str).str.strip() == "")

    before = int(mask_to_fill.sum())
    df.loc[mask_to_fill, contenant_col] = df.loc[mask_to_fill, designation_col].apply(extract_contenu)
    after = int((df[contenant_col].isna() | (df[contenant_col].astype(str).str.strip() == "")).sum())

    stats['contenants_filled'] = before - after
    return df, stats
