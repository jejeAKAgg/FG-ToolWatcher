import os
import time

import csv
import pandas as pd
import re
import gspread

from oauth2client.service_account import ServiceAccountCredentials
from gspread.exceptions import APIError, WorksheetNotFound
from gspread_dataframe import set_with_dataframe

from APP.SERVICES.__init__ import *
from APP.SERVICES.LOGservice import LogService



# ====================
#     LOGGER SETUP
# ====================
Logger = LogService.logger("EXCELutils")


# ====================
#    VARIABLE SETUP
# ====================
FINALcsv = os.path.join(RESULTS_SUBFOLDER, "RESULTSproducts.csv")
FINALxlsx = os.path.join(RESULTS_SUBFOLDER, "RESULTSproducts.xlsx")


# ===================
#   EXCEL FUNCTIONS 
# ===================
def EXCELreader(worksheet):
    
    """
    Read the specific sheet 'MPNs/Articles' available online and return
    a list containing all specific values present on the sheet.

    Args:
        worksheet (gspread.models.Worksheet): 
            The Google Sheets worksheet object to read from.

    Returns:
        list[str]: 
            A list containing all extracted values from the sheet.

    """

    # === Access ===
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

    # === Auth ===
    creds = ServiceAccountCredentials.from_json_keyfile_name(os.path.join(BASE_TEMP_PATH, "APP", "CONFIGS", "BOTconfig.json"), scope)
    client = gspread.authorize(creds)

    # === Opening the given sheet and reading the first column (only place where MPNs/Articles are put) ===
    sheet = client.open("FG-ToolWatcher List").worksheet(worksheet)
    urls = sheet.col_values(1)

    # === Returning a list of all the content available ===
    return [url.strip() for url in urls if url.strip()]


def FINALcsvCONVERTER(files):

    """
    Merges multiple DataFrames, creates hyperlinks in the 'Article' column,
    normalizes price columns, and exports as CSV ready for Google Sheets.

    Args:
        files (list[pd.DataFrame]): List of DataFrames to merge.

    Returns:
        str: Path to the generated CSV file.
    
    """

    price_cols = ["Prix (HTVA)", "Prix (TVA)", "Ancien Prix (HTVA)"]

    # --- Merge ---
    final_df = pd.concat(files, ignore_index=True)

    # --- Priorité FERNAND GEORGES pour tri ---
    final_df['priority'] = final_df['Société'].apply(lambda x: 0 if x == "FERNAND GEORGES" else 1)
    final_df = final_df.sort_values(by=["MPN", "priority", "Société"]).reset_index(drop=True)
    final_df.drop(columns=['priority'], inplace=True)

    # --- Fusion Article + ArticleURL en HYPERLINK ---
    if "Article" in final_df.columns and "ArticleURL" in final_df.columns:
        final_df["Article"] = final_df.apply(
            lambda x: f'=HYPERLINK("{x["ArticleURL"]}"; "{x["Article"]}")'
            if pd.notna(x["ArticleURL"]) and x["ArticleURL"] not in ["", "-", "None"] else "Produit indisponible",
            axis=1
        )
        final_df = final_df.drop(columns=["ArticleURL"])

    # --- Normalisation prix ---
    if price_cols:
        for col in price_cols:
            if col in final_df.columns:
                final_df[col] = final_df[col].apply(lambda x: "" if pd.isna(x) else str(x).replace('.', ','))

    # --- Export CSV ---
    final_df.to_csv(FINALcsv, sep=';', index=False, encoding='utf-8-sig', quoting=csv.QUOTE_ALL)

    # --- Return ---
    return FINALcsv


def FINALxlsxCONVERTER(files):

    """
    Merges multiple DataFrames, creates hyperlinks in the 'Article' column,
    normalizes price columns, exports as XLSX for Excel, and applies formatting:
    - Bold rows where 'Société' is 'FERNAND GEORGES'.
    - Secure hyperlinks in the 'Article' column.

    Args:
        files (list[pd.DataFrame]): List of DataFrames to merge.

    Returns:
        str: Path to the generated XLSX file.
    
    """

    price_cols = ["Prix (HTVA)", "Prix (TVA)", "Ancien Prix (HTVA)"]

    # --- Merge ---
    final_df = pd.concat(files, ignore_index=True)

    # --- Priorité FERNAND GEORGES pour tri ---
    final_df['priority'] = final_df['Société'].apply(lambda x: 0 if x == "FERNAND GEORGES" else 1)
    final_df = final_df.sort_values(by=["MPN", "priority", "Société"]).reset_index(drop=True)
    final_df.drop(columns=['priority'], inplace=True)

    # --- Préparer hyperliens Article directement dans Article ---
    if "Article" in final_df.columns and "ArticleURL" in final_df.columns:
        final_df["Article"] = final_df.apply(
            lambda x: f'=HYPERLINK("{x["ArticleURL"]}"; "{x["Article"]}")'
            if pd.notna(x["ArticleURL"]) and x["ArticleURL"] not in ["", "-", "None"] else "Produit indisponible",
            axis=1
        )
        final_df = final_df.drop(columns=["ArticleURL"])

    # --- Export Excel ---
    with pd.ExcelWriter(FINALxlsx, engine='xlsxwriter') as writer:
        final_df.to_excel(writer, index=False, sheet_name="Feuille1")
        workbook = writer.book
        worksheet = writer.sheets["Feuille1"]

        # --- Bold FERNAND GEORGES ---
        bold_format = workbook.add_format({'bold': True})
        for row_idx, societe in enumerate(final_df['Société'], start=1):
            if societe == "FERNAND GEORGES":
                worksheet.set_row(row_idx, None, bold_format)

        # --- Hyperliens sécurisés dans Article ---
        article_col_idx = final_df.columns.get_loc("Article")
        hyperlink_pattern = re.compile(r'=HYPERLINK\("([^"]+)"; "([^"]+)"\)', re.IGNORECASE)

        for row_idx, val in enumerate(final_df["Article"], start=1):
            if isinstance(val, str):
                match = hyperlink_pattern.match(val.strip())
                if match:
                    url, text = match.groups()
                    if url.startswith(("http://", "https://", "mailto:")):
                        worksheet.write_url(row_idx, article_col_idx, url, string=text)
                    else:
                        worksheet.write(row_idx, article_col_idx, "Produit indisponible")
                else:
                    worksheet.write(row_idx, article_col_idx, val)

        # --- Formattage prix ---
        money_format = workbook.add_format({'num_format': '#,##0.00'})
        for col_name in price_cols:
            if col_name in final_df.columns:
                col_idx = final_df.columns.get_loc(col_name)
                worksheet.set_column(col_idx, col_idx, 15, money_format)

    return FINALxlsx


def EXCELsender(file, retries=3, delay=10):

    """
    Uploads a local CSV or XLSX file to Google Sheets ("FG-ToolWatcher List" > "RESULTS").
    - Creates the worksheet if it doesn't exist.
    - Clears existing content before upload.
    - Automatically retries on API errors.

    Args:
        file (str): Path to the CSV or XLSX file.
        retries (int, optional): Maximum retry attempts. Default is 3.
        delay (int, optional): Delay in seconds between retries. Default is 10.

    Returns:
        None
    """

    attempt = 0

    while attempt < retries:
        try:
            Logger.info(f"Tentative d'envoi vers Google Sheets (tentative {attempt + 1}/{retries})...")

            # === Auth ===
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                os.path.join(BASE_TEMP_PATH, "APP", "CONFIGS", "BOTconfig.json"), scope)
            client = gspread.authorize(creds)

            # === Opening sheet and switching to correct worksheet ===
            spreadsheet = client.open("FG-ToolWatcher List")

            try:
                sheet = spreadsheet.worksheet("RESULTS")
            except WorksheetNotFound:
                Logger.warning("Onglet 'RESULTS' non trouvé. Création en cours...")
                sheet = spreadsheet.add_worksheet(title="RESULTS", rows="1000", cols="20")

            # === Cleaning ===
            sheet.clear()

            # --- Lecture CSV/XLSX ---
            df = pd.read_csv(file, sep=';', encoding='utf-8-sig', quoting=csv.QUOTE_ALL) if file.lower().endswith('.csv') else pd.read_excel(file)

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