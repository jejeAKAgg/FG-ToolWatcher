import os
import sys
import time

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
from UTILS.WEBsearch import *



# ====================
#     LOGGER SETUP
# ====================
Logger = logger("FERNAND GEORGES")


# ====================
#    VARIABLE SETUP
# ====================
if sys.platform.startswith("win"):
    BASE_SYSTEM_PATH = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    BASE_TEMP_PATH = sys._MEIPASS if getattr(sys, 'frozen', False) else ""

    CORE_FOLDER = os.path.join(BASE_SYSTEM_PATH, "CORE")
    DATA_FOLDER = os.path.join(BASE_SYSTEM_PATH, "DATA")
    LOGS_FOLDER = os.path.join(BASE_SYSTEM_PATH, "LOGS")

    os.makedirs(CORE_FOLDER, exist_ok=True)
    os.makedirs(DATA_FOLDER, exist_ok=True)
    os.makedirs(LOGS_FOLDER, exist_ok=True)

    CHROME_PATH = os.path.join(BASE_SYSTEM_PATH, "CORE", "chrome-win", "chrome.exe")
    CHROMEDRIVER_PATH = os.path.join(BASE_SYSTEM_PATH, "CORE", "chromedriver_win32", "chromedriver.exe")
    PYTHON_EXE = os.path.join(BASE_SYSTEM_PATH, "CORE", "python", "python.exe")

if sys.platform.startswith("linux"):
    BASE_SYSTEM_PATH = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    BASE_TEMP_PATH = sys._MEIPASS if getattr(sys, 'frozen', False) else ""

    CORE_FOLDER = os.path.join(BASE_SYSTEM_PATH, "CORE")
    DATA_FOLDER = os.path.join(BASE_SYSTEM_PATH, "DATA")
    LOGS_FOLDER = os.path.join(BASE_SYSTEM_PATH, "LOGS")

    os.makedirs(CORE_FOLDER, exist_ok=True)
    os.makedirs(DATA_FOLDER, exist_ok=True)
    os.makedirs(LOGS_FOLDER, exist_ok=True)


# ====================
#      FUNCTIONS
# ====================
def extract_FG_products_data(MPN):

    # === PARAMETERS ===
    ATTEMPT = 0
    MAX_RETRIES = 3
    RETRY_DELAY = 5
    
    # === Selenium OPTIONS ===
    options = Options()

    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
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

    # === Initializing WebDriver & running search ===
    driver = webdriver.Chrome(options=options, service=service)
    while ATTEMPT < MAX_RETRIES:
        try:
            REQUESTurl = f"https://www.georges.be/fr-be/search?q={MPN}"
            driver.get(REQUESTurl)
            
            time.sleep(3)  # Loading time (JS)

            ARTICLEpage = driver.page_source
            ARTICLEurl = driver.current_url
            
            if ARTICLEurl == REQUESTurl or "search?" in ARTICLEurl:
                soup = BeautifulSoup(ARTICLEpage, "html.parser")
                link = soup.find("div", class_="l-products-item")
    
                if link:
                    a_tag = link.find("a", href=True)
                    if a_tag:
                        ARTICLEurl = "https://www.georges.be" + a_tag['href'].split("#")[0]
                    else:
                        Logger.warning(f"Pas de liens trouvés pour la REF-{MPN}")
                        Logger.warning(f"Tentative de recherche avec Google...")
                        ARTICLEurl = WEBsearch(MPN, "georges.be")
                else:
                    Logger.warning(f"Pas de produits trouvés pour la REF-{MPN}")
                    product = {
                        'MPN': "REF-" + MPN,
                        'Société': "FERNAND GEORGES",
                        'Article': "Produit indisponible",
                        'Marque': "-",
                        'Prix (HTVA)': "-",
                        'Prix (TVA)': "-",
                        'Ancien Prix (HTVA)': "-",
                        'Evolution du prix': "-",
                        'Offres': "-",
                        'Stock': "-",
                        'Checked on': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }

                    return product

                driver.quit() # Restarting the driver to avoid issues with BOT detection
                driver = webdriver.Chrome(options=options, service=service)

                driver.get(ARTICLEurl)
                
                time.sleep(3) # Loading time (JS)

                ARTICLEpage = driver.page_source
                ARTICLEurl = driver.current_url

            soup = BeautifulSoup(ARTICLEpage, "html.parser")

            #if (extract_cipac_ref(soup) is not None and extract_cipac_ref(soup) != MPN):
                #Logger.warning(f"Faux positif détecté pour la REF-{MPN}: REF-{extract_cipac_ref(soup)} détectée à la place! Pas pris en compte...")
                #product = {
                    #'MPN': "REF-" + MPN,
                    #'Société': "FERNAND GEORGES",
                    #'Article': "Produit indisponible",
                    #'Marque': "-",
                    #'Prix (HTVA)': "-",
                    #'Prix (TVA)': "-",
                    #'Ancien Prix (HTVA)': "-",
                    #'Evolution du prix': "-",
                    #'Offres': "-",
                    #'Stock': "-",
                    #'Checked on': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                #}

                #return product

            product = {}

            product['MPN'] = "REF-" + MPN
            product['Société'] = "FERNAND GEORGES"
            product['Article'] = (
                (name := soup.find("h1", class_="font-product-title"))
                and f'=HYPERLINK("{ARTICLEurl}"; "{standardize_name(name.get_text(strip=True).replace("\"", "\"\""), html=ARTICLEpage)}")'
            )
            product['Marque'] = (
                (name := soup.find("h1", class_="font-product-title"))
                and extract_brand_from_all_sources(name.get_text(strip=True).replace("\"", "\"\""), html=ARTICLEpage)
            )

            HTVA, TVA = calculate_missing_price(
                htva=(
                    (prices_action := soup.find("div", class_="prices-action")) and
                    (htva_div := prices_action.find("div", string=lambda t: t and "HTVA" in t)) and
                    (e := htva_div.find_previous("meta", itemprop="price")) and
                    parse_price(e["content"])
                ),
                tva=(
                    (price_tvac := soup.find("div", class_="price-tvac")) and
                    (e := price_tvac.find("meta", itemprop="price")) and
                    parse_price(e["content"])
                )
            )

            product['Prix (HTVA)'] = format_price_for_excel(HTVA)
            product['Prix (TVA)'] = format_price_for_excel(TVA)
            product['Ancien Prix (HTVA)'] = "TODO"
            product['Evolution du prix'] = "TODO"
            product['Offres'] = "-"
            product['Stock'] = any(
                int(s.get_text(strip=True).split()[0]) > 0
                for s in soup.select(".multiple-locations-wrapper .stock-amount")
            )
            product['Checked on'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            return product


        except Exception as e:
            Logger.warning(f"Erreur lors de l'extraction des données pour la REF-{MPN}: {e}")
            
            ATTEMPT+=1
            if ATTEMPT == MAX_RETRIES:
                Logger.warning(f"Abandon après {MAX_RETRIES} tentatives pour REF-{MPN}")
                product = {
                    'MPN': MPN,
                    'Société': "FERNAND GEORGES",
                    'Article': "Erreur lors de l'extraction",
                    'Marque': "-",
                    'Prix (HTVA)': "-",
                    'Prix (TVA)': "-",
                    'Ancien Prix (HTVA)': "-",
                    'Evolution du prix': "-",
                    'Offres': "-",
                    'Stock': "-",
                    'Checked on': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

                return product
            
            else:
                time.sleep(RETRY_DELAY)

        # === Closing WebDriver ===
        finally:
            driver.quit()



# ====================
#        MAIN
# ====================
def FGwatcher():

    MPNs = EXCELreader("MPNs")

    CSVpath = os.path.join(BASE_SYSTEM_PATH, "DATA", "FGproducts.csv")
    XLSXpath = os.path.join(BASE_SYSTEM_PATH, "DATA", "FGproducts.xlsx")

    products = []
    for MPN in MPNs:
        data = extract_FG_products_data(MPN)
        if data:
            products.append(data)
        time.sleep(random.uniform(1.5, 3))

    df = pd.DataFrame(products)
    df.to_csv(CSVpath, index=False, encoding='utf-8-sig')
    df.to_excel(XLSXpath, index=False)

    Logger.info("Processus FGwatcher terminé...")

    return df