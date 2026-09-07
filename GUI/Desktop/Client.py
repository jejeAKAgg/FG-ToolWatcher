# GUI/Desktop/Client.py

import logging
import os

from PySide6 import QtSvg
from PySide6.QtCore import QUrl
from PySide6.QtGui import QCloseEvent, QDesktopServices, QIcon
from PySide6.QtWidgets import QStackedLayout, QVBoxLayout, QWidget

from CORE.Services.setup import *
from CORE.Services.translator import TranslatorService
from CORE.Services.user import UserService

from GUI.Desktop.pages.dashboard import DashboardPage
from GUI.Desktop.pages.profile import ProfilePage
from GUI.Desktop.pages.search import SearchPage
from GUI.Desktop.pages.settings import SettingsPage
from GUI.Desktop.pages.setup import SetupPage

from GUI.__assets.layouts.bottom_buttons import create_bottom_bar
from GUI.__assets.layouts.top_buttons import create_top_bar
from GUI.__assets.layouts.top_header import create_header, create_logo_widget, create_title_widget
from GUI.__assets.widgets.background import BackgroundOverlay
from GUI.__assets.widgets.buttons import LanguageButton, MenuButton, UpdateButton
from GUI.__assets.widgets.transitions import FadeTransition


LOG = logging.getLogger(__name__)

class WatcherGUI(QWidget):

    """
    Main Application Window (GUI) for FG-ToolWatcher.

    Roles:
        Primary application stack
        Manages global navigation
        Language switching
    """

    def __init__(self, config_service: UserService, translator_service: TranslatorService):

        """
        Initializes the main GUI components, styles, and page stack.

        Args:
            config_service (UserService): Instance for handling user data and preferences.
            translator_service (TranslatorService): Instance for handling multi-language support.
        """
        super().__init__()

        # === INTERNAL SERVICE(S) ===
        self.configs = config_service
        self.translator = translator_service

        # === INITIALIZATION ===
        self.translator.load_language(self.configs.get("system_language", "fr"))

        # === UI BUILDER(S) ===
        self._build_ui()
        self._connect_signals()


    # === PUBLIC METHOD(S) ===
    def closeEvent(self, event: QCloseEvent):

        """
        Handles the window close event to ensure threads are stopped.

        This method ensures that any active background processes (such as the
        watcher thread) are gracefully terminated, and that persistent resources
        (like SQLite database connections) are properly closed before the
        application exits. This prevents data corruption, memory leaks, and
        zombie processes.

        Args:
            event (QCloseEvent): The close event object triggered by the system
                                 or user action. It is explicitly accepted
                                 (`event.accept()`) at the end of the method
                                 to authorize the window to close normally.
        """
        LOG.debug("Close event triggered...")

        if hasattr(self, 'main_page') and self.main_page.watcher_thread.isRunning():
            LOG.debug("Watcher thread is running, attempting to stop...")
            self.main_page.stop_watcher()

            if self.main_page.watcher_thread.isRunning():
                 LOG.debug("Warning: Watcher thread still running after stop attempt during close.")

        if hasattr(self, 'search_page') and self.search_page._db_conn:
            LOG.debug("SQLite connection is running, attempting to stop...")
            self.search_page.close_db_connection()
            LOG.debug("SQLite connection closed.")

        LOG.debug("Accepting close event.")
        event.accept()


    def sync_db(self):
        return #TODO

    def toggle_settings(self):
        if self.stack.currentWidget() != self.settings_page:
            self.transition.switch_to(self.settings_page, on_start=lambda: None, on_finished=lambda: self._update_top_buttons())
        elif self.stack.currentWidget() != self.main_page:
            self.transition.switch_to(self.main_page, on_start=lambda: None, on_finished=lambda: self._update_top_buttons())

    def toggle_calibration(self):
        self.transition.switch_to(self.search_page, on_start=lambda: None, on_finished=lambda: self._update_top_buttons())

    def show_docs(self):
        QDesktopServices.openUrl(QUrl("https://github.com/jejeAKAgg/FG-ToolWatcher/wiki"))

    def show_github(self):
        QDesktopServices.openUrl(QUrl("https://github.com/jejeAKAgg/FG-ToolWatcher"))

    def show_ticket(self):
        #TicketService(self.USERconfig, parent=self).exec()
        return

    # === PRIVATE METHOD(S) ===
    def _build_ui(self):

        """
        Constructs the main user interface, including the window settings,
        navigation bars, background, and the page stack.
        """
        LOG.debug("Building Client GUI...")

        # --- Window Settings ---
        self.setWindowTitle("FG-ToolWatcher")
        self.setGeometry(100, 100, 1280, 800)
        self.setFixedSize(1280, 800)

        icon_path = os.path.join(ASSETS_FOLDER, "icons", "FG-TWicoBG.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # --- APP Background ---
        self.background_widget = BackgroundOverlay(
            background_path=os.path.join(ASSETS_FOLDER, "backgrounds", "FGbackground8.jpg"),
            parent=self
        )
        self.background_widget.setGeometry(0, 0, self.width(), self.height())
        self.background_widget.lower()

        # --- TOP BAR & HEADER ---
        self.settings_button = MenuButton(icon_path=os.path.join(ASSETS_FOLDER, "icons", "settings_White.svg"))
        self.sync_button = UpdateButton(icon_path=os.path.join(ASSETS_FOLDER, "icons", "synchronize_White.svg"))
        self.docs_button = MenuButton(icon_path=os.path.join(ASSETS_FOLDER, "icons", "documentation_White.svg"))

        self.english_button = LanguageButton(icon_path=os.path.join(ASSETS_FOLDER, "icons", "english.svg"))
        self.french_button = LanguageButton(icon_path=os.path.join(ASSETS_FOLDER, "icons", "french.svg"))
        self.netherlands_button = LanguageButton(icon_path=os.path.join(ASSETS_FOLDER, "icons", "netherlands.svg"))

        TOP_BAR = create_top_bar(
            left_widgets=[self.settings_button, self.sync_button],
            center_widgets=[self.english_button, self.french_button, self.netherlands_button],
            right_widgets=[self.docs_button]
        )
        HEADER = create_header(
            widgets=["STRETCH", create_logo_widget(os.path.join(ASSETS_FOLDER, "icons", "FG-Black.svg")), create_title_widget("TOOLWATCHER"), "STRETCH"]
        )

        # --- BOTTOM BAR ---
        self.ticket_button = MenuButton(icon_path=os.path.join(ASSETS_FOLDER, "icons", "bug_White.svg"))
        self.github_button = MenuButton(icon_path=os.path.join(ASSETS_FOLDER, "icons", "github_White.svg"))

        BOTTOM_BAR = create_bottom_bar(widgets=[self.ticket_button, "STRETCH", self.github_button])

        # --- INITIAL BUTTON STATE ---
        self.settings_button.setEnabled(False)
        self.sync_button.setEnabled(False)
        self.docs_button.setEnabled(False)
        self.ticket_button.setEnabled(False)
        self.github_button.setEnabled(False)

        # === PAGES & STACK ===
        self.stack = QStackedLayout()
        self.stack_container = QWidget()
        self.transition = FadeTransition(self.stack)

        self.setup_page = SetupPage(config=self.configs, translator=self.translator, parent=self.stack_container)
        self.profile_page = ProfilePage(config=self.configs, translator=self.translator, parent=self.stack_container)
        self.main_page = DashboardPage(config=self.configs, translator=self.translator, parent=self.stack_container)
        self.search_page = SearchPage(config=self.configs, translator=self.translator, parent=self.stack_container)
        self.settings_page = SettingsPage(config=self.configs, translator=self.translator, parent=self.stack_container)

        self.stack.addWidget(self.setup_page)       # index 0
        self.stack.addWidget(self.profile_page)     # index 1
        self.stack.addWidget(self.main_page)        # index 2
        self.stack.addWidget(self.search_page)      # index 3
        self.stack.addWidget(self.settings_page)    # index 4

        self.stack_container.setLayout(self.stack)

        # === MAIN LAYOUT ===
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(20)

        main_layout.addWidget(TOP_BAR)
        main_layout.addWidget(HEADER)
        main_layout.addWidget(self.stack_container)
        main_layout.addWidget(BOTTOM_BAR)

    def _connect_signals(self):

        """
        Connects all UI signals to their respective slot functions.
        """
        LOG.debug("Connecting Client GUI signals...")

        # Navigation
        self.settings_button.clicked.connect(self.toggle_settings)
        self.sync_button.clicked.connect(self.sync_db)
        self.docs_button.clicked.connect(self.show_docs)
        self.ticket_button.clicked.connect(self.show_ticket)
        self.github_button.clicked.connect(self.show_github)

        # Page Transitions
        self.setup_page.setup_finished.connect(
            lambda: self.transition.switch_to(
                self.profile_page if not self.configs.get("user_mail") else self.main_page,
                on_finished=self._update_top_buttons
            )
        )
        self.profile_page.configs_updated.connect(
            lambda: self.transition.switch_to(
                self.main_page,
                on_finished=self._update_top_buttons
            )
        )

        # Language Selection
        self.english_button.clicked.connect(lambda: self._set_language(code="EN"))
        self.french_button.clicked.connect(lambda: self._set_language(code="FR"))
        self.netherlands_button.clicked.connect(lambda: self._set_language(code="NL"))

    def _retranslate_ui(self):

        """
        Function that updates all translatable texts in WatcherGUI and its child pages when the language is changed.

        NOTE: QMessageBox (like function show_info()) do not need to be updated as they read traduction only once it got opened.
        """
        LOG.debug("Retranslating UI...")

        # === Refreshing child pages ===
        self.main_page.retranslate_ui()
        self.profile_page.retranslate_ui()
        self.search_page.retranslate_ui()
        self.settings_page.retranslate_ui()
        self.setup_page.retranslate_ui()

    def _set_language(self, code: str):

        """
        Sets the selected language in the user configuration service.

        Args:
            code (str): The language code (e.g., "FR", "EN").
        """
        LOG.debug("Setting language...")

        # === LOGIC ===
        # --- Setting new Language & Loading it ---
        self.configs.set("language", code)
        self.translator.load_language(code)

        # --- Signal ---
        self._retranslate_ui()

    def _update_top_buttons(self):

        """
        Function that updates all buttons in WatcherGUI and its child pages when a lambda action is made by the user.
        """
        LOG.debug("Updating buttons...")

        current_index = self.stack.currentIndex()
        current_page = self.stack.widget(current_index)
        current_button_state = current_page not in (self.setup_page, self.profile_page)

        self.settings_button.setEnabled(current_button_state)
        self.sync_button.setEnabled(current_button_state)
        self.docs_button.setEnabled(current_button_state)
        self.ticket_button.setEnabled(current_button_state)
        self.github_button.setEnabled(current_button_state)
