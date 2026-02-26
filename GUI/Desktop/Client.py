# GUI/Desktop/Client.py
import os

import logging

from PySide6.QtCore import QUrl
from PySide6.QtGui import QIcon, QDesktopServices, QCloseEvent
from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedLayout, QMessageBox

from CORE.Services.setup import *
from CORE.Services.user import UserService
from CORE.Services.translator import TranslatorService

from GUI.Desktop.pages.setup import SetupPage
from GUI.Desktop.pages.menu import MainPage
from GUI.Desktop.pages.profile import ProfilePage
from GUI.Desktop.pages.search import SearchPage
from GUI.Desktop.pages.settings import SettingsPage

from GUI.__ASSETS.layouts.bottom_buttons import create_bottom_buttons
from GUI.__ASSETS.layouts.top_buttons import create_top_buttons
from GUI.__ASSETS.layouts.top_header import create_top_header

from GUI.__ASSETS.widgets.background_overlay import BackgroundOverlay
from GUI.__ASSETS.widgets.fade_transition import FadeTransition
from GUI.__ASSETS.widgets.push_buttons import CustomPushButton



# ======= LOGGING SYSTEM ========
LOG = logging.getLogger(__name__)
# ===============================

class WatcherGUI(QWidget):

    """
    Main Application Window (GUI) for FG-ToolWatcher.
    Manages global navigation, language switching, and the primary application stack.
    """

    def __init__(self, config_service: UserService, translator_service: TranslatorService):

        """
        Initializes the main GUI components, styles, and page stack.

        Args:
            config_service (UserService): Instance for handling user data and preferences.
            translator_service (TranslatorService): Instance for handling multi-language support.
        """

        super().__init__()

        # === INPUT VARIABLE(S) ===
        self.configs = config_service
        self.translator = translator_service
        
        # === INTERNAL VARIABLE(S) ===
        self.translator.load_language(self.configs.get("language", "en"))

        # === WINDOW SETTINGS ===
        self.setWindowTitle("FG-ToolWatcher")
        self.setGeometry(300, 300, 1000, 700)
        self.setFixedSize(1000, 700)

        # --- Window ICON ---
        icon_path = os.path.join(ASSETS_FOLDER, "icons", "FG-TWicoBG.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # --- APP Background ---
        self.background_widget = BackgroundOverlay(
            bg_path=os.path.join(ASSETS_FOLDER, "icons", "FGbackground.jpg"),
            parent=self
        )
        self.background_widget.setGeometry(0, 0, self.width(), self.height())
        self.background_widget.lower()

        # --- TOP BAR & HEADER ---
        self.settings_button = CustomPushButton(icon_path=os.path.join(ASSETS_FOLDER, "icons", "settings.ico"), icon_size_width=35, icon_size_height=35, width=100, height=50, bg_color="#818386", hover_color="#6d6e70", text_color="#FFFFFF", alpha=0.5)
        self.update_button = CustomPushButton(icon_path=os.path.join(ASSETS_FOLDER, "icons", "update.ico"))
        self.profile_button = CustomPushButton(icon_path=os.path.join(ASSETS_FOLDER, "icons", "profile.ico"))

        self.english_button = CustomPushButton(icon_path=os.path.join(ASSETS_FOLDER, "icons", "english.ico"), width=55, height=35, bg_color='#818386', hover_color='#6d6e70',  text_color="#FFFFFF", alpha=0.5)
        self.french_button = CustomPushButton(icon_path=os.path.join(ASSETS_FOLDER, "icons", "french.ico"), width=55, height=35, bg_color='#818386', hover_color='#6d6e70', text_color="#FFFFFF", alpha=0.5)
        self.netherlands_button = CustomPushButton(icon_path=os.path.join(ASSETS_FOLDER, "icons", "netherlands.ico"), width=55, height=35, bg_color='#818386', hover_color='#6d6e70', text_color="#FFFFFF", alpha=0.5)

        self.update_button.setToolTip(self.translator.get("tip_update.button"))
        self.profile_button.setToolTip(self.translator.get("tip_profile.button"))
        self.settings_button.setToolTip(self.translator.get("tip_settings.button"))
        
        self.update_button.clicked.connect(self.toggle_setup)
        self.profile_button.clicked.connect(self.toggle_profile)
        self.settings_button.clicked.connect(self.toggle_settings)

        TOP_BAR = create_top_buttons(update_button=self.update_button, profile_button=self.profile_button, settings_button=self.settings_button, english_button=self.english_button, french_button=self.french_button, netherlands_button=self.netherlands_button)
        HEADER = create_top_header("FG-ToolWatcher", os.path.join(ASSETS_FOLDER, "icons", "FG-TWicoBG.ico"))

        # --- BOTTOM BAR ---
        self.info_button = CustomPushButton(icon_path=os.path.join(ASSETS_FOLDER, "icons", "info.ico"))
        self.ticket_button = CustomPushButton(icon_path=os.path.join(ASSETS_FOLDER, "icons", "problem.ico"), icon_size_width=35, icon_size_height=35, width=100, height=50, bg_color="#818386", hover_color="#6d6e70", text_color="#FFFFFF", alpha=0.5)
        self.github_button = CustomPushButton(icon_path=os.path.join(ASSETS_FOLDER, "icons", "github.ico"), icon_size_width=35, icon_size_height=35, width=100, height=50, bg_color="#818386", hover_color="#6d6e70", text_color="#FFFFFF", alpha=0.5)

        self.info_button.setToolTip(self.translator.get("tip_info.button"))
        self.ticket_button.setToolTip(self.translator.get("tip_ticket.button"))
        self.github_button.setToolTip(self.translator.get("tip_github.button"))

        self.info_button.clicked.connect(lambda: self.show_info())
        self.ticket_button.clicked.connect(lambda: self.show_ticket())
        self.github_button.clicked.connect(lambda: self.show_github())

        BOTTOM_BAR = create_bottom_buttons(info_button=self.info_button, ticket_button=self.ticket_button, github_button=self.github_button)

        # --- BUTTONS STATE (top disabled by default) ---
        self.settings_button.setEnabled(False)  
        self.update_button.setEnabled(False)
        self.profile_button.setEnabled(False)
        
        # === PAGES ===
        self.stack = QStackedLayout()
        self.stack_container = QWidget()

        self.transition = FadeTransition(self.stack)

        self.setup_page = SetupPage(config=self.configs, translator=self.translator, parent=self.stack_container)
        self.profile_page = ProfilePage(config=self.configs, translator=self.translator, parent=self.stack_container)
        self.main_page = MainPage(config=self.configs, translator=self.translator, parent=self.stack_container)
        self.search_page = SearchPage(config=self.configs, translator=self.translator, parent=self.stack_container)
        self.settings_page = SettingsPage(config=self.configs, translator=self.translator, parent=self.stack_container)

        self.setup_page.setup_finished.connect(lambda: self.transition.fade_to(self.profile_page if not self.configs.get("user_mail") else self.main_page, on_finished=lambda: self._update_top_buttons()))
        self.profile_page.configs_updated.connect(lambda: self.transition.fade_to(self.main_page, on_finished=lambda: self._update_top_buttons()))

        self.stack.addWidget(self.setup_page)       # index 0
        self.stack.addWidget(self.profile_page)     # index 1
        self.stack.addWidget(self.main_page)        # index 2
        self.stack.addWidget(self.search_page)      # index 3
        self.stack.addWidget(self.settings_page)    # index 4

        self.stack_container.setLayout(self.stack)

        # === MAIN Layout ===
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(20)
        
        main_layout.addWidget(TOP_BAR)
        main_layout.addWidget(HEADER)
        main_layout.addWidget(self.stack_container)
        main_layout.addWidget(BOTTOM_BAR)

        # === ACTIONS ===
        # --- GLOBAL ---
        self.english_button.clicked.connect(lambda: self._set_language(code="EN"))
        self.french_button.clicked.connect(lambda: self._set_language(code="FR"))
        self.netherlands_button.clicked.connect(lambda: self._set_language(code="NL"))

        # --- Menu Page ---
        self.main_page.calibrate_button.clicked.connect(self.toggle_calibration)
        self.main_page.start_button.clicked.connect(self._update_top_buttons)
        self.main_page.stop_button.clicked.connect(self._update_top_buttons)


    # === PUBLIC METHOD(S) ===
    def closeEvent(self, event: QCloseEvent):
        
        """
        Handles the window close event to ensure threads are stopped.
        """
        
        LOG.debug("[WatcherGUI] Close event triggered.")
        
        if hasattr(self, 'main_page') and self.main_page.watcher_thread.isRunning():
            LOG.debug("[WatcherGUI] Watcher thread is running, attempting to stop...")
            self.main_page.stop_watcher()

            if self.main_page.watcher_thread.isRunning():
                 LOG.debug("[WatcherGUI] Warning: Watcher thread still running after stop attempt during close.")

        LOG.debug("[WatcherGUI] Accepting close event.")
        event.accept()

    def toggle_settings(self):        
        if self.stack.currentIndex() == 2:
            self.transition.fade_to(self.settings_page, on_start=lambda: None, on_finished=lambda: self._update_top_buttons())
        else:
            self.transition.fade_to(self.main_page, on_start=lambda: None, on_finished=lambda: self._update_top_buttons())

    def toggle_setup(self):
        self.setup_page.start_setup()
        self.transition.fade_to(self.setup_page, on_start=lambda: None, on_finished=lambda: self._update_top_buttons())

    def toggle_profile(self):
        if self.stack.currentIndex() == 2:
            self.transition.fade_to(self.profile_page, on_start=lambda: None, on_finished=lambda: self._update_top_buttons())
        else:
            self.transition.fade_to(self.main_page, on_start=lambda: None, on_finished=lambda: self._update_top_buttons())

    def toggle_calibration(self):
        self.transition.fade_to(self.search_page, on_start=lambda: None, on_finished=lambda: self._update_top_buttons())


    def show_info(self):
        QMessageBox.information(self, self.translator.get("box_info_type.text"), self.translator.get("credits.text"))
    
    def show_ticket(self):
        #TicketService(self.USERconfig, parent=self).exec()
        return
    
    def show_github(self):
        QDesktopServices.openUrl(QUrl("https://github.com/jejeAKAgg/FG-ToolWatcher"))
    

    # === PRIVATE METHOD(S) ===
    def _set_language(self, code: str):
        
        """
        Sets the selected language in the user configuration service.

        Args:
            code (str): The language code (e.g., "FR", "EN").
        """
        
        # === LOGIC ===
        # --- Setting new Language & Loading it ---
        self.configs.set("language", code)
        self.translator.load_language(code)
        
        # --- Signal ---
        self._retranslate_ui()

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

        # === Refreshing tooltips of top/bottom buttons ===
        self.update_button.setToolTip(self.translator.get("tip_update.button"))
        self.profile_button.setToolTip(self.translator.get("tip_profile.button"))
        self.settings_button.setToolTip(self.translator.get("tip_settings.button"))

        self.info_button.setToolTip(self.translator.get("tip_info.button"))
        self.ticket_button.setToolTip(self.translator.get("tip_ticket.button"))
        self.github_button.setToolTip(self.translator.get("tip_github.button"))

    def _update_top_buttons(self):

        """
        Function that updates all buttons in WatcherGUI and its child pages when a lambda action is made by the user.
        """

        LOG.debug("Updating buttons...")

        current_index = self.stack.currentIndex()
        current_page = self.stack.widget(current_index)

        if current_page == self.main_page:               # menu_page
            self.profile_button.setEnabled(True)
            self.profile_button.setText("")
            self.settings_button.setEnabled(True)
            self.settings_button.setText("")
            self.update_button.setEnabled(True)
        elif current_page == self.profile_page:          # profile_page 
            if self.configs.get("user_mail"):
                self.profile_button.setEnabled(True)
                self.profile_button.setText("Menu")
                self.settings_button.setEnabled(False)
                self.update_button.setEnabled(False)
            else:
                self.profile_button.setEnabled(False)
                self.settings_button.setEnabled(False)
                self.settings_button.setText("")
                self.update_button.setEnabled(False)
        elif current_page == self.search_page:           # search_page
            self.settings_button.setEnabled(True)
            self.settings_button.setText("Menu")
            self.update_button.setEnabled(False)
            self.profile_button.setEnabled(False)
        elif current_page == self.settings_page:         # settings_page
            self.profile_button.setEnabled(False)
            self.settings_button.setEnabled(True)
            self.settings_button.setText("Menu")
            self.update_button.setEnabled(False)
        elif current_page == self.setup_page:            # setup_page
            self.profile_button.setEnabled(False)
            self.settings_button.setEnabled(False)
            self.settings_button.setText("")
            self.update_button.setEnabled(False)
        else:                                            # Other pages
            self.update_button.setEnabled(True)
            self.settings_button.setText("")
            self.profile_button.setEnabled(True)
            self.settings_button.setEnabled(True)