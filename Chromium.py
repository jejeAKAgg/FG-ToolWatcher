import os
import urllib.request
import zipfile

BASE_URL = "https://commondatastorage.googleapis.com/chromium-browser-snapshots/Win_x64/"
DEST_FOLDER = os.path.join(os.path.dirname(__file__), "CORE")

def get_latest_build_number():
    last_change_url = BASE_URL + "LAST_CHANGE"
    with urllib.request.urlopen(last_change_url) as response:
        return response.read().decode('utf-8').strip()

def download_chromium():
    if not os.path.exists(DEST_FOLDER):
        os.makedirs(DEST_FOLDER)
    
    build_number = get_latest_build_number()
    print(f"Téléchargement de la build Chromium #{build_number}...")
    
    zip_path = os.path.join(DEST_FOLDER, "chrome-win.zip")
    download_url = f"{BASE_URL}{build_number}/chrome-win.zip"
    
    if not os.path.isfile(zip_path):
        urllib.request.urlretrieve(download_url, zip_path)
        print("Téléchargement terminé.")
        
        print("Décompression...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(DEST_FOLDER)
        print("Chromium prêt.")
    else:
        print("Chromium déjà téléchargé.")

if __name__ == "__main__":
    download_chromium()
