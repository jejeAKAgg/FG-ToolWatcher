import numpy as np
import re

from bs4 import BeautifulSoup


# =======================
#  GLOBAL VARIABLE SETUP
# =======================
KNOWN_BRANDS = [
    "ABB", "Bosch", "Contimac", "Cembre", "Dewalt", "DL Chemicals", "Eaton", "Facom",
    "Festool", "Fluke", "Hager", "HellermannTyton", "Hikoki", "Karcher",
    "Klauke", "Knipex", "Kraftwerk", "Kranzle", "Legrand", "Makita", "Meno", "Milwaukee",
    "Petzl", "Phoenix Contact", "Rothenberger", "Schneider", "Siemens",
    "Solid", "Soudal", "Weidmüller", "Wago"
]

BLACKLIST_TERMS = ["ral", "color", "silirub", "silicone", "acrylique", "cartouche", "colle"]

REF_PATTERN = re.compile(r'\b[A-Z0-9\-\/]{4,15}\b')
POWER_OR_DIMENSION_PATTERN = re.compile(r'^\d+[\s]?(W|V|MM|AH|A|KG|M|CM|ML|G)$')
PACKS_OR_OTHER_PATTERN = ["SDS-MAX", "SDS-PLUS", "LXT", "LI-ION", "BOSCH", "MAKITA"]


# ============================
#   NAME FORMATTER FUNCTIONS
# ============================
def standardize_name(product_name: str, html: str | None = None) -> str:
    
    """
    Returns a standardized product name in the format 'Brand - Product Name'.
    Uses optional HTML input to better detect the brand.

    Args:
        product_name (str): Raw product name string.
        html (str | None): Optional HTML source to extract brand information.

    Returns:
        str: Standardized product name.
    
    """

    brand = extract_brand_from_all_sources(product_name, html)
    model, extracted_ref = extract_product_name(product_name)

    if brand:
        return f"[{extracted_ref}] {brand} - {model.upper()}"
    return f"[{extracted_ref}] {model.upper()}".strip()

def extract_brand(product_name: str) -> str | None:
    
    """
    Detects a known brand within the product name.

    Args:
        product_name (str): Raw product name string.

    Returns:
        str | None: Brand name in uppercase if found, else None.
    
    """

    for brand in KNOWN_BRANDS:
        if brand.lower() in product_name.lower():
            return brand.upper()
    return None

def extract_brand_from_all_sources(product_name: str, html: str | None = None) -> str | None:
    
    """
    Attempts to detect the brand from HTML (div with class 'fabricant') first,
    falling back to product name if HTML is not provided or brand not found.

    Args:
        product_name (str): Raw product name string.
        html (str | None): Optional HTML source.

    Returns:
        str | None: Detected brand in uppercase or None if not found.
    
    """

    if html:
        soup = BeautifulSoup(html, "html.parser")
        fabricant_tag = soup.find("div", class_="fabricant")
        if fabricant_tag:
            text = fabricant_tag.get_text(strip=True)
            for brand in KNOWN_BRANDS:
                if brand.lower() in text.lower():
                    return brand.upper()

    return extract_brand(product_name)

def clean_product_name(product_name: str) -> str:
    
    """
    Cleans unnecessary elements from the product name, such as quantities, sizes, 
    parenthesis content, color codes, references, and normalizes separators.

    Args:
        product_name (str): Raw product name.

    Returns:
        str: Cleaned product name.
    
    """

    EXTRACTEDref = None
    VALIDrefs = []


    name = product_name.strip()

    # Supprime le contenu entre parenthèses
    name = re.sub(r'\(.*?\)', '', name)

    # Supprime les RAL/codes couleur (RAL 5011, RAL5011)
    name = re.sub(r'\bRAL\s?-?\d{4}\b', '', name, flags=re.IGNORECASE)

    # Supprime les références types : EAN, REF, etc.
    name = re.sub(r'\b(Ref|Réf|EAN|CIPAC|Code)[\.:]?\s?\w+\b', '', name, flags=re.IGNORECASE)

    # Supprime les tailles / unités
    name = re.sub(r'\b\d+\s?(pcs|pièces|x|unités?|mm|cm|m|ml|g|kg)\b', '', name, flags=re.IGNORECASE)

    # Normalisation des séparateurs
    name = re.sub(r'[-_/|]+', ' ', name)
    name = re.sub(r'\s+', ' ', name)

    # Remplace les guillemets droits par des apostrophes pour éviter les problèmes Excel
    name = name.replace('"', "'")

    # --- NOUVELLE LOGIQUE D'EXTRACTION DE RÉFÉRENCE ---
    ref_matches = REF_PATTERN.findall(name)
    
    for candidate in ref_matches:
        # A. Condition pour REJETER les puissances/dimensions (Ex: '900W')
        # On vérifie si la chaîne correspond au pattern de rejet.
        if POWER_OR_DIMENSION_PATTERN.match(candidate.upper()):
            continue # Ignorer et passer au candidat suivant

        if candidate.upper() in PACKS_OR_OTHER_PATTERN:
            continue
            
        # B. Condition pour ACCEPTER : Doit contenir au moins une lettre pour être un code produit (ex: RP0900J)
        if any(c.isalpha() for c in candidate):
            VALIDrefs.append(candidate.upper())

    
    # --- 3. TRAITEMENT du MPN trouvé (s'il existe) ---
    if VALIDrefs:

        EXTRACTEDref = max(VALIDrefs, key=len)

        pattern = re.compile(re.escape(EXTRACTEDref), 0)
        name = pattern.sub('', name).strip()
        
    else:
        name = name

    return name.strip(), EXTRACTEDref

def extract_product_name(product_name: str) -> str:
    
    """
    Extracts the product name by removing the detected brand.

    Args:
        product_name (str): Raw product name.

    Returns:
        str: Product name with brand removed and formatted in title case.
    
    """

    brand = extract_brand(product_name)
    cleaned, extracted_ref = clean_product_name(product_name)

    if brand:
        # Supprime la marque du nom s'il y a correspondance
        pattern = re.compile(re.escape(brand), re.IGNORECASE)
        cleaned = pattern.sub('', cleaned).strip()

    return cleaned.title(), extracted_ref

def extract_product_ref(product_name: str) -> str:
    _, extracted_ref = clean_product_name(product_name)

    return extracted_ref


def parse_price(text: str | None) -> float | None:

    """
    Parses a price string into a float. Handles European formats and removes
    currency symbols, special spaces, and labels (HTVA, TTC).

    Args:
        text (str | None): Raw price string.

    Returns:
        float | None: Parsed price as float, or None if parsing fails.
    
    """

    if not text:
        return None

    # Supprime symboles monétaires, libellés inutiles, et espaces spéciaux
    clean = (
        text.replace('€', '')
            .replace('HTVA', '')
            .replace('TTC', '')
            .replace('\xa0', '')
            .replace('\u200e', '')
            .strip()
    )

    # Supprime tous les caractères non numériques sauf , et .
    clean = re.sub(r"[^\d,\.]", "", clean)

    # Si le prix est en format européen : "1.003,09"
    if ',' in clean and clean.count('.') >= 1:
        # On suppose que . est un séparateur de milliers
        clean = clean.replace('.', '').replace(',', '.')
    elif ',' in clean:
        # Si uniquement une virgule, c'est probablement un séparateur décimal
        clean = clean.replace(',', '.')

    try:
        return float(clean)
    except ValueError:
        return None
    
def calculate_missing_price(htva: float | None, tva: float | None, tva_rate: float = 0.21) -> tuple[float | None, float | None]:
    
    """
    Calculates the missing HTVA or TVA price if the other is provided.

    Args:
        htva (float | None): Price excluding VAT.
        tva (float | None): Price including VAT.
        tva_rate (float, optional): VAT rate. Default is 0.21 (21%).

    Returns:
        tuple[float | None, float | None]: Tuple of (HTVA, TVA).
    
    """

    if htva is not None and tva is None:
        tva = htva * (1 + tva_rate)
    elif tva is not None and htva is None:
        htva = tva / (1 + tva_rate)
    return htva, tva
    
def format_price_for_excel(price: float | None) -> float:
    
    """
    Converts a raw price to a float rounded to 2 decimals for Excel.

    Args:
        price (float | None): Raw price value.

    Returns:
        float: Rounded float value, or np.nan if conversion fails.
    
    """
    
    try:
        return round(float(str(price).replace(",", ".")), 2)
    except (TypeError, ValueError):
        return np.nan