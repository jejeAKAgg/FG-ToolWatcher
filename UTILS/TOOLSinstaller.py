import os
import shutil
import sys
import subprocess

import tempfile
import urllib.request
import zipfile

from UTILS.LOGmaker import *


# ====================
#     LOGGER SETUP
# ====================
Logger = logger("TOOLinstaller")


# ====================
#    VARIABLE SETUP
# ====================
BASE_SYSTEM_PATH = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BASE_TEMP_PATH = sys._MEIPASS if getattr(sys, 'frozen', False) else ""

CORE_FOLDER = os.path.join(BASE_SYSTEM_PATH, "CORE")
DATA_FOLDER = os.path.join(BASE_SYSTEM_PATH, "DATA")
LOGS_FOLDER = os.path.join(BASE_SYSTEM_PATH, "LOGS")

os.makedirs(CORE_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(LOGS_FOLDER, exist_ok=True)

if sys.platform.startswith("win"):
    CHROME_PATH = os.path.join(BASE_SYSTEM_PATH, "CORE", "chrome-win", "chrome.exe")
    CHROMEDRIVER_PATH = os.path.join(BASE_SYSTEM_PATH, "CORE", "chromedriver_win32", "chromedriver.exe")
    PYTHON_EXE = os.path.join(BASE_SYSTEM_PATH, "CORE", "python", "python.exe")

    BASE_CHROMIUM_URL = "https://commondatastorage.googleapis.com/chromium-browser-snapshots/Win_x64/"
    CHROMIUM_ZIP_NAME = "chrome-win.zip"
    CHROMEDRIVER_ZIP_NAME = "chromedriver_win32.zip"

if sys.platform.startswith("linux"):
    CHROME_PATH = os.path.join(BASE_SYSTEM_PATH, "CORE", "chrome-win", "chrome.exe")
    CHROMEDRIVER_PATH = os.path.join(BASE_SYSTEM_PATH, "CORE", "chromedriver_win32", "chromedriver.exe")
    PYTHON_EXE = shutil.which("python3") or "/usr/bin/python3"

    BASE_CHROMIUM_URL = "https://commondatastorage.googleapis.com/chromium-browser-snapshots/Linux_x64/"
    CHROMIUM_ZIP_NAME = "chrome-linux.zip"
    CHROMEDRIVER_ZIP_NAME = "chromedriver_linux64.zip"

elif sys.platform.startswith("darwin"):
    machine = sys.platform.machine().lower()
    PYTHON_EXE = shutil.which("python3") or "/usr/bin/python3"

    if machine in ["arm64", "aarch64"]:
        BASE_CHROMIUM_URL = "https://commondatastorage.googleapis.com/chromium-browser-snapshots/Mac_Arm/"
        CHROMIUM_ZIP_NAME = "chrome-mac.zip"
        CHROMEDRIVER_ZIP_NAME = "chromedriver_mac64.zip"
        CHROME_PATH = os.path.join(CORE_FOLDER, "chrome-mac", "Chromium.app", "Contents", "MacOS", "Chromium")
        CHROMEDRIVER_PATH = os.path.join(CORE_FOLDER, "chromedriver_mac64", "chromedriver")

    else:  # Mac Intel
        BASE_CHROMIUM_URL = "https://commondatastorage.googleapis.com/chromium-browser-snapshots/Mac/"
        CHROMIUM_ZIP_NAME = "chrome-mac.zip"
        CHROMEDRIVER_ZIP_NAME = "chromedriver_mac64.zip"
        CHROME_PATH = os.path.join(CORE_FOLDER, "chrome-mac", "Chromium.app", "Contents", "MacOS", "Chromium")
        CHROMEDRIVER_PATH = os.path.join(CORE_FOLDER, "chromedriver_mac64", "chromedriver")

else:
    raise RuntimeError(f"Système non supporté: {sys.platform}")


# ========================
#    CHROMIUM INSTALLER
# ========================
def get_latest_build_number():
    last_change_url = BASE_CHROMIUM_URL + "LAST_CHANGE"
    Logger.info(f"Récupération du dernier build Chromium via {last_change_url}...")
    try:
        with urllib.request.urlopen(last_change_url) as response:
            build_number = response.read().decode('utf-8').strip()
            Logger.info(f"Dernier build disponible : {build_number}")
            return build_number
    except Exception as e:
        Logger.error(f"Erreur lors de la récupération du build number : {e}")
        raise

def download_and_extract(url, dest_zip_path, extract_to):
    Logger.info(f"Vérification du fichier {dest_zip_path}...")
    if not os.path.exists(dest_zip_path):
        Logger.info(f"Téléchargement depuis {url} vers {dest_zip_path}...")
        try:
            urllib.request.urlretrieve(url, dest_zip_path)
            Logger.info(f"Téléchargement terminé : {dest_zip_path}")
        except Exception as e:
            Logger.error(f"Erreur lors du téléchargement : {e}")
            raise
        
        Logger.info(f"Extraction de {dest_zip_path} vers {extract_to}...")
        try:
            with zipfile.ZipFile(dest_zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
            Logger.info("Extraction terminée.")
        except Exception as e:
            Logger.error(f"Erreur lors de l'extraction : {e}")
            raise
    else:
        Logger.info(f"Fichier {dest_zip_path} déjà présent, saut du téléchargement.")

def getCHROMIUMpackage():
    Logger.info("Début de la récupération du package Chromium...")
    build_number = get_latest_build_number()

    # Chromium
    chromium_zip_path = os.path.join(CORE_FOLDER, CHROMIUM_ZIP_NAME)
    chromium_url = f"{BASE_CHROMIUM_URL}{build_number}/{CHROMIUM_ZIP_NAME}"
    download_and_extract(chromium_url, chromium_zip_path, CORE_FOLDER)

    # Chromedriver
    chromedriver_zip_path = os.path.join(CORE_FOLDER, CHROMEDRIVER_ZIP_NAME)
    chromedriver_url = f"{BASE_CHROMIUM_URL}{build_number}/{CHROMEDRIVER_ZIP_NAME}"
    download_and_extract(chromedriver_url, chromedriver_zip_path, CORE_FOLDER)
    
    Logger.info("Package Chromium et Chromedriver récupérés avec succès.")

# ========================
#     PYTHON INSTALLER
# ========================
PYTHON_VERSION = "3.13.6"
PYTHON_ZIP_NAME = f"python-{PYTHON_VERSION}-embed-amd64.zip"
PYTHON_ZIP_PATH = os.path.join(BASE_SYSTEM_PATH, "CORE", PYTHON_ZIP_NAME)
BASE_PYTHON_URL = f"https://www.python.org/ftp/python/{PYTHON_VERSION}/{PYTHON_ZIP_NAME}"

if sys.platform == "win32":
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
else:
    startupinfo = None

def getPYTHONpackage():
    if sys.platform.startswith("linux"):
        Logger.info("Sur Linux, utilisation du Python système. Étape ignorée.")
        return

    os.makedirs(os.path.join(CORE_FOLDER, "python"), exist_ok=True)

    if not os.path.exists(PYTHON_ZIP_PATH):
        Logger.info(f"Téléchargement de Python {PYTHON_VERSION}...")
        urllib.request.urlretrieve(BASE_PYTHON_URL, PYTHON_ZIP_PATH)
        Logger.info("Téléchargement terminé.")

    if not os.path.exists(PYTHON_EXE):
        Logger.info("Extraction de Python...")
        with zipfile.ZipFile(PYTHON_ZIP_PATH, 'r') as zip_ref:
            zip_ref.extractall(os.path.join(CORE_FOLDER, "python"))
        Logger.info("Extraction terminée.")

        # --- Modifier le fichier ._pth pour activer import site ---
        pth_filename = f"python{PYTHON_VERSION.replace('.', '')[:3]}._pth"  # ex: python312._pth
        pth_path = os.path.join(os.path.join(CORE_FOLDER, "python"), pth_filename)
        if os.path.exists(pth_path):
            with open(pth_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            new_lines = []
            found = False
            for line in lines:
                if line.strip() == "#import site":
                    new_lines.append("import site\n")
                    found = True
                else:
                    new_lines.append(line)
            
            if found:
                with open(pth_path, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                Logger.info(f"Modification de {pth_filename} : ligne 'import site' activée.")
            else:
                Logger.info(f"Ligne '#import site' non trouvée dans {pth_filename}, aucune modification faite.")
        else:
            Logger.warning(f"Fichier {pth_filename} non trouvé, impossible de modifier pour activer 'import site'.")

def getPIPpackage():
    try:
        subprocess.run(
            [PYTHON_EXE, "-m", "pip", "--version"],
            capture_output=True,
            text=True,
            startupinfo=startupinfo,
            check=True
        )
        Logger.info("pip est déjà installé.")
        return
    except subprocess.CalledProcessError:
        Logger.warning("pip non trouvé.")

    Logger.info("Tentative d'installation via ensurepip...")
    try:
        subprocess.run(
            [PYTHON_EXE, "-m", "ensurepip", "--default-pip"],
            capture_output=True,
            text=True,
            startupinfo=startupinfo,
            check=True
        )
    except subprocess.CalledProcessError:
        Logger.warning("ensurepip non disponible, téléchargement manuel de get-pip.py...")
        get_pip_url = "https://bootstrap.pypa.io/get-pip.py"
        temp_file = os.path.join(tempfile.gettempdir(), "get-pip.py")
        urllib.request.urlretrieve(get_pip_url, temp_file)
        subprocess.run([PYTHON_EXE, temp_file], check=True, startupinfo=startupinfo)
        os.remove(temp_file)

    subprocess.run([PYTHON_EXE, "-m", "pip", "install", "--upgrade", "pip"], check=True, startupinfo=startupinfo)
    subprocess.run([PYTHON_EXE, "-m", "pip", "install", "--upgrade", "setuptools", "wheel"], check=True, startupinfo=startupinfo)

    Logger.info("pip, setuptools et wheel installés et prêts.")

def getREQUIREMENTSpackage():
    PACKAGE_IMPORT_MAP = {
        "beautifulsoup4": "bs4",
        "gspread-dataframe": "gspread_dataframe",
        "undetected-chromedriver": "undetected_chromedriver",
        "webdriver-manager": "webdriver_manager",
        "pyinstaller": "PyInstaller",
    }

    requirements_path = os.path.join(BASE_TEMP_PATH, "CONFIGS", "requirements.txt")

    with open(requirements_path, "r", encoding="utf-8") as f:
        required_packages = [
            line.strip() for line in f if line.strip() and not line.startswith("#")
        ]

    missing = []
    for pkg in required_packages:
        pkg_name = pkg.split("==")[0].split(">=")[0].split("<=")[0].split(">")[0].split("<")[0].split("[")[0]
        import_name = PACKAGE_IMPORT_MAP.get(pkg_name, pkg_name)
        try:
            subprocess.run(
                [PYTHON_EXE, "-c", f"import {import_name}"],
                capture_output=True,
                text=True,
                startupinfo=startupinfo,
                check=True
            )
        except subprocess.CalledProcessError:
            missing.append(pkg)

    if missing:
        Logger.warning(f"Packages manquants : {missing}")
        subprocess.run(
            [PYTHON_EXE, "-m", "pip", "install", *missing],
            check=True,
            startupinfo=startupinfo
        )
    else:
        Logger.info("Tous les packages sont déjà installés.")