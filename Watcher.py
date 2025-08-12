import os
import sys

from UTILS.EXCELutils import *
from UTILS.LOGmaker import *
from UTILS.PRODUCTformatter import *
from UTILS.TOOLSbox import *
from UTILS.TOOLSinstaller import *

from WEBSITES.CIPACwatcher import CIPACwatcher
from WEBSITES.CLABOTSwatcher import CLABOTSwatcher
from WEBSITES.FGwatcher import FGwatcher
from WEBSITES.FIXAMIwatcher import FIXAMIwatcher
from WEBSITES.KLIUMwatcher import KLIUMwatcher
from WEBSITES.LECOTwatcher import LECOTwatcher


# ====================
#    VARIABLE SETUP
# ====================
if sys.platform.startswith("win"):
    BASE_SYSTEM_PATH = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(os.path.join(os.path.dirname(__file__)))
    BASE_TEMP_PATH = sys._MEIPASS if getattr(sys, 'frozen', False) else ""

    CORE_FOLDER = os.path.join(BASE_SYSTEM_PATH, "CORE")
    DATA_FOLDER = os.path.join(BASE_SYSTEM_PATH, "DATA")
    LOGS_FOLDER = os.path.join(BASE_SYSTEM_PATH, "LOGS")

    os.makedirs(CORE_FOLDER, exist_ok=True)
    os.makedirs(DATA_FOLDER, exist_ok=True)
    os.makedirs(LOGS_FOLDER, exist_ok=True)

if sys.platform.startswith("linux"):
    BASE_SYSTEM_PATH = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(os.path.join(os.path.dirname(__file__)))
    BASE_TEMP_PATH = sys._MEIPASS if getattr(sys, 'frozen', False) else ""

    CORE_FOLDER = os.path.join(BASE_SYSTEM_PATH, "CORE")
    DATA_FOLDER = os.path.join(BASE_SYSTEM_PATH, "DATA")
    LOGS_FOLDER = os.path.join(BASE_SYSTEM_PATH, "LOGS")

    os.makedirs(CORE_FOLDER, exist_ok=True)
    os.makedirs(DATA_FOLDER, exist_ok=True)
    os.makedirs(LOGS_FOLDER, exist_ok=True)
    

# ====================
#     LOGGER SETUP
# ====================
Logger = logger("WATCHER")


# ====================
#        MAIN
# ====================
def main_watcher():
    Logger.info("Démarrage de Watcher...")


    # === TOOLS SETUP ===
    Logger.info("Vérification de Chromium...")
    getCHROMIUMpackage()

    Logger.info("Vérification de Python...")
    getPYTHONpackage()

    Logger.info("Vérification de pip/ensurepip")
    getPIPpackage()

    Logger.info("Vérification des packages requis...")
    getREQUIREMENTSpackage()


    # === WATCHER MAIN ===
    Logger.info("Démarrage de CIPACwatcher...")
    CIPACdf = CIPACwatcher()

    Logger.info("Démarrage de CLABOTSwatcher...")
    CLABOTSdf = CLABOTSwatcher()

    Logger.info("Démarrage de FGwatcher...")
    FGdf = FGwatcher()

    Logger.info("Démarrage de FIXAMIwatcher...")
    FIXAMIdf = FIXAMIwatcher()

    Logger.info("Démarrage de KLIUMwatcher...")
    KLIUMdf = KLIUMwatcher()

    Logger.info("Démarrage de LECOTwatcher...")
    LECOTdf = LECOTwatcher()

    Logger.info("Démarrage de CSVmerger...")
    FINALxlsx = FINALdf([CIPACdf, CLABOTSdf, FGdf, FIXAMIdf, KLIUMdf, LECOTdf])

    Logger.info("Envoi des résultats pour la version WEB...")
    EXCELsender(FINALxlsx)

    Logger.info("Envoi des résultats pour la version MAIL...")
    MAILconfig = JSONloader(os.path.join(BASE_TEMP_PATH, "CONFIGS", "EMAILconfig.json"))
    body = "\n".join(MAILconfig["BodyLines"])

    MAILsender(
        sender_email=MAILconfig["Source"],
        password=MAILconfig["Password"],
        recipient_email=MAILconfig["Target"],
        subject=MAILconfig["Subject"],
        body=body,
        filename=FINALxlsx
    )

    Logger.info("Analyse terminée.")