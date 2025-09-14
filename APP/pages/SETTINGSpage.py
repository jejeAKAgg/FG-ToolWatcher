from UTILS.LOGmaker import *
from UTILS.TOOLSbox import *

from APP.widgets.PUSHbuttons import CustomPushButton

from PySide6.QtWidgets import QWidget, QVBoxLayout, QCheckBox, QTextEdit, QPushButton, QComboBox
import os, json

class SettingsPage(QWidget):

    CONFIG_PATH = os.path.join(BASE_TEMP_PATH, "CONFIGS", "settings.json")

    DEFAULT_SETTINGS = {
        "language": "FR",
        "send_email": False,
        "email_list": []
    }

    def __init__(self, update_button=None, profile_button=None, settings_button=None, parent=None):
        super().__init__(parent)

        self.update_button = update_button
        self.profile_button = profile_button
        self.settings_button = settings_button

        # Assurer la présence du fichier dès l'ouverture
        self.ensure_config_file()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10,10,10,10)
        layout.setSpacing(10)

        # --- Choix de la langue ---
        self.language_combo = QComboBox()
        self.language_combo.addItems(["FR", "EN"])  # Tu peux ajouter d'autres langues ici

        # --- Options mail ---
        self.check_send_email = QCheckBox("Envoyer les résultats par mail")
        self.text_emails = QTextEdit()
        self.text_emails.setPlaceholderText("Entrez les adresses mail, une par ligne")

        # --- Bouton Save ---
        self.save_button = CustomPushButton(os.path.join(BASE_TEMP_PATH, "ASSETS", "save.ico"), bg_color="#eb6134", hover_color="#78351f" )
        self.save_button.clicked.connect(self.save_settings)

        # Ajout des widgets au layout
        layout.addWidget(self.language_combo)
        layout.addWidget(self.check_send_email)
        layout.addWidget(self.text_emails)
        layout.addWidget(self.save_button)
        layout.addStretch()

        self.load_settings()

    # -------------------------
    # FONCTIONS
    # -------------------------
    def ensure_config_file(self):
        """Crée le fichier settings.json avec des valeurs par défaut s'il n'existe pas."""
        if not os.path.exists(self.CONFIG_PATH):
            os.makedirs(os.path.dirname(self.CONFIG_PATH), exist_ok=True)
            with open(self.CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.DEFAULT_SETTINGS, f, indent=4)

    def load_settings(self):
        if os.path.exists(self.CONFIG_PATH):
            with open(self.CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Mettre à jour la langue
                lang = data.get("language", "FR")
                index = self.language_combo.findText(lang)
                if index >= 0:
                    self.language_combo.setCurrentIndex(index)
                # Mail
                self.check_send_email.setChecked(data.get("send_email", False))
                self.text_emails.setText("\n".join(data.get("email_list", [])))

    def save_settings(self):
        os.makedirs(os.path.dirname(self.CONFIG_PATH), exist_ok=True)
        data = {
            "language": self.language_combo.currentText(),
            "send_email": self.check_send_email.isChecked(),
            "email_list": [e.strip() for e in self.text_emails.toPlainText().splitlines() if e.strip()]
        }
        with open(self.CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        print("✅ Paramètres sauvegardés !")

    def get_email_settings(self):
        """Retourne un booléen et la liste d'emails"""
        return self.check_send_email.isChecked(), [
            e.strip() for e in self.text_emails.toPlainText().splitlines() if e.strip()
        ]

    def get_language(self):
        """Retourne la langue sélectionnée"""
        return self.language_combo.currentText()