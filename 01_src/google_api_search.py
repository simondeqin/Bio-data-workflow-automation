# google_api_search.py

import requests
import pandas as pd
import time, random, json, re
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

# === CONFIG ===
API_KEY = "AIzaSyDq859F2GSXtnO_FFo5ogGV_59Rdc_cZAQ"   # <- mets ta clé
CX_ID  = "038780f2ae47c4901"                          # <- mets ton CX
FREE_QUOTA = 100
REQUEST_COUNT = 0

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
]

MISSING_MARKERS = {"", "non cree", "non créé", "inconnu", "?", "nan", "none", "null"}

def _is_missing(x) -> bool:
    if x is None:
        return True
    s = str(x).strip().lower()
    return (s in MISSING_MARKERS)

def _norm_url(u: str, base: str | None = None) -> str:
    if not u:
        return ""
    parsed = urlparse(u)
    if not parsed.scheme:
        if u.startswith("//"):
            return "https:" + u
        return urljoin(base or "https://", u)
    return u

def google_search_official(query: str, num: int = 3) -> list[str]:
    """
    Appelle l'API Google Custom Search et renvoie une liste d'URLs.
    """
    global REQUEST_COUNT
    if REQUEST_COUNT >= FREE_QUOTA:
        print("🚫 Quota gratuit atteint. Arrêt de l'appel API.")
        return []

    url = "https://www.googleapis.com/customsearch/v1"
    params = {"key": API_KEY, "cx": CX_ID, "q": query, "num": min(max(num,1),10)}
    resp = requests.get(url, params=params, timeout=15)

    if resp.status_code != 200:
        print(f"❌ Erreur API: {resp.status_code}, {resp.text[:300]}")
        return []

    REQUEST_COUNT += 1
    items = resp.json().get("items", []) or []
    return [it.get("link") for it in items if it.get("link")]

def _load_json_safe(txt: str):
    try:
        return json.loads(txt)
    except Exception:
        return None

def _extract_brand_from_jsonld(obj) -> str | None:
    """
    Cherche un champ 'brand' (ou 'manufacturer') dans un JSON-LD Product.
    """
    def _brand_name(b):
        if isinstance(b, dict):
            # ex: {"@type":"Brand","name":"Solaray"}
            return b.get("name") or b.get("brand") or b.get("manufacturer")
        if isinstance(b, str):
            return b
        return None

    if isinstance(obj, list):
        for el in obj:
            name = _extract_brand_from_jsonld(el)
            if name:
                return name
        return None

    if not isinstance(obj, dict):
        return None

    types = obj.get("@type")
    # Parfois "@type" peut être une liste
    if isinstance(types, list):
        types = [t.lower() for t in types]
    elif isinstance(types, str):
        types = [types.lower()]
    else:
        types = []

    # Si Product détecté, on tente brand/manufacturer
    if any(t in {"product", "offer"} for t in types):
        for key in ("brand", "manufacturer"):
            if key in obj:
                name = _brand_name(obj[key])
                if name:
                    return str(name).strip()

    # Parfois le Product est imbriqué
    for key, val in obj.items():
        if isinstance(val, (dict, list)):
            name = _extract_brand_from_jsonld(val)
            if name:
                return name
    return None

def extract_brand_from_url(url: str) -> str | None:
    """
    Récupère la page et essaie d'extraire la marque via :
    - JSON-LD Product -> brand/manufacturer
    - meta tags (product:brand, og:brand, name='brand', itemprop='brand')
    - microdata itemprop="brand"
    """
    url = _norm_url(url)
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    try:
        resp = requests.get(url, headers=headers, timeout=12)
        resp.raise_for_status()
    except Exception as e:
        # print(f"⚠️ Fetch error on {url}: {e}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # 1) JSON-LD
    for script in soup.find_all("script", type="application/ld+json"):
        data = _load_json_safe(script.string or "")
        if data:
            name = _extract_brand_from_jsonld(data)
            if name:
                return name.strip()

    # 2) Meta tags usuels
    meta_candidates = [
        ("property", "product:brand"),
        ("property", "og:brand"),
        ("name", "brand"),
        ("itemprop", "brand"),
    ]
    for attr, val in meta_candidates:
        tag = soup.find("meta", attrs={attr: val})
        if tag:
            content = tag.get("content") or tag.get("value")
            if content and content.strip():
                return content.strip()

    # 3) Microdata générique itemprop=brand
    tag = soup.find(attrs={"itemprop": "brand"})
    if tag:
        # <meta itemprop="brand" content="Solaray"> ou <span itemprop="brand">Solaray</span>
        txt = (tag.get("content") or tag.get_text(" ")).strip()
        if txt:
            return txt

    # 4) Heuristique légère sur le titre (dernier recours : très prudent)
    title = (soup.title.get_text(" ").strip() if soup.title else "")
    # Cherche un pattern style "Marque : X" ou "Brand: X"
    m = re.search(r"(?:marque|brand)\s*[:：]\s*([A-Z][\w\- '&]+)", title, flags=re.I)
    if m:
        return m.group(1).strip()

    return None

# Mémoire simple pour éviter de re-parser plusieurs fois la même URL/EAN
_URL_BRAND_CACHE: dict[str, str] = {}
_EAN_RESULT_CACHE: dict[str, tuple[str|None, str|None]] = {}

def ean_to_brand_and_designation_official(ean: str, top_k_urls: int = 3) -> tuple[str | None, str | None]:
    if ean in _EAN_RESULT_CACHE:
        return _EAN_RESULT_CACHE[ean]

    query = f'"{ean}" produit'
    urls = google_search_official(query, num=top_k_urls)
    brand = None
    for u in urls:
        if not u:
            continue
        if u in _URL_BRAND_CACHE:
            brand = _URL_BRAND_CACHE[u]
        else:
            brand = extract_brand_from_url(u)
            if brand:
                _URL_BRAND_CACHE[u] = brand
        if brand:
            break

    designation = f"Produit {brand}" if brand else None
    _EAN_RESULT_CACHE[ean] = (brand, designation)
    return brand, designation

def fill_with_google_api(
    df: pd.DataFrame,
    designation_col: str = "Désignation",
    marque_col: str = "Marque",
    ean_col: str = "EAN",
    pause_min_sec: float = 0.8,
):
    """
    Remplit Marque/Désignation UNIQUEMENT si manquantes.
    - Ne modifie pas les valeurs déjà présentes.
    - Tente d'extraire la brand depuis les pages trouvées via l'API Google.
    """
    stats = {
        "eans_considered": 0,
        "api_calls": 0,
        "marque_filled_cells": 0,
        "designation_filled_cells": 0,
        "skipped_already_filled": 0,
        "failed_eans": 0,
    }

    # S'assurer que les colonnes existent
    for col in (designation_col, marque_col, ean_col):
        if col not in df.columns:
            df[col] = ""

    # Lignes où AU MOINS un des deux champs est manquant et EAN non vide
    def _row_needs_fill(row) -> bool:
        need_m = _is_missing(row.get(marque_col))
        need_d = _is_missing(row.get(designation_col))
        return (need_m or need_d) and bool(str(row.get(ean_col, "")).strip())

    needs = df[df.apply(_row_needs_fill, axis=1)]
    unique_eans = needs[ean_col].dropna().astype(str).str.strip().unique()
    stats["eans_considered"] = len(unique_eans)

    print(f"🔎 Google API: {len(unique_eans)} EAN(s) à traiter (remplissage conditionnel).")

    for i, ean in enumerate(unique_eans, 1):
        # Vérifier si VRAIMENT nécessaire (toutes les lignes de cet EAN déjà remplies ?)
        subset = df[df[ean_col].astype(str).str.strip() == ean]
        all_marque_ok = subset[marque_col].apply(lambda x: not _is_missing(x)).all()
        all_desig_ok = subset[designation_col].apply(lambda x: not _is_missing(x)).all()
        if all_marque_ok and all_desig_ok:
            stats["skipped_already_filled"] += len(subset)
            continue

        # Appel API + parsing des pages
        brand, designation = ean_to_brand_and_designation_official(ean, top_k_urls=3)
        # Comptage approximatif des appels API (1 par ean quand on n'a pas le cache)
        global REQUEST_COUNT
        stats["api_calls"] = REQUEST_COUNT

        if not brand and not designation:
            stats["failed_eans"] += 1
        else:
            # Remplir uniquement les cellules manquantes
            mask_ean = df[ean_col].astype(str).str.strip() == ean

            # Marque
            if brand:
                mask_missing_marque = df[marque_col].apply(_is_missing)
                filled = mask_ean & mask_missing_marque
                n = int(filled.sum())
                if n:
                    df.loc[filled, marque_col] = brand
                    stats["marque_filled_cells"] += n

            # Désignation (si tu veux la même logique)
            if designation:
                mask_missing_desig = df[designation_col].apply(_is_missing)
                filled = mask_ean & mask_missing_desig
                n = int(filled.sum())
                if n:
                    df.loc[filled, designation_col] = designation
                    stats["designation_filled_cells"] += n

        # petit sleep pour être gentil
        time.sleep(random.uniform(pause_min_sec, pause_min_sec + 0.7))

    return df, stats

