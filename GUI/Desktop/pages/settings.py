# GUI/Desktop/pages/settings.py
import os

import logging

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel, QSpacerItem,
    QSizePolicy, QComboBox
)
from PySide6.QtCore import Qt, Signal

from CORE.Services.setup import *
from CORE.Services.user import UserService
from CORE.Services.translator import TranslatorService

from GUI.__ASSETS.widgets.push_buttons import CustomPushButton



# ======= LOGGING SYSTEM ========
LOG = logging.getLogger(__name__)
# ===============================

class SettingsPage(QWidget):
    
    """
    QSide6 widget that allows users to modify language, site tracking, and general app options.
    """
    
    settings_saved = Signal()
    language_changed = Signal()

    def __init__(self, config: UserService, translator: TranslatorService, parent=None):
        super().__init__(parent)

        # === INTERNAL VARIABLE(S) ===
        self.configs = config
        self.translator = translator

        # === MAIN LAYOUT ===
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(25)
        layout.setAlignment(Qt.AlignTop)

        layout.addSpacerItem(QSpacerItem(0, 30, QSizePolicy.Minimum, QSizePolicy.Fixed))

        
        # =====================================================
        #                       WEBSITES
        # =====================================================
        sites_layout = QHBoxLayout()
        sites_layout.setAlignment(Qt.AlignCenter)
        sites_layout.setSpacing(15)

        self.sites = {
            "CIPAC": "site_CIPAC",
            "CLABOTS": "site_CLABOTS",
            "GEORGES": "site_FG",
            "FIXAMI": "site_FIXAMI",
            "KLIUM": "site_KLIUM",
            "LECOT": "site_LECOT"
        }

        self.site_checkboxes = {}
        selected_sites = self.configs.get("websites_to_watch", [])

        for name, key in self.sites.items():
            cb = QCheckBox(name)
            cb.setChecked(name in selected_sites)
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

        layout.addSpacerItem(QSpacerItem(0, 30, QSizePolicy.Minimum, QSizePolicy.Fixed))

        
        # =====================================================
        #                  EMAILS & CACHE DURATION
        # =====================================================
        self.cache_options = {
            self.translator.get("page_settings_0day"): 0,
            self.translator.get("page_settings_1day"): 1,
            self.translator.get("page_settings_3days"): 3,
            self.translator.get("page_settings_7days"): 7,
            self.translator.get("page_settings_14days"): 14
        }

        wrapper_layout = QHBoxLayout()
        wrapper_layout.setAlignment(Qt.AlignCenter)
        wrapper_layout.setSpacing(10)

        # Email checkbox
        self.check_send_email = QCheckBox(self.translator.get("page_settings_send_email"))
        self.check_send_email.setChecked(self.configs.get("send_email", False))
        self.check_send_email.setStyleSheet("""
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

        # Cache duration
        self.cache_duration = QComboBox()
        self.cache_duration.addItems(list(self.cache_options.keys()))
        self.cache_duration.setFixedWidth(120)
        self.cache_duration.setFixedHeight(30)
        self.cache_duration.setStyleSheet("""
            QComboBox {
                padding: 4px 8px;
                border-radius: 6px;
                border: 1px solid #ccc;
                font-size: 14px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #ccc;
                selection-background-color: #eb6134;
            }
        """)

        self.cache_label = QLabel(self.translator.get("page_settings_cache_title"))
        self.cache_label.setStyleSheet("color: #000000; font-weight: bold;")

        # Définir valeur actuelle
        current_value = self.configs.get("cache_duration", 1)
        for text, val in self.cache_options.items():
            if val == current_value:
                self.cache_duration.setCurrentText(text)
                break

        wrapper_layout.addWidget(self.check_send_email)
        wrapper_layout.addWidget(self.cache_duration)
        wrapper_layout.addWidget(self.cache_label)

        layout.addLayout(wrapper_layout)

        layout.addSpacerItem(QSpacerItem(0, 40, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # =====================================================
        #                        SAVE BUTTON
        # =====================================================
        save_layout = QHBoxLayout()
        save_layout.setAlignment(Qt.AlignCenter)

        self.save_button = CustomPushButton(
            os.path.join(ASSETS_FOLDER, "icons", "save.ico"),
            width=150, height=50,
            bg_color="#eb6134", hover_color="#78351f"
        )
        self.save_button.setText(self.translator.get("save.button"))
        self.save_button.clicked.connect(self.save_settings)

        save_layout.addWidget(self.save_button)
        layout.addLayout(save_layout)
        layout.addStretch()


    # =====================================================
    #                     FUNCTIONS
    # =====================================================
    def save_settings(self):
        selected_sites = [name for name, key in self.sites.items() if self.site_checkboxes[key].isChecked()]
        self.configs.set("websites_to_watch", selected_sites)
        self.configs.set("cache_duration", self.cache_options[self.cache_duration.currentText()])    
        self.configs.set("send_email", self.check_send_email.isChecked())
        
        self.settings_saved.emit()
    
    def retranslate_ui(self):
        
        """
        Update the texte of every widget of the application depending the new user language input.
        """

        current_value_key = self.cache_duration.currentText()
        current_value = self.cache_options.get(current_value_key, self.configs.get("cache_duration", 1))

        self.cache_options = {
            self.translator.get("page_settings_0day"): 0,
            self.translator.get("page_settings_1day"): 1,
            self.translator.get("page_settings_3days"): 3,
            self.translator.get("page_settings_7days"): 7,
            self.translator.get("page_settings_14days"): 14
        }
        
        self.cache_duration.clear()
        self.cache_duration.addItems(list(self.cache_options.keys()))

        for text, val in self.cache_options.items():
            if val == current_value:
                self.cache_duration.setCurrentText(text)
                break
        
        self.check_send_email.setText(self.translator.get("page_settings_send_email"))
        self.cache_label.setText(self.translator.get("page_settings_cache_title"))
        self.save_button.setText(self.translator.get("save.button"))