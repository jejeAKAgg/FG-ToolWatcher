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


class KLIUMwatcher:
    def __init__(self, items, user_config: dict, catalog_config: dict):
        
        # === LOGGER SETUP ===
        self.logger = LogService.logger("KLIUM")
        
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
            accept_button = driver.find_element(By.ID, "CybotCookiebotDialogBodyButtonAccept")
            if accept_button.is_displayed():
                accept_button.click()
                self.logger.info(f"Cookies accepted for KLIUM: {driver.current_url}.")
                time.sleep(5)
        except Exception:
            self.logger.info(f"No cookies to accept or already accepted for KLIUM: {driver.current_url}.")


    def _extract_offers(self, soup: BeautifulSoup) -> Optional[str]:

        """
        Extracts quantity/price offers from KLIUM product page.

        Args:
            soup (BeautifulSoup): Parsed HTML.

        Returns:
            str: Offers formatted as 'quantity: price€ (discount)', or '-' if none found.
        
        """

        offers = []

        # Sélectionne tous les blocs d'offres
        for offer_div in soup.select("div.prod_discount_btn"):
            label = offer_div.find("label", class_="prod_discount_label")
            if not label:
                continue
            
            quantity_span = label.select_one("span.label-discount-text")
            price_span = label.select_one("span.label-discount-price")
            discount_span = label.select_one("span.label-discount.discounted-price")

            if quantity_span and price_span:
                quantity_text = quantity_span.get_text(strip=True)
                price_text = price_span.get_text(strip=True).replace('\xa0', '').replace(',', '.').replace('€', '')
                try:
                    price = float(price_text)
                except ValueError:
                    continue

                discount_text = f" ({discount_span.get_text(strip=True)})" if discount_span else ""
                offers.append(f"{quantity_text}: {price:.2f}€{discount_text}")

        return "\n".join(offers) if offers else "-"
    
    def _extract_ref(self, soup):

        """
        Extracts the KLIUM reference from the parsed HTML.

        Args:
            soup (BeautifulSoup): Parsed HTML of the product page.

        Returns:
            str | None: KLIUM reference or None if not found.
        
        """

        supplier_ref_li = soup.find('li', id='supplier_reference_value')
        if supplier_ref_li:
            span = supplier_ref_li.find('span')
            if span:
                span.extract()  # enlève le span
            
            ref_text = supplier_ref_li.get_text(strip=True)

            # Supprimer la marque si elle est en début de chaîne (insensible à la casse)
            for brand in KNOWN_BRANDS:
                if ref_text.lower().startswith(brand.lower() + ' '):
                    # Enlever la marque + espace
                    ref_text = ref_text[len(brand)+1:]
                    break
            
            return ref_text
        return None
    

    def _extract_FINALproduct(self, item, driver):
        
        # === INTERNAL VARIABLE(S) ===
        ATTEMPT = 0
        MAX_RETRIES = 3
        RETRY_DELAY = 5

        # === INTERNAL PARAMETER(S) ===
        REQUESTurl = f"https://www.klium.be/fr/recherche?s={item}"
        PRODUCTvar = {   
            'MPN': item,
            'Société': "KLIUM",
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

                ARTICLEpage =  driver.page_source
                ARTICLEurl = driver.current_url

                if "/recherche?" in ARTICLEurl or "/search?" in ARTICLEurl:
                    soup = BeautifulSoup(ARTICLEpage, "html.parser")
                    link = soup.select_one("div.thumbnail-container")

                    if link:
                        a_tag = link.find("a", class_="thumbnail product-thumbnail", href=True)
                        if a_tag:
                            ARTICLEurl = a_tag['href'].split("#")[0]

                    else:
                        self.logger.warning(f"Pas de produits trouvés pour le produit suivant: {item}")

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

                    if (res := self.ref_matcher.match(item, standardize_name((soup.find("h1", id="product_name_value")).get_text(strip=True).replace("\"", "\"\""), html=ARTICLEpage)))["score"] >= 0.70:
                        self.logger.info(f"Probabilité de {res['score']:.2f} pour le produit {item}: correspond probablement au produit")

                    else:
                        self.logger.warning(f"Faux positif détecté avec probabilité de {res['score']:.2f} pour le produit {item}, pas pris en compte: {res}")
                        return PRODUCTvar
                    
                
                PRODUCTvar['MPN'] = item
                PRODUCTvar['Société'] = 'KLIUM'
                PRODUCTvar['Article'] = (
                    (name := soup.find("h1", id="product_name_value"))
                    and standardize_name(name.get_text(strip=True).replace("\"", "\"\""), html=ARTICLEpage)
                )
                PRODUCTvar['ArticleURL'] = ARTICLEurl
                PRODUCTvar['Marque'] = (
                    (name := soup.find("h1", id="product_name_value"))
                    and extract_brand_from_all_sources(name.get_text(strip=True).replace("\"", "\"\""), html=ARTICLEpage)
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

                PRODUCTvar['Prix (HTVA)'] = format_price_for_excel(HTVA)
                PRODUCTvar['Prix (TVA)'] = format_price_for_excel(TVA)
                PRODUCTvar['Ancien Prix (HTVA)'] = "TODO"
                PRODUCTvar['Evolution du prix'] = "TODO"
                PRODUCTvar['Offres'] = self._extract_offers(soup)
                PRODUCTvar['Stock'] = bool(soup.select_one("#product-availability .availability-label.in-stock"))
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

    def run(self):
        
        CSVpath = os.path.join(RESULTS_SUBFOLDER_TEMP, "KLIUMproducts.csv")
        XLSXpath = os.path.join(RESULTS_SUBFOLDER_TEMP, "KLIUMproducts.xlsx")

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
            self.logger.error(f"Erreur fatale dans KLIUMwatcher: {e}")
        
        finally:
            if 'WEBdriver' in locals() and WEBdriver:
                WEBdriver.quit()

        df = pd.DataFrame(products)
        df.to_csv(CSVpath, index=False, encoding='utf-8-sig')
        df.to_excel(XLSXpath, index=False)

        self.logger.info("Processus KLIUMwatcher terminé...")

        return df