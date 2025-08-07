import json

from UTILS.LOGmaker import logger

from WEBSITES.CIPACwatcher import CIPACwatcher
from WEBSITES.CLABOTSwatcher import CLABOTSwatcher
from WEBSITES.FIXAMIwatcher import FIXAMIwatcher
from WEBSITES.KLIUMwatcher import KLIUMwatcher

from UTILS.EXCELsender import EXCELsender
from UTILS.CSVmerger import FINALdf
from UTILS.MAILsender import MAILsender
from UTILS.NAMEformatter import *

from Chromium import download_chromium_and_driver


# ====================
#    VARIABLE SETUP
# ====================
if sys.platform.startswith("win"):
    BASE_PATH = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    CHROME_PATH = os.path.join(BASE_PATH, "CORE", "chrome-win", "chrome.exe")
    CHROMEDRIVER_PATH = os.path.join(BASE_PATH, "CORE", "chromedriver_win32", "chromedriver.exe")
    DATA_FOLDER = os.path.join(BASE_PATH, "DATA")

    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)
    else:
        print("ok")


# ====================
#    CHROMIUM SETUP
# ====================
download_chromium_and_driver()

Logger = logger("WATCHER")
Logger.info("Démarrage de Watcher.py...")

Logger.info("Démarrage de CIPACwatcher.py...")
CIPACdf, CIPACxlsx = CIPACwatcher()

Logger.info("Démarrage de CLABOTSwatcher.py...")
CLABOTSdf, CLABOTSxlsx = CLABOTSwatcher()

Logger.info("Démarrage de FIXAMIwatcher.py...")
FIXAMIdf, FIXAMIxlsx = FIXAMIwatcher()

Logger.info("Démarrage de KLIUMwatcher.py...")
KLIUMdf, KLIUMxlsx = KLIUMwatcher()

Logger.info("Démarrage de CSVmerger.py...")
FINALcsv, FINALxlsx = FINALdf([CIPACdf, CLABOTSdf, FIXAMIdf, KLIUMdf])

Logger.info("Sending results...")
EXCELsender(FINALcsv)

Logger.info("Sending report...")
with open(resource_path("CONFIGS/EMAILconfig.json"), "r", encoding="utf-8") as f:
    mail_config = json.load(f)
body = "\n".join(mail_config["BodyLines"])

MAILsender(
    sender_email=mail_config["Source"],
    password=mail_config["password"],
    recipient_email=mail_config["Target"],
    subject=mail_config["Subject"],
    body=mail_config["Body"],
    filename=FINALxlsx
)

Logger.info("Shutting down...")
exit()