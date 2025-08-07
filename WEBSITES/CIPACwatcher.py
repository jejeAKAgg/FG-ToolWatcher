import os
import sys
import time
import random
import pandas as pd

from datetime import datetime

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from UTILS.LOGmaker import logger
from UTILS.NAMEformatter import *

from UTILS.EXCELreader import EXCELreader
from UTILS.WEBsearch import WEBsearch


# ====================
#     LOGGER SETUP
# ====================
Logger = logger("CIPAC")


# ====================
#    VARIABLE SETUP
# ====================
if sys.platform.startswith("win"):
    BASE_PATH = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    CHROME_PATH = os.path.join(BASE_PATH, "CORE", "chrome-win", "chrome.exe")
    CHROMEDRIVER_PATH = os.path.join(BASE_PATH, "CORE", "chromedriver_win32", "chromedriver.exe")


# ====================
#      FUNCTIONS
# ====================
def extract_CIPAC_products_data(MPN):
    
    # === Selenium OPTIONS ===
    options = Options()
    
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=400,400")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        )
    
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.add_experimental_option('useAutomationExtension', False)

    if sys.platform.startswith("win"):
        options.binary_location = CHROME_PATH
        service = Service(executable_path=CHROMEDRIVER_PATH)
    else:
        service = None

    # === Initializing WebDriver & running search ===
    driver = webdriver.Chrome(options=options, service=service)
    try:
        REQUESTurl = f"https://www.cipac.be/produits?ts-obj=produits&ts={MPN}"
        driver.get(REQUESTurl)
        
        time.sleep(5)  # Loading time (JS)

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
                    Logger.warning(f"No links found for this REF-{MPN}")
                    Logger.warning(f"Searching with Google")
                    ARTICLEurl = WEBsearch(MPN, "cipac.be")
            else:
                Logger.warning(f"No links found for this REF-{MPN}")
                product = {
                    'MPN': "REF-" + MPN,
                    'Société': "CIPAC",
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
            driver = webdriver.Chrome(options=options)

            driver.get(ARTICLEurl)
            
            time.sleep(5) # Loading time (JS)

            ARTICLEpage = driver.page_source
            ARTICLEurl = driver.current_url

        soup = BeautifulSoup(ARTICLEpage, "html.parser")

        if (extract_cipac_ref(soup) is not None and extract_cipac_ref(soup) != MPN):
            Logger.warning(f"False positive detected for REF-{MPN}: got REF-{extract_cipac_ref(soup)}! Skipping...")
            product = {
                'MPN': "REF-" + MPN,
                'Société': "CIPAC",
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

        product = {}

        product['MPN'] = "REF-" + MPN
        product['Société'] = "CIPAC"
        product['Article'] = (
            (name := (soup.find("h1") or soup.select_one("div[class*='col-'] h1")))
            and f'=HYPERLINK("{ARTICLEurl}"; "{standardize_name(name.get_text(strip=True).replace("\"", "\"\""), html=ARTICLEpage)}")'
        )
        product['Marque'] = (
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

        product['Prix (HTVA)'] = format_price_for_excel(HTVA)
        product['Prix (TVA)'] = format_price_for_excel(TVA)
        product['Ancien Prix (HTVA)'] = "TODO"
        product['Evolution du prix'] = "TODO"
        product['Offres'] = "-"
        product['Stock'] = bool(soup.select_one(".stock-mag .stock-mag-1, .stock-info .enstock"))
        product['Checked on'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return product
    

    except Exception as e:
        Logger.warning(f"Error extracting data for {MPN}: {e}")

        product = {
            'MPN': MPN,
            'Société': "CIPAC",
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

    # === Closing WebDriver ===
    finally:
        driver.quit()



# ====================
#        MAIN
# ====================
def CIPACwatcher():

    MPNs = EXCELreader("MPNs")

    CSVpath = "DATA/CIPACproducts.csv"
    XLSXpath = "DATA/CIPACproducts.xlsx"

    products = []
    for MPN in MPNs:
        data = extract_CIPAC_products_data(MPN)
        if data:
            products.append(data)
        time.sleep(random.uniform(1.5, 3))

    df = pd.DataFrame(products)
    df.to_csv(CSVpath, index=False, encoding='utf-8-sig')
    df.to_excel(XLSXpath, index=False)

    Logger.info("Processus CIPACwatcher terminé...")

    return df, XLSXpath