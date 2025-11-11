# CORE/Services/parser.py
import re
import json
from pathlib import Path
from typing import Set, Dict, Optional, Tuple

from bs4 import BeautifulSoup

# ==================================
#   CONSTANTS CONFIGURATION
# ==================================

# 1. Regex patterns are compiled once on class initialization.
#    We define them here for clarity.
REF_PATTERN = re.compile(r'\b[A-Z0-9\-\/]{4,15}\b')
POWER_OR_DIMENSION_PATTERN = re.compile(r'^\d+[\s]?(W|V|MM|AH|A|KG|M|CM|ML|G)$')

# 2. Renamed for clarity and converted to a Set for performance
INVALID_REF_TERMS = {"SDS-MAX", "SDS-PLUS", "LXT", "LI-ION", "BOSCH", "MAKITA"}

# 3. Regex for general name cleanup
PARENTHESIS_PATTERN = re.compile(r'\(.*?\)')
RAL_PATTERN = re.compile(r'\bRAL\s?-?\d{4}\b', re.IGNORECASE)
GENERIC_REF_PATTERN = re.compile(r'\b(Ref|Réf|EAN|CIPAC|Code)[\.:]?\s?\w+\b', re.IGNORECASE)
UNITS_PATTERN = re.compile(r'\b\d+\s?(pcs|pièces|x|unités?|mm|cm|m|ml|g|kg)\b', re.IGNORECASE)
SEPARATOR_PATTERN = re.compile(r'[-_/|]+')
WHITESPACE_PATTERN = re.compile(r'\s+')


class ProductDataParser:
    
    """
    Utility class for parsing, cleaning, and standardizing
    product data (names, brands, prices) from raw strings.
    """
    
    def __init__(self, brands_file_path: Path | str):
        """
        Initializes the parser by loading the list of brands.

        Args:
            brands_file_path (Path | str): Path to a JSON file
                                             containing a list of brands.
        """
        self.brands: Set[str] = self._load_brands(brands_file_path)

    def _load_brands(self, file_path: Path | str) -> Set[str]:
        """Loads brands from a JSON file and returns them as a lowercase Set."""
        try:
            p = Path(file_path)
            with p.open('r', encoding='utf-8') as f:
                brands_list = json.load(f)
            # Convert to Set and lowercase for fast lookups (O(1))
            return {brand.lower() for brand in brands_list}
        except FileNotFoundError:
            print(f"Error: Brands file '{file_path}' not found.")
            return set()
        except json.JSONDecodeError:
            print(f"Error: Brands file '{file_path}' is not valid JSON.")
            return set()

    # ============================
    #   NAME PARSING METHODS
    # ============================

    def parse_product_name(self, product_name: str, html: Optional[str] = None) -> Dict[str, Optional[str]]:
        
        """
        Main public method to parse a product name.
        Returns a structured dictionary.

        Args:
            product_name (str): Raw product name.
            html (Optional[str]): Source HTML of the page to help find the brand.

        Returns:
            Dict[str, Optional[str]]: A dictionary containing 'brand', 'reference', 
                                      'model', and 'standard_name'.
        """
        
        brand = self._find_brand(product_name, html)
        reference = self._find_reference(product_name)
        model = self._clean_model_name(product_name, brand, reference)

        # Final standardized name formatting
        ref_part = f"[{reference}]" if reference else "[NO_REF]"
        brand_part = brand.upper() if brand else "[NO_BRAND]"
        
        standard_name = f"{ref_part} {brand_part} - {model.upper()}".strip()

        return {
            "brand": brand.upper() if brand else None,
            "reference": reference,
            "model": model,
            "standard_name": standard_name
        }

    def _find_brand(self, product_name: str, html: Optional[str] = None) -> Optional[str]:
        
        """
        Attempts to find the brand, first via HTML, then in the product name.
        """
        
        # 1. Search in HTML (if provided)
        if html:
            try:
                soup = BeautifulSoup(html, "html.parser")
                fabricant_tag = soup.find("div", class_="fabricant")
                if fabricant_tag:
                    text = fabricant_tag.get_text(strip=True).lower()
                    for brand in self.brands:
                        if brand in text:
                            return brand
            except Exception:
                pass  # Ignore BS4 parsing errors

        # 2. Search in the product name
        name_lower = product_name.lower()
        for brand in self.brands:
            if brand in name_lower:
                return brand
        
        return None

    def _find_reference(self, product_name: str) -> Optional[str]:
        
        """
        Extracts the most likely reference (MPN) from the product name.
        """
        
        valid_refs = []
        
        # Use the global compiled regex
        ref_matches = REF_PATTERN.findall(product_name)

        for candidate in ref_matches:
            candidate_upper = candidate.upper()
            
            # Reject powers/dimensions (e.g., '900W')
            if POWER_OR_DIMENSION_PATTERN.match(candidate_upper):
                continue
            
            # Reject invalid terms (e.g., 'SDS-PLUS')
            if candidate_upper in INVALID_REF_TERMS:
                continue
                
            # Accept if it contains at least one letter (e.g., RP0900J)
            if any(c.isalpha() for c in candidate):
                valid_refs.append(candidate_upper)
        
        # Return the longest valid reference
        if valid_refs:
            return max(valid_refs, key=len)
        
        return None

    def _clean_model_name(self, product_name: str, brand: Optional[str], reference: Optional[str]) -> str:
        
        """
        Cleans the product name to keep only the "model".
        Removes already extracted info (brand, ref) and unnecessary info.
        """
        
        name = product_name.strip()

        # 1. Remove content inside parentheses
        name = PARENTHESIS_PATTERN.sub('', name)
        
        # 2. Remove RAL codes
        name = RAL_PATTERN.sub('', name)
        
        # 3. Remove generic references (Ref:, EAN:, etc.)
        name = GENERIC_REF_PATTERN.sub('', name)
        
        # 4. Remove sizes / units
        name = UNITS_PATTERN.sub('', name)
        
        # 5. Remove the brand if it was found
        if brand:
            brand_pattern = re.compile(re.escape(brand), re.IGNORECASE)
            name = brand_pattern.sub('', name)

        # 6. Remove the reference if it was found
        if reference:
            ref_pattern = re.compile(re.escape(reference), re.IGNORECASE)
            name = ref_pattern.sub('', name)
            
        # 7. Final normalization
        name = SEPARATOR_PATTERN.sub(' ', name) # Normalize separators into spaces
        name = WHITESPACE_PATTERN.sub(' ', name) # Replace multiple whitespaces
        name = name.replace('"', "'")           # Replace double quotes for Excel
        
        return name.strip().title() # Capitalize the first letter of each word


    # ============================
    #   STATIC METHODS (PRICE)
    # ============================
    # These functions do not need 'self' (the instance state).
    # We declare them as @staticmethod to call them directly
    # e.g.: ProductDataParser.parse_price("10,50 €")
    
    @staticmethod
    def parse_price(text: Optional[str]) -> Optional[float]:
        
        """
        Parses a price string into a float. Handles European formats 
        and removes currency symbols and labels.
        """
        
        if not text:
            return None
        
        # More robust cleaning
        clean = text.strip().lower()
        clean = (
            clean.replace('€', '')
                 .replace('htva', '')
                 .replace('ttc', '')
                 .replace('\xa0', '')  # Non-breaking space
                 .replace('\u200e', '') # Left-to-right mark
                 .strip()
        )
        
        # Keep only digits, commas, and periods
        clean = re.sub(r"[^\d,\.]", "", clean)

        # Conversion logic (European format "1.003,09" -> "1003.09")
        if ',' in clean and '.' in clean:
            clean = clean.replace('.', '').replace(',', '.')
        elif ',' in clean:
            clean = clean.replace(',', '.')

        try:
            return float(clean)
        except ValueError:
            return None

    @staticmethod
    def calculate_missing_price(htva: Optional[float], tva: Optional[float], 
                                tva_rate: float = 0.21) -> Tuple[Optional[float], Optional[float]]:
        
        """
        Calculates the missing VAT-exclusive (htva) or VAT-inclusive (tva)
        price if the other is provided.
        """
        
        if htva is not None and tva is None:
            tva = round(htva * (1 + tva_rate), 2)
        elif tva is not None and htva is None:
            htva = round(tva / (1 + tva_rate), 2)
        return htva, tva

    @staticmethod
    def format_price_for_excel(price: Optional[float]) -> float:
        
        """
        Formats a price for Excel (rounded float, or 'nan').
        Removes the numpy dependency.
        """
        
        if price is None:
            return float('nan')
        try:
            return round(float(price), 2)
        except (TypeError, ValueError):
            return float('nan')