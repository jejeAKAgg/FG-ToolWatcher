# WEB/FIXAMIloader.py
import os
import sys
import time

import cloudscraper
import gzip
import json
import pandas as pd
import random
import requests

from bs4 import BeautifulSoup
from datetime import datetime
from typing import List
from urllib.parse import unquote

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By


from APP.SERVICES.__init__ import *

from APP.UTILS.LOGmaker import *
from APP.UTILS.PRODUCTformatter import *


class FIXAMIloader:
    """
    Classe pour télécharger et extraire les URL d'un fichier Sitemap XML.
    """
    def __init__(self):

        # === LOGGER SETUP ===
        self.logger = logger("FIXAMIloader")

        # === INTERNAL VARIABLE(S) ===
        self.ATTEMPT = 0
        self.MAX_RETRIES = 3
        self.RETRY_DELAY = 5
        self.SAVE_COUNTER = 0
        self.SAVE_THRESHOLD = 500
        self.WAIT_TIME = 3

        self.PRODUCTS: List[str] = []

        # === INTERNAL PARAMETER(S) ===
        self.SITEMAPurls = [
            'https://www.fixami.be/single-sitemap?file=salesChannel-9de899910ab34fbd8a41563711c5f261-1d5cf9aa726a4968ab4fad445565607f/9de899910ab34fbd8a41563711c5f261-sitemap-www-fixami-be-fr-1.xml.gz',
            'https://www.fixami.be/single-sitemap?file=salesChannel-9de899910ab34fbd8a41563711c5f261-1d5cf9aa726a4968ab4fad445565607f/9de899910ab34fbd8a41563711c5f261-sitemap-www-fixami-be-fr-2.xml.gz',
            'https://www.fixami.be/single-sitemap?file=salesChannel-9de899910ab34fbd8a41563711c5f261-1d5cf9aa726a4968ab4fad445565607f/9de899910ab34fbd8a41563711c5f261-sitemap-www-fixami-be-fr-3.xml.gz'
        ]
        self.NAMESPACESurl = {'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        self.CATEGORYnames = [
            'accessoire', 'accessoires.html',
            'accessoires', 'accessoires.html',
            'actualites', 'actualites.html',
            'aide-contact', 'aide-contact.html',
            'a-propos-de-fixami', 'a-propos-de-fixami.html',
            'black-friday', 'black-friday.html',
            'carte-cadeaux', 'carte-cadeaux.html',
            'cartes-cadeaux', 'cartes-cadeaux.html',
            'climatisations', 'climatisations.html',
            'code-de-reduction', 'code-de-reduction.html',
            'codes-de-reduction', 'codes-de-reduction.html',
            'conseils', 'conseils.html',
            'cookies', 'cookies.html',
            'demander-a-payer-sur-facture', 'demander-a-payer-sur-facture.html',
            'devis', 'devis.html',
            'epi-et-vetements-de-travail', 'epi-et-vetements-de-travail.html',
            'fixami', 'fixami.html',
            'home', 'home.html',
            'marques', 'marques.html',
            'materiel-electrique', 'materiel-electrique.html',
            'materiaux-de-fixation', 'materiaux-de-fixation.html',
            'media', 'media.html',
            'navigation', 'navigation.html',
            'nettoyage', 'nettoyage.html',
            'newsletter','newsletter.html',
            'offre', 'offre.html',
            'offres', 'offres.html',
            'offres-du-jour', 'offres-du-jour.html',
            'outils-a-main', 'outils-a-main.html',
            'outils-de-jardinage', 'outils-de-jardinage.html',
            'outils-de-mesure', 'outils-de-mesure.html',
            'outils-electriques', 'outils-electriques.html',
            'outils-pneumatiques', 'outils-pneumatiques.html',
            'outil-sans-fil', 'outil-sans-fil.html',
            'outils-sans-fil', 'outils-sans-fil.html',
            'outlet', 'outlet.html',
            'peinture-fournitures', 'peinture-fournitures.html',
            'produits', 'produits.html',
            'promotion', 'promotion.html',
            'promotions', 'promotions.html',
            'service-client', 'service-client.html',
            'transports-et-atelier', 'transports-et-atelier.html']
        self.URLs: List[str] = []

        # === PARAMETERS & OPTIONS SETUP (CloudSCRAPER) ===
        self.requests = cloudscraper.create_scraper()

        self.REQUESTS_HEADERS = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            'Referer': 'https://www.fixami.be/',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive'
        }

        # === PARAMETERS & OPTIONS SETUP (Selenium) ===
        self.options = Options()

        self.options.add_argument(f"--user-data-dir={CHROME_PROFILE_PATH}")

        self.options.add_argument("--headless=new")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--disable-software-rasterizer")
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--window-size=400,400")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-infobars")
        self.options.add_argument("--disable-extensions")
        self.options.add_argument("--disable-software-rasterizer")
        self.options.add_argument("--disable-logging")
        self.options.add_argument("--log-level=3")
        self.options.add_argument("--remote-debugging-port=9222")
        self.options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")

        self.options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        self.options.add_experimental_option('useAutomationExtension', False)

        if sys.platform.startswith("win"):
            self.options.binary_location = CHROME_PATH
            self.service = Service(executable_path=CHROMEDRIVER_PATH)
        else:
            self.service = None

    
    def _init_driver(self):
        return webdriver.Chrome(options=self.options, service=self.service)


    def _accept_cookies(self, driver):
    
        """
        Automatically clicks the "accept cookies" button for known sites.

        Args:
            driver (selenium.webdriver): Selenium WebDriver instance.
            site_name (str): Name of the website to accept cookies for.

        Notes:
            - Supported sites (for now): fixami, klium, lecot
            - If button is not found or already accepted, logs info.
        
        """

        try:
            accept_button = driver.find_element(By.ID, "ac")
            if accept_button.is_displayed():
                accept_button.click()
                self.logger.info(f"Cookies accepted for FIXAMI: {driver.current_url}.")
                time.sleep(self.WAIT_TIME)
        except Exception:
            self.logger.info(f"No cookies to accept or already accepted for FIXAMI: {driver.current_url}.")

    def _fetch_and_decompress_sitemap(self, link: str):
        
        """
        Downloads the sitemap (which may be a compressed .gz file) and returns the decompressed XML content.

        Args:
            link (str): The URL of the sitemap file (e.g., 'sitemap-index-1.xml' or 'sitemap-index-1.xml.gz').

        Returns:
            str | None: The decompressed XML content as a string, or None if the download or decompression fails.
        """

        self.logger.info(f"Fetching sitemap: {link}...")
        
        try:
            # 1. Utiliser cloudscraper pour le téléchargement
            response = self.requests.get(link, headers=self.REQUESTS_HEADERS)
            response.raise_for_status()

            time.sleep(self.WAIT_TIME)

            # 2. Vérifier si le contenu est compressé (le sitemap de Clabots l'est)
            if link.endswith('.gz'):
                self.logger.info("Content is GZIP compressed. Decompressing...")
                # gzip.decompress prend le contenu binaire (response.content)
                decompressed_content = gzip.decompress(response.content)
                # Le convertir en chaîne de caractères (utf-8 est standard pour XML)
                return decompressed_content.decode('utf-8')
            else:
                # Sinon, retourner le texte normal
                return response.text
                
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP Error {e.response.status_code} on sitemap: {link}")
            return None
        except Exception as e:
            self.logger.error(f"Error during decompression/fetch: {e}")
            return None

    def _load_DBurls(self, csv_path: str) -> set:
        
        """
        Loads already processed URLs from the existing DB for restart logic (cache checker).
        """
        
        if os.path.exists(csv_path):
            try:
                # Charger uniquement la colonne ArticleURL pour la rapidité
                df_existing = pd.read_csv(csv_path, usecols=['ArticleURL'], encoding='utf-8-sig')
                
                # Le convertir en un ensemble (set) pour des recherches ultra-rapides (O(1))
                existing_urls = set(df_existing['ArticleURL'].astype(str).tolist())
                
                self.logger.info(f"Existing database found: {len(existing_urls)} URLs already processed.")
                return existing_urls
            except Exception as e:
                self.logger.warning(f"Error loading existing DB: {e}. Full restart needed.")
                return set()
        return set()
    
    def _save_batch(self, csv_path: str, batch_data: List[dict], is_emergency: bool = False):
        
        """
        Sauvegarde le lot de données actuel en le concaténant avec la base de données existante.
        """
        
        NEWdf = pd.DataFrame(batch_data)
        
        if not os.path.exists(csv_path):
            # CAS 1: Nouvelle base de données (écriture simple)
            NEWdf.to_csv(csv_path, index=False, encoding='utf-8-sig')
            self.logger.info(f"New DB created with {len(NEWdf.index)} lines.")
            return

        # CAS 2: Reprise (concaténation)
        try:
            # Charger l'ancienne DB
            OLDdf = pd.read_csv(csv_path, encoding='utf-8-sig', usecols=NEWdf.columns)
            
            # Concaténer
            FINALdf = pd.concat([OLDdf, NEWdf], ignore_index=True)
            
            # Sauvegarder la totalité du DataFrame
            FINALdf.to_csv(csv_path, index=False, encoding='utf-8-sig')
            
            if not is_emergency:
                self.logger.info(f"Batch saved. Total lines: {len(FINALdf.index)}.")
            
        except Exception as e:
            # Cette erreur est rare mais possible si le CSV a été corrompu entre-temps.
            self.logger.error(f"CRITICAL: Failed to merge batch due to {e}. New lines might be lost.")
        

    def _extract_SITEMAPurls(self, link):
        
        """
        Downloads the sitemap and extracts all <loc> URLs (applying filtering logic).
        """
        
        self.logger.info(f"Downloading sitemap: {link}...")

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

                    if PRODUCTurl.endswith('/'):
                        continue

                    if [w for w in PRODUCTurl.split('/') if w][1] not in ["www.fixami.be"]:
                        continue

                    if [w for w in PRODUCTurl.split('/') if w][3] in self.CATEGORYnames:
                        continue

                    if len([w for w in PRODUCTurl.split('/') if w]) > 4:
                        continue

                    self.URLs.append(PRODUCTurl)

                break

            
            except Exception as e:
                self.logger.warning(f"Error during sitemap extraction: {e}")
                
                self.ATTEMPT+=1
                if self.ATTEMPT == self.MAX_RETRIES:
                    self.logger.warning(f"Abandoning after {self.MAX_RETRIES} attempts.")

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

                #self.logger.info(ARTICLEpage)     # [TESTING ONLY]

                soup = BeautifulSoup(ARTICLEpage, "html.parser")


                PRODUCTvar['Article'] = (
                    (json_tag := soup.find('script', {'id': 'product-offer-json-ld', 'type': 'application/ld+json'}))
                    and (data := json.loads(json_tag.string))
                    and data.get('name')
                )

                HTVA, TVA = calculate_missing_price(
                    htva=None,
                    tva=(
                        (json_tag := soup.find('script', {'id': 'product-offer-json-ld', 'type': 'application/ld+json'}))
                        and (data := json.loads(json_tag.string))
                        and (price_float := data.get('offers', {}).get('price')) 
                        and price_float 
                    )
                )

                PRODUCTvar['Base Price (HTVA)'] = format_price_for_excel(HTVA)
                PRODUCTvar['Base Price (TVA)'] = format_price_for_excel(TVA)

                return PRODUCTvar
            
            except requests.exceptions.HTTPError as http_err:
                if response.status_code == 404:
                    self.logger.error(f"Invalid link (404 Not Found). Saving failure for future skip: {link}")
                    
                    return PRODUCTvar
                else:
                    self.logger.warning(f"HTTP Error ({response.status_code}) for {link}: {http_err}")
            
            except Exception as e:
                self.logger.warning(f"Error during data extraction for product {link}: {e}")
                
                self.ATTEMPT+=1
                if self.ATTEMPT == self.MAX_RETRIES:
                    self.logger.warning(f"Abandoning after {self.MAX_RETRIES} attempts for product {link}")

                    return PRODUCTvar
                
                else:
                    time.sleep(self.RETRY_DELAY)
    

    def run(self):

        CSVpathDB = os.path.join(DATABASE_FOLDER, "FIXAMIproductsDB.csv")
        DBurls = self._load_DBurls(CSVpathDB)

        try:

            for SITEMAPurl in self.SITEMAPurls:
                self._extract_SITEMAPurls(SITEMAPurl)

            self.logger.info(f"Found link(s): {len(self.URLs)}")

            self.URLs = [url for url in self.URLs if url not in DBurls]

            if self.URLs:
                for PRODUCTurl in self.URLs:
                    data = self._ONLINEextract_FINALproduct(PRODUCTurl)

                    print(data)     # [TESTING ONLY]
                    
                    self.PRODUCTS.append(data)

                    self.SAVE_COUNTER+=1

                    if self.SAVE_COUNTER >= self.SAVE_THRESHOLD:
                        self._save_batch(CSVpathDB, self.PRODUCTS)
                        
                        self.PRODUCTS = []
                        self.SAVE_COUNTER = 0
                    
                    time.sleep(random.uniform(0.5, 1)) # Loading time (STABILITY)
                
                if self.PRODUCTS:
                    self._save_batch(CSVpathDB, self.PRODUCTS)
        
        except Exception as e:
            self.logger.error(f"Critical error for FIXAMIloader: {e}")

        self.logger.info("FIXAMIloader process terminated...")



# === Independent running system ===
if __name__ == "__main__":

    FIXAMIloader = FIXAMIloader()
    FIXAMIloader.run()