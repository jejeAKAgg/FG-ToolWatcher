# GUI/Desktop/pages/profile.py
import re

import logging

from PySide6.QtCore import Signal, Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QMessageBox,
    QSpacerItem, QSizePolicy, QHBoxLayout
)

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

    configs_updated = Signal()
    language_changed = Signal()

    def __init__(self, config: UserService, translator: TranslatorService, parent=None):

        """
        Initializes the ProfilePage UI components and layout.

        Args:
            user_config (UserService): The service instance for managing user settings.
            parent (Optional[QWidget]): The parent widget.
        """

        super().__init__(parent)

        # === INTERNAL VARIABLE(S) ===
        self.configs = config
        self.translator = translator

        # === LAYOUT ===
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(20, 20, 20, 20) # Added margins for better spacing

        # --- Title ---
        self.title = QLabel(self.translator.get("page_profile_informations.bar"))
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet("font-size: 24px; font-weight: bold; color: #333;")
        layout.addWidget(self.title)

        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # --- Input Fields ---
        # First Name
        self.first_layout, self.first_label, self.first_name_input = self._create_input_field(
            label_text=self.translator.get("page_profile_firstname.bar"),
            text_value=self.configs.get("user_firstname", ""),
            width=500
        )
        layout.addLayout(self.first_layout)

        # Last Name
        self.last_layout, self.last_label, self.last_name_input = self._create_input_field(
            label_text=self.translator.get("page_profile_name.bar"),
            text_value=self.configs.get("user_lastname", ""),
            width=500
        )
        layout.addLayout(self.last_layout)

        # Email
        self.email_layout, self.email_label, self.email_input = self._create_input_field(
            label_text=self.translator.get("page_profile_mail.bar"),
            text_value=self.configs.get("user_mail", ""),
            width=500
        )
        layout.addLayout(self.email_layout)

        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # --- Save Button ---
        self.save_button = CustomPushButton(
            os.path.join(ASSETS_FOLDER, "icons", "save.ico"),
            width=150, height=50,
            bg_color="#eb6134", hover_color="#78351f"
        )
        self.save_button.setText(self.translator.get("save.button"))
        self.save_button.clicked.connect(self.save_user)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)
        layout.addStretch(1) # Add stretch to push content to the top/center

    def _create_input_field(self, label_text: str, text_value: str, width: int = 300, height: int = 50) -> Tuple[QVBoxLayout, QLineEdit]:

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
        label = QLabel(label_text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 16px; color: #555;")
        container.addWidget(label)

        line_edit = QLineEdit()
        line_edit.setFixedWidth(width)
        line_edit.setFixedHeight(height)
        line_edit.setText(text_value)
        line_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        line_edit.setStyleSheet("""
            padding: 5px;
            border-radius: 8px;
            border: 1px solid #ccc;
            font-size: 16px;
        """)

        # Center the QLineEdit horizontally using a nested QHBoxLayout
        line_layout = QHBoxLayout()
        line_layout.addStretch()
        line_layout.addWidget(line_edit)
        line_layout.addStretch()
        container.addLayout(line_layout)

        return container, label, line_edit

    def save_user(self):
        
        """
        Validates and saves user profile data to the configuration file.
        Emits 'user_saved' signal on success.
        """
        
        # === INTERNAL PARAMETER(S) ===
        first_name = self.first_name_input.text().strip()
        last_name = self.last_name_input.text().strip()
        email = self.email_input.text().strip()

        # === LOGIC ===
        # --- Verification ---
        if not all([first_name, last_name, email]):
            QMessageBox.warning(self, self.translator.get("box_error_type.text"), self.translator.get("page_profile_error_incomplete.box"))
            return
        
        if not re.compile(r"^[^@\s]+@[^@\s]+\.[a-zA-Z0-9._-]+$").match(email):
            QMessageBox.warning(self, self.translator.get("box_error_type.text"), self.translator.get("page_profile_error_mail.box"))
            return

        # --- Saving ---
        self.configs.set("user_firstname", first_name)
        self.configs.set("user_lastname", last_name)
        self.configs.set("user_mail", email)

        # --- Signal ---
        self.configs_updated.emit()   # Emitting signal to notify parent (Client.py)

    def retranslate_ui(self):
        
        """
        Update the texte of every widget of the application depending the new user language input.
        """

        self.title.setText(self.translator.get("page_profile_informations.bar"))

        self.first_label.setText(self.translator.get("page_profile_firstname.bar"))
        self.last_label.setText(self.translator.get("page_profile_name.bar"))
        self.email_label.setText(self.translator.get("page_profile_mail.bar"))
        
        self.save_button.setText(self.translator.get("save.button"))