# WEBSITES/FIXAMIwatcher.py
import os
import sys
import time

import numpy as np
import pandas as pd
import random

from bs4 import BeautifulSoup

from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from APP.SERVICES.__init__ import *

from APP.UTILS.LOGmaker import *
from APP.UTILS.PRODUCTformatter import *
from APP.UTILS.WEBSITEutils import *



# ====================
#     LOGGER SETUP
# ====================
Logger = logger("FIXAMI")


# ================================
#    PARAMETERS & OPTIONS SETUP
# ================================
options = Options()

options.add_argument(f"--user-data-dir={CHROME_PROFILE_PATH}")

options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--disable-software-rasterizer")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--no-sandbox")
options.add_argument("--window-size=400,400")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-infobars")
options.add_argument("--disable-extensions")
options.add_argument("--disable-software-rasterizer")
options.add_argument("--disable-logging")
options.add_argument("--log-level=3")
options.add_argument("--remote-debugging-port=9222")
options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")

options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
options.add_experimental_option('useAutomationExtension', False)

if sys.platform.startswith("win"):
    options.binary_location = CHROME_PATH
    service = Service(executable_path=CHROMEDRIVER_PATH)
else:
    service = None


# ====================
#      FUNCTIONS
# ====================
def extract_FIXAMI_products_data(MPN, driver):

    # === PARAMETERS ===
    ATTEMPT = 0
    MAX_RETRIES = 3
    RETRY_DELAY = 5

    # === INTERNAL PARAMETER(S) ===
    REQUESTurl = f"https://www.fixami.be/fr/produits.html?s={MPN}"
    PRODUCTvar = {   
        'MPN': "REF-" + MPN,
        'Société': "FIXAMI",
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

    # === Running search ===
    while ATTEMPT < MAX_RETRIES:
        try:
            driver.get(REQUESTurl)
            
            time.sleep(5)

            accept_cookies(driver, "Fixami")

            ARTICLEpage = driver.page_source
            ARTICLEurl = driver.current_url

            # Si on est resté sur la page de recherche (pas redirigé)
            if "/produits.html?" in ARTICLEurl:
                soup = BeautifulSoup(ARTICLEpage, "html.parser")
                link = soup.find("span", {"data-testid": "product-name"})
                
                if link:
                    a_tag = link.find_parent("a", href=True)
                    if a_tag:
                        ARTICLEurl = "https://www.fixami.be" + a_tag['href'].split("#")[0]
                    else:
                        Logger.warning(f"Pas de liens trouvés pour la REF-{MPN}")
                        Logger.warning(f"Tentative de recherche avec Google...")
                        #ARTICLEurl = WEBsearch(MPN, "fixami.be")
                else:
                    Logger.warning(f"Pas de produits trouvés pour la REF-{MPN}")

                    return PRODUCTvar
                    
                driver.get(ARTICLEurl)
                
                time.sleep(5)

                accept_cookies(driver, "Fixami")
                    
                ARTICLEpage = driver.page_source
                ARTICLEurl = driver.current_url


            soup = BeautifulSoup(ARTICLEpage, "html.parser")

            if (extract_fixami_ref(soup) is not None and extract_fixami_ref(soup) != MPN):
                Logger.warning(f"Faux positif détecté pour la REF-{MPN}: REF-{extract_fixami_ref(soup)} détectée à la place! Pas pris en compte...")

                return PRODUCTvar
            
            PRODUCTvar['MPN'] = "REF-" + MPN
            PRODUCTvar['Société'] = 'FIXAMI'
            PRODUCTvar['Article'] = (
                (name := soup.find("h1", class_="sc-9a380768-0"))
                and standardize_name(name.get_text(strip=True).replace("\"", "\"\""), html=ARTICLEpage)
            )
            PRODUCTvar['ArticleURL'] = ARTICLEurl
            PRODUCTvar['Marque'] = (
                (name := soup.find("h1", class_="sc-9a380768-0"))
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
                    (e := soup.select_one("span.sc-f3d015ac-0")) and parse_price(e.get_text(strip=True))
                )
            )

            PRODUCTvar['Prix (HTVA)'] = format_price_for_excel(HTVA)
            PRODUCTvar['Prix (TVA)'] = format_price_for_excel(TVA)
            PRODUCTvar['Ancien Prix (HTVA)'] = "TODO"
            PRODUCTvar['Evolution du prix'] = "TODO"
            PRODUCTvar['Offres'] = extract_offers_FIXAMI(soup)
            PRODUCTvar['Stock'] = bool(
                (delivery := soup.find("p", attrs={"data-testid": "delivery-time"}))
                and ("livré demain" in delivery.get_text(strip=True).lower())
            )
            PRODUCTvar['Checked on'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            return PRODUCTvar
        

        except Exception as e:
            Logger.warning(f"Erreur lors de l'extraction des données pour la REF-{MPN}: {e}")
            
            ATTEMPT+=1
            if ATTEMPT == MAX_RETRIES:
                Logger.warning(f"Abandon après {MAX_RETRIES} tentatives pour REF-{MPN}")

                return PRODUCTvar
            
            else:
                time.sleep(RETRY_DELAY)


# ====================
#        MAIN
# ====================
def FIXAMIwatcher(ITEMs):

    CSVpath = os.path.join(RESULTS_SUBFOLDER_TEMP, "FIXAMIproducts.csv")
    XLSXpath = os.path.join(RESULTS_SUBFOLDER_TEMP, "FIXAMIproducts.xlsx")

    CACHEdata = load_cache(CSVpath)

    products = []
    try:
        driver = webdriver.Chrome(options=options, service=service)

        for ITEM in ITEMs:
            if cached := check_cache(CACHEdata, ITEM):
                Logger.info(f"REF-{ITEM} récupéré depuis le cache")
                products.append(cached)
                continue

            data = extract_FIXAMI_products_data(ITEM, driver)
            if data:
                products.append(data)
            time.sleep(random.uniform(1.5, 3))
    
    finally:
        if 'driver' in locals() and driver:
            driver.quit()

    df = pd.DataFrame(products)
    df.to_csv(CSVpath, index=False, encoding='utf-8-sig')
    df.to_excel(XLSXpath, index=False)

    Logger.info("Processus FIXAMIwatcher terminé...")

    return df