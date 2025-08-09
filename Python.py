import os
import sys
import urllib.request
import zipfile

# Version de Python portable à télécharger
PYTHON_VERSION = "3.11.4"
PYTHON_ZIP_NAME = f"python-{PYTHON_VERSION}-embed-amd64.zip"
BASE_URL = f"https://www.python.org/ftp/python/{PYTHON_VERSION}/{PYTHON_ZIP_NAME}"

# Base path = emplacement du .exe ou du script
if getattr(sys, 'frozen', False):
    base_path = os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

DEST_FOLDER = os.path.join(base_path, "CORE", "python")
PYTHON_ZIP_PATH = os.path.join(base_path, "CORE", PYTHON_ZIP_NAME)

def download_and_extract_python():
    # Crée CORE/python si besoin
    os.makedirs(DEST_FOLDER, exist_ok=True)

    # Télécharge Python si besoin
    if not os.path.exists(PYTHON_ZIP_PATH):
        print(f"Téléchargement de Python {PYTHON_VERSION} ...")
        urllib.request.urlretrieve(BASE_URL, PYTHON_ZIP_PATH)
        print("Téléchargement terminé.")
    else:
        print(f"Archive déjà présente : {PYTHON_ZIP_PATH}")

    # Décompresse si pas encore extrait
    marker_file = os.path.join(DEST_FOLDER, "python.exe")
    if not os.path.exists(marker_file):
        print("Décompression...")
        with zipfile.ZipFile(PYTHON_ZIP_PATH, 'r') as zip_ref:
            zip_ref.extractall(DEST_FOLDER)
        print("Décompression terminée.")
    else:
        print("Python déjà extrait.")

if __name__ == "__main__":
    download_and_extract_python()