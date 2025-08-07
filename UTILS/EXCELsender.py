import time
import gspread
import pandas as pd

from UTILS.LOGmaker import logger
from UTILS.NAMEformatter import *

from gspread_dataframe import set_with_dataframe
from oauth2client.service_account import ServiceAccountCredentials
from gspread.exceptions import APIError, WorksheetNotFound

# ====================
#     LOGGER SETUP
# ====================
Logger = logger("CSVmerger")

# ====================
#    EXCEL Sender 
# ====================
def EXCELsender(file, retries=3, delay=10):
    attempt = 0

    while attempt < retries:
        try:
            Logger.info(f"Tentative d'envoi vers Google Sheets (tentative {attempt + 1}/{retries})...")

            # === AUTHENTIFICATION === #
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            creds = ServiceAccountCredentials.from_json_keyfile_name(resource_path('CONFIGS/BOTconfig.json'), scope)
            client = gspread.authorize(creds)

            # === OUVERTURE DE LA FEUILLE === #
            spreadsheet = client.open("FG-ToolWatcher List")

            # === OUVERTURE/CRÉATION DE L'ONGLET "RESULTS" === #
            try:
                sheet = spreadsheet.worksheet("RESULTS")
            except WorksheetNotFound:
                Logger.warning("Onglet 'RESULTS' non trouvé. Création en cours...")
                sheet = spreadsheet.add_worksheet(title="RESULTS", rows="1000", cols="20")

            # === VIDAGE DU CONTENU EXISTANT (optionnel) === #
            sheet.clear()

            # === CHARGEMENT DU CSV DANS UN DATAFRAME === #
            df = pd.read_csv(file)

            # === ENVOI VERS GOOGLE SHEETS === #
            set_with_dataframe(sheet, df)

            Logger.info("✅ Envoi vers Google Sheets réussi.")
            return

        except APIError as e:
            attempt += 1
            Logger.error(f"❌ Erreur Google API (APIError) : {e}")
            if attempt < retries:
                Logger.info(f"Nouvelle tentative dans {delay} secondes...")
                time.sleep(delay)
            else:
                Logger.critical("⛔ Échec après plusieurs tentatives. Abandon.")
                return

        except Exception as e:
            Logger.exception(f"❌ Erreur inattendue pendant l'envoi à Google Sheets : {e}")
            return