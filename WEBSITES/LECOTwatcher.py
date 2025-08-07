import requests
import time
import random
import pandas as pd

from datetime import datetime

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from UTILS.LOGmaker import logger
from UTILS.NAMEformatter import *

from UTILS.EXCELreader import EXCELreader
from UTILS.WEBsearch import WEBsearch


# ====================
#     LOGGER SETUP
# ====================
Logger = logger("LECOT")


# ====================
#      FUNCTIONS
# ====================
def extract_LECOT_products_data(MPN):

    # === Selenium OPTIONS ===
    options = Options()
    
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=400,400")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    )
    
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    # === HEADERS & PARAMS ===
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0",
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate",
        "Referer": "https://shop.lecot.be/"
    }
    params = {
        "type": "suggest",
        "searchQuery": MPN,
        "filterInitiated": "false",
        "filtersShowAll": "false",
        "enableFiltersShowAll": "false",
        "securedFiltersHash": "false",
        "sortBy": "0",
        "offset": "0",
        "limit": "15",
        "requestIndex": "3",
        "locale": "nl_NL",
        "url": "/fr-be/",
        "index": "collection:20522",
        "view": "dc81f66a42b2a145",
        "account": "SQ-120522-1"
    }

    # === Initializing WebDriver & running search ===
    driver = webdriver.Chrome(options=options)
    try:
        REQUESTurl = f"https://shop.lecot.be/fr-be/#sqr:(q[{MPN}])"
        driver.get(REQUESTurl)
        
        time.sleep(5)  # Loading time (JS)

        ARTICLEpage =  driver.page_source
        ARTICLEurl = driver.current_url

        # Si on est resté sur la page de recherche (pas redirigé)
        if "#sqr:" in ARTICLEurl:
            ARTICLEurl = WEBsearch(MPN, "shop.lecot.be")

            if ARTICLEurl is None:
                product = {
                    'MPN': "REF-" + MPN,
                    'Société': "LECOT",
                    'Article': "Produit indisponible",
                    'Marque': "Marque indisponible",
                    'Changement de prix?': "-",
                    'Prix (HTVA)': "-",
                    'Prix (TVA)': "-",
                    'Ancien Prix (HTVA)': "-",
                    'Offres?': "-",
                    'Stock?': "-",
                    'Checked on': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                return product
            
            else:
                driver.quit()
                driver = webdriver.Chrome(options=options)
                
                driver.get(ARTICLEurl)
                
                time.sleep(5)
                
                ARTICLEpage = driver.page_source

        soup = BeautifulSoup(ARTICLEpage, "html.parser")
        product = {}

        # Function using CSS selectors to find the relevant meta tags and product details (name of product, Manufacturer Part Number, price, currency, availability, ...)
        def get_meta_content(selector):
            tag = soup.select_one(selector)
            return tag['content'] if tag and 'content' in tag.attrs else None

        # Structuring my dictionnary with the needed product datas
        product['MPN'] = "REF-" + MPN
        product['Société'] = "LECOT"
        product['Article'] = f'=HYPERLINK("{ARTICLEurl}"; "{soup.select_one("h1.product-detail-name").text.strip().replace("\"", "\"\"")}")' if soup.select_one("h1.product-detail-name") else None
        product['Marque'] = get_meta_content('[itemprop="brand"] meta[itemprop="name"]').upper() if get_meta_content('[itemprop="brand"] meta[itemprop="name"]') else None
        product['Changement de prix?'] = "TODO"
        product['Prix (HTVA)'] = float(re.search(r'[\d,.]+', soup.select_one('div.product-price-vat.product-price-info').text.replace('\xa0', '').replace('€', '').strip()).group(0).replace(',', '.')) if soup.select_one('div.product-price-vat.product-price-info') else None
        product['Prix (TVA)'] = float(get_meta_content('meta[itemprop="price"]'))
        product['Ancien Prix (HTVA)'] = "TODO"
        product['Offres?'] = "TODO"
        product['Stock?'] = bool(soup.select_one('[itemprop="availability"]') and 'OutOfStock' not in soup.select_one('[itemprop="availability"]').get('href', ''))
        product['Checked on'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Returning the final product dictionary
        return product
    

    except Exception as e:
        print(f"Error extracting data for {MPN}: {e}")
        product = {
            'MPN': MPN,
            'Société': "CLABOTS",
            'Article': "Erreur lors de l'extraction",
            'Marque': "Marque indisponible",
            'Changement de prix?': "-",
            'Prix (HTVA)': "-",
            'Prix (TVA)': "-",
            'Ancien Prix (HTVA)': "-",
            'Offres?': "-",
            'Stock?': "-",
            'Checked on': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
    finally:
        driver.quit()


##### MAIN EXECUTION #####
def LECOTwatcher():
    
    MPNs = EXCELreader("MPNs")

    CSVpath = "DATA/LECOTproducts.csv"
    XLSXpath = "DATA/LECOTproducts.xlsx"

    products = []
    for MPN in MPNs:
        data = extract_LECOT_products_data(MPN)
        if data:
            products.append(data)
        time.sleep(random.uniform(1.5, 3)) # Setting a random delay between requests to avoid being blocked by server

    df = pd.DataFrame(products)
    df.to_csv(CSVpath, index=False, encoding='utf-8-sig')
    df.to_excel(XLSXpath, index=False)


    return df, XLSXpath