# CORE/Services/user.py
import os
import json

from typing import Dict, Any, List, Optional



class UserService:
    
    """
    Manages both application settings (user preferences) and the external 
    product list configuration (Article(s)).
    
    This service ensures configuration files exist with valid default settings 
    and provides unified get/set methods.
    """

    def __init__(self, user_config_path: str, catalog_config_path: str):
        
        # === INPUT VARIABLE(S) ===
        self.user_config_path = user_config_path
        self.catalog_config_path = catalog_config_path

        # === INTERNAL VARIABLE(S) ===
        self.user_config: Dict[str, Any] = {
            'cache_duration': 3,
            'language': "EN",
            'send_email': False,
            'user_firstname': "",
            'user_lastname': "",
            'user_mail': "",
            'websites_to_watch': ["CIPAC", "CLABOTS", "GEORGES", "FIXAMI", "KLIUM", "LECOT", "TOOLNATION"],
        }

        self.catalog_config: Dict[str, List[str]] = {
            'items': []
        }
        
        # Loading configurations at initialization
        self.load()

    
    def load(self):
        
        """
        Loads user settings and catalog settings from their respective JSON files.
        Creates files or adds missing keys if necessary.
        """

        self._load_and_validate_file(self.user_config_path, self.user_config, target_attr='user_config')

        self._load_and_validate_file(self.catalog_config_path, self.catalog_config, target_attr='catalog_config')

    
    def _load_and_validate_file(self, file_path: str, defaults: Dict[str, Any], target_attr: str):
        
        """
        Helper to load a JSON file, validate its structure against defaults, and handle creation.
        """
        
        current_config = {}
        config_loaded = False
        
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    current_config = json.load(f)
                    config_loaded = True
            except Exception:
                current_config = {}

        updated = False
        for key, value in defaults.items():
            if key not in current_config:
                current_config[key] = value
                updated = True

        setattr(self, target_attr, current_config)

        if not config_loaded or updated:
            self._save_file(file_path, current_config)


    def save(self):
        
        """
        Saves both the user settings and the catalog settings to their respective files.
        """
     
        self._save_file(self.user_config_path, self.user_config)
        
        self._save_file(self.catalog_config_path, self.catalog_config)


    def _save_file(self, file_path: str, data: Dict[str, Any]):
        
        """
        Helper function to create directories and dump data to a specific JSON file.
        """
        
        folder = os.path.dirname(file_path)
        if folder:
            os.makedirs(folder, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)


    def get(self, key: str, default: Optional[Any] = None) -> Any:
        
        """
        Accesses a configuration value from user settings (self.config) with a fallback default.
        """
        
        return self.user_config.get(key, default)

    def set(self, key: str, value: Any):
        
        """
        Modifies a user setting value (self.config) and saves the configuration immediately.
        """
        
        self.user_config[key] = value
        self.save()

    def get_catalog_items(self) -> List[str]:
        
        """
        Accesses the list of items (MPNs/Articles) from the catalog configuration.
        """
        
        return self.catalog_config.get('items', [])

    def set_catalog_items(self, items: List[str]):
        
        """
        Modifies the list of items in the catalog configuration and saves immediately.
        """
        
        self.catalog_config['items'] = items
        self.save()