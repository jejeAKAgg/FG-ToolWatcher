import os
import shutil
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

from UTILS.EXCELutils import *
from UTILS.LOGmaker import *
from UTILS.PRODUCTformatter import *
from UTILS.TOOLSbox import *
from UTILS.WEBsearch import *



# ====================
#     LOGGER SETUP
# ====================
Logger = logger("CLABOTS")


# ====================
#    VARIABLE SETUP
# ====================
BASE_SYSTEM_PATH = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BASE_TEMP_PATH = sys._MEIPASS if getattr(sys, 'frozen', False) else ""

PROFILE_PATH = os.path.join(BASE_SYSTEM_PATH, "CORE", "chrome_profile")

CORE_FOLDER = os.path.join(BASE_SYSTEM_PATH, "CORE")
DATA_FOLDER = os.path.join(BASE_SYSTEM_PATH, "DATA")
LOGS_FOLDER = os.path.join(BASE_SYSTEM_PATH, "LOGS")

os.makedirs(CORE_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(LOGS_FOLDER, exist_ok=True)

if sys.platform.startswith("win"):
    CHROME_PATH = os.path.join(BASE_SYSTEM_PATH, "CORE", "chrome-win", "chrome.exe")
    CHROMEDRIVER_PATH = os.path.join(BASE_SYSTEM_PATH, "CORE", "chromedriver_win32", "chromedriver.exe")
    PYTHON_EXE = os.path.join(BASE_SYSTEM_PATH, "CORE", "python", "python.exe")

    BASE_CHROMIUM_URL = "https://commondatastorage.googleapis.com/chromium-browser-snapshots/Win_x64/"
    CHROMIUM_ZIP_NAME = "chrome-win.zip"
    CHROMEDRIVER_ZIP_NAME = "chromedriver_win32.zip"

elif sys.platform.startswith("linux"):
    CHROME_PATH = os.path.join(BASE_SYSTEM_PATH, "CORE", "chrome-win", "chrome.exe")
    CHROMEDRIVER_PATH = os.path.join(BASE_SYSTEM_PATH, "CORE", "chromedriver_win32", "chromedriver.exe")
    PYTHON_EXE = shutil.which("python3") or "/usr/bin/python3"

    BASE_CHROMIUM_URL = "https://commondatastorage.googleapis.com/chromium-browser-snapshots/Linux_x64/"
    CHROMIUM_ZIP_NAME = "chrome-linux.zip"
    CHROMEDRIVER_ZIP_NAME = "chromedriver_linux64.zip"

else:
    raise RuntimeError(f"Système non supporté: {sys.platform}")


# ================================
#    PARAMETERS & OPTIONS SETUP
# ================================
options = Options()

options.add_argument(f"--user-data-dir={PROFILE_PATH}")

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
def extract_CLABOTS_products_data(MPN, driver):

    # === INTERNAL VARIABLE(S) ===
    ATTEMPT = 0
    MAX_RETRIES = 3
    RETRY_DELAY = 5

    # === INTERNAL PARAMETER(S) ===
    REQUESTurl = f"https://www.clabots.be/fr/product/search?search={MPN}&_rand=0.9565057069184605"
    PRODUCTvar = {   
        'MPN': "REF-" + MPN,
        'Société': "CLABOTS",
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
            
            time.sleep(5)  # Loading time (JS)

            ARTICLEpage =  driver.page_source
            ARTICLEurl = driver.current_url
            
            if "/recherche?" in ARTICLEurl or "/search?" in ARTICLEurl:
                soup = BeautifulSoup(ARTICLEpage, "html.parser")
                link = soup.select_one('.grid-row.product-item')

                if link:
                    a_tag = link.select_one('a.view-product[href]')
                    if a_tag:
                        ARTICLEurl = "https://www.clabots.be" + a_tag['href'].split("#")[0]
                    else:
                        Logger.warning(f"Pas de liens trouvés pour la REF-{MPN}")
                        Logger.warning("Tentative de recherche avec Google...")
                        ARTICLEurl = WEBsearch(MPN, "clabots.be")
                else:
                    Logger.warning(f"Pas de produits trouvés pour la REF-{MPN}")
                    
                    return PRODUCTvar
                    
                driver.get(ARTICLEurl)
                
                time.sleep(5) # Loading time (JS)

                ARTICLEpage = driver.page_source
                ARTICLEurl = driver.current_url

            
            soup = BeautifulSoup(ARTICLEpage, "html.parser")

            if (extract_clabots_ref(soup) is not None and extract_clabots_ref(soup) != MPN):
                Logger.warning(f"Incompatibilité détectée pour la REF-{MPN}: REF-{extract_clabots_ref(soup)} scannée à la place!")
                Logger.warning("Recherche de match potentiel...")

                if (res := potential_match(MPN, standardize_name((soup.find("h1", class_="page-title") or soup.find("h1")).get_text(strip=True).replace("\"", "\"\""), html=ARTICLEpage)))["score"] >= 0.75:
                    Logger.info(f"Probabilité de {res['score']:.2f} pour la REF-{MPN}: correspond probablement au produit")
                else:
                    Logger.warning(f"Faux positif détecté avec probabilité de {res['score']:.2f} pour la REF-{MPN}, pas pris en compte: {res}")
                    return PRODUCTvar
            
            PRODUCTvar['MPN'] = "REF-" + MPN
            PRODUCTvar['Société'] = 'CLABOTS'
            PRODUCTvar['Article'] = (
                (name := (soup.find("h1", class_="page-title") or soup.find("h1"))) 
                and standardize_name(name.get_text(strip=True).replace("\"", "\"\""), html=ARTICLEpage)
            )
            PRODUCTvar['ArticleURL'] = ARTICLEurl
            PRODUCTvar['Marque'] = (
                (name := (soup.find("h1", class_="page-title") or soup.find("h1"))) and
                extract_brand_from_all_sources(name.get_text(strip=True).replace("\"", "\"\""), html=ARTICLEpage)
            )

            HTVA, TVA = calculate_missing_price((
                (e := soup.find("div", class_="price-htvac")) and parse_price(e.get_text(strip=True).split()[0])
            ), (
                (e := soup.select_one("p.your-price")) and parse_price(e.get_text(strip=True))
            ))

            PRODUCTvar['Prix (HTVA)'] = format_price_for_excel(HTVA)
            PRODUCTvar['Prix (TVA)'] = format_price_for_excel(TVA)
            PRODUCTvar['Ancien Prix (HTVA)'] = "TODO"
            PRODUCTvar['Evolution du prix'] = "TODO"
            PRODUCTvar['Offres'] = "-"
            PRODUCTvar['Stock'] = bool(soup.select_one("#product-availability .availability-label.in-stock"))
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
def CLABOTSwatcher(ITEMs):

    CSVpath = os.path.join(BASE_SYSTEM_PATH, "DATA", "CLABOTSproducts.csv")
    XLSXpath = os.path.join(BASE_SYSTEM_PATH, "DATA", "CLABOTSproducts.xlsx")

    CACHEdata = load_cache(CSVpath)

    products = []
    try:
        driver = webdriver.Chrome(options=options, service=service)

        for ITEM in ITEMs:
            if cached := check_cache(CACHEdata, ITEM):
                Logger.info(f"REF-{ITEM} récupéré depuis le cache")
                products.append(cached)
                continue

            data = extract_CLABOTS_products_data(ITEM, driver)
            if data:
                products.append(data)
            time.sleep(random.uniform(1.5, 3))
    
    finally:
        if 'driver' in locals() and driver:
            driver.quit()


    df = pd.DataFrame(products)
    df.to_csv(CSVpath, index=False, encoding='utf-8-sig')
    df.to_excel(XLSXpath, index=False)

    Logger.info("Processus CLABOTSwatcher terminé...")

    return df