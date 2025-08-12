import os
import sys

import psutil
import platform
import signal

import json
import smtplib

from email.message import EmailMessage

from UTILS.LOGmaker import *



# ====================
#     LOGGER SETUP
# ====================
Logger = logger("TOOLSbox")


# ====================
#    VARIABLE SETUP
# ====================
if sys.platform.startswith("win"):
    BASE_SYSTEM_PATH = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    BASE_TEMP_PATH = sys._MEIPASS if getattr(sys, 'frozen', False) else ""
    CHROME_PATH = os.path.join(BASE_SYSTEM_PATH, "CORE", "chrome-win", "chrome.exe")
    CHROMEDRIVER_PATH = os.path.join(BASE_SYSTEM_PATH, "CORE", "chromedriver_win32", "chromedriver.exe")
    PYTHON_EXE = os.path.join(BASE_SYSTEM_PATH, "CORE", "python", "python.exe") if getattr(sys, 'frozen', False) else sys.executable
    
    CORE_FOLDER = os.path.join(BASE_SYSTEM_PATH, "CORE")
    DATA_FOLDER = os.path.join(BASE_SYSTEM_PATH, "DATA")
    LOGS_FOLDER = os.path.join(BASE_SYSTEM_PATH, "LOGS")

if sys.platform.startswith("linux"):
    BASE_SYSTEM_PATH = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    BASE_TEMP_PATH = sys._MEIPASS if getattr(sys, 'frozen', False) else ""
    CHROME_PATH = os.path.join(BASE_SYSTEM_PATH, "CORE", "chrome-win", "chrome.exe")
    CHROMEDRIVER_PATH = os.path.join(BASE_SYSTEM_PATH, "CORE", "chromedriver_win32", "chromedriver.exe")
    
    CORE_FOLDER = os.path.join(BASE_SYSTEM_PATH, "CORE")
    DATA_FOLDER = os.path.join(BASE_SYSTEM_PATH, "DATA")
    LOGS_FOLDER = os.path.join(BASE_SYSTEM_PATH, "LOGS")


# ====================
#      FUNCTIONS
# ====================
def JSONloader(path):
    with open(path, 'r', encoding='utf-8') as file:
        cfg = json.load(file)
    return cfg

def kill_chromium_processes():
    targets = ["chromedriver", "chrome", "chromium"]
    system_os = platform.system().lower()

    for proc in psutil.process_iter(['pid', 'name']):
        try:
            pname = proc.info['name']
            if pname and any(t in pname.lower() for t in targets):
                if system_os == "windows":
                    proc.terminate()  # plus sûr que kill sur Windows
                else:
                    proc.send_signal(signal.SIGTERM)  # SIGTERM par défaut
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass


def MAILsender(sender_email, password, recipient_email, subject, body, filename):

    attachment_name = os.path.basename(filename)

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = "FG-ToolWatcher <fgtoolwatcher@gmail.com>"
    msg['To'] = recipient_email
    msg.set_content(body, subtype='html')

    with open(filename, 'rb') as f:
        file_data = f.read()
        msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=attachment_name)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, password)
            smtp.send_message(msg)
        Logger.info("Mail envoyé avec succès.")
    except Exception as e:
        Logger.warning(f"Erreur lors de l’envoi du mail: {e}")