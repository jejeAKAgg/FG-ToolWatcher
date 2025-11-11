# CORE/__DATABASES/loader/clabots.py
import os
import time

import logging

import cloudscraper
import gzip
import pandas as pd
import random
import requests

from bs4 import BeautifulSoup
from datetime import datetime
from typing import List
from urllib.parse import unquote

from CORE.Services.setup import *
from CORE.Services.parser import ProductDataParser



# ======= LOGGING SYSTEM ========
LOG = logging.getLogger(__name__)
# ===============================

class CLABOTSloader:
    
    """
    Class to download and extract product URLs and data from CLABOTS.
    """

    def __init__(self):

        # === INTERNAL VARIABLE(S) ===
        self.ATTEMPT = 0
        self.MAX_RETRIES = 3
        self.RETRY_DELAY = 5
        self.SAVE_COUNTER = 0
        self.SAVE_THRESHOLD = 500
        self.WAIT_TIME = 3

        # === INTERNAL PARAMETER(S) ===
        self.SITEMAPurls: List[str] = [
            'https://www.clabots.be/media/sitemaps/1/sitemap-product-1.xml.gz',
            'https://www.clabots.be/media/sitemaps/1/sitemap-product-2.xml.gz',
        ]
        self.NAMESPACESurl = {'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        self.CATEGORYnames: List[str] = []
        self.URLs: List[str] = []

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


    # === INTERNAL METHOD(S) ===
    # --- FETCH & DECOMPRESS SITEMAP ---
    def _fetch_and_decompress_sitemap(self, link: str):
        
        """
        Downloads the sitemap (which may be a compressed .gz file) and returns the decompressed XML content.

        Args:
            link (str): The URL of the sitemap file (e.g., 'sitemap-index-1.xml' or 'sitemap-index-1.xml.gz').

        Returns:
            str | None: The decompressed XML content as a string, or None if the download or decompression fails.
        """

        print(f"Fetching sitemap: {link}...")
        
        try:
            
            response = self.requests.get(link, headers=self.REQUESTS_HEADERS)
            response.raise_for_status()

            time.sleep(self.WAIT_TIME)

            if link.endswith('.gz'):
                LOG.info("Content is GZIP compressed. Decompressing...")
                decompressed_content = gzip.decompress(response.content)
                return decompressed_content.decode('utf-8')
            else:
                LOG.info("Content is Sitemap. Reading...")
                return response.text
                
        except requests.exceptions.HTTPError as e:
            LOG.exception(f"HTTP Error {e.response.status_code} on sitemap: {link}")
            return None
        except Exception as e:
            LOG.exception(f"Error during decompression/fetch: {e}")
            return None

    # --- LOAD EXISTING DB URLS ---
    def _load_DBurls(self, csv_path: str) -> set:
        
        """
        Loads already processed URLs from the existing DB for restart logic (cache checker).
        """
        
        if os.path.exists(csv_path):
            try:
                df_existing = pd.read_csv(csv_path, usecols=['ArticleURL'], encoding='utf-8-sig')
                existing_urls = set(df_existing['ArticleURL'].astype(str).tolist())   # Converting into set for better performance
                LOG.info(f"Existing database found: {len(existing_urls)} URLs already processed.")
                return existing_urls
            except Exception as e:
                LOG.exception(f"Error loading existing DB: {e}. Full restart needed.")
                return set()
        return set()
    
    # --- SAVE BATCH TO CSV ---
    def _save_batch(self, csv_path: str, batch_data: List[dict], is_emergency: bool = False):
        
        """
        Saves the current batch of data by appending it to the existing database file.
        This avoids RAM saturation (pd.concat).
        """
        
        NEWdf = pd.DataFrame(batch_data)
        
        if not os.path.exists(csv_path):
            NEWdf.to_csv(csv_path, index=False, encoding='utf-8-sig')
            LOG.info(f"New DB created with {len(NEWdf.index)} lines.")
            return

        try:
            NEWdf.to_csv(csv_path, mode='a', header=not os.path.exists(csv_path), index=False, encoding='utf-8-sig')
            
            if not is_emergency:
                LOG.info(f"Batch saved.")
            
        except Exception as e:
            LOG.exception(f"CRITICAL: Failed to merge batch due to {e}. New lines might be lost.")   # Low probability to happen
        
    # --- EXTRACT SITEMAP URLS ---
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

                soup = BeautifulSoup(ARTICLEpage, "xml")

                for loc_tag in soup.find_all('loc'):
                    PRODUCTurl = unquote(loc_tag.text.strip())

                    if PRODUCTurl.endswith(('/', '.jpg', '.jpeg', '.png', '.gif', '.pdf')):
                        continue

                    if [w for w in PRODUCTurl.split('/') if w][1] not in ('www.clabots.be', 'clabots.be'):
                        continue

                    if [w for w in PRODUCTurl.split('/') if w][2] in ['en', 'nl']:
                        continue

                    if [w for w in PRODUCTurl.split('/') if w][3] in self.CATEGORYnames:
                        continue

                    if len([w for w in PRODUCTurl.split('/') if w]) > 4:
                        continue

                    self.URLs.append(PRODUCTurl)

                break
            
            except Exception as e:
                LOG.exception(f"Error during sitemap extraction: {e}")
                self.ATTEMPT+=1

                if self.ATTEMPT == self.MAX_RETRIES:
                    LOG.warning(f"Abandoning after {self.MAX_RETRIES} attempts.")
                    return []
                else:
                    time.sleep(self.RETRY_DELAY)
    
    # --- ONLINE EXTRACT FINAL PRODUCT DATA ---
    def _ONLINEextract_FINALproduct(self, link):

        # === INTERNAL VARIABLE(S) ===
        self.ATTEMPT = 0
        self.MAX_RETRIES = 3
        self.RETRY_DELAY = 5

        # === INTERNAL PARAMETER(S) ===
        PRODUCTvar = {
            'Article': "-",
            'Base Price (HTVA)': "-",
            'Base Price (TVA)': "-",
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

                PRODUCTvar['Article'] = (
                    (name := (soup.find("h1", class_="page-title") or soup.find("h1"))) 
                    and (name.get_text(strip=True).replace("\"", "\"\"").strip('"'))
                )

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

                PRODUCTvar['Base Price (HTVA)'] = self.parser.format_price_for_excel(HTVA)
                PRODUCTvar['Base Price (TVA)'] = self.parser.format_price_for_excel(TVA)

                return PRODUCTvar
            
            except requests.exceptions.HTTPError as http_err:
                if response.status_code == 404:
                    LOG.exception(f"Invalid link (404 Not Found). Saving failure for future skip: {link}")
                    return PRODUCTvar
                else:
                    LOG.exception(f"HTTP Error ({response.status_code}) for {link}: {http_err}")
                    return PRODUCTvar
            
            except Exception as e:
                LOG.exception(f"Error during data extraction for product {link}: {e}")
                self.ATTEMPT+=1

                if self.ATTEMPT == self.MAX_RETRIES:
                    LOG.warning(f"Abandoning after {self.MAX_RETRIES} attempts for product {link}")
                    return PRODUCTvar
                else:
                    time.sleep(self.RETRY_DELAY)
    

    def run(self):

        CSVpathDB = os.path.join(DATABASE_FOLDER, "CLABOTSproductsDB.csv")
        DBurls = self._load_DBurls(CSVpathDB)

        if DBurls:
            LOG.info("Resuming from existing database...")
        else:
            LOG.info("Starting fresh database...")

        PRODUCTS: List[dict] = []

        try:
            for SITEMAPurl in self.SITEMAPurls:
                self._extract_SITEMAPurls(SITEMAPurl)

            self.URLs = [url for url in self.URLs if url not in DBurls]

            LOG.info(f"Found link(s): {len(self.URLs)}")

            if self.URLs:
                for PRODUCTurl in self.URLs:
                    try:
                        data = self._ONLINEextract_FINALproduct(PRODUCTurl)

                        LOG.debug(data)     # [TESTING ONLY]
                        
                        PRODUCTS.append(data)

                        self.SAVE_COUNTER+=1

                        if self.SAVE_COUNTER >= self.SAVE_THRESHOLD:
                            self._save_batch(CSVpathDB, PRODUCTS)

                            self.SAVE_COUNTER = 0
                            PRODUCTS = []
                        
                        time.sleep(random.uniform(0.5, 1)) # Loading time (STABILITY)

                    except Exception as e:
                        LOG.info(f"An unexpected error occurred for URL {PRODUCTurl}: {e}")
                        continue
                
                if PRODUCTS:
                    self._save_batch(CSVpathDB, PRODUCTS)
                    self.SAVE_COUNTER = 0
                    PRODUCTS = []
        
        except Exception as e:
            LOG.exception(f"Critical error for CLABOTSloader: {e}")

            if PRODUCTS: # EMERGENCY SAVE
                self._save_batch(CSVpathDB, PRODUCTS, is_emergency=True)

                self.SAVE_COUNTER = 0
                PRODUCTS = []

                LOG.exception("Emergency save triggered due to critical error.")

        LOG.info("CLABOTSloader process terminated...")



# === Independent running system ===
if __name__ == "__main__":

    CLABOTSloader = CLABOTSloader()
    CLABOTSloader.run()