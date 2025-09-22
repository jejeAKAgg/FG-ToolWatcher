from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QMessageBox,
    QSpacerItem, QSizePolicy, QHBoxLayout, QPushButton
)
from PySide6.QtGui import QIcon
from APP.WIDGETS.PUSHbuttons import CustomPushButton
from APP.SERVICES.__init__ import *
import os
import re

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[a-zA-Z0-9]+$")


class ProfilePage(QWidget):
    user_saved = Signal()  # signal à émettre quand l'utilisateur valide

    def __init__(self, update_button, profile_button, settings_button, config, parent=None):
        super().__init__(parent)

        self.update_button = update_button
        self.profile_button = profile_button
        self.settings_button = settings_button
        self.config = config

        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)

        # Titre
        title = QLabel("Vos informations")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #333;")
        layout.addWidget(title)

        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Fonction pour créer un champ centré
        def create_input(label_text, text_value, width=300, height=50):
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
            # centrer le QLineEdit horizontalement
            line_layout = QHBoxLayout()
            line_layout.addStretch()
            line_layout.addWidget(line_edit)
            line_layout.addStretch()
            container.addLayout(line_layout)

            return container, line_edit

        # Prénom
        first_layout, self.first_name_input = create_input(
            "Prénom :", self.config.get("user_firstname", "")
        )
        layout.addLayout(first_layout)

        # Nom
        last_layout, self.last_name_input = create_input(
            "Nom :", self.config.get("user_lastname", "")
        )
        layout.addLayout(last_layout)

        # E-mail
        email_layout, self.email_input = create_input(
            "Adresse e-mail :", self.config.get("user_mail", ""), width=500
        )
        layout.addLayout(email_layout)

        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # === LANGUAGE SELECTION ===
        lang_layout = QHBoxLayout()
        lang_layout.setAlignment(Qt.AlignCenter)

        self.lang_buttons = {}
        for code, icon_file in [("FR", "french.ico"), ("EN", "english.ico"), ("NL", "netherlands.ico")]:
            btn = QPushButton()
            icon_path = os.path.join(BASE_TEMP_PATH, "APP", "ASSETS", icon_file)
            btn.setIcon(QIcon(icon_path))
            btn.setIconSize(QSize(32, 32))
            btn.setCheckable(True)
            btn.setAutoExclusive(True)

            btn.setStyleSheet("""
                QPushButton {
                    border: none;
                    background: transparent;
                    padding: 0px;
                }
                QPushButton:checked {
                    border: 2px solid #eb6134;
                    border-radius: 4px;
                }
            """)
            btn.setFixedSize(32, 32)

            btn.clicked.connect(lambda checked, c=code: self.set_language(c))

            lang_layout.addWidget(btn)
            self.lang_buttons[code] = btn

        # Pré-sélection d’après le JSON ou FR par défaut
        self.lang_buttons[self.config.get("language", "FR")].setChecked(True)
        layout.addLayout(lang_layout)

        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Bouton sauvegarder centré
        self.save_button = CustomPushButton(
            os.path.join(BASE_TEMP_PATH, "APP", "ASSETS", "save.ico"),
            width=150, height=50,
            bg_color="#eb6134", hover_color="#78351f"
        )
        self.save_button.setText("Sauvegarder")
        self.save_button.clicked.connect(self.save_user)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)
        layout.addStretch()

    def set_language(self, code):
        self.config.set("language", code)

    def save_user(self):
        first_name = self.first_name_input.text().strip()
        last_name = self.last_name_input.text().strip()
        email = self.email_input.text().strip()

        if not first_name or not last_name or not email:
            QMessageBox.warning(self, "Erreur", "Tous les champs doivent être remplis !")
            return

        if not is_valid_email(email):
            QMessageBox.warning(self, "Erreur", "Veuillez entrer une adresse e-mail valide !")
            return

        # Sauvegarde dans la config
        self.config.set("user_firstname", first_name)
        self.config.set("user_lastname", last_name)
        self.config.set("user_mail", email)

        self.user_saved.emit()


def is_valid_email(email: str) -> bool:
    return EMAIL_REGEX.match(email) is not None