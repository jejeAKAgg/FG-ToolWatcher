# GUI/Desktop/pages/settings.py

import logging
import os

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QListWidget, QListWidgetItem,
    QStackedWidget, QVBoxLayout, QWidget
)

from CORE.Services.setup import ASSETS_FOLDER
from CORE.Services.translator import TranslatorService
from CORE.Services.user import UserService

from GUI.Desktop.pages.subpages.settings.ai import AIPage
from GUI.Desktop.pages.subpages.settings.general import GeneralPage
from GUI.Desktop.pages.subpages.settings.profile import ProfilePage
from GUI.Desktop.pages.subpages.settings.system import SystemPage
from GUI.Desktop.pages.subpages.settings.websites import WebsitesPage
from GUI.__assets.widgets.transitions import FadeTransition

LOG = logging.getLogger(__name__)

class SettingsPage(QWidget):

    """
    QSide6 widget dedicated to user settings management.
    Provides a sidebar for navigating between different settings categories
    and a main area for displaying the corresponding configuration subpages.
    """

    def __init__(self, config: UserService, translator: TranslatorService, parent: QWidget | None = None):

        """
        Initializes the SettingsPage UI components and layout.

        Args:
            config (UserService): The service instance for managing user settings.
            translator (TranslatorService): The service instance for managing translations.
            parent (Optional[QWidget]): The parent widget.
        """
        super().__init__(parent)

        # === INTERNAL SERVICE(S) ===
        self.configs = config
        self.translator = translator

        # === UI BUILDER(S) ===
        self._build_ui()
        self._apply_stylesheet()
        self._connect_signals()

    # === PUBLIC METHOD(S) ===
    def retranslate_ui(self):

        """
        Updates the text of every widget of the application depending on the new user language input.
        """
        LOG.debug("Retranslating UI in SettingsPage...")

        self.sidebar.item(0).setText(self.translator.get("page_settings_general.category"))
        self.sidebar.item(1).setText(self.translator.get("page_settings_websites.category"))
        self.sidebar.item(2).setText(self.translator.get("page_settings_profile.category"))
        self.sidebar.item(3).setText(self.translator.get("page_settings_system.category"))
        self.sidebar.item(4).setText(self.translator.get("page_settings_AI.category"))

        self.subpage_general.retranslate_ui()
        self.subpage_websites.retranslate_ui()
        self.subpage_profile.retranslate_ui()
        self.subpage_system.retranslate_ui()
        self.subpage_ai.retranslate_ui()

    # === PRIVATE METHOD(S) ===
    def _build_ui(self):

        """
        Constructs the main layout, sidebar navigation, and the stacked widget for subpages.
        """
        LOG.debug("Building UI for SettingsPage...")

        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # --- SIDEBAR ---
        self.sidebar = QListWidget()
        self.sidebar.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.sidebar.setFixedWidth(260)
        self.sidebar.setFrameShape(QFrame.Shape.NoFrame)
        self.sidebar.setSpacing(10)
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setIconSize(QSize(30, 30))

        sidebar_font = QFont("Arial Black", 15)
        sidebar_font.setWeight(QFont.Weight.Black)
        self.sidebar.setFont(sidebar_font)

        # --- CONTENT STACK ---
        self.content_stack = QStackedWidget()
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

        # --- CONTAINER ASSEMBLY ---
        right_container = QVBoxLayout()
        right_container.addWidget(self.content_stack)

        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addLayout(right_container)

        # --- POPULATE SIDEBAR ---
        sidebar_pages = [
            ("general_Black.svg", self.translator.get("page_settings_general.category")),
            ("websites_Black.svg", self.translator.get("page_settings_websites.category")),
            ("profile_Black.svg", self.translator.get("page_settings_profile.category")),
            ("system_Black.svg", self.translator.get("page_settings_system.category")),
            ("ai_Black.svg", self.translator.get("page_settings_AI.category")),
        ]

        for icon_file, label in sidebar_pages:
            item = QListWidgetItem(label)
            icon_path = os.path.join(ASSETS_FOLDER, "icons", icon_file)
            if os.path.exists(icon_path):
                item.setIcon(QIcon(icon_path))
            self.sidebar.addItem(item)

        self.sidebar.setCurrentRow(0)
        self.content_stack.setCurrentIndex(0)

    def _apply_stylesheet(self):

        """
        Applies CSS styling to the Settings page and its sidebar.
        """
        self.setStyleSheet("background: transparent;")
        self.content_stack.setStyleSheet("background-color: transparent; border: none;")

        self.sidebar.setStyleSheet("""
            QListWidget#Sidebar {
                background-color: transparent;
                border: none;
                border-right: 5px solid rgba(0, 0, 0, 1);
                padding-top: 30px;
                outline: none;
            }
            QListWidget#Sidebar::item {
                padding: 10px 20px;
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

    def _connect_signals(self):

        """
        Connects sidebar navigation signals.
        """
        self.sidebar.itemClicked.connect(self._routes)

    def _routes(self):

        """
        Direct routing based on the selected sidebar index.
        """
        index = self.sidebar.currentRow()

        if index == 0: QTimer.singleShot(10, self._toggle_general)
        elif index == 1: QTimer.singleShot(10, self._toggle_websites)
        elif index == 2: QTimer.singleShot(10, self._toggle_profile)
        elif index == 3: QTimer.singleShot(10, self._toggle_system)
        elif index == 4: QTimer.singleShot(10, self._toggle_ai)

    # --- ROUTING TRANSITIONS ---
    def _toggle_general(self):
        if self.content_stack.currentWidget() != self.subpage_general:
            self.transition.switch_to(self.subpage_general, on_start=lambda: self.sidebar.setEnabled(False), on_finished=lambda: self.sidebar.setEnabled(True))

    def _toggle_websites(self):
        if self.content_stack.currentWidget() != self.subpage_websites:
            self.transition.switch_to(self.subpage_websites, on_start=lambda: self.sidebar.setEnabled(False), on_finished=lambda: self.sidebar.setEnabled(True))

    def _toggle_profile(self):
        if self.content_stack.currentWidget() != self.subpage_profile:
            self.transition.switch_to(self.subpage_profile, on_start=lambda: self.sidebar.setEnabled(False), on_finished=lambda: self.sidebar.setEnabled(True))

    def _toggle_system(self):
        if self.content_stack.currentWidget() != self.subpage_system:
            self.transition.switch_to(self.subpage_system, on_start=lambda: self.sidebar.setEnabled(False), on_finished=lambda: self.sidebar.setEnabled(True))

    def _toggle_ai(self):
        if self.content_stack.currentWidget() != self.subpage_ai:
            self.transition.switch_to(self.subpage_ai, on_start=lambda: self.sidebar.setEnabled(False), on_finished=lambda: self.sidebar.setEnabled(True))
