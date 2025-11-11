# CORE/__DATABASES/loader/georges.py
import os
import time

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



class FGloader:
    
    """
    Class to download and extract product URLs and data from Fernand GEORGES.
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
            'https://www.georges.be/fr-be/sitemap_0.xml',
        ]
        self.NAMESPACESurl = {'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        self.CATEGORYnames: List[str] = [
            'aération-et-ventilation', 'aération-et-ventilation.html',
            'bâtiment', 'bâtiment.html',
            'chassis', 'chassis.html',
            'chimie-et-fixation', 'chimie-et-fixation.html',
            'consommables-pour-machines', 'consommables-pour-machines.html',
            'décoration', 'décoration.html',
            'électricité', 'électricité.html',
            'meuble-et-aménagement', 'meuble-et-aménagement.html',
            'outillage', 'outillage.html',
            'porte', 'porte.html',
            'sécurité-électronique', 'sécurité-électronique.html',
            'vêtements-et-protections', 'vêtements-et-protections.html',
        ]
        self.URLs: List[str] = []

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


    # === INTERNAL METHOD(S) ===
    # --- Sitemap Fetch & Decompress ---
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
                print("Content is GZIP compressed. Decompressing...")
                decompressed_content = gzip.decompress(response.content)

                return decompressed_content.decode('utf-8')
            else:

                return response.text
                
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error {e.response.status_code} on sitemap: {link}")
            
            return None
        except Exception as e:
            print(f"Error during decompression/fetch: {e}")
            
            return None
        
    def _load_DBurls(self, csv_path: str) -> set:
        
        """
        Loads already processed URLs from the existing DB for restart logic (cache checker).
        """
        
        if os.path.exists(csv_path):
            try:
                df_existing = pd.read_csv(csv_path, usecols=['ArticleURL'], encoding='utf-8-sig')
                existing_urls = set(df_existing['ArticleURL'].astype(str).tolist())   # Converting into set for better performance

                print(f"Existing database found: {len(existing_urls)} URLs already processed.")
                return existing_urls
            except Exception as e:
                print(f"Error loading existing DB: {e}. Full restart needed.")
                return set()
        return set()
    
    def _save_batch(self, csv_path: str, batch_data: List[dict], is_emergency: bool = False):
        
        """
        Saves the current batch of data by appending it to the existing database file.
        This avoids RAM saturation (pd.concat).
        """
        
        NEWdf = pd.DataFrame(batch_data)
        
        if not os.path.exists(csv_path):
            NEWdf.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"New DB created. Total lines: {len(NEWdf.index)}")
            
            return

        try:
            NEWdf.to_csv(csv_path, mode='a', header=not os.path.exists(csv_path), index=False, encoding='utf-8-sig')
            
            if not is_emergency:
                print(f"Batch saved.")
            
        except Exception as e:
            print(f"CRITICAL: Failed to merge batch due to {e}. New lines might be lost.")   # Low probability to happen
        

    def _extract_SITEMAPurls(self, link):
        
        """
        Downloads the sitemap and extracts all <loc> URLs (applying filtering logic).
        """
        
        print(f"Downloading sitemap: {link}...")

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

                    if [w for w in PRODUCTurl.split('/') if w][1] not in ('www.georges.be', 'georges.be'):
                        continue

                    if [w for w in PRODUCTurl.split('/') if w][2] in ['en-be', 'nl-be']:
                        continue
                            
                    if [w for w in PRODUCTurl.split('/') if w][3] not in self.CATEGORYnames:
                        continue

                    if len([w for w in PRODUCTurl.split('/') if w]) <= 3:
                        continue

                    self.URLs.append(PRODUCTurl)

                break
            
            except Exception as e:
                print(f"Error during sitemap extraction: {e}")
                
                self.ATTEMPT+=1
                if self.ATTEMPT == self.MAX_RETRIES:
                    print(f"Abandoning after {self.MAX_RETRIES} attempts.")

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
            'Article': "-",
            'Local REF': "-",
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

                #self.logger.info(ARTICLEpage)     # [TESTING ONLY]

                soup = BeautifulSoup(ARTICLEpage, "html.parser")

                PRODUCTvar['Article'] = (
                    (name := soup.find("h1", class_="font-product-title"))
                    and (name.get_text(strip=True).replace("\"", "\"\"").strip('"'))
                )
                PRODUCTvar['Local REF'] = (
                    (ref_tag := soup.find("span", class_="value", itemprop="productID")) 
                    and ref_tag.get_text(strip=True)
                )

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

                PRODUCTvar['Base Price (HTVA)'] = self.parser.format_price_for_excel(HTVA)
                PRODUCTvar['Base Price (TVA)'] = self.parser.format_price_for_excel(TVA)

                return PRODUCTvar
            
            except requests.exceptions.HTTPError as http_err:
                if response.status_code == 404:
                    print(f"Invalid link (404 Not Found). Saving failure for future skip: {link}")
                    
                    return PRODUCTvar
                else:
                    print(f"HTTP Error ({response.status_code}) for {link}: {http_err}")

                    return PRODUCTvar
            
            except Exception as e:
                print(f"Error during data extraction for product {link}: {e}")
                
                self.ATTEMPT+=1
                if self.ATTEMPT == self.MAX_RETRIES:
                    print(f"Abandoning after {self.MAX_RETRIES} attempts for product {link}")

                    return PRODUCTvar
                
                else:
                    time.sleep(self.RETRY_DELAY)
    

    def run(self):

        CSVpathDB = os.path.join(DATABASE_FOLDER, "FGproductsDB.csv")
        DBurls = self._load_DBurls(CSVpathDB)

        PRODUCTS: List[dict] = []

        try:

            for SITEMAPurl in self.SITEMAPurls:
                self._extract_SITEMAPurls(SITEMAPurl)

            self.URLs = [url for url in self.URLs if url not in DBurls]

            print(f"Found link(s): {len(self.URLs)}")

            if self.URLs:
                for PRODUCTurl in self.URLs:
                    try:
                        data = self._ONLINEextract_FINALproduct(PRODUCTurl)

                        print(data)     # [TESTING ONLY]
                        
                        PRODUCTS.append(data)

                        self.SAVE_COUNTER+=1

                        if self.SAVE_COUNTER >= self.SAVE_THRESHOLD:
                            self._save_batch(CSVpathDB, PRODUCTS)
                            
                            self.SAVE_COUNTER = 0
                            PRODUCTS = []
                        
                        time.sleep(random.uniform(0.5, 1)) # Loading time (STABILITY)
                    
                    except Exception as e:
                        print(f"An unexpected error occurred for URL {PRODUCTurl}: {e}")
                        continue
                
                if PRODUCTS:
                    self._save_batch(CSVpathDB, PRODUCTS)
                    
                    self.SAVE_COUNTER = 0
                    PRODUCTS = []
        
        except Exception as e:
            print(f"Critical error for FGloader: {e}")

            if PRODUCTS: # EMERGENCY SAVE
                self._save_batch(CSVpathDB, PRODUCTS, is_emergency=True)

                self.SAVE_COUNTER = 0
                PRODUCTS = []

                print("Emergency save triggered due to critical error.")

        print("FGloader process terminated...")



# === Independent running system ===
if __name__ == "__main__":

    FGloader = FGloader()
    FGloader.run()