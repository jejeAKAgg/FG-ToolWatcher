# WEB/KLIUMloader.py
import os
import sys
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

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By


from APP.SERVICES.__init__ import *

from APP.UTILS.LOGmaker import *
from APP.UTILS.PRODUCTformatter import *


class KLIUMloader:
    """
    Classe pour télécharger et extraire les URL d'un fichier Sitemap XML.
    Utilise WebDriver pour contourner Cloudflare et extraire les fiches produits.
    """
    def __init__(self):

        # === LOGGER SETUP ===
        self.logger = logger("KLIUMloader")

        # === INTERNAL VARIABLE(S) ===
        self.ATTEMPT = 0
        self.MAX_RETRIES = 3
        self.RETRY_DELAY = 5
        self.WAIT_TIME = 3

        # === INTERNAL PARAMETER(S) ===
        self.SITEMAPurls = [
            'https://www.klium.be/download/feeds/sitemap/www.klium.be/Sitemapp1.xml',
            'https://www.klium.be/download/feeds/sitemap/www.klium.be/Sitemapp2.xml',
            'https://www.klium.be/download/feeds/sitemap/www.klium.be/Sitemapp3.xml',
            'https://www.klium.be/download/feeds/sitemap/www.klium.be/Sitemapp4.xml',
            'https://www.klium.be/download/feeds/sitemap/www.klium.be/Sitemapp5.xml',
            'https://www.klium.be/download/feeds/sitemap/www.klium.be/Sitemapp6.xml',
            'https://www.klium.be/download/feeds/sitemap/www.klium.be/Sitemapp7.xml',
            'https://www.klium.be/download/feeds/sitemap/www.klium.be/Sitemapp8.xml',
            'https://www.klium.be/download/feeds/sitemap/www.klium.be/Sitemapp9.xml',
            'https://www.klium.be/download/feeds/sitemap/www.klium.be/Sitemapp10.xml',
            'https://www.klium.be/download/feeds/sitemap/www.klium.be/Sitemapp11.xml'
        ]
        self.URLs: List[str] = []

        # === PARAMETERS & OPTIONS SETUP (CloudSCRAPER) ===
        self.requests = cloudscraper.create_scraper()

        self.REQUESTS_HEADERS = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            'Referer': 'https://www.klium.be/',
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
            accept_button = driver.find_element(By.ID, "CybotCookiebotDialogBodyButtonAccept")
            if accept_button.is_displayed():
                accept_button.click()
                
                time.sleep(self.WAIT_TIME)

                self.logger.info(f"Cookies accepted for KLIUM: {driver.current_url}.")
        except Exception:
            self.logger.info(f"No cookies to accept or already accepted for KLIUM: {driver.current_url}.")

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
    

    # Méthode modifiée pour l'extraction du sitemap enfant (utilise driver)
    def _extract_SITEMAPurls(self, link):
        
        """
        Télécharge le sitemap et extrait toutes les URL <loc>.
        """
        
        self.logger.info(f"Téléchargement du sitemap : {link}...")

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

                    if PRODUCTurl.split('/')[2] not in ["www.klium.be"]:
                        continue

                    if PRODUCTurl.split('/')[3] in ["en", "nl"]:
                        continue

                    self.URLs.append(PRODUCTurl)

                return self.URLs
            
            except Exception as e:
                self.logger.warning(f"Erreur lors de l'extraction des données: {e}")
                
                self.ATTEMPT+=1
                if self.ATTEMPT == self.MAX_RETRIES:
                    self.logger.warning(f"Abandon après {self.MAX_RETRIES} tentatives")

                    return []
                
                else:
                    time.sleep(self.RETRY_DELAY)

    # Méthode modifiée pour l'extraction de la fiche produit (utilise driver)
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

                print(ARTICLEpage)

                soup = BeautifulSoup(ARTICLEpage, "html.parser")

                PRODUCTvar['Article'] = (
                    (name := soup.find("h1", id="product_name_value"))
                    and name.get_text(strip=True).replace("\"", "\"\"")
                )

                HTVA, TVA = calculate_missing_price(
                    htva=(
                        (e := soup.find("div", class_="price-htvac"))
                        and parse_price(e.get_text(strip=True))
                    ),
                    tva=(
                        (e := soup.find("span", class_="current-price-value"))
                        and parse_price(e.get_text(strip=True))
                    )
                )

                PRODUCTvar['Base Price (HTVA)'] = format_price_for_excel(HTVA)
                PRODUCTvar['Base Price (TVA)'] = format_price_for_excel(TVA)

                return PRODUCTvar
            
            except requests.exceptions.HTTPError as http_err:
                if response.status_code == 404:
                    self.logger.error(f"Lien invalide (404 Not Found). Abandon immédiat: {link}")
                    
                    return PRODUCTvar 
                else:
                    self.logger.warning(f"Erreur HTTP ({response.status_code}) pour {link}: {http_err}")
            
            except Exception as e:
                self.logger.warning(f"Erreur lors de l'extraction des données pour le produit {link}: {e}")
                
                attempt += 1
                if self.ATTEMPT == self.MAX_RETRIES:
                    self.logger.warning(f"Abandon après {self.ATTEMPT} tentatives pour produit {link}")
                    return PRODUCTvar
                
                else:
                    time.sleep(self.RETRY_DELAY)

    
    def run(self):

        CSVpathDB = os.path.join(DATABASE_FOLDER, "KLIUMproductsDB.csv")

        DBurls = self._load_DBurls(CSVpathDB)

        products = []

        try:

            for SITEMAPurl in self.SITEMAPurls:
                self._extract_SITEMAPurls(SITEMAPurl)

            self.logger.info(f"Nombre de lien(s) touvé(s): {len(self.URLs)}")

            self.URLs = [url for url in self.URLs if url not in DBurls]

            if self.URLs:
                for PRODUCTurl in self.URLs:
                    data = self._ONLINEextract_FINALproduct(PRODUCTurl)

                    print(data)     # [TESTING ONLY]

                    products.append(data)

                    time.sleep(random.uniform(0.5, 1)) # Loading time (STABILITY)
        
        except Exception as e:
            self.logger.error(f"Erreur fatale dans KLIUMloader: {e}")

        NEWdf = pd.DataFrame(products)

        if not DBurls: # Initiating new DB
            FINALdf = NEWdf
        
        else: # Loading existing DB
            try:
                OLDdf = pd.read_csv(CSVpathDB, encoding='utf-8-sig', usecols=NEWdf.columns) # Loading only needed columns
                FINALdf = pd.concat([OLDdf, NEWdf], ignore_index=True)
                
                self.logger.info(f"Database updated.")
            
            except Exception as e:
                FINALdf = NEWdf

                self.logger.error(f"Critical error with the database: {e}. Saving new DB only.") 

        # Saving
        FINALdf.to_csv(CSVpathDB, index=False, encoding='utf-8-sig')

        self.logger.info("CLABOTSloader process terminated...")


# === Independent running system ===
if __name__ == "__main__":

    KLIUMloader = KLIUMloader()
    KLIUMloader.run()