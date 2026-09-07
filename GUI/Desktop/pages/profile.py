# GUI/Desktop/pages/settings/profile.py

import logging
import re

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget
)

from CORE.Services.setup import *
from CORE.Services.translator import TranslatorService
from CORE.Services.user import UserService

from GUI.__assets.widgets.buttons import CustomPushButton


LOG = logging.getLogger(__name__)

class ProfilePage(QWidget):

    """
    QSide6 widget dedicated to user profile management.
    Displays user information and handles validation/saving of profile updates.
    """

    configs_updated = Signal()

    def __init__(self, config: UserService, translator: TranslatorService, parent=None):

        """
        Initializes the ProfilePage UI components and layout.
        """
        super().__init__(parent)

        # === INTERNAL SERVICE(S) ===
        self.configs = config
        self.translator = translator

        # === UI BUILDER(S) ===
        self._build_ui()
        self._connect_signals()

    # === PUBLIC METHODS ===
    def save_user(self):

        """
        Validates and saves user profile data to the configuration file,
        then disables the save button.
        """
        first_name = self.first_name_input.text().strip()
        last_name = self.last_name_input.text().strip()
        email = self.email_input.text().strip()

        # --- Saving ---
        self.configs.set("user_firstname", first_name)
        self.configs.set("user_lastname", last_name)
        self.configs.set("user_mail", email)

        # --- Checking changes ---
        self.save_button.setEnabled(False)
        self.configs_updated.emit()
        LOG.debug("[ProfilePage] User profile successfully saved.")

    def check_validity_and_changes(self):

        """
        Validates the data of the profile management page and enables
        the save button only if inputs are valid and have actually changed.
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
        Updates the text of every widget of the application depending on the new user language input.
        """
        self.title.setText(self.translator.get("page_profile_informations.title"))
        self.first_label.setText(self.translator.get("page_profile_firstname.subtitle"))
        self.last_label.setText(self.translator.get("page_profile_lastname.subtitle"))
        self.email_label.setText(self.translator.get("page_profile_mail.subtitle"))
        self.save_button.setText(self.translator.get("page_settings_save.button"))

    # === PRIVATE METHOD(S) ===
    def _build_ui(self):

        """
        Constructs the user interface elements for the profile page.
        """
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(60, 50, 60, 0)
        self.main_layout.setSpacing(10)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- TITLE ---
        self.title = QLabel(self.translator.get("page_profile_informations.title"))
        self.title.setStyleSheet("font-size: 26px; font-weight: 900; color: #000; margin-bottom: 15px;")
        self.title.setFixedWidth(450)

        title_layout = QHBoxLayout()
        title_layout.addStretch()
        title_layout.addWidget(self.title)
        title_layout.addStretch()

        self.main_layout.addLayout(title_layout)

        # --- FIRST NAME FIELD ---
        self.first_layout, self.first_label, self.first_name_input = self._create_input_field(
            label_text=self.translator.get("page_profile_firstname.subtitle"),
            text_value=self.configs.get("user_firstname", ""),
            width=450
        )
        self.main_layout.addLayout(self.first_layout)

        # --- LAST NAME FIELD ---
        self.last_layout, self.last_label, self.last_name_input = self._create_input_field(
            label_text=self.translator.get("page_profile_lastname.subtitle"),
            text_value=self.configs.get("user_lastname", ""),
            width=450
        )
        self.main_layout.addLayout(self.last_layout)

        # --- EMAIL FIELD ---
        self.email_layout, self.email_label, self.email_input = self._create_input_field(
            label_text=self.translator.get("page_profile_mail.subtitle"),
            text_value=self.configs.get("user_mail", ""),
            width=450
        )
        self.main_layout.addLayout(self.email_layout)

        # --- SAVE BUTTON ---
        self.save_button = CustomPushButton(
            width=100, height=50,
            bg_color="#eb6134", hover_color="#78351f"
        )
        self.save_button.setText(self.translator.get("page_settings_save.button"))
        self.save_button.setEnabled(False)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addStretch()

        self.main_layout.addStretch()
        self.main_layout.addLayout(button_layout)

    def _connect_signals(self):

        """
        Connects input field changes to the validation method and save button click.
        """
        self.save_button.clicked.connect(self.save_user)
        self.first_name_input.textChanged.connect(self.check_validity_and_changes)
        self.last_name_input.textChanged.connect(self.check_validity_and_changes)
        self.email_input.textChanged.connect(self.check_validity_and_changes)

    def _create_input_field(self, label_text, text_value, width=300, height=45):

        """
        Private helper to create a labeled and centered input field.
        """
        container = QVBoxLayout()
        container.setSpacing(5)

        label = QLabel(label_text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 15px; font-weight: 600; color: #000000;")
        container.addWidget(label)

        line_edit = QLineEdit()
        line_edit.setFixedWidth(width)
        line_edit.setFixedHeight(height)
        line_edit.setText(text_value)
        line_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)

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
                border: 2px solid #ffffff;
            }
        """)

        # Center the QLineEdit horizontally
        line_layout = QHBoxLayout()
        line_layout.addStretch()
        line_layout.addWidget(line_edit)
        line_layout.addStretch()

        container.addLayout(line_layout)

        return container, label, line_edit
