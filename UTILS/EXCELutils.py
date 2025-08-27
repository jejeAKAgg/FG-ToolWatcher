import os
import time

import csv
import pandas as pd
import re
import gspread

from oauth2client.service_account import ServiceAccountCredentials
from gspread.exceptions import APIError, WorksheetNotFound
from gspread_dataframe import set_with_dataframe

from UTILS.LOGmaker import *
from UTILS.TOOLSbox import *



# ====================
#     LOGGER SETUP
# ====================
Logger = logger("EXCELutils")


# ====================
#    VARIABLE SETUP
# ====================
FINALcsv = os.path.join(BASE_SYSTEM_PATH, "DATA", "RESULTSproducts.csv")
FINALxlsx = os.path.join(BASE_SYSTEM_PATH, "DATA", "RESULTSproducts.xlsx")


# ====================
#     CSV MERGER 
# ====================
def FINALdf(files):
    # Fusion + tri + réindexation
    final_df = pd.concat(files, ignore_index=True)
    
    final_df['priority'] = final_df['Société'].apply(lambda x: 0 if x == "FERNAND GEORGES" else 1)
    final_df = final_df.sort_values(by=["MPN", "priority", "Société"], ascending=[True, True, True]).reset_index(drop=True)
    final_df.drop(columns=['priority'], inplace=True)

    # CSV brut
    final_df.to_csv(FINALcsv, index=False, encoding='utf-8-sig', quoting=csv.QUOTE_ALL)


    # Excel avec hyperliens
    with pd.ExcelWriter(FINALxlsx, engine='xlsxwriter') as writer:
        workbook = writer.book
        worksheet = workbook.add_worksheet("Feuille1")
        writer.sheets["Feuille1"] = worksheet

        # Format gras
        bold_format = workbook.add_format({'bold': True})

        # En-tête
        for col_idx, col_name in enumerate(final_df.columns):
            worksheet.write(0, col_idx, col_name)

        hyperlink_pattern = re.compile(r'=HYPERLINK\("([^"]+)"\s*;\s*"([^"]+)"\)', re.IGNORECASE)

        # Colonnes à mettre en gras uniquement pour FERNAND GEORGES
        cols_to_bold = ["Société", "Prix (HTVA)", "Prix (TVA)"]

        # Écriture lignes
        for row_idx in range(len(final_df)):
            is_fg = final_df.iloc[row_idx]['Société'] == "FERNAND GEORGES"
            for col_idx, col_name in enumerate(final_df.columns):
                value = final_df.iloc[row_idx, col_idx]

                # Appliquer gras uniquement sur ces colonnes ET si Société == FERNAND GEORGES
                if is_fg and col_name in cols_to_bold:
                    cell_format = bold_format
                else:
                    cell_format = None

                if col_name == "Article" and isinstance(value, str):
                    match = hyperlink_pattern.match(value.strip())
                    if match:
                        url, text = match.groups()
                        text = text.replace('""', '"')  # Correction des doubles guillemets
                        worksheet.write_url(row_idx + 1, col_idx, url.strip(), string=text.strip(), cell_format=cell_format)
                    else:
                        worksheet.write(row_idx + 1, col_idx, value, cell_format)
                else:
                    worksheet.write(row_idx + 1, col_idx, value, cell_format)

    return FINALxlsx


# ====================
#     EXCEL READER 
# ====================
def EXCELreader(worksheet):
    # Portée de l'accès
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

    # Authentification
    creds = ServiceAccountCredentials.from_json_keyfile_name(os.path.join(BASE_TEMP_PATH,'CONFIGS/BOTconfig.json'), scope)
    client = gspread.authorize(creds)

    # Ouvre la feuille
    sheet = client.open("FG-ToolWatcher List").worksheet(worksheet)

    # Lit la colonne A (URLs)
    urls = sheet.col_values(1)

    return [url.strip() for url in urls if url.strip()]


# ====================
#     EXCEL SENDER 
# ====================
def EXCELsender(file, retries=3, delay=10):
    attempt = 0

    while attempt < retries:
        try:
            Logger.info(f"Tentative d'envoi vers Google Sheets (tentative {attempt + 1}/{retries})...")

            # === AUTHENTIFICATION === #
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            creds = ServiceAccountCredentials.from_json_keyfile_name(os.path.join(BASE_TEMP_PATH,'CONFIGS/BOTconfig.json'), scope)
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

            # === CHARGEMENT DU XLSX DANS UN DATAFRAME === #
            df = pd.read_excel(file, engine="openpyxl")

            # === ENVOI VERS GOOGLE SHEETS === #
            set_with_dataframe(sheet, df)

            Logger.info("Envoi vers Google Sheets réussi.")
            return

        except APIError as e:
            attempt += 1
            Logger.error(f"Erreur Google API (APIError) : {e}")
            if attempt < retries:
                Logger.info(f"Nouvelle tentative dans {delay} secondes...")
                time.sleep(delay)
            else:
                Logger.critical("Échec après plusieurs tentatives. Abandon.")
                return

        except Exception as e:
            Logger.exception(f"Erreur inattendue pendant l'envoi à Google Sheets : {e}")
            return