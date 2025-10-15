# APP/WEBSITES/CIPACwatcher.py
import os
import sys
import time

import numpy as np
import pandas as pd
import random

import requests

from bs4 import BeautifulSoup

from datetime import datetime

from typing import List

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from urllib.parse import unquote

from APP.SERVICES.__init__ import *

from APP.SERVICES.CACHEservice import CacheService
from APP.SERVICES.MATCHERservice import MatcherService

from APP.UTILS.LOGmaker import *
from APP.UTILS.PRODUCTformatter import *


class LECOTloader:
    """
    Classe pour télécharger et extraire les URL d'un fichier Sitemap XML.
    """
    def __init__(self):

        # === LOGGER SETUP ===
        self.logger = logger("KLIUMloader")

        # === INTERNAL VARIABLE(S) ===
        self.ATTEMPT = 0
        self.MAX_RETRIES = 3
        self.RETRY_DELAY = 5

        # === INTERNAL PARAMETER(S) ===
        self.SITEMAPurl = 'https://www.klium.be/sitemap.xml'
        self.NAMESPACESurl = {'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        self.SITEMAPurls_child = []
        self.URLs = []

        # === PARAMETERS & OPTIONS SETUP ===
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

        self.REQUESTS_HEADERS = {
            # Maintenez le User-Agent
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            
            # AJOUTER le Referer pour simuler une navigation depuis la page d'accueil
            'Referer': 'https://www.klium.be/', 
            
            # AJOUTER l'Accept-Encoding (compression)
            'Accept-Encoding': 'gzip, deflate, br', 
            
            # Maintenez les autres headers...
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive'
        }


    
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
        
        pass
    

    def _extract_childSITEMAPSurls(self, driver) -> List[str]:
        
        """
        Télécharge le sitemap et extrait toutes les URL <loc>.
        """
        
        self.logger.info(f"Téléchargement du sitemap : {self.SITEMAPurl}...")

        # === INTERNAL VARIABLE(S) ===
        self.ATTEMPT = 0
        self.MAX_RETRIES = 3
        self.RETRY_DELAY = 5

        # === SEARCH ENGINE ===
        while self.ATTEMPT < self.MAX_RETRIES:
            try:

                driver.get(self.SITEMAPurl)
                
                time.sleep(5)  # Loading time (JS)

                ARTICLEpage = driver.page_source

                soup = BeautifulSoup(ARTICLEpage, "xml")

                for loc_tag in soup.find_all('loc')[:11]:
                    PRODUCTurl = unquote(loc_tag.text.strip())

                    if PRODUCTurl.endswith('/'):
                        continue

                    if PRODUCTurl.split('/')[3] in ["en", "nl"]:
                        continue

                    self.SITEMAPurls_child.append(PRODUCTurl)

                return self.SITEMAPurls_child
            
            except Exception as e:
                self.logger.warning(f"Erreur lors de l'extraction des données: {e}")
                
                self.ATTEMPT+=1
                if self.ATTEMPT == self.MAX_RETRIES:
                    self.logger.warning(f"Abandon après {self.MAX_RETRIES} tentatives")

                    return []
                
                else:
                    time.sleep(self.RETRY_DELAY)

    def _extract_SITEMAPurls(self, link, driver):
        
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
                
                driver.get(link)
                
                time.sleep(5)  # Loading time (JS)

                ARTICLEpage = driver.page_source

                soup = BeautifulSoup(ARTICLEpage, "xml")

                for loc_tag in soup.find_all('loc'):
                    PRODUCTurl = unquote(loc_tag.text.strip())

                    if PRODUCTurl.endswith('/'):
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
    

    def _ONLINEextract_FINALproduct(self, link, driver):

        # === INTERNAL VARIABLE(S) ===
        self.ATTEMPT = 0
        self.MAX_RETRIES = 3
        self.RETRY_DELAY = 5

        # === INTERNAL PARAMETER(S) ===
        PRODUCTvar = {
            'Article': "Produit indisponible",
            'Base Price (HTVA)': "-",
            'Base Price (TVA)': "-",
            'ArticleURL': link,
            'Checked on': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # === SEARCH ENGINE ===
        while self.ATTEMPT < self.MAX_RETRIES:
            try:

                driver.get(link)
                
                time.sleep(1)  # Loading time (JS)

                ARTICLEpage = driver.page_source

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
            
            except Exception as e:
                self.logger.warning(f"Erreur lors de l'extraction des données pour le produit {link}: {e}")
                
                self.ATTEMPT+=1
                if self.ATTEMPT == self.MAX_RETRIES:
                    self.logger.warning(f"Abandon après {self.MAX_RETRIES} tentatives pour produit {link}")

                    return None
                
                else:
                    time.sleep(self.RETRY_DELAY)
    

    def run(self):

        CSVpathDB = os.path.join(DATABASE_FOLDER, "KLIUMproductsDB.csv")

        products = []

        try:

            WEBdriver = self._init_driver()

            childSITEMAPSurls = self._extract_childSITEMAPSurls(driver=WEBdriver)

            self.logger.info(f"Nombre de lien(s) de sitemap trouvé(s): {len(childSITEMAPSurls)}")

            if childSITEMAPSurls:
                for childSITEMAPurl in childSITEMAPSurls:
                    self._extract_SITEMAPurls(link=childSITEMAPurl, driver=WEBdriver)

                self.logger.info(f"Nombre de lien(s) trouvé(s): {len(self.URLs)}")

                if self.URLs:
                    for PRODUCTurl in self.URLs:
                        data = self._ONLINEextract_FINALproduct(link=PRODUCTurl, driver=WEBdriver)
                        print(data)

                        if data is not None:
                            products.append(data)

                        time.sleep(random.uniform(1, 1.5))
        
        except Exception as e:
            self.logger.error(f"Erreur fatale dans FGloader: {e}")


        df = pd.DataFrame(products)
        df.to_csv(CSVpathDB, index=False, encoding='utf-8-sig')

        self.logger.info("Processus FGloader terminé...")



# === Independent running system ===
if __name__ == "__main__":

    LECOTloader = LECOTloader()
    
    result = LECOTloader.run()