import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import List
from APP.SERVICES.__init__ import *


class CatalogService:
    """
    Gère la lecture, écriture et synchronisation des MPN
    entre la Google Sheet et un cache local JSON.
    """

    def __init__(self, path: str):
        
        self.path = path
        self.scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]

        creds_path = os.path.join(BASE_TEMP_PATH, "APP", "CONFIGS", "BOTconfig.json")
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, self.scope)
        self.client = gspread.authorize(creds)
        self.sheet = self.client.open("FG-ToolWatcher List").worksheet("MPNs/Articles")

        self.mpns: List[str] = []

        # Chargement automatique au démarrage
        #self.load()

    # === LOCAL FILE ===
    def load(self):
        """Charge depuis le cache local ou crée un fichier si inexistant, puis sync Google Sheet."""
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self.mpns = json.load(f)
            except Exception:
                self.mpns = []
        else:
            self.mpns = []
            self.save()

        # Synchronisation avec la feuille Google
        self.sync_with_sheet()

    def save(self):
        """Sauvegarde la liste actuelle localement."""
        folder = os.path.dirname(self.path)
        os.makedirs(folder, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.mpns, f, indent=4, ensure_ascii=False)

    # === SHEET SYNC ===
    def sync_with_sheet(self):
        """Mets à jour la liste locale depuis la Google Sheet."""
        sheet_mpns = [m.strip() for m in self.sheet.col_values(1) if m.strip()]
        combined = sorted(set(sheet_mpns + self.mpns))  # union des deux sources
        if combined != self.mpns:
            self.mpns = combined
            self.save()

    def push_to_sheet(self):
        """Pousse les nouveaux MPN du cache local vers la Google Sheet."""
        sheet_mpns = [m.strip() for m in self.sheet.col_values(1) if m.strip()]
        missing = [m for m in self.mpns if m not in sheet_mpns]
        if missing:
            self.sheet.append_rows([[m] for m in missing])

    # === EDIT ===
    def get_all(self) -> List[str]:
        return list(self.mpns)

    def add(self, mpn: str) -> bool:
        mpn = mpn.strip()
        if not mpn or mpn in self.mpns:
            return False
        self.mpns.append(mpn)
        self.save()
        self.push_to_sheet()
        return True

    def remove(self, mpn: str) -> bool:
        if mpn not in self.mpns:
            return False
        self.mpns.remove(mpn)
        self.save()
        # Supprimer côté Google
        sheet_mpns = [m.strip() for m in self.sheet.col_values(1) if m.strip()]
        if mpn in sheet_mpns:
            index = sheet_mpns.index(mpn) + 1
            self.sheet.delete_rows(index)
        return True