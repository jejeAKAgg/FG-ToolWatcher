# APP/WEBSITES/CIPACwatcher.py
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

from APP.SERVICES.__init__ import *

from APP.SERVICES.CACHEservice import CacheService
from APP.SERVICES.MATCHERservice import MatcherService

from APP.SERVICES.LOGservice import LogService
from APP.UTILS.PRODUCTformatter import *


class CIPACwatcher:
    def __init__(self, items, user_config: dict, catalog_config: dict):
        
        # === LOGGER SETUP ===
        self.logger = LogService.logger("CIPAC")
        
        # === INPUT VARIABLE(S) ===
        self.items = items
        self.user_config = user_config
        self.catalog_config = catalog_config

        # === SERVICE(S) ===
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
        
        pass
    
    
    def _extract_offers(self, soup: BeautifulSoup) -> Optional[str]:

        """
        Extracts quantity/price offers from CIPAC product page.

        Args:
            soup (BeautifulSoup): Parsed HTML.

        Returns:
            str: Offers formatted as 'quantity: price€ (discount)', or '-' if none found.
        """

        pass

    def _extract_ref(self, soup):

        """
        Extracts the CIPAC reference from the parsed HTML.

        Args:
            soup (BeautifulSoup): Parsed HTML of the product page.

        Returns:
            str | None: CIPAC reference or None if not found.
        """

        p_ref = soup.find("p", class_="ref")
        if p_ref:
            text = p_ref.get_text(separator=" ").strip()
            # Capture only until another label (EAN, Code...) or end of line
            match = re.search(r"Réf\. ?: ?([A-Za-z0-9\-\s_/.,]+?)(?=\s*[A-Z]+\s*:|$)", text)
            if match:
                return match.group(1).strip()

        return None


    def _extract_FINALproduct(self, item, driver):
        
        # === INTERNAL VARIABLE(S) ===
        ATTEMPT = 0
        MAX_RETRIES = 3
        RETRY_DELAY = 5

        # === INTERNAL PARAMETER(S) ===
        REQUESTurl = f"https://www.cipac.be/produits?ts-obj=produits&ts={item}"
        PRODUCTvar = {   
            'MPN': item,
            'Société': "CIPAC",
            'Article': "Produit indisponible",
            'ArticleURL': "-",
            'Marque': "-",
            'Prix (HTVA)': np.nan,
            'Prix (TVA)': np.nan,
            'Ancien Prix (HTVA)': np.nan,
            'Evolution du prix': "-",
            'Offres': "-",
            'Stock': "-",
            'Checked on': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # === SEARCH ENGINE ===
        while ATTEMPT < MAX_RETRIES:
            try:
                driver.get(REQUESTurl)
                
                time.sleep(5)  # Loading time (JS)

                self._accept_cookies(driver)

                ARTICLEpage = driver.page_source
                ARTICLEurl = driver.current_url
                
                if ARTICLEurl == REQUESTurl or "produits?" in ARTICLEurl:
                    soup = BeautifulSoup(ARTICLEpage, "html.parser")
                    link = soup.find("div", class_="item-content")
                    
                    if link:
                        a_tag = link.find("a", href=True)
                        if a_tag:
                            ARTICLEurl = "https://www.cipac.be" + a_tag['href'].split("#")[0]

                    else:
                        self.logger.warning(f"Pas de liens trouvés pour le produit suivant: {item}")
                        
                        return PRODUCTvar

                    driver.get(ARTICLEurl)
                    
                    time.sleep(5) # Loading time (JS)

                    self._accept_cookies(driver)

                    ARTICLEpage = driver.page_source
                    ARTICLEurl = driver.current_url

                soup = BeautifulSoup(ARTICLEpage, "html.parser")

                if (self._extract_ref(soup) is not None and self._extract_ref(soup) != item):           
                    self.logger.warning(f"Incompatibilité détectée pour le produit {item}: {self._extract_ref(soup)} scannée à la place!")
                    self.logger.warning("Recherche de match potentiel...")

                    if (res := self.ref_matcher.match(item, standardize_name((soup.find("h1") or soup.select_one("div[class*='col-'] h1")).get_text(strip=True).replace("\"", "\"\""), html=ARTICLEpage)))["score"] >= 0.70:
                        self.logger.info(f"Probabilité de {res['score']:.2f} pour le produit {item}: correspond probablement au produit. [{res}]")

                    else:
                        self.logger.warning(f"Faux positif détecté avec probabilité de {res['score']:.2f} pour le produit {item}, pas pris en compte: {res}")
                        return PRODUCTvar


                PRODUCTvar['MPN'] = item
                PRODUCTvar['Société'] = "CIPAC"
                PRODUCTvar['Article'] = (
                    (name := (soup.find("h1") or soup.select_one("div[class*='col-'] h1")))
                    and standardize_name(name.get_text(strip=True).replace("\"", "\"\""), html=ARTICLEpage)
                )
                PRODUCTvar['ArticleURL'] = ARTICLEurl
                PRODUCTvar['Marque'] = (
                    (name := (soup.find("h1") or soup.select_one("div[class*='col-'] h1")))
                    and extract_brand_from_all_sources(name.get_text(strip=True).replace("\"", "\"\""), html=ARTICLEpage)
                )
                
                HTVA, TVA = calculate_missing_price(
                    htva=(
                        (e := next(
                            (soup.select_one(sel) for sel in ['span.promo', 'span.regular', 'p.prixcatalogue']
                            if soup.select_one(sel)), None
                        )) and parse_price(e.get_text(strip=True))
                    ),
                    tva=(
                        (e := soup.select_one("span.htva")) and parse_price(e.get_text(strip=True))
                    )
                )

                PRODUCTvar['Prix (HTVA)'] = format_price_for_excel(HTVA)
                PRODUCTvar['Prix (TVA)'] = format_price_for_excel(TVA)
                PRODUCTvar['Ancien Prix (HTVA)'] = "TODO"
                PRODUCTvar['Evolution du prix'] = "TODO"
                PRODUCTvar['Offres'] = "-"
                PRODUCTvar['Stock'] = bool(soup.select_one(".stock-mag .stock-mag-1, .stock-info .enstock"))
                PRODUCTvar['Checked on'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                return PRODUCTvar
            

            except Exception as e:
                self.logger.warning(f"Erreur lors de l'extraction des données pour le produit {item}: {e}")
                
                ATTEMPT+=1
                if ATTEMPT == MAX_RETRIES:
                    self.logger.warning(f"Abandon après {MAX_RETRIES} tentatives pour produit {item}")

                    return PRODUCTvar
                
                else:
                    time.sleep(RETRY_DELAY)


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
            self.logger.error(f"Erreur fatale dans CIPACwatcher: {e}")
        
        finally:
            if 'WEBdriver' in locals() and WEBdriver:
                WEBdriver.quit()

        df = pd.DataFrame(products)
        df.to_csv(CSVpath, index=False, encoding='utf-8-sig')
        df.to_excel(XLSXpath, index=False)

        self.logger.info("Processus CIPACwatcher terminé...")

        return df
    


# === Independent running system for potential testing ===
if __name__ == "__main__":

    # 1️⃣ Items
    items = ["MCR 75 GC", "JET.T7NM3A"]

    # 2️⃣ Simulating User Configuration [disabling cache for testing purposes]
    user_config = {
        "cache_duration": 0
    }

    # 3️⃣ Simulating Catalog Configuration
    catalog_config = {
        "source": "cipac"
    }

    CIPACwatcher = CIPACwatcher(items, user_config, catalog_config)
    df = CIPACwatcher.run()

    print(df)