# CORE/__DATABASES/loader/klium.py
import os
import time

import logging

import cloudscraper
import csv
import gzip
import json
import pandas as pd
import random
import requests

from bs4 import BeautifulSoup
from datetime import datetime
from functools import reduce
from typing import List
from urllib.parse import unquote

from CORE.Services.setup import *
from CORE.Services.parser import ProductDataParser



# ======= LOGGING SYSTEM ========
LOG = logging.getLogger(__name__)
# ===============================

class KLIUMloader:
    
    """
    Class to download and extract product URLs and data from KLIUM.
    """
    
    def __init__(self):

        # === INTERNAL VARIABLE(S) ===
        self.ATTEMPT = 0
        self.MAX_RETRIES = 3
        self.RETRY_DELAY = 5
        self.SAVE_COUNTER = 0
        self.SAVE_THRESHOLD = 100
        self.WAIT_TIME = 3

        # === INTERNAL PARAMETER(S) ===
        self.SITEMAPindex = 'https://www.klium.be/sitemap.xml'
        self.SITEMAPurls: List[str] = []
        self.NAMESPACESurl = {'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        self.URLs: List[str] = []

        # === INTERNAL SERVICE(S) ===
        self.parser = ProductDataParser(brands_file_path=os.path.join(UTILS_FOLDER, 'brands.json'))

        # === PARAMETERS & OPTIONS SETUP (CloudSCRAPER) ===
        self.requests = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )

        self.REQUESTS_HEADERS = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            'Referer': 'https://www.klium.be/',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive',
            'DNT': '1' # Do Not Track
        }


    def _discover_sitemaps(self):
        
        """
        Dynamically retrieves product sitemap URLs (Sitemapp) from the KLIUM sitemap index.
        
        """
        
        try:
            response = self.requests.get(self.SITEMAPindex, headers=self.REQUESTS_HEADERS)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "xml")
            
            links = [
                loc.text.strip() 
                for loc in soup.find_all('loc')
            ]

            self.SITEMAPurls = links
            LOG.info(f"Discovered {len(self.SITEMAPurls)} product sitemaps via the index.")
        
        except Exception as e:
            LOG.error(f"Failed to retrieve KLIUM sitemap index: {e}")
    
    def _fetch_and_decompress_sitemap(self, link: str):
        
        """
        Downloads the sitemap (which may be a compressed .gz file) and returns the decompressed XML content.

        Args:
            link (str): The URL of the sitemap file (e.g., 'sitemap-index-1.xml' or 'sitemap-index-1.xml.gz').

        Returns:
            str | None: The decompressed XML content as a string, or None if the download or decompression fails.
        
        """

        LOG.info(f"Fetching sitemap: {link}...")
        
        try:
            response = self.requests.get(link, headers=self.REQUESTS_HEADERS)
            response.raise_for_status()

            time.sleep(self.WAIT_TIME)

            if link.endswith('.gz'):
                LOG.info("Content is GZIP compressed. Decompressing...")
                
                decompressed_content = gzip.decompress(response.content)
                return decompressed_content.decode('utf-8')
            else:
                return response.text
                
        except requests.exceptions.HTTPError as e:
            LOG.exception(f"HTTP Error {e.response.status_code} on sitemap: {link}")
            return None
        except Exception as e:
            LOG.exception(f"Error during decompression/fetch: {e}")
            return None

    def _load_DBurls(self, csv_path: str) -> set:
        
        """
        Loads already processed URLs from the existing DB for restart logic (cache checker).
        
        """
        
        if os.path.exists(csv_path):
            try:
                df_existing = pd.read_csv(csv_path, usecols=['ArticleURL'], encoding='utf-8-sig')
                existing_urls = set(df_existing['ArticleURL'].astype(str).tolist())   # Converting into set for better performance
                
                LOG.info(f"Existing database found for {csv_path}: {len(existing_urls)} URLs already processed.")
                return existing_urls
            except Exception as e:
                LOG.exception(f"Error loading existing DB: {e}. Full restart needed.")
                return set()
        return set()
    
    def _save_batch(self, csv_path: str, batch_data: List[dict], is_emergency: bool = False):
        
        """
        Saves the current batch of data by appending it to the existing database file.
        
        """

        if not batch_data:
            return
        
        NEWdf = pd.DataFrame(batch_data)
        
        COLS = ['EAN', 'MPN', 'Brand', 'Article', 'Base Price (HTVA)', 'Base Price (TVA)', 'ArticleURL', 'Checked on']

        try:
            # On boucle sur ta liste pour préparer chaque colonne selon son type
            for col in COLS:
                if col in NEWdf.columns:
                    if "Price" in col:
                        # C'est un prix : on force en float (SANS guillemets dans le CSV)
                        NEWdf[col] = pd.to_numeric(NEWdf[col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0.0).astype(float)
                    else:
                        # C'est du texte : on force en string (AVEC guillemets + conservation des 0)
                        NEWdf[col] = NEWdf[col].astype(str)

            # On réordonne les colonnes selon ta liste unique
            NEWdf = NEWdf[COLS]
            
            file_exists = os.path.exists(csv_path)

            if not file_exists:
                NEWdf.to_csv(csv_path,
                        index=False,
                        encoding='utf-8-sig',
                        quoting=csv.QUOTE_MINIMAL,
                        quotechar='"'
                )   
                
                LOG.info(f"New DB created with {len(NEWdf.index)} lines.")
            else:
                NEWdf.to_csv(csv_path,
                        mode='a',
                        header=not file_exists,
                        index=False,
                        encoding='utf-8-sig',
                        quoting=csv.QUOTE_MINIMAL,
                        quotechar='"'
                )
                
                if not is_emergency:
                    LOG.info(f"Batch saved.")
        
        except Exception as e:
            LOG.exception(f"CRITICAL: Failed to merge batch due to {e}.")


    def _extract_SITEMAPurls(self, link):
        
        """
        Downloads the sitemap and extracts all <loc> URLs (applying filtering logic).
        
        """
        
        LOG.info(f"Downloading sitemap: {link}...")

        # === INTERNAL VARIABLE(S) ===
        self.ATTEMPT = 0
        self.MAX_RETRIES = 3
        self.RETRY_DELAY = 5

        # === SEARCH ENGINE ===
        while self.ATTEMPT < self.MAX_RETRIES:
            try:
                ARTICLEpage = self._fetch_and_decompress_sitemap(link) 

                if ARTICLEpage is None:
                    LOG.error(f"Sitemap empty or unavailable for {link}")
                    
                    self.ATTEMPT += 1
                    time.sleep(self.RETRY_DELAY)
                    
                    continue # Retry the download

                soup = BeautifulSoup(ARTICLEpage, "xml")

                for loc_tag in soup.find_all('loc'):
                    PRODUCTurl = unquote(loc_tag.text.strip())
                    SEGMENTSdata = [w for w in PRODUCTurl.split('/') if w]

                    if len(SEGMENTSdata) < 3:
                        continue

                    if len(SEGMENTSdata[-1]) < 15:
                        continue

                    if SEGMENTSdata[1] not in ('www.klium.be', 'klium.be'):
                        continue

                    if any(S.lower() in {'nl', 'de', 'en', 'nl-be', 'nl-nl', 'de-de', 'en-be'} for S in SEGMENTSdata):
                        continue

                    if PRODUCTurl.endswith(('/', '.jpg', '.jpeg', '.png', '.gif', '.pdf')):
                        continue

                    self.URLs.append(PRODUCTurl)

                return list(set(self.URLs))  # Removing duplicates if any (though unlikely in a single sitemap)
            
            except Exception as e:
                LOG.exception(f"Error during sitemap extraction: {e}")
                
                self.ATTEMPT+=1
                if self.ATTEMPT == self.MAX_RETRIES:
                    LOG.warning(f"Abandoning after {self.MAX_RETRIES} attempts.")

                    return []
                
                else:
                    time.sleep(self.RETRY_DELAY)
    

    def _ONLINEextract_FINALproduct(self, link):

        # === INTERNAL VARIABLE(S) ===
        self.ATTEMPT = 0
        self.MAX_RETRIES = 3
        self.RETRY_DELAY = 5

        # === INTERNAL PARAMETER(S) ===
        PRODUCTvar = {
            'EAN': "-",
            'MPN': "-",
            'Brand': "-",
            'Article': "-",
            'Base Price (HTVA)': 0.0,
            'Base Price (TVA)': 0.0,
            'ArticleURL': link,
            'Checked on': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # === SEARCH ENGINE ===
        while self.ATTEMPT < self.MAX_RETRIES:
            try:

                response = self.requests.get(link, headers=self.REQUESTS_HEADERS)
                response.raise_for_status()
                
                time.sleep(self.WAIT_TIME)  # Loading time (JS)

                ARTICLEpage = response.content

                soup = BeautifulSoup(ARTICLEpage, "html.parser")

                JSONdata = next((i for s in soup.find_all('script', type='application/ld+json') for i in ([json.loads(s.string)] if isinstance(json.loads(s.string), dict) else (json.loads(s.string) if isinstance(json.loads(s.string), list) else [])) if isinstance(i, dict) and i.get("@type") == "Product"), {})

                PRODUCTvar["EAN"] = (lambda e: "".join(filter(str.isalnum, str(e))) or "-")(
                    next((li.get_text(strip=True).upper().replace("EAN:", "").strip() for li in soup.find_all("li") if "EAN:" in li.get_text().upper()), None) or
                    JSONdata.get('gtin13') or 
                    "-"
                ).upper()

                PRODUCTvar["MPN"] = (lambda raw, brands: (lambda b_sorted: (lambda res: res if res else "-")(" ".join(reduce(lambda s, b: s.replace(b.lower(), ""), b_sorted, str(raw).lower()).split()).strip().upper()))(sorted(brands, key=len, reverse=True)))(
                    (
                        ((v := soup.find("li", id="supplier_reference_value")) and v.get_text(strip=True).upper().replace("NUMÉRO D'ARTICLE DU FOURNISSEUR:", "").strip()) or 
                        JSONdata.get('mpn') or 
                        "-"
                    ),
                    self.parser.brands
                )

                PRODUCTvar['Brand'] = str(
                    (b := soup.find("li", class_="product-manufacturer")) and b.find("a").get_text(strip=True) or 
                    (isinstance(JSONdata.get('brand'), dict) and JSONdata.get('brand', {}).get('name') or JSONdata.get('brand', "-"))
                ).upper().strip()

                PRODUCTvar['Article'] = (
                    (n := soup.find("h1", id="product_name_value")) and n.get_text(strip=True) or 
                    JSONdata.get('name', "-")
                ).replace("\"", "\"\"").strip('"')

                PRODUCTvar['Base Price (HTVA)'], PRODUCTvar['Base Price (TVA)'] = (
                    lambda p: (
                        self.parser.format_price_for_excel(round(p / 1.21, 2)),
                        self.parser.format_price_for_excel(p),
                    )
                )(
                    (lambda raw: self.parser.parse_price(str(raw)) if raw not in (None, "-", "") else 0.0)(
                        (m := soup.find("span", class_="current-price-value")) and m.get("content") or 
                        (isinstance(o := JSONdata.get("offers"), list) and o and o[0].get("price") or (isinstance(o, dict) and o.get("price") or 0.0))
                    )
                )

                return PRODUCTvar
            
            except requests.exceptions.HTTPError as http_err:
                if response.status_code == 404:
                    LOG.warning(f"Invalid link (404 Not Found). Saving failure for future skip: {link}")
                    return PRODUCTvar 
                else:
                    LOG.exception(f"HTTP Error ({response.status_code}) for {link}: {http_err}")

                    self.ATTEMPT+=1
                    time.sleep(self.RETRY_DELAY)
            
            except Exception as e:
                LOG.exception(f"Error during data extraction for product {link}: {e}")
                
                self.ATTEMPT+=1
                time.sleep(self.RETRY_DELAY)

        LOG.warning(f"Abandoning after {self.MAX_RETRIES} attempts for product {link}")        
        return None
    

    def run(self):

        CSVpathDB = os.path.join(DATA_SUBFOLDER, "KLIUMproductsDB.csv")
        CSVpathDBnot = os.path.join(DATA_SUBFOLDER, "KLIUMproductsDBnot.csv")
        DBurls = self._load_DBurls(CSVpathDB)
        DBurlsNOT = self._load_DBurls(CSVpathDBnot)

        PRODUCTS: List[dict] = []
        FAILS: List[dict] = []

        try:

            self._discover_sitemaps()

            for SITEMAPurl in self.SITEMAPurls:
                self._extract_SITEMAPurls(SITEMAPurl)

            self.URLs = [url for url in self.URLs if url not in DBurls and url not in DBurlsNOT]

            LOG.info(f"Found link(s): {len(self.URLs)}")

            if self.URLs:
                for PRODUCTurl in self.URLs:
                    try:
                        data = self._ONLINEextract_FINALproduct(PRODUCTurl)

                        LOG.debug(data)     # [TESTING ONLY]

                        if data is None: continue
                        
                        if data and (data['MPN'] != "-" or data['EAN'] != "-") and not pd.isna(data['Base Price (HTVA)']) and data['Base Price (HTVA)'] > 0: PRODUCTS.append(data)
                        else: FAILS.append(data)
                        
                        self.SAVE_COUNTER+=1

                        if self.SAVE_COUNTER >= self.SAVE_THRESHOLD:
                            self._save_batch(CSVpathDB, PRODUCTS)
                            self._save_batch(CSVpathDBnot, FAILS)
                            
                            self.SAVE_COUNTER = 0
                            PRODUCTS = []
                            FAILS = []
                        
                        time.sleep(random.uniform(0.5, 1)) # Loading time (STABILITY)

                    except Exception as e:
                        LOG.exception(f"An unexpected error occurred for URL {PRODUCTurl}: {e}")
                        continue

                if PRODUCTS:
                    self._save_batch(CSVpathDB, PRODUCTS)

                    self.SAVE_COUNTER = 0
                    PRODUCTS = []
                
                if FAILS:
                    self._save_batch(CSVpathDBnot, FAILS)

                    self.SAVE_COUNTER = 0
                    FAILS = []
        
        except Exception as e:
            LOG.exception(f"Critical error for KLIUMloader: {e}")

            if PRODUCTS: # EMERGENCY SAVE
                self._save_batch(CSVpathDB, PRODUCTS, is_emergency=True)

                self.SAVE_COUNTER = 0
                PRODUCTS = []

                LOG.warning("Emergency save triggered due to critical error.")

            if FAILS: # EMERGENCY SAVE
                self._save_batch(CSVpathDBnot, FAILS, is_emergency=True)

                self.SAVE_COUNTER = 0
                FAILS = []

                LOG.warning("Emergency save for failures triggered due to critical error.")

        LOG.info("KLIUMloader process terminated...")



# === Independent running system ===
if __name__ == "__main__":

    KLIUMloader = KLIUMloader()
    result = KLIUMloader.run()