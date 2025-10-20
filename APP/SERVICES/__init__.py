# UTILS/__init__.py
import os
import sys



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

    DATABASE_FOLDER = os.path.join(BASE_TEMP_PATH, "APP", "DATABASE")

    USER_FOLDER = os.path.join(BASE_SYSTEM_PATH, "USER")
    CORE_SUBFOLDER = os.path.join(BASE_SYSTEM_PATH, "USER", "CORE")
    CONFIG_SUBFOLDER = os.path.join(BASE_SYSTEM_PATH, "USER", "CONFIG")
    LOGS_SUBFOLDER = os.path.join(BASE_SYSTEM_PATH, "USER", "LOGS")
    RESULTS_SUBFOLDER = os.path.join(BASE_SYSTEM_PATH, "USER", "RESULTS")
    RESULTS_SUBFOLDER_TEMP = os.path.join(RESULTS_SUBFOLDER, "TEMP")

    USER_CONFIG_PATH = os.path.join(CONFIG_SUBFOLDER, "settings.json")
    CATALOG_CONFIG_PATH = os.path.join(CONFIG_SUBFOLDER, "MPNs.json")

elif sys.platform.startswith("linux"):
    BASE_SYSTEM_PATH = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    BASE_TEMP_PATH = sys._MEIPASS if getattr(sys, 'frozen', False) else ""

    USER_FOLDER = os.path.join(BASE_SYSTEM_PATH, "USER")
    CONFIG_SUBFOLDER = os.path.join(BASE_SYSTEM_PATH, "USER", "CONFIG")
    CORE_SUBFOLDER = os.path.join(BASE_SYSTEM_PATH, "USER", "CORE")
    LOGS_SUBFOLDER = os.path.join(BASE_SYSTEM_PATH, "USER", "LOGS")
    RESULTS_SUBFOLDER = os.path.join(BASE_SYSTEM_PATH, "USER", "RESULTS")
    RESULTS_SUBFOLDER_TEMP = os.path.join(RESULTS_SUBFOLDER, "TEMP")
    
    USER_CONFIG_PATH = os.path.join(CONFIG_SUBFOLDER, "settings.json")
    CATALOG_CONFIG_PATH = os.path.join(CONFIG_SUBFOLDER, "MPNs.json")


    BASE_CHROMIUM_URL = "https://commondatastorage.googleapis.com/chromium-browser-snapshots/Linux_x64/"
    CHROMIUM_ZIP_NAME = "chrome-linux.zip"
    CHROMEDRIVER_ZIP_NAME = "chromedriver_linux64.zip"
    
    CHROME_PATH = os.path.join(CORE_SUBFOLDER, "chrome-linux", "chrome")
    CHROME_PROFILE_PATH = os.path.join(CORE_SUBFOLDER, "chrome_profile")
    CHROMEDRIVER_PATH = os.path.join(CORE_SUBFOLDER, "chromedriver_linux64", "chromedriver")
    
    PYTHON_EXE = sys.executable  

elif sys.platform.startswith("darwin"):
    BASE_SYSTEM_PATH = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    BASE_TEMP_PATH = sys._MEIPASS if getattr(sys, 'frozen', False) else ""

    BASE_CHROMIUM_URL = ""
    CHROMIUM_ZIP_NAME = ""
    CHROMEDRIVER_ZIP_NAME = ""

    CHROME_PATH = ""
    CHROME_PROFILE_PATH = ""
    CHROMEDRIVER_PATH = ""

    PYTHON_EXE = sys.executable

    DATABASE_FOLDER = os.path.join(BASE_TEMP_PATH, "APP", "DATABASE")

    USER_FOLDER = os.path.join(BASE_SYSTEM_PATH, "USER")
    CORE_SUBFOLDER = os.path.join(BASE_SYSTEM_PATH, "USER", "CORE")
    CONFIG_SUBFOLDER = os.path.join(BASE_SYSTEM_PATH, "USER", "CONFIG")
    LOGS_SUBFOLDER = os.path.join(BASE_SYSTEM_PATH, "USER", "LOGS")
    RESULTS_SUBFOLDER = os.path.join(BASE_SYSTEM_PATH, "USER", "RESULTS")
    RESULTS_SUBFOLDER_TEMP = os.path.join(RESULTS_SUBFOLDER, "TEMP")

    USER_CONFIG_PATH = os.path.join(CONFIG_SUBFOLDER, "settings.json")
    CATALOG_CONFIG_PATH = os.path.join(CONFIG_SUBFOLDER, "MPNs.json")

else:
    raise RuntimeError(f"Système non supporté: {sys.platform}")


# ===============
#   FUNCTION(S)
# ===============
def make_dirs():
    os.makedirs(USER_FOLDER, exist_ok=True)
    os.makedirs(CONFIG_SUBFOLDER, exist_ok=True)
    os.makedirs(CORE_SUBFOLDER, exist_ok=True)
    os.makedirs(LOGS_SUBFOLDER, exist_ok=True)
    os.makedirs(RESULTS_SUBFOLDER, exist_ok=True)
    os.makedirs(RESULTS_SUBFOLDER_TEMP, exist_ok=True)