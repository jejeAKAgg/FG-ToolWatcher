import random
import time

from seleniumbase import SB
from selenium.webdriver.chrome.options import Options

from APP.UTILS.LOGmaker import *



# ====================
#     LOGGER SETUP
# ====================
Logger = logger("CLABOTS")


# ====================
#      FUNCTIONS
# ====================
def WEBsearch(npm, shop):
    Logger = logger("WEBsearch")
    Logger.info("Démarrage de WEBsearch.py...")
    Logger.info(f"Recherche de NPM {npm} sur {shop}...")

    # Liste de proxies à utiliser (ajoute les tiens ici)
    proxies = [
        "138.128.92.102:8080",
        "45.77.68.240:8080",
        "165.22.81.6:3128",
        "103.216.82.137:6667",
    ]
    proxy = random.choice(proxies)
    Logger.info(f"Using proxy: {proxy}")

    # 🔍 Requête + langue FR
    query = f'site:{shop}+{npm}'
    url = f"https://www.google.com/search?q={query}&hl=fr"

    # 🧠 Fixe ou random UA (stabilité vs contournement)
    stable_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.139 Safari/537.36"
    user_agents = [
        stable_user_agent,
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.85 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.94 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0"
    ]
    user_agent = random.choice(user_agents)

    with SB(uc=True, headed=True, incognito=True) as sb:

        # Création des options Chrome avec proxy
        chrome_options = Options()
        chrome_options.add_argument(f'--proxy-server=http://{proxy}')
        # Optionnel : désactiver les notifications ou autres selon besoin
        chrome_options.add_argument("--disable-notifications")

        # 🧠 Configuration réseau + headers
        sb.driver.execute_cdp_cmd("Network.setUserAgentOverride", {"userAgent": user_agent})
        sb.driver.execute_cdp_cmd("Network.enable", {})
        sb.driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {
            "headers": {
                "Accept-Language": "fr-FR,fr;q=0.9",
                "User-Agent": user_agent,
                "Referer": "https://www.google.com/",
                "DNT": "1",
                "Upgrade-Insecure-Requests": "1"
            }
        })

        sb.set_window_size(400, 400)
        sb.open(url)

        # ⏱️ Comportement humain simulé
        sb.sleep(random.uniform(1.5, 3))
        sb.scroll_to_bottom()
        sb.sleep(random.uniform(0.5, 1.5))
        sb.scroll_to_top()

        # 🍪 Consentement Google
        try:
            sb.wait_for_element("#L2AGLb", timeout=5)
            sb.click("#L2AGLb")
            Logger.info("Consentement Google accepté (#L2AGLb).")
            sb.sleep(1.5)
        except Exception:
            Logger.info("Pas de bouton de consentement à cliquer.")

        # 🔍 Extraction des résultats
        try:
            sb.wait_for_element("div#search", timeout=15)
            links = sb.find_elements("div.yuRUbf a")

            for link in links:
                href = link.get_attribute("href")
                if shop in href:
                    Logger.info(f"[✅] Lien trouvé pour NPM {npm}: {href}")
                    time.sleep(3)
                    return href

            Logger.warning(f"[❌] Aucun lien trouvé pour NPM {npm}")
            return None

        except Exception as e:
            Logger.warning(f"[❌] Erreur lors de la récupération des résultats : {e}")

            return None