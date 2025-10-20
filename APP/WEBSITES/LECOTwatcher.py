# APP/WEBSITES/KLIUMwatcher.py
import os
import sys
import time

import numpy as np
import pandas as pd
import random
import re

from bs4 import BeautifulSoup

from datetime import datetime

from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from APP.SERVICES.__init__ import *

from APP.SERVICES.CACHEservice import CacheService
from APP.SERVICES.MATCHERservice import MatcherService

from APP.SERVICES.LOGservice import LogService
from APP.UTILS.PRODUCTformatter import *


class LECOTwatcher:
    def __init__(self, items, user_config: dict, catalog_config: dict):
        
        # === LOGGER SETUP ===
        self.logger = LogService.logger("LECOT")
        
        # === INPUT VARIABLES ===
        self.items = items
        self.user_config = user_config
        self.catalog_config = catalog_config

        # === SERVICES ===
        self.cache_service = CacheService(cache_duration_days=self.user_config.get("cache_duration", 3))
        self.ref_matcher = MatcherService()

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
            accept_button = driver.find_element(By.ID, "CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll")
            if accept_button.is_displayed():
                accept_button.click()
                self.logger.info(f"Cookies accepted for LECOT: {driver.current_url}.")
                time.sleep(5)
        except Exception:
            self.logger.info(f"No cookies to accept or already accepted for LECOT: {driver.current_url}.")

    
    def _extract_offers(self, soup: BeautifulSoup) -> Optional[str]:

        """
        Extracts quantity/price offers from LECOT product page.

        Args:
            soup (BeautifulSoup): Parsed HTML.

        Returns:
            str: Offers formatted as 'quantity: price€ (discount)', or '-' if none found.
        
        """

        pass

    def _extract_ref(self, soup):

        """
        Extracts the LECOT reference from the parsed HTML.

        Args:
            soup (BeautifulSoup): Parsed HTML of the product page.

        Returns:
            str | None: LECOT reference or None if not found.
        
        """

        rows = soup.select('tr.properties-row')
        for row in rows:
            label = row.select_one('th.properties-label')
            value = row.select_one('td.properties-value')
            if label and value:
                if label.get_text(strip=True).lower() == "numéro de fournisseur":
                    return value.get_text(strip=True)
        return None
    

    def _extract_FINALproduct(self, item, driver):
        
        # === INTERNAL VARIABLE(S) ===
        ATTEMPT = 0
        MAX_RETRIES = 3
        RETRY_DELAY = 5

        # === INTERNAL PARAMETER(S) ===
        REQUESTurl = f"https://shop.lecot.be/fr-be/#sqr:(q[{item}])"
        PRODUCTvar = {
            'MPN': item,
            'Société': "LECOT",
            'Article': "Produit indisponible",
            'ArticleURL': "-",
            'Marque': "-",
            'Prix (HTVA)': "-",
            'Prix (TVA)': "-",
            'Ancien Prix (HTVA)': "-",
            'Evolution du prix': "-",
            'Offres': "-",
            'Stock': "-",
            'Checked on': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # === SEARCH ENGINE ===
        while ATTEMPT < MAX_RETRIES:
            try:
                
                driver.get(REQUESTurl)
                
                time.sleep(3)  # Loading time (JS)

                self._accept_cookies(driver)

                ARTICLEpage =  driver.page_source
                ARTICLEurl = driver.current_url

                # Si on est resté sur la page de recherche (pas redirigé)
                if "#sqr:" in ARTICLEurl:
                    soup = BeautifulSoup(ARTICLEpage, "html.parser")
                    link = soup.find("div", class_="card-body product-box-info")

                    if link:
                        a_tag = link.find("a", class_="product-name", href=True)
                        if a_tag:
                            ARTICLEurl = a_tag['href'].split("#")[0]

                    else:
                        self.logger.warning(f"Pas de liens trouvés pour le produit suivant: {item}")
                        
                        return PRODUCTvar

                    driver.get(ARTICLEurl)
                    
                    time.sleep(3)

                    self._accept_cookies(driver)

                    ARTICLEpage = driver.page_source
                    ARTICLEurl = driver.current_url

                soup = BeautifulSoup(ARTICLEpage, "html.parser")
                
                if (self._extract_ref(soup) is not None and self._extract_ref(soup) != item):
                    self.logger.warning(f"Incompatibilité détectée pour le produit {item}: {self._extract_ref(soup)} scannée à la place!")
                    self.logger.warning("Recherche de match potentiel...")

                    if (res := self.ref_matcher.match(item, standardize_name((soup.select_one("h1.product-detail-name")).get_text(strip=True).replace("\"", "\"\""), html=ARTICLEpage)))["score"] >= 0.70:
                        self.logger.info(f"Probabilité de {res['score']:.2f} pour le produit {item}: correspond probablement au produit")

                    else:
                        self.logger.warning(f"Faux positif détecté avec probabilité de {res['score']:.2f} pour le produit {item}, pas pris en compte: {res}")
                        return PRODUCTvar


                PRODUCTvar['MPN'] = item
                PRODUCTvar['Société'] = "LECOT"
                PRODUCTvar['Article'] = (
                    (name := (soup.select_one("h1.product-detail-name")))
                    and standardize_name(name.get_text(strip=True).replace("\"", "\"\""), html=ARTICLEpage)
                )
                PRODUCTvar['ArticleURL'] = ARTICLEurl,
                PRODUCTvar['Marque'] = (
                    (name := soup.select_one("h1.product-detail-name"))
                    and extract_brand_from_all_sources(name.get_text(strip=True).replace("\"", "\"\""), html=ARTICLEpage)
                )

                HTVA, TVA = calculate_missing_price(
                    htva=(
                        (e := soup.select_one('div.product-price-vat.product-price-info'))
                        and parse_price(e.get_text(strip=True))
                    ),
                    tva=(
                        (e := soup.select_one('p.product-detail-price'))
                        and parse_price(e.get_text(strip=True))
                    )
                )

                PRODUCTvar['Prix (HTVA)'] = format_price_for_excel(HTVA)
                PRODUCTvar['Prix (TVA)'] = format_price_for_excel(TVA)
                PRODUCTvar['Ancien Prix (HTVA)'] = "TODO"
                PRODUCTvar['Evolution du prix'] = "TODO"
                PRODUCTvar['Offres'] = "-"
                PRODUCTvar['Stock'] = "INCONNU"
                PRODUCTvar['Checked on'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                return PRODUCTvar
            

            except Exception as e:
                self.logger.warning(f"Erreur lors de l'extraction des données pour le produit {item}: {e}")

                ATTEMPT+=1
                if ATTEMPT == MAX_RETRIES:
                    self.logger.warning(f"Abandon après {MAX_RETRIES} tentatives pour le produit suivant: {item}")
                    
                    return PRODUCTvar
                
                else:
                    time.sleep(RETRY_DELAY)
                
            finally:
                driver.quit()


    def run(self):

        CSVpath = os.path.join(RESULTS_SUBFOLDER_TEMP, "CIPACproducts.csv")
        XLSXpath = os.path.join(RESULTS_SUBFOLDER_TEMP, "CIPACproducts.xlsx")

        CACHEdata = self.cache_service.load_cache(CSVpath)

        products = []

        try:
            WEBdriver = self._init_driver()

            for ITEM in self.items:
                if cached := self.cache_service.check_cache(CACHEdata, ITEM):
                    self.logger.info(f"Produit {ITEM} récupéré depuis le cache")
                    products.append(cached)
                    
                    continue

                data = self._extract_FINALproduct(ITEM, WEBdriver)
                if data:
                    products.append(data)
                time.sleep(random.uniform(1.5, 3))
        
        except Exception as e:
            self.logger.error(f"Erreur fatale dans LECOTwatcher: {e}")
        
        finally:
            if 'WEBdriver' in locals() and WEBdriver:
                WEBdriver.quit()

        df = pd.DataFrame(products)
        df.to_csv(CSVpath, index=False, encoding='utf-8-sig')
        df.to_excel(XLSXpath, index=False)

        self.logger.info("Processus LECOTwatcher terminé...")

        return df