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