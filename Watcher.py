import json
import sys
import threading

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QMessageBox
from PySide6.QtCore import Qt

from UTILS.LOGmaker import logger

from WEBSITES.CIPACwatcher import CIPACwatcher
from WEBSITES.CLABOTSwatcher import CLABOTSwatcher
from WEBSITES.FIXAMIwatcher import FIXAMIwatcher
from WEBSITES.KLIUMwatcher import KLIUMwatcher

from UTILS.EXCELsender import EXCELsender
from UTILS.CSVmerger import FINALdf
from UTILS.MAILsender import MAILsender
from UTILS.NAMEformatter import *


# ====================
#    VARIABLE SETUP
# ====================
if sys.platform.startswith("win"):
    BASE_PATH = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    CHROME_PATH = os.path.join(BASE_PATH, "CORE", "chrome-win", "chrome.exe")
    CHROMEDRIVER_PATH = os.path.join(BASE_PATH, "CORE", "chromedriver_win32", "chromedriver.exe")
    DATA_FOLDER = os.path.join(BASE_PATH, "DATA")

    os.makedirs(DATA_FOLDER, exist_ok=True)


# ====================
#    CHROMIUM SETUP
# ====================
Logger = logger("WATCHER")
Logger.info("Démarrage de Watcher.py...")

Logger.info("Démarrage de CIPACwatcher.py...")
CIPACdf = CIPACwatcher()

Logger.info("Démarrage de CLABOTSwatcher.py...")
CLABOTSdf = CLABOTSwatcher()

Logger.info("Démarrage de FIXAMIwatcher.py...")
FIXAMIdf = FIXAMIwatcher()

Logger.info("Démarrage de KLIUMwatcher.py...")
KLIUMdf = KLIUMwatcher()

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
    password=mail_config["Password"],
    recipient_email=mail_config["Target"],
    subject=mail_config["Subject"],
    body=body,
    filename=FINALxlsx
)

Logger.info("Shutting down...")
sys.exit()