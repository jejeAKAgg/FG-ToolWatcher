# GUI/Desktop/pages/subpages/settings/profile.py
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

class ProfilePage(QWidget):

    """
    QSide6 widget dedicated to the user profile management.
    It displays user information and allows profile updates.
    """

    def __init__(self, config: UserService, translator: TranslatorService, parent=None):

        """
        Initializes the ProfilePage UI components and layout.

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
        
        # --- TITLE ---
        self.title = QLabel(self.translator.get("subpage_settings_profile.title"))
        self.title.setStyleSheet("font-size: 26px; font-weight: 900; color: #000; margin-bottom: 15px;")
        self.main_layout.addWidget(self.title)
        
        # --- FIRST NAME ---
        self.first_layout, self.first_label, self.first_name_input = self._create_input_field(
            label_text=self.translator.get("subpage_settings_profile_firstname.bar"),
            text_value=self.configs.get("user_firstname", ""),
            width=450
        )
        
        self.main_layout.addLayout(self.first_layout)

        # --- LAST NAME ---
        self.last_layout, self.last_label, self.last_name_input = self._create_input_field(
            label_text=self.translator.get("subpage_settings_profile_lastname.bar"),
            text_value=self.configs.get("user_lastname", ""),
            width=450
        )
        self.main_layout.addLayout(self.last_layout)

        # --- EMAIL ---
        self.email_layout, self.email_label, self.email_input = self._create_input_field(
            label_text=self.translator.get("subpage_settings_profile_mail.bar"),
            text_value=self.configs.get("user_mail", ""),
            width=450
        )
        self.main_layout.addLayout(self.email_layout)

        # --- SAVE BUTTON ---
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

        self.first_name_input.textChanged.connect(self.check_validity_and_changes)
        self.last_name_input.textChanged.connect(self.check_validity_and_changes)
        self.email_input.textChanged.connect(self.check_validity_and_changes)


    # === PUBLIC METHODS ===
    def save_user(self):
        
        """
        Validates and saves user profile data to the configuration file.
        """
        
        # === INTERNAL PARAMETER(S) ===
        first_name = self.first_name_input.text().strip()
        last_name = self.last_name_input.text().strip()
        email = self.email_input.text().strip()

        # --- Saving ---
        self.configs.set("user_firstname", first_name)
        self.configs.set("user_lastname", last_name)
        self.configs.set("user_mail", email)

        # --- Checking changes ---
        self.save_button.setEnabled(False)
    
    def check_validity_and_changes(self):
       
        """
        Validates the data of the profile management page and enables the save button in case of valid change.
        """

        first = self.first_name_input.text().strip()
        last = self.last_name_input.text().strip()
        email = self.email_input.text().strip()

        email_pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$")
        
        is_valid = (
            len(first) >= 2 and
            len(last) >= 2 and 
            bool(email_pattern.match(email))
        )

        has_changed = (
            first != self.configs.get("user_firstname", "") or
            last != self.configs.get("user_lastname", "") or
            email != self.configs.get("user_mail", "")
        )

        self.save_button.setEnabled(bool(is_valid and has_changed))
    
    def retranslate_ui(self):
        
        """
        Update the texte of every widget of the application depending the new user language input.
        """

        self.title.setText(self.translator.get("subpage_settings_profile.title"))

        self.first_label.setText(self.translator.get("subpage_settings_profile_firstname.bar"))
        self.last_label.setText(self.translator.get("subpage_settings_profile_lastname.bar"))
        self.email_label.setText(self.translator.get("subpage_settings_profile_mail.bar"))

        self.save_button.setText(self.translator.get("save.button"))

    def _create_input_field(self, label_text: str, text_value: str, width: int = 300, height: int = 45) -> Tuple[QVBoxLayout, QLabel, QLineEdit]:
        
        """
        Private helper to create a labeled and centered input field.
        
        Args:
            label_text (str): The text for the field's label.
            text_value (str): The default value for the QLineEdit.
            width (int): The fixed width of the QLineEdit.
            height (int): The fixed height of the QLineEdit.

        Returns:
            Tuple[QVBoxLayout, QLineEdit]: A layout containing the label and field,
            and a reference to the QLineEdit itself.
        """
        
        container = QVBoxLayout()
        container.setSpacing(5) # Colle le label à son input

        label = QLabel(label_text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 15px; font-weight: 600; color: #000000;")
        container.addWidget(label)

        line_edit = QLineEdit()
        line_edit.setFixedWidth(width)
        line_edit.setFixedHeight(height)
        line_edit.setText(text_value)
        line_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Ton style exact de la page profile originale
        line_edit.setStyleSheet("""
            QLineEdit {
                padding: 5px;
                border-radius: 8px;
                border: 1px solid #ccc;
                background-color: #333;
                color: #ffffff;
                font-size: 16px;
            }
            QLineEdit:focus {
                border: 2px solid #ffffff; /* Changé de orange à blanc */
            }
        """)

        # Center the QLineEdit horizontally
        line_layout = QHBoxLayout()
        line_layout.addStretch()
        line_layout.addWidget(line_edit)
        line_layout.addStretch()
        container.addLayout(line_layout)

        return container, label, line_edit