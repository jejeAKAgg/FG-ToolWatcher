# GUI/Desktop/pages/settings.py
import os

import logging

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QStackedWidget, QFrame, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont

from CORE.Services.setup import *
from CORE.Services.user import UserService
from CORE.Services.translator import TranslatorService

from GUI.Desktop.pages.subpages.settings.general import GeneralPage
from GUI.Desktop.pages.subpages.settings.websites import WebsitesPage
from GUI.Desktop.pages.subpages.settings.profile import ProfilePage
from GUI.Desktop.pages.subpages.settings.system import SystemPage
from GUI.Desktop.pages.subpages.settings.ai import AIPage

from GUI.__ASSETS.widgets.fade_transition import FadeTransition
from GUI.__ASSETS.widgets.push_buttons import CustomPushButton



# ======= LOGGING SYSTEM ========
LOG = logging.getLogger(__name__)
# ===============================

class SettingsPage(QWidget):

    """
    QSide6 widget dedicated to the user settings management.
    It provides a sidebar for navigating between different settings categories and a main area for displaying the corresponding settings pages.
    
    """

    def __init__(self, config: UserService, translator: TranslatorService, parent=None):

        """
        Initializes the SettingsPage UI components and layout.

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
        self.setStyleSheet("background: transparent;")
        
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # === SIDEBAR ===
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(260) 
        self.sidebar.setFrameShape(QFrame.NoFrame)
        self.sidebar.setSpacing(12) 
        self.sidebar.setObjectName("Sidebar")
        
        sidebar_font = QFont("Arial Black", 14)
        sidebar_font.setWeight(QFont.Black)
        self.sidebar.setFont(sidebar_font)

        self.sidebar.setStyleSheet("""
            QListWidget#Sidebar {
                background-color: transparent;
                border: none;
                border-right: 5px solid rgba(0, 0, 0, 1);
                padding-top: 30px;
                outline: none;
            }
            QListWidget#Sidebar::item {
                padding: 12px 20px;
                border-radius: 15px; 
                margin: 0px 15px;
                color: #000000;
                background-color: transparent;
            }
            QListWidget#Sidebar::item:selected {
                background-color: rgba(0, 0, 0, 0.25); 
                color: #000000;
                border: 1px solid rgba(0, 0, 0, 0.05);
                font-size: 16px;
                font-weight: 900;
            }
            QListWidget#Sidebar::item:hover:!selected {
                background-color: rgba(0, 0, 0, 0.15);
                color: #000000;
            }
            QListWidget#Sidebar::item:disabled {
                color: #3c3c3c;
            }
        """)

        # === CONTENT ===
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet("background-color: transparent; border: none;")

        self.transition = FadeTransition(self.content_stack)

        self.subpage_general = GeneralPage(config=self.configs, translator=self.translator, parent=self)
        self.subpage_websites = WebsitesPage(config=self.configs, translator=self.translator, parent=self)
        self.subpage_profile = ProfilePage(self.configs, self.translator, parent=self)
        self.subpage_system = SystemPage(config=self.configs, translator=self.translator, parent=self)
        self.subpage_ai = AIPage(config=self.configs, translator=self.translator, parent=self)

        self.content_stack.addWidget(self.subpage_general)
        self.content_stack.addWidget(self.subpage_websites)
        self.content_stack.addWidget(self.subpage_profile)
        self.content_stack.addWidget(self.subpage_system)
        self.content_stack.addWidget(self.subpage_ai)

        # --- CONTAINER FOR CONTENT OF SUBPAGES ---
        right_container = QVBoxLayout()
        right_container.addWidget(self.content_stack)

        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addLayout(right_container)

        # --- SIDEBAR ITEMS ---
        self.sidebar.addItem("⚙️  " + self.translator.get("subpage_settings_general"))
        self.sidebar.addItem("🌐  " + self.translator.get("subpage_settings_websites"))
        self.sidebar.addItem("👤  " + self.translator.get("subpage_settings_profile"))
        self.sidebar.addItem("💻  " + self.translator.get("subpage_settings_system"))
        self.sidebar.addItem("🤖  " + self.translator.get("subpage_settings_ai"))

        self.sidebar.itemClicked.connect(self._routes)

        self.sidebar.setCurrentRow(0)
        self.content_stack.setCurrentIndex(0)


    # === PUBLIC METHOD(S) ===
    def retranslate_ui(self):
        
        """
        Update the texte of every widget of the application depending the new user language input.
        
        """

        self.sidebar.item(0).setText("⚙️  " + self.translator.get("subpage_settings_general"))
        self.sidebar.item(1).setText("🌐  " + self.translator.get("subpage_settings_websites"))
        self.sidebar.item(2).setText("👤  " + self.translator.get("subpage_settings_profile"))
        self.sidebar.item(3).setText("💻  " + self.translator.get("subpage_settings_system"))
        self.sidebar.item(4).setText("🤖  " + self.translator.get("subpage_settings_ai"))

        self.subpage_general.retranslate_ui()
        self.subpage_websites.retranslate_ui()
        self.subpage_profile.retranslate_ui()
        self.subpage_system.retranslate_ui()
        self.subpage_ai.retranslate_ui()


    # === PRIVATE METHOD(S) ===
    def _routes(self):
        
        """
        Direct routing based on index. 
        This is the closest equivalent to button.clicked for a Sidebar.
        
        """

        index = self.sidebar.currentRow()

        if index == 0: QTimer.singleShot(10, self._toggle_general)
        elif index == 1: QTimer.singleShot(10, self._toggle_websites)
        elif index == 2: QTimer.singleShot(10, self._toggle_profile)
        elif index == 3: QTimer.singleShot(10, self._toggle_system)
        elif index == 4: QTimer.singleShot(10, self._toggle_ai)

    # --- ROUTES ---
    def _toggle_general(self):
        if self.content_stack.currentWidget() != self.subpage_general:
            self.transition.fade_to(self.subpage_general, on_start=lambda: self.sidebar.setEnabled(False), on_finished=lambda: self.sidebar.setEnabled(True))

    def _toggle_websites(self):
        if self.content_stack.currentWidget() != self.subpage_websites:
            self.transition.fade_to(self.subpage_websites, on_start=lambda: self.sidebar.setEnabled(False), on_finished=lambda: self.sidebar.setEnabled(True))

    def _toggle_profile(self):
        if self.content_stack.currentWidget() != self.subpage_profile:
            self.transition.fade_to(self.subpage_profile, on_start=lambda: self.sidebar.setEnabled(False), on_finished=lambda: self.sidebar.setEnabled(True))

    def _toggle_system(self):
        if self.content_stack.currentWidget() != self.subpage_system:
            self.transition.fade_to(self.subpage_system, on_start=lambda: self.sidebar.setEnabled(False), on_finished=lambda: self.sidebar.setEnabled(True))
    
    def _toggle_ai(self):
        if self.content_stack.currentWidget() != self.subpage_ai:
            self.transition.fade_to(self.subpage_ai, on_start=lambda: self.sidebar.setEnabled(False), on_finished=lambda: self.sidebar.setEnabled(True))