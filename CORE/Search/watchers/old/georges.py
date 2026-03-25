# CORE/Watchers/GEORGES.py
import os
import time

import logging

import cloudscraper
import numpy as np
import pandas as pd
import random
import requests

from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from CORE.Services.setup import *
from CORE.Services.parser import ProductDataParser
from CORE.Services.user import UserService



# ======= LOGGING SYSTEM ========
LOG = logging.getLogger(__name__)
# ===============================

class FGwatcher:

    """
    Watcher class for Fernand Georges (georges.be).
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
        
        self.DB = os.path.join(DATABASE_FOLDER, "FGproductsDB.csv")

        # === INTERNAL SERVICE(S) ===
        self.parser = ProductDataParser(brands_file_path=os.path.join(UTILS_FOLDER, 'brands.json'))

        # === PARAMETERS & OPTIONS SETUP (CloudSCRAPER) ===
        self.requests = cloudscraper.create_scraper()

        self.REQUESTS_HEADERS = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            'Referer': 'https://www.georges.be/',
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

    def _extract_DBproduct(self, ITEM: str) -> Optional[Dict[str, Any]]:
        
        """Extracts key data from embedded JSON-LD scripts, prioritizing the 'Product' schema."""
        
        if not os.path.exists(self.DB):
            print(f"Main database not found: {self.DB}")
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
            print(f"An error occured during DB search for the folliwing item {ITEM}: {e}")
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
            'Entreprise': "GEORGES",
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
                            (len(soup.find_all("meta", itemprop="price")) >= 2) and 
                            (htva_tag := soup.find_all("meta", itemprop="price")[1]) and 
                            self.parser.parse_price(htva_tag.get('content'))
                        ),
                        tva=(
                            (len(soup.find_all("meta", itemprop="price")) >= 1) and 
                            (tva_tag := soup.find_all("meta", itemprop="price")[0]) and 
                            self.parser.parse_price(tva_tag.get('content'))
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
                print(f"An error occured during the extraction for the following product {DATA.get('Article')}: {e}")
                
                self.ATTEMPT+=1
                if self.ATTEMPT == self.MAX_RETRIES:
                    print(f"Aborting after {self.MAX_RETRIES} attempts for the following product {DATA.get('Article')}")

                    return PRODUCTvar
                
                else:
                    time.sleep(self.RETRY_DELAY)


    def run(self):

        CSVpath = os.path.join(RESULTS_SUBFOLDER_TEMP, "FGproducts.csv")
        XLSXpath = os.path.join(RESULTS_SUBFOLDER_TEMP, "FGproducts.xlsx")

        CACHEdata = self._cache_checker(path=CSVpath)

        PRODUCTS: List[dict] = []

        try:
            for ITEM in self.items:
                
                if CACHED := self._cache_checker(cache_df=CACHEdata, item=ITEM):
                    print(f"Produit {ITEM} récupéré depuis le cache")
                    
                    PRODUCTS.append(CACHED)
                    continue

                else:
                    DATA = self._extract_DBproduct(ITEM=ITEM)
                    DATA = self._extract_FINALproduct(DATA=DATA)
                    if DATA:
                        PRODUCTS.append(DATA)
                    time.sleep(random.uniform(1.5, 3))
        
        except Exception as e:
            print(f"Erreur fatale dans FGwatcher: {e}")

        df = pd.DataFrame(PRODUCTS)
        df.to_csv(CSVpath, index=False, encoding='utf-8-sig')
        df.to_excel(XLSXpath, index=False)

        print("Processus FGwatcher terminé...")

        return df



# === Independent running system for potential testing ===
if __name__ == "__main__":

    items = ["Scie circulaire plongeante Makita SP6000J1"]

    config_service = UserService(
        user_config_path=USER_CONFIG_PATH,
        catalog_config_path=CATALOG_CONFIG_PATH
    )

    FGwatcher = FGwatcher(items=items, config=config_service)
    df = FGwatcher.run()

    print(df)