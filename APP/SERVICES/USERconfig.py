import os
import json

class UserConfig:
    DEFAULT_SETTINGS = {
        "language": "FR",
        "user_firstname": "",
        "user_lastname": "",
        "user_mail": "",
        "websites_to_watch": [],
        "cache_duration": 3,
        "send_email": False
    }

    def __init__(self, path: str):
        self.path = path
        self.config = {}
        self.load()  # Charge ou crée la config au démarrage

    def load(self):
        """
        Charge la configuration depuis le fichier.
        Si le fichier n'existe pas, le crée avec les valeurs par défaut.
        Si des clés manquent, les ajoute automatiquement.
        """
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
            except Exception:
                # En cas de fichier corrompu → repartir de zéro
                self.config = {}

        # Mise à jour avec valeurs par défaut (ajoute les nouvelles clés si besoin)
        updated = False
        for key, value in self.DEFAULT_SETTINGS.items():
            if key not in self.config:
                self.config[key] = value
                updated = True

        if not os.path.exists(self.path) or updated:
            self.save()

    def save(self):
        """Sauvegarde la configuration actuelle dans le fichier."""
        folder = os.path.dirname(self.path)
        if folder:
            os.makedirs(folder, exist_ok=True)

        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    def get(self, key, default=None):
        """Accède à une valeur avec fallback."""
        return self.config.get(key, default)

    def set(self, key, value):
        """Modifie une valeur et sauvegarde directement."""
        self.config[key] = value
        self.save()