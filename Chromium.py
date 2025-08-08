import os
import sys
import urllib.request
import zipfile

BASE_URL = "https://commondatastorage.googleapis.com/chromium-browser-snapshots/Win_x64/"

if getattr(sys, 'frozen', False):
    base_path = os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

DEST_FOLDER = os.path.join(base_path, "CORE")

def get_latest_build_number():
    last_change_url = BASE_URL + "LAST_CHANGE"
    with urllib.request.urlopen(last_change_url) as response:
        return response.read().decode('utf-8').strip()

def download_and_extract(url, dest_zip_path, extract_to):
    if not os.path.exists(dest_zip_path):
        print(f"Téléchargement depuis {url} ...")
        urllib.request.urlretrieve(url, dest_zip_path)
        print("Téléchargement terminé.")
        
        print("Décompression...")
        with zipfile.ZipFile(dest_zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print("Décompression terminée.")
    else:
        print(f"Archive déjà présente : {dest_zip_path}")

def download_chromium_and_driver():
    print(f"Destination : {DEST_FOLDER}")
    os.makedirs(DEST_FOLDER, exist_ok=True)

    build_number = get_latest_build_number()
    print(f"Build Chromium : {build_number}")

    # Chromium
    chromium_zip_path = os.path.join(DEST_FOLDER, "chrome-win.zip")
    chromium_url = f"{BASE_URL}{build_number}/chrome-win.zip"
    download_and_extract(chromium_url, chromium_zip_path, DEST_FOLDER)

    # Chromedriver
    chromedriver_zip_path = os.path.join(DEST_FOLDER, "chromedriver.zip")
    chromedriver_url = f"{BASE_URL}{build_number}/chromedriver_win32.zip"
    download_and_extract(chromedriver_url, chromedriver_zip_path, DEST_FOLDER)

if __name__ == "__main__":
    download_chromium_and_driver()
