# UTILS/__init__.py
import os
import sys
import json

from APP.UTILS.LOGmaker import *

# ====================
#     LOGGER SETUP
# ====================
Logger = logger("FOLDERSinitializer")


# ====================
#    VARIABLE SETUP
# ====================
if sys.platform.startswith("win"):
    BASE_SYSTEM_PATH = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    BASE_TEMP_PATH = sys._MEIPASS if getattr(sys, 'frozen', False) else ""

    BASE_CHROMIUM_URL = "https://commondatastorage.googleapis.com/chromium-browser-snapshots/Win_x64/"
    CHROMIUM_ZIP_NAME = "chrome-win.zip"
    CHROMEDRIVER_ZIP_NAME = "chromedriver_win32.zip"
    
    CHROME_PATH = os.path.join(BASE_SYSTEM_PATH, "CORE", "chrome-win", "chrome.exe")
    CHROME_PROFILE_PATH = os.path.join(BASE_SYSTEM_PATH, "CORE", "chrome_profile")
    CHROMEDRIVER_PATH = os.path.join(BASE_SYSTEM_PATH, "CORE", "chromedriver_win32", "chromedriver.exe")

    PYTHON_VERSION = "3.13.6"
    PYTHON_ZIP_NAME = f"python-{PYTHON_VERSION}-embed-amd64.zip"
    PYTHON_ZIP_PATH = os.path.join(BASE_SYSTEM_PATH, "CORE", PYTHON_ZIP_NAME)
    BASE_PYTHON_URL = f"https://www.python.org/ftp/python/{PYTHON_VERSION}/{PYTHON_ZIP_NAME}"
    PYTHON_EXE = os.path.join(BASE_SYSTEM_PATH, "CORE", "python", "python.exe") if getattr(sys, 'frozen', False) else sys.executable

    CORE_FOLDER = os.path.join(BASE_SYSTEM_PATH, "CORE")
    DATA_FOLDER = os.path.join(BASE_SYSTEM_PATH, "DATA")
    LOGS_SUBFOLDER = os.path.join(BASE_SYSTEM_PATH, "DATA", "LOGS")
    RESULTS_SUBFOLDER = os.path.join(BASE_SYSTEM_PATH, "DATA", "RESULTS")
    RESULTS_SUBFOLDER_TEMP = os.path.join(RESULTS_SUBFOLDER, "TEMP")
    USER_SUBFOLDER = os.path.join(BASE_SYSTEM_PATH, "DATA", "USER")

    USER_CONFIG_PATH = os.path.join(USER_SUBFOLDER, "settings.json")

elif sys.platform.startswith("linux"):
    BASE_SYSTEM_PATH = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    BASE_TEMP_PATH = sys._MEIPASS if getattr(sys, 'frozen', False) else ""

    BASE_CHROMIUM_URL = "https://commondatastorage.googleapis.com/chromium-browser-snapshots/Linux_x64/"
    CHROMIUM_ZIP_NAME = "chrome-linux.zip"
    CHROMEDRIVER_ZIP_NAME = "chromedriver_linux64.zip"
    
    CHROME_PATH = os.path.join(BASE_SYSTEM_PATH, "CORE", "chrome-win", "chrome.exe")
    CHROME_PROFILE_PATH = os.path.join(BASE_SYSTEM_PATH, "CORE", "chrome_profile")
    CHROMEDRIVER_PATH = os.path.join(BASE_SYSTEM_PATH, "CORE", "chromedriver_win32", "chromedriver.exe")
    
    PYTHON_EXE = sys.executable
    
    CORE_FOLDER = os.path.join(BASE_SYSTEM_PATH, "CORE")
    DATA_FOLDER = os.path.join(BASE_SYSTEM_PATH, "DATA")
    LOGS_SUBFOLDER = os.path.join(BASE_SYSTEM_PATH, "DATA", "LOGS")
    RESULTS_SUBFOLDER = os.path.join(BASE_SYSTEM_PATH, "DATA", "RESULTS")
    RESULTS_SUBFOLDER_TEMP = os.path.join(RESULTS_SUBFOLDER, "TEMP")
    USER_SUBFOLDER = os.path.join(BASE_SYSTEM_PATH, "DATA", "USER")

    USER_CONFIG_PATH = os.path.join(USER_SUBFOLDER, "settings.json")

else:
    raise RuntimeError(f"Système non supporté: {sys.platform}")


# ===============
#   FUNCTION(S)
# ===============
def make_dirs():
    os.makedirs(CORE_FOLDER, exist_ok=True)
    os.makedirs(DATA_FOLDER, exist_ok=True)
    os.makedirs(LOGS_SUBFOLDER, exist_ok=True)
    os.makedirs(RESULTS_SUBFOLDER, exist_ok=True)
    os.makedirs(RESULTS_SUBFOLDER_TEMP, exist_ok=True)
    os.makedirs(USER_SUBFOLDER, exist_ok=True)

def make_user_config():
    DEFAULT_SETTINGS = {
        "language": "FR",
        "send_email": False,
        "email_list": []
    }

    folder = os.path.dirname(USER_CONFIG_PATH)
    if folder:
        os.makedirs(folder, exist_ok=True)

    # Si le fichier existe déjà → on charge et on complète
    if os.path.exists(USER_CONFIG_PATH):
        with open(USER_CONFIG_PATH, "r", encoding="utf-8") as f:
            try:
                user_settings = json.load(f)
            except json.JSONDecodeError:
                user_settings = {}
    else:
        user_settings = {}

    # Fusion : priorité aux valeurs déjà présentes, mais ajout des nouvelles clés par défaut
    updated_settings = {**DEFAULT_SETTINGS, **user_settings}

    # Si les deux dicts sont différents → écraser avec les paramètres à jour
    if updated_settings != user_settings:
        with open(USER_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(updated_settings, f, indent=4)