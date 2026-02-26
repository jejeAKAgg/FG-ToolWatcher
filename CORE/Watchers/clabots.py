# CORE/Watchers/GEORGES.py
import os
import time

import cloudscraper
import numpy as np
import pandas as pd
import random
import re
import requests

from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from thefuzz import fuzz, process
from typing import Dict, Any, Optional, List

from CORE.Services.setup import *
from CORE.Services.parser import ProductDataParser
from CORE.Services.user import UserService


class CLABOTSwatcher:

    """
    Watcher class for Clabots (clabots.be).
    It manages fetching data, local DB lookup, cache validation,
    and structured data extraction (JSON-LD first, then HTML fallback).
    """

    def __init__(self, items: str, config: UserService):
        
        # === INPUT VARIABLE(S) ===
        self.items = items
        self.config = config

        # === INTERNAL VARIABLE(S) ===
        self.ATTEMPT = 0
        self.CACHE_DELAY = self.config.get(key="cache_duration", default=3)
        self.DEFAULT_COLUMNS = [
            'Local REF', 'Entreprise', 'Article',
            'Base Price (HTVA)', 'Base Price (TVA)',
            'Price (HTVA)', 'Price (TVA)',
            'Price Evolution',
            'Offers',
            'ArticleURL',
            'Checked on',
        ]
        self.MAX_RETRIES = 3
        self.RETRY_DELAY = 5
        self.WAIT_TIME = 3
        
        self.DB = os.path.join(DATABASE_FOLDER, "CLABOTSproductsDB.csv")
        self.ArticleDB = self._db_loader()

        # === INTERNAL SERVICE(S) ===
        self.parser = ProductDataParser(brands_file_path=os.path.join(UTILS_FOLDER, 'brands.json'))

        # === PARAMETERS & OPTIONS SETUP (CloudSCRAPER) ===
        self.requests = cloudscraper.create_scraper()

        self.REQUESTS_HEADERS = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            'Referer': 'https://www.clabots.be/',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive'
        }

    def _cache_checker(self, path: Optional[str] = None, cache_df: Optional[pd.DataFrame] = None, item: Optional[str] = None) -> pd.DataFrame | dict | None:
        
        """
        Manages cache operations.
        - Mode 1 (path): Loads the entire cache file from the given path.
        - Mode 2 (cache_df, item): Checks if a specific item in the loaded DataFrame is still valid based on self.CACHE_DELAY.

        Args:
            path (Optional[str]): Path to the cache CSV file to load.
            cache_df (Optional[pd.DataFrame]): The already loaded cache DataFrame.
            item (Optional[str]): The specific 'Article' name to check in the cache.

        Returns:
            pd.DataFrame: If Mode 1 is used, returns the loaded DataFrame.
            dict: If Mode 2 is used and a valid cache hit is found, returns the row as a dictionary.
            None: If no cache file is found, or no valid cache hit is found for the item.
        """
        
        # === LOGIC ===
        # --- Mode 1: Loading cache file ---
        if path:
            if os.path.exists(path):
                try:
                    if os.path.getsize(path) == 0:
                        print(f"Cache file '{path}' is empty. Returning empty DataFrame.")
                        return pd.DataFrame(columns=self.DEFAULT_COLUMNS)
                    
                    df = pd.read_csv(path, encoding='utf-8-sig')
                    missing_cols = set(self.DEFAULT_COLUMNS) - set(df.columns)
                    
                    for col in missing_cols:
                        df[col] = None
                    return df[self.DEFAULT_COLUMNS]
                except pd.errors.EmptyDataError:
                    print(f"Cache file '{path}' is empty (EmptyDataError). Returning empty DataFrame.")
                    return pd.DataFrame(columns=self.DEFAULT_COLUMNS)
                except Exception as e:
                    print(f"Error loading cache '{path}': {e}")
                    return pd.DataFrame(columns=self.DEFAULT_COLUMNS)
            else:
                return pd.DataFrame(columns=self.DEFAULT_COLUMNS)
        
        # --- Mode 2: Checking for a specific item ---
        elif cache_df is not None and item:
            if cache_df.empty or 'Article' not in cache_df.columns:   # Check if DataFrame is empty or missing the key column
                return None

            row = cache_df[cache_df['Article'] == item]
            if row.empty:
                return None   # Item not in cache

            row_dict = row.iloc[0].to_dict()
            checked_on_str = row_dict.get("Checked on")

            try:   # Try to validate the timestamp
                last_checked = pd.to_datetime(checked_on_str)
                if datetime.now() - last_checked <= timedelta(days=self.CACHE_DELAY):
                    return row_dict   # Cache valid
            except Exception:
                return None   # Invalid timestamp, ...

            return None   # Cache too old
        
        # --- Default case (invalid arguments or no match) ---
        else:
            return None
        
    def _extract_mpns(self, text: str) -> set:
        
        """
        Extracts potential Manufacturer Part Numbers (MPNs) from a text string.
        An MPN is defined here as a mix of letters and numbers, at least 4 chars long.
        """
        
        if not isinstance(text, str):
            return set()
        
        # Convertit en majuscules pour une RegEx cohérente
        text_upper = text.upper()
        
        # RegEx pour trouver les MPNs (ex: DGA506Z, HR3200C, CDD12-FX-DD-AS)
        # Trouve les mots contenant à la fois des lettres et des chiffres
        mpns = re.findall(r'([A-Z]+[0-9]+[A-Z0-9-]*|[0-9]+[A-Z]+[A-Z0-9-]*)', text_upper)
        
        # Ajoute aussi les "mots" alphanumériques de 5+ caractères qui pourraient être des refs
        mpns.extend(re.findall(r'([A-Z0-9-]{5,})', text_upper))
        
        return set(mpn for mpn in mpns if len(mpn) > 3) # Nettoyage final
    
    def _custom_scorer(self, query: str, choice: str, mpn_weight: float = 0.7) -> int:
        """
        Custom weighted scorer V2.
        - Prioritizes matching the *entire set* of MPNs.
        - Uses a fallback score for general title similarity.
        """
        
        # --- 1. Extraire les *sets* de MPN ---
        query_mpns = self._extract_mpns(query)
        choice_mpns = self._extract_mpns(choice)
        
        mpn_score = 0

        # --- 2. Calcul du Score MPN (le plus important) ---
        # Convertir les sets en chaînes triées pour la comparaison
        q_mpn_str = " ".join(sorted(query_mpns))
        c_mpn_str = " ".join(sorted(choice_mpns))

        if q_mpn_str and c_mpn_str:
            # *LA CORRECTION CLÉ*
            # Compare les "sets de MPN" triés.
            # Pénalise lourdement les différences (ex: 1 MPN vs 4 MPN)
            mpn_score = fuzz.token_sort_ratio(q_mpn_str, c_mpn_str)
            
        elif not q_mpn_str and not c_mpn_str:
            # Si aucun titre n'a de MPN, on se base sur le titre
            mpn_score = fuzz.token_sort_ratio(query, choice)
            
        elif q_mpn_str and not c_mpn_str:
            # La requête a un MPN mais le choix n'en a pas
            mpn_score = 0 # Grosse pénalité
        
        else: # c_mpn_str and not q_mpn_str
            mpn_score = 0

        # --- 3. Calcul du Score Titre (pour le contexte/bruit) ---
        # Utilise token_set_ratio pour ignorer le "bruit" (mots en plus)
        title_score = fuzz.token_set_ratio(query, choice)

        # --- 4. Score final pondéré ---
        title_weight = 1.0 - mpn_weight
        final_score = (mpn_score * mpn_weight) + (title_score * title_weight)
        
        # Cas spécial: Si le match MPN est parfait (100) mais que le 
        # titre est très différent (ex: DGA506Z vs Combopack), on se
        # fie au mpn_score qui sera bas.
        # Si le match MPN est parfait (ex: DGA506Z vs DGA506Z), 
        # le title_score (élevé) confirmera le match.
        
        return int(final_score)
    
    def _match_checker(self, item: str, score_cutoff: int = 89) -> Optional[str]:
        
        """
        Finds the best match for 'item' in the Clabots product list 
        using fuzzy string matching.

        Args:
            item (str): The FG article name to search for.
            score_cutoff (int): The minimum similarity score (0-100) to 
                                consider a match valid.

        Returns:
            Optional[str]: The best-matching Clabots article name, 
                           or None if no match reaches the score_cutoff.
        """
        
        """
        Custom weighted scorer that prioritizes MPN matching.
        """
        
        if not self.ArticleDB: 
            print("Clabots product list is empty. Matching impossible.")
            return None

        # process.extractOne trouve le meilleur choix en utilisant notre fonction
        best_match = process.extractOne(
            item, 
            self.ArticleDB, 
            scorer=self._custom_scorer  # <-- ✨ UTILISE LE SCOREUR "MAISON"
        )

        # Nous gardons un score_cutoff de 85 pour commencer.
        # Nos scores pondérés devraient être plus fiables.
        if best_match and best_match[1] >= score_cutoff:
            print(f"Match found for '{item}': '{best_match[0]}' (Score: {best_match[1]}%)")
            return best_match[0]
        elif best_match:
            print(f"No sufficient match for '{item}' (Best score: {best_match[1]}% with '{best_match[0]}').")
            return None
        else:
            print(f"No match found for '{item}'.")
            return None
    
    def _db_loader(self) -> List[str]:
        
        """
        Loads the 'Article' column from the Clabots DB for fuzzy matching.
        """
        
        if not os.path.exists(self.DB):
            print(f"CLABOTS database not found for matching: {self.DB}")
            return []
        try:
            # We only read the 'Article' column to save memory
            df = pd.read_csv(self.DB, usecols=['Article'], encoding='utf-8-sig')
            df.dropna(subset=['Article'], inplace=True)
            # Returns a unique list of all article names
            return df['Article'].astype(str).unique().tolist()
        except Exception as e:
            print(f"Error loading CLABOTS DB for matching: {e}")
            return []

    def _extract_DBproduct(self, ITEM: str) -> Optional[Dict[str, Any]]:
        
        """Extracts key data from embedded JSON-LD scripts, prioritizing the 'Product' schema."""
        
        if not os.path.exists(self.DB):
            print(f"Base de données principale non trouvée: {self.DB}")
            return None

        try:
            df = pd.read_csv(self.DB, encoding='utf-8-sig') 
            search_term = str(ITEM).strip()
            
            mask = (df['Article'] == search_term)
            result = df[mask]
            
            if not result.empty:
                return result.iloc[0].to_dict()
                
            return None

        except Exception as e:
            print(f"Erreur lors de la recherche DB pour {ITEM}: {e}")
            return None
    

    def _extract_FINALproduct(self, DATA: Optional[Dict[str, Any]] = None):

        """
        Fetches the product page, attempts JSON-LD extraction, and falls back to HTML parsing.
        Uses initial_data (DB row) for pre-filling known values.
        """
        
        # === INTERNAL VARIABLE(S) ===
        self.ATTEMPT = 0
        self.MAX_RETRIES = 3
        self.RETRY_DELAY = 5

        # === INTERNAL PARAMETER(S) ===
        PRODUCTvar = {
            'Local REF': DATA.get('Local REF', '-'),
            'Entreprise': "CLABOTS",
            'Article': DATA.get('Article', '-'),
            'Base Price (HTVA)': DATA.get('Base Price (HTVA)', np.nan),
            'Base Price (TVA)': DATA.get('Base Price (TVA)', np.nan),
            'Price (HTVA)': np.nan,
            'Price (TVA)': np.nan,
            'Price Evolution': "-",
            'Offers': "-",
            'ArticleURL': DATA.get('ArticleURL', '-'),
            'Checked on': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # === SEARCH ENGINE ===
        while self.ATTEMPT < self.MAX_RETRIES:
            try:
                response = self.requests.get(DATA.get('ArticleURL'), headers=self.REQUESTS_HEADERS)
                response.raise_for_status()
                
                time.sleep(self.WAIT_TIME)  # Loading time (JS)

                ARTICLEpage = response.content

                soup = BeautifulSoup(ARTICLEpage, "html.parser")

                # --- CHECK FOR JSON-LD DATA ---
                if soup.find_all('script', type='application/ld+json'):
                    print(f"Product JSON-LD found for item {DATA.get('Article')}. Proceeding with extraction...")
                    
                    continue
                
                # --- FALLBACK TO MANUAL EXTRACTION ---
                else:
                    print(f"No Product JSON-LD found for item {DATA.get('Article')}. Extracting manually...")
                    
                    # --- Price (HTVA) & (TVA) ---
                    HTVA, TVA = self.parser.calculate_missing_price(
                        htva=(
                            (e := soup.find("div", class_="price-htvac")) and
                            self.parser.parse_price(e.get_text(strip=True).split()[0])
                        ),
                        tva=(
                            (e := soup.select_one("p.your-price")) and
                            self.parser.parse_price(e.get_text(strip=True))
                        )
                    )

                    PRODUCTvar['Price (HTVA)'] = self.parser.format_price_for_excel(HTVA)
                    PRODUCTvar['Price (TVA)'] = self.parser.format_price_for_excel(TVA)

                    # --- Price Evolution ---
                    PRODUCTvar['Price Evolution'] = "-"

                    # --- Offers ---
                    PRODUCTvar['Offers'] = "-"

                    return PRODUCTvar
                
            except requests.exceptions.HTTPError as http_err:
                if response.status_code == 404:
                    print(f"Invalid link (404 Not Found). Saving failure for future skip: {DATA.get('ArticleURL')}")
                    
                    return PRODUCTvar
                else:
                    print(f"HTTP Error ({response.status_code}) for {DATA.get('ArticleURL')}: {http_err}")

                    return PRODUCTvar

            except Exception as e:
                print(f"Erreur lors de l'extraction des données pour le produit {DATA.get('Article')}: {e}")
                
                self.ATTEMPT+=1
                if self.ATTEMPT == self.MAX_RETRIES:
                    print(f"Abandon après {self.MAX_RETRIES} tentatives pour le produit {DATA.get('Article')}")

                    return PRODUCTvar
                
                else:
                    time.sleep(self.RETRY_DELAY)


    def run(self):

        CSVpath = os.path.join(RESULTS_SUBFOLDER_TEMP, "CLABOTSproducts.csv")
        XLSXpath = os.path.join(RESULTS_SUBFOLDER_TEMP, "CLABOTSproducts.xlsx")

        CACHEdata = self._cache_checker(path=CSVpath)

        PRODUCTS: List[dict] = []

        try:
            for ITEM in self.items:

                ITEM = self._match_checker(item=ITEM)
                
                if CACHED := self._cache_checker(cache_df=CACHEdata, item=ITEM):
                    print(f"Produit {ITEM} récupéré depuis le cache")
                    
                    PRODUCTS.append(CACHED)
                    continue

                else:
                    DATA = self._extract_DBproduct(ITEM=ITEM)
                    if DATA:
                        DATA = self._extract_FINALproduct(DATA=DATA)
                        if DATA:
                            PRODUCTS.append(DATA)
                    else:
                        print(f"Error: {ITEM} was matched but not found in Clabots DB.")
                    time.sleep(random.uniform(1.5, 3))
        
        except Exception as e:
            print(f"Erreur fatale dans CLABOTSwatcher: {e}")

        df = pd.DataFrame(PRODUCTS)
        df.to_csv(CSVpath, index=False, encoding='utf-8-sig')
        df.to_excel(XLSXpath, index=False)

        print("Processus CLABOTSwatcher terminé...")

        return df



# === Independent running system for potential testing ===
if __name__ == "__main__":

    items = ["Scie circulaire plongeante Makita SP6000J1"]

    config_service = UserService(
        user_config_path=USER_CONFIG_PATH,
        catalog_config_path=CATALOG_CONFIG_PATH
    )

    CLABOTSwatcher = CLABOTSwatcher(items=items, config=config_service)
    df = CLABOTSwatcher.run()

    print(df)