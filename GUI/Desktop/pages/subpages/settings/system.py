# GUI/Desktop/pages/subpages/settings/system.py
import os

import logging

import re

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt

from CORE.Services.setup import *
from CORE.Services.user import UserService
from CORE.Services.translator import TranslatorService

from GUI.__ASSETS.widgets.push_buttons import CustomPushButton



# ======= LOGGING SYSTEM ========
LOG = logging.getLogger(__name__)
# ===============================

class SystemPage(QWidget):

    """
    QSide6 widget dedicated to the user system management.
    It displays system information and allows system configuration updates.
    """

    def __init__(self, config: UserService, translator: TranslatorService, parent=None):

        """
        Initializes the SystemPage UI components and layout.

        Args:
            config (UserService): The service instance for managing user settings.
            translator (TranslatorService): The service instance for managing translations.
            parent (Optional[QWidget]): The parent widget.
        """

        super().__init__(parent)

        # === INTERNAL VARIABLE(S) ===
        self.configs = config
        self.translator = translator

        # === MAIN LAYOUT ===
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(60, 50, 60, 0) 
        self.main_layout.setSpacing(10)
        self.main_layout.setAlignment(Qt.AlignTop)

        # --- SUBPAGE TITLE ---
        self.title = QLabel(self.translator.get("subpage_settings_system.title"))
        self.title.setStyleSheet("font-size: 26px; font-weight: 900; color: #000; margin-bottom: 20px;")
        self.main_layout.addWidget(self.title)

        # --- CONTENT ---
        # TODO: ajouter ici les éléments de la page système (ex: vérification des mises à jour, infos sur le système, etc.)

        self.save_button = CustomPushButton(
            width=100, height=50,
            bg_color="#eb6134", hover_color="#78351f"
        )
        self.save_button.setText(self.translator.get("save.button"))
        self.save_button.clicked.connect(self.save_user)

        self.save_button.setEnabled(False)

        self.button_layout = QHBoxLayout()
        self.button_layout.addStretch()
        self.button_layout.addWidget(self.save_button)
        self.button_layout.addStretch()
            
        self.main_layout.addStretch()

        self.main_layout.addLayout(self.button_layout)


    # === PUBLIC METHODS ===
    def save_user(self):
        
        """
        Validates and saves user profile data to the configuration file.
        """
        
        # === INTERNAL PARAMETER(S) ===
        # (TODO: ajouter ici les paramètres nécessaires à la sauvegarde des données de la page de gestion des sites web)

        # --- Checking changes ---
        self.save_button.setEnabled(False)

    def retranslate_ui(self):
        
        """
        Update the texte of every widget of the application depending the new user language input.
        """

        self.title.setText(self.translator.get("subpage_settings_system.title"))

        self.save_button.setText(self.translator.get("save.button"))