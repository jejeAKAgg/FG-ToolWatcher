# APP/pages/SETTINGSpage.py
import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QListWidget, QPushButton,
    QLineEdit, QSpinBox, QLabel, QSpacerItem, QSizePolicy, QComboBox
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize, Qt, Signal

from APP.ASSETS.WIDGETS.PUSHbuttons import CustomPushButton
from APP.SERVICES.__init__ import *

class SettingsPage(QWidget):
    settings_saved = Signal()

    def __init__(self, update_button, profile_button, settings_button, user_config, catalog_config, parent=None):
        super().__init__(parent)

        self.update_button = update_button
        self.profile_button = profile_button 
        self.settings_button = settings_button

        # USER config
        self.user_config = user_config
        self.catalog_config = catalog_config

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10,10,10,10)
        layout.setSpacing(10)

        # === LANGUAGE === #
        lang_layout = QHBoxLayout()
        lang_layout.setAlignment(Qt.AlignCenter)

        self.lang_buttons = {}
        for code, icon_file in [("FR", "french.ico"), ("EN", "english.ico"), ("NL", "netherlands.ico")]:
            btn = QPushButton()
            icon_path = os.path.join(BASE_TEMP_PATH, "APP", "ASSETS", "ICONS", icon_file)
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
                    border: 2px solid #eb6134;  /* optionnel : cadre visible si sélectionné */
                    border-radius: 4px;
                }
            """)
            btn.setFixedSize(32, 32)
            
            btn.clicked.connect(lambda checked, c=code: self.set_language(c))
            
            lang_layout.addWidget(btn)
            self.lang_buttons[code] = btn

        self.lang_buttons[self.user_config.get("language", "FR")].setChecked(True)
        layout.addLayout(lang_layout)

        layout.addSpacerItem(QSpacerItem(0, 50, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # === WEBSITES === #
        self.sites = {
            "CIPAC": "site_CIPAC",
            "CLABOTS": "site_CLABOTS",
            "FERNAND GEORGES": "site_FG",
            "FIXAMI": "site_FIXAMI",
            "KLIUM": "site_KLIUM",
            "LECOT": "site_LECOT"
        }

        sites_layout = QHBoxLayout()
        sites_layout.setSpacing(15)
        sites_layout.setAlignment(Qt.AlignCenter)

        self.site_checkboxes = {}

        # Récupérer la liste des sites à observer depuis le JSON
        selected_sites = self.user_config.get("websites_to_watch", [])

        for name, key in self.sites.items():
            cb = QCheckBox(name)
            cb.setChecked(name in selected_sites)   # <-- ici on utilise le nom affiché
            cb.setStyleSheet("""
                QCheckBox {
                    spacing: 5px;
                    padding: 4px 8px;
                    border-radius: 6px;
                    color: #000000;
                    font-weight: bold; 
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                }
                QCheckBox::indicator:checked {
                    background-color: #007e2d;
                    border-radius: 6px;
                }
                QCheckBox:hover {
                    background-color: #f5f5f5;
                }
            """)
            self.site_checkboxes[key] = cb
            sites_layout.addWidget(cb)


        layout.addLayout(sites_layout)

        layout.addSpacerItem(QSpacerItem(0, 50, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # === EMAILS & CACHE === #
        self.cache_options = {
            "1 jour": 1,
            "3 jours": 3,
            "7 jours": 7,
            "14 jours": 14
        }

        # Checkbox
        self.check_send_email = QCheckBox("Envoyer les résultats par mail")
        self.check_send_email.setChecked(self.user_config.get("send_email", False))
        self.check_send_email.setStyleSheet("""
            QCheckBox {
                spacing: 5px;
                padding: 4px 8px;
                border-radius: 6px;
                color: #000000;        /* texte noir */
                font-weight: bold; 
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:checked {
                background-color: #007e2d;
                border-radius: 6px;
            }
            QCheckBox:hover {
                background-color: #f5f5f5;
            }
        """)

        self.cache_duration = QComboBox()
        self.cache_label = QLabel("Durée du cache (jours)")
        self.cache_label.setStyleSheet("color: #000000; font-weight: bold;")
        self.cache_duration.addItems(list(self.cache_options.keys()))
        self.cache_duration.setFixedWidth(120)  # largeur plus courte
        self.cache_duration.setFixedHeight(30)
        self.cache_duration.setStyleSheet("""
            QComboBox {
                padding: 4px 8px;
                border-radius: 6px;
                border: 1px solid #ccc;
                font-size: 14px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #ccc;
                selection-background-color: #eb6134;
            }
        """)

        # Définir la valeur actuelle en fonction du .json
        current_value = self.user_config.get("cache_duration", 1)  # valeur int
        # Chercher le texte correspondant
        for text, val in self.cache_options.items():
            if val == current_value:
                self.cache_duration.setCurrentText(text)
                break

        wrapper_layout = QHBoxLayout()
        wrapper_layout.addStretch()
        wrapper_layout.addWidget(self.check_send_email)
        wrapper_layout.addWidget(self.cache_duration)
        wrapper_layout.addWidget(self.cache_label)
        wrapper_layout.addStretch()

        layout.addLayout(wrapper_layout)

        layout.addSpacerItem(QSpacerItem(0, 50, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # -------------------
        # BOUTON SAVE
        # -------------------
        # Bouton sauvegarder centré
        self.save_button = CustomPushButton(
            os.path.join(BASE_TEMP_PATH, "APP", "ASSETS", "ICONS", "save.ico"),
            width=150, height=50,
            bg_color="#eb6134", hover_color="#78351f"
        )
        self.save_button.setText("Sauvegarder")
        self.save_button.clicked.connect(self.save_settings)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)
        layout.addStretch()

    # -------------------
    # LANGUE
    # -------------------
    def set_language(self, code):
        self.user_config.set("language", code)

    # -------------------
    # SAVE SETTINGS
    # -------------------
    def save_settings(self):

        # WEBSITES
        selected_sites = []
        for name, key in self.sites.items():   
            if self.site_checkboxes[key].isChecked():
                selected_sites.append(name)
        self.user_config.set("websites_to_watch", selected_sites)

        # EMAILS + CACHE
        self.user_config.set("cache_duration", self.cache_options[self.cache_duration.currentText()])
        self.user_config.set("send_email", self.check_send_email.isChecked())

        self.settings_saved.emit()