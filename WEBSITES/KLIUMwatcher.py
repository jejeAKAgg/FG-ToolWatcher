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
Logger = logger("KLIUM")


# ====================
#      FUNCTIONS
# ====================
def extract_KLIUM_products_data(MPN):
    
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


    # === Initializing WebDriver & running search ===
    driver = webdriver.Chrome(options=options)
    try:
        REQUESTurl=f"https://www.klium.be/fr/recherche?s={MPN}"
        driver.get(REQUESTurl)
        
        time.sleep(5)  # Loading time (JS)

        accept_cookies(driver, "Klium")

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
                    Logger.warning(f"No links found for this REF-{MPN}")
                    Logger.warning(f"Searching with Google")
                    ARTICLEurl = WEBsearch(MPN, "klium.be")
            else:
                Logger.warning(f"No links found for this REF-{MPN}")
                product = {
                    'MPN': "REF-" + MPN,
                    'Société': "KLIUM",
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

            accept_cookies(driver, "Klium")

            ARTICLEpage = driver.page_source
            ARTICLEurl = driver.current_url
                 
        soup = BeautifulSoup(ARTICLEpage, "html.parser")

        if (extract_klium_ref(soup) is not None and extract_klium_ref(soup) != MPN):
            Logger.warning(f"False positive detected for REF-{MPN}: got REF-{extract_klium_ref(soup)}! Skipping...")
            product = {
                'MPN': "REF-" + MPN,
                'Société': "KLIUM",
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
        product['Société'] = 'KLIUM'
        product['Article'] = (
            (name := soup.find("h1", id="product_name_value"))
            and f'=HYPERLINK("{ARTICLEurl}"; "{standardize_name(name.get_text(strip=True).replace("\"", "\"\""), html=ARTICLEpage)}")'
        )
        product['Marque'] = (
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

        product['Prix (HTVA)'] = format_price_for_excel(HTVA)
        product['Prix (TVA)'] = format_price_for_excel(TVA)
        product['Ancien Prix (HTVA)'] = "TODO"
        product['Evolution du prix'] = "TODO"
        product['Offres'] = extract_offers_KLIUM(soup)
        product['Stock'] = bool(soup.select_one("#product-availability .availability-label.in-stock"))
        product['Checked on'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return product


    except Exception as e:
        print(f"Error extracting data for {MPN}: {e}")
        product = {
            'MPN': MPN,
            'Société': "KLIUM",
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
def KLIUMwatcher():

    MPNs = EXCELreader("MPNs")

    CSVpath = "DATA/KLIUMproducts.csv"
    XLSXpath = "DATA/KLIUMproducts.xlsx"

    products = []
    for MPN in MPNs:
        data = extract_KLIUM_products_data(MPN)
        if data:
            products.append(data)
        time.sleep(random.uniform(1.5, 3))

    df = pd.DataFrame(products)
    df.to_csv(CSVpath, index=False, encoding='utf-8-sig')
    df.to_excel(XLSXpath, index=False)

    Logger.info("Processus KLIUMwatcher terminé...")

    return df, XLSXpath