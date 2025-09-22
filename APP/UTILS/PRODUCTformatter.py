import numpy as np
import re
import time

from bs4 import BeautifulSoup

from typing import Optional

from APP.UTILS.LOGmaker import *



# ====================
#     LOGGER SETUP
# ====================
Logger = logger("PRODUCTformatter")


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
    model = extract_product_name(product_name)

    if brand:
        return f"{brand} - {model.upper()}"
    return model.upper()

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

    return name.strip()

def extract_product_name(product_name: str) -> str:
    
    """
    Extracts the product name by removing the detected brand.

    Args:
        product_name (str): Raw product name.

    Returns:
        str: Product name with brand removed and formatted in title case.
    
    """

    brand = extract_brand(product_name)
    cleaned = clean_product_name(product_name)

    if brand:
        # Supprime la marque du nom s'il y a correspondance
        pattern = re.compile(re.escape(brand), re.IGNORECASE)
        cleaned = pattern.sub('', cleaned).strip()

    return cleaned.title()

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

# ============================
#   REFs EXTRACTOR FUNCTIONS
# ============================
def extract_cipac_ref(soup):

    """
    Extracts the CIPAC reference from the parsed HTML.

    Args:
        soup (BeautifulSoup): Parsed HTML of the product page.

    Returns:
        str | None: CIPAC reference or None if not found.
    
    """

    p_ref = soup.find('p', class_='ref')
    if p_ref:
        text = p_ref.get_text(separator=' ').strip()  # on remplace les <br> par des espaces
        # Regex pour récupérer la valeur après "Réf. :"
        match = re.search(r'Réf\. :\s*(.+)', text)
        if match:
            return match.group(1).strip()
        
    return None

def extract_clabots_ref(soup):

    """
    Extracts the supplier reference for Clabots products.

    Args:
        soup (BeautifulSoup): Parsed HTML.

    Returns:
        str | None: Supplier reference or None if not found.
    
    """

    rows = soup.select('div.attribute-table__row')
    for row in rows:
        label = row.select_one('div.attribute-table__column__label')
        value = row.select_one('div.attribute-table__column__value')
        if label and value:
            if label.get_text(strip=True) == "Code article du fournisseur":
                return value.get_text(strip=True)
    return None

def extract_fixami_ref(soup):

    """
    Extracts the Fixami model code from HTML.

    Args:
        soup (BeautifulSoup): Parsed HTML.

    Returns:
        str | None: Model code or None if not found.
    
    """

    dt = soup.find('dt', string=lambda x: x and "Code du modèle" in x)
    if dt:
        dd = dt.find_next_sibling('dd')
        if dd:
            p = dd.find('p', attrs={'type': 'BODY_BOLD'})
            if p:
                return p.get_text(strip=True)
    return None

def extract_klium_ref(soup):

    """
    Extracts the Klium supplier reference from HTML, removing brand prefix.

    Args:
        soup (BeautifulSoup): Parsed HTML.

    Returns:
        str | None: Supplier reference or None if not found.
    
    """

    supplier_ref_li = soup.find('li', id='supplier_reference_value')
    if supplier_ref_li:
        span = supplier_ref_li.find('span')
        if span:
            span.extract()  # enlève le span
        
        ref_text = supplier_ref_li.get_text(strip=True)

        # Supprimer la marque si elle est en début de chaîne (insensible à la casse)
        for brand in KNOWN_BRANDS:
            if ref_text.lower().startswith(brand.lower() + ' '):
                # Enlever la marque + espace
                ref_text = ref_text[len(brand)+1:]
                break
        
        return ref_text
    return None

def extract_lecot_ref(soup):

    """
    Extracts the Lecot supplier reference from HTML.

    Args:
        soup (BeautifulSoup): Parsed HTML.

    Returns:
        str | None: Supplier reference or None if not found.
    
    """

    rows = soup.select('tr.properties-row')
    for row in rows:
        label = row.select_one('th.properties-label')
        value = row.select_one('td.properties-value')
        if label and value:
            if label.get_text(strip=True).lower() == "numéro de fournisseur":
                return value.get_text(strip=True)
    return None


# ============================
#  OFFERS EXTRACTOR FUNCTIONS
# ============================
def extract_offers_FIXAMI(soup: BeautifulSoup) -> Optional[str]:

    """
    Extracts quantity/price offers from Fixami product page.

    Args:
        soup (BeautifulSoup): Parsed HTML.

    Returns:
        str: Offers formatted as 'quantity: price€ (discount)', or '-' if none found.
    
    """

    offers = []

    for offer_block in soup.select("div.sc-cd80083d-1"):
        quantity_label = offer_block.select_one("label.sc-cd80083d-2")
        price_label = offer_block.select_one("label.sc-cd80083d-4")
        discount_label = offer_block.select_one("label.sc-cd80083d-5")

        if quantity_label and price_label:
            quantity_text = quantity_label.get_text(strip=True)
            price_text = price_label.get_text(strip=True).replace(',', '.')

            try:
                price = float(price_text)
            except ValueError:
                continue

            discount_text = f" ({discount_label.get_text(strip=True)})" if discount_label else ""
            offers.append(f"{quantity_text}: {price:.2f}€{discount_text}")

    return "\n".join(offers) if offers else "-"

def extract_offers_KLIUM(soup: BeautifulSoup) -> Optional[str]:

    """
    Extracts quantity/price offers from KLIUM product page.

    Args:
        soup (BeautifulSoup): Parsed HTML.

    Returns:
        str: Offers formatted as 'quantity: price€ (discount)', or '-' if none found.
    
    """

    offers = []

    # Sélectionne tous les blocs d'offres
    for offer_div in soup.select("div.prod_discount_btn"):
        label = offer_div.find("label", class_="prod_discount_label")
        if not label:
            continue
        
        quantity_span = label.select_one("span.label-discount-text")
        price_span = label.select_one("span.label-discount-price")
        discount_span = label.select_one("span.label-discount.discounted-price")

        if quantity_span and price_span:
            quantity_text = quantity_span.get_text(strip=True)
            price_text = price_span.get_text(strip=True).replace('\xa0', '').replace(',', '.').replace('€', '')
            try:
                price = float(price_text)
            except ValueError:
                continue

            discount_text = f" ({discount_span.get_text(strip=True)})" if discount_span else ""
            offers.append(f"{quantity_text}: {price:.2f}€{discount_text}")

    return "\n".join(offers) if offers else "-"