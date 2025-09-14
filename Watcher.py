# FICHIER: Watcher.py
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
BASE_SYSTEM_PATH = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(os.path.join(os.path.dirname(__file__)))
BASE_TEMP_PATH = getattr(sys, '_MEIPASS', "")

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
#    MAIN FUNCTION
# ====================
def main_watcher(progress_callback=None):

    Logger.info("Démarrage de Watcher...")

    steps = 12
    current = 0

    def update_progress():
        nonlocal current
        current += 1
        if progress_callback:
            progress_callback(int(current / steps * 100))

    # === TOOLS SETUP ===
    Logger.info("Vérification de Chromium...")
    getCHROMIUMpackage()
    update_progress()

    Logger.info("Vérification de Python...")
    getPYTHONpackage()
    update_progress()

    Logger.info("Vérification de pip/ensurepip")
    getPIPpackage()
    update_progress()

    Logger.info("Vérification des packages requis...")
    getREQUIREMENTSpackage()
    update_progress()

    # === WATCHER MAIN ===
    Logger.info("Réception des données [REFs/Articles] et synchronisation...")
    ITEMs = EXCELreader("MPNs/Articles")
    update_progress()

    Logger.info("Démarrage de CIPACwatcher...")
    CIPACdf = CIPACwatcher(ITEMs)
    update_progress()

    Logger.info("Démarrage de CLABOTSwatcher...")
    CLABOTSdf = CLABOTSwatcher(ITEMs)
    update_progress()

    Logger.info("Démarrage de FGwatcher...")
    FGdf = FGwatcher(ITEMs)
    update_progress()

    Logger.info("Génération du CSV...")
    FINALcsv = FINALcsvCONVERTER([CIPACdf, CLABOTSdf, FGdf])
    update_progress()

    Logger.info("Génération du XLSX...")
    FINALxlsx = FINALxlsxCONVERTER([CIPACdf, CLABOTSdf, FGdf])
    update_progress()

    Logger.info("Envoi des résultats pour la version WEB...")
    EXCELsender(FINALcsv)
    update_progress()

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
    update_progress()

    Logger.info("Analyse terminée.")


# ====================
#      EXECUTION DIRECTE
# ====================
if __name__ == "__main__":
    main_watcher()