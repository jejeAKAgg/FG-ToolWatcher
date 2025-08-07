import gspread
from oauth2client.service_account import ServiceAccountCredentials
from UTILS.NAMEformatter import *

def EXCELreader(worksheet):
    # Portée de l'accès
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

    # Authentification
    creds = ServiceAccountCredentials.from_json_keyfile_name(resource_path('CONFIGS/BOTconfig.json'), scope)
    client = gspread.authorize(creds)

    # Ouvre la feuille
    sheet = client.open("FG-ToolWatcher List").worksheet(worksheet)

    # Lit la colonne A (URLs)
    urls = sheet.col_values(1)
    return [url.strip() for url in urls if url.strip()]
