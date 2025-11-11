# CORE/Services/translator.py
import json
import os

from CORE.Services.setup import * 


class TranslatorService:
    def __init__(self):
        self.translations = {}
        self.current_lang = "en"

    def load_language(self, lang_code: str):
        
        """
        Load .json according language file.
        """
        
        self.current_lang = lang_code
        file_path = os.path.join(ASSETS_FOLDER, "i18n", f"{lang_code}.json")
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                self.translations = json.load(f)
        except FileNotFoundError:
            print(f"Erreur: Fichier de langue '{lang_code}.json' non trouvé.")
            if lang_code != "en":
                self.load_language("en")
            
    def get(self, key: str, fallback: str = "") -> str:
        
        """
        Fetch a specific traduction for a given key.
        """
        
        return self.translations.get(key, fallback or key)