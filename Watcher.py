# Watcher.py
import os

from APP.SERVICES.__init__ import *

from APP.UTILS.LOGmaker import *

from APP.UTILS.EXCELutils import *
from APP.UTILS.TOOLSbox import *

from APP.WEBSITES.CIPACwatcher import CIPACwatcher
from APP.WEBSITES.CLABOTSwatcher import CLABOTSwatcher
from APP.WEBSITES.FGwatcher import FGwatcher
from APP.WEBSITES.FIXAMIwatcher import FIXAMIwatcher
from APP.WEBSITES.KLIUMwatcher import KLIUMwatcher
from APP.WEBSITES.LECOTwatcher import LECOTwatcher


# ====================
#     LOGGER SETUP
# ====================
Logger = logger("WATCHER")


# ====================
#    MAIN FUNCTION
# ====================
def main_watcher(progress_callback=None):

    Logger.info("Démarrage de Watcher...")

    steps = 8
    current = 0

    def update_progress():
        nonlocal current
        current += 1
        if progress_callback:
            progress_callback(int(current / steps * 100))


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