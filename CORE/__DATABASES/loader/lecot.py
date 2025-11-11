# CORE/__DATABASES/loader/lecot.py
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



class LECOTloader:
    
    """
    Class to download and extract product URLs and data from LECOT.
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
            'https://shop.lecot.be/sitemap/salesChannel-62a4f8977cbe4817b8955353b2ace1c8-a7f1e6a55f0e4b5ea0019f7d4991e7cb/62a4f8977cbe4817b8955353b2ace1c8-sitemap-shop-lecot-be-fr-be-1.xml.gz',
        ]
        self.NAMESPACESurl = {'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        self.CATEGORYnames: List[str] = [
            'accessoires-marques', 'accessoires-marques.html',
            'airpress-slider', 'airpress-slider.html',
            'alle-acties', 'alle-acties.html',
            'a-propos-de-lecot.shop', 'a-propos-de-lecot.shop.html',
            'arlu-slider', 'arlu-slider.html',
            'artline-slider', 'artline-slider.html',
            'atg-slider', 'atg-slider.html',
            'base-slider', 'base-slider.html',
            'b-c-slider', 'b-c-slider.html',
            'blaklader-slider', 'blaklader-slider.html',
            'blackweek', 'blackweek.html',
            'black-week-categories', 'black-week-categories.html',
            'black-week-marques', 'black-week-marques.html',
            'bosch-categories', 'bosch-categories.html',
            'brennenstuhl-slider', 'brennenstuhl-slider.html',
            'brigadedeforce-x-lecot.shop', 'brigadedeforce-x-lecot.shop.html',
            'brigade-de-force-x-lecot.shop', 'brigade-de-force-x-lecot.shop.html',
            'carat-slider', 'carat-slider.html',
            'categorie', 'categorie.html',
            'categories', 'categories.html',
            'colorline-slider', 'colorline-slider.html',
            'conditions-de-garantie', 'conditions-de-garantie.html',
            'conditions-d-utilisation', 'conditions-d-utilisation.html',
            'conditions-generales', 'conditions-generales.html',
            'configurateur-hettich', 'configurateur-hettich.html',
            'cookies', 'cookies.html',
            'delai-de-livraison-estime', 'delai-de-livraison-estime.html',
            'delta-plus-slider', 'delta-plus-slider.html',
            'detectaplast-slider', 'detectaplast-slider.html',
            'dewalt-slider', 'dewalt-slider.html',
            'dl-chemicals-slider', 'dl-chemicals-slider.html',
            'dormakaba-slider', 'dormakaba-slider.html',
            'erko-slider', 'erko-slider.hmtl',
            'facom-slider', 'facom-slider.html',
            'fein-slider', 'fein-slider.html',
            'festool-slider', 'festool-slider.html',
            'filiales', 'filiales.html',
            'fischer-slider', 'fischer-slider.html',
            'fixations-marques', 'fixations-marques.html',
            'futech-slider', 'futech-slider.html',
            'gardena-slider', 'gardena-slider.html',
            'geze-slider', 'geze-slider.html',
            'hdd-slider', 'hdd-slider.html',
            'heller-slider', 'heller-slider.html',
            'herock-slider', 'herock-slider.html',
            'hikoki-slider', 'hikoki-slider',
            'hpx-slider', 'hpx-slider.html',
            'jardin-categories', 'jardin-categories.html',
            'kaercher-slider', 'kaercher-slider.html',
            'knipex-slider', 'knipex-slider.html',
            'ko-ken-slider', 'ko-ken-slider.html',
            'kraeftwerk-slider', 'kraeftwerk-slider.html',
            'ledlenser-slider', 'ledlenser-slider.html',
            'ledrope-pro-slider', 'ledrope-pro-slider.html',
            'leica-slider', 'leica-slider.html',
            'lemaitre-slider', 'lemaitre-slider.html',
            'lot2023-fr', 'lot2023-fr.html',
            'lumx-slider', 'lumx-slider.html',
            'machines-de-jardinage-marques', 'machines-de-jardinage-marques.html',
            'machines-marques', 'machines-marques.html',
            'makita-slider', 'makita-slider.html',
            'makita-tuin-slider', 'makita-tuin-slider.html',
            'marques', 'marques.html',
            'metabo-slider', 'metabo-slider.html',
            'milwaukee-slider', 'milwaukee-slider.html',
            'navigation', 'navigation.html',
            'nouvel-assortiment', 'nouvel-assortiment.html',
            'outils-a-main-marques', 'outils-a-main-marques.html',
            'outils-electriques-marques', 'outils-electriques-marques.html',
            'outils-sur-batterie-marques', 'outils-sur-batterie-marques.html',
            'outlet', 'outlet.html',
            'outlet-categories', 'outlet-categories.html',
            'outlet-marques', 'outlet-marques.html',
            'paslode-slider', 'paslode-slider.html',
            'polet-slider', 'polet-slider.html',
            'politique-de-confidentialite', 'politique-de-confidentialite.html',
            'preview', 'preview.html',
            'produits-chimiques-marques', 'produits-chimiques-marques.html',
            'protection-et-vetements-marques', 'protection-et-vetements-marques.html',
            'puma-slider', 'puma-slider.html',
            'quincaillerie-de-batiment-marques', 'quincaillerie-de-batiment-marques.html',
            'rectavit-slider', 'rectavit-slider.html',
            'safety-jogger-slider', 'safety-jogger-slider.html',
            'scangrip-slider', 'scangrip-slider.html',
            'service-client', 'service-client.html',
            'soldes-categories', 'soldes-categories.html',
            'soldes-marques', 'soldes-marques.html',
            'soudal-slider', 'soudal-slider.html',
            'spit-slider', 'spit-slider.html',
            'stanley-slider', 'stanley-slider.html',
            'stihl-slider', 'stihl-slider.html',
            'stockage', 'stockage.html',
            'stroxx-slider', 'stroxx-slider.html',
            'stroxx-merken-slider', 'stroxx-merken-slider.html',
            'tec7-slider', 'tec7-slider.html',
            'tourex-slider', 'tourex-slider.html',
            'toutes-les-actions', 'toutes-les-actions.html',
            'wd-40-slider', 'wd-40-slider.html',
            'wera-slider', 'wera-slider.html',
            '15-daagse-storage-merken', '15-daagse-storage-merken.html',
            '3m-slider', '3m-slider.html',
        ]
        self.URLs: List[str] = []

        # === INTERNAL SERVICE(S) ===
        self.parser = ProductDataParser(brands_file_path=os.path.join(UTILS_FOLDER, 'brands.json'))

        # === PARAMETERS & OPTIONS SETUP (CloudSCRAPER) ===
        self.requests = cloudscraper.create_scraper()

        self.REQUESTS_HEADERS = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            'Referer': 'https://lecot.be/fr-be/',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive'
        }

    
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
            
            print(f"New DB created with {len(NEWdf.index)} lines.")
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
        
        print(f"Téléchargement du sitemap : {link}...")

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

                    if [w for w in PRODUCTurl.split('/') if w][1] not in ('www.shop.lecot.be', 'shop.lecot.be'):
                        continue

                    if [w for w in PRODUCTurl.split('/') if w][2] in ['en-be', 'en-nl', 'nl-be', 'nl-nl']:
                        continue

                    if [w for w in PRODUCTurl.split('/') if w][3] in self.CATEGORYnames:
                        continue

                    if len([w for w in PRODUCTurl.split('/') if w]) > 4:
                        continue

                    self.URLs.append(PRODUCTurl)

                return self.URLs
            
            except Exception as e:
                print(f"Erreur lors de l'extraction des données: {e}")
                
                self.ATTEMPT+=1
                if self.ATTEMPT == self.MAX_RETRIES:
                    print(f"Abandon après {self.MAX_RETRIES} tentatives")

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

                #print(ARTICLEpage)     # [TESTING ONLY]

                soup = BeautifulSoup(ARTICLEpage, "html.parser")

                PRODUCTvar['Article'] = (
                    (name := soup.find("h1", class_="page-title"))
                    and (name.get_text(strip=True).replace("\"", "\"\"").strip('"'))
                )

                HTVA, TVA = self.parser.calculate_missing_price(
                    htva=(
                        (e := soup.find("div", class_="price-htvac"))
                        and self.parser.parse_price(e.get_text(strip=True))
                    ),
                    tva=(
                        (e := soup.find("span", class_="current-price-value"))
                        and self.parser.parse_price(e.get_text(strip=True))
                    )
                )

                PRODUCTvar['Base Price (HTVA)'] = self.parser.format_price_for_excel(HTVA)
                PRODUCTvar['Base Price (TVA)'] = self.parser.format_price_for_excel(TVA)

                return PRODUCTvar
            
            except requests.exceptions.HTTPError as http_err:
                if response.status_code == 404:
                    print(f"Lien invalide (404 Not Found). Abandon immédiat: {link}")
                    
                    return PRODUCTvar 
                else:
                    print(f"Erreur HTTP ({response.status_code}) pour {link}: {http_err}")

                    return PRODUCTvar
            
            except Exception as e:
                print(f"Erreur lors de l'extraction des données pour le produit {link}: {e}")
                
                self.ATTEMPT+=1
                if self.ATTEMPT == self.MAX_RETRIES:
                    print(f"Abandon après {self.MAX_RETRIES} tentatives pour produit {link}")

                    return PRODUCTvar
                
                else:
                    time.sleep(self.RETRY_DELAY)
    

    def run(self):

        CSVpathDB = os.path.join(DATABASE_FOLDER, "LECOTproductsDB.csv")
        DBurls = self._load_DBurls(CSVpathDB)

        PRODUCTS: List[dict] = []

        try:
            for SITEMAPurl in self.SITEMAPurls:
                self._extract_SITEMAPurls(SITEMAPurl)

            self.URLs = [url for url in self.URLs if url not in DBurls]

            print(f"Nombre de lien(s) touvé(s): {len(self.URLs)}")

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
            print(f"Critical error for LECOTloader: {e}")

            if PRODUCTS: # EMERGENCY SAVE
                self._save_batch(CSVpathDB, PRODUCTS, is_emergency=True)

                self.SAVE_COUNTER = 0
                PRODUCTS = []

                print("Emergency save triggered due to critical error.")

        print("LECOTloader process terminated...")



# === Independent running system ===
if __name__ == "__main__":

    LECOTloader = LECOTloader()
    
    result = LECOTloader.run()