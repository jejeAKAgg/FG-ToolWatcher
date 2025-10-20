import os
import sys

from PySide6.QtCore import QUrl
from PySide6.QtGui import QIcon, QDesktopServices
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QStackedLayout, QMessageBox

# IMPORTING SERVICES AND UTILS FIRST
from APP.SERVICES.__init__ import *
from APP.SERVICES.CATALOGservice import CatalogService
from APP.SERVICES.LOGservice import LogService
from APP.SERVICES.TICKETservice import TicketService
from APP.SERVICES.USERservice import UserService

from APP.UTILS.TOOLSbox import *

from APP.PAGES.MAINpage import *
from APP.PAGES.CATALOGpage import *
from APP.PAGES.PROFILEpage import *
from APP.PAGES.SETTINGSpage import *
from APP.PAGES.SETUPpage import *

from APP.ASSETS.LAYOUTS.BOTTOMbuttons import create_bottom_buttons
from APP.ASSETS.LAYOUTS.TOPbuttons import create_top_buttons
from APP.ASSETS.LAYOUTS.TOPheader import create_header

from APP.ASSETS.WIDGETS.FADEtransition import FadeTransition
from APP.ASSETS.WIDGETS.MAINbackground import BackgroundOverlay
from APP.ASSETS.WIDGETS.PUSHbuttons import CustomPushButton



# ===================
#     MAIN CLASS
# ===================
class WatcherGUI(QWidget):
    def __init__(self):
        super().__init__()
        
        self.USERconfig = UserService(USER_CONFIG_PATH)
        self.CATALOGconfig = CatalogService(CATALOG_CONFIG_PATH)
        
        self.setWindowTitle("FG-ToolWatcher")
        self.setGeometry(300, 300, 1000, 700)
        self.setFixedSize(1000, 700)

        # === Window ICON === 
        icon_path = os.path.join(BASE_TEMP_PATH, "APP", "ASSETS", "ICONS", "FG-TWicoBG.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # === APP Background ===
        self.background_widget = BackgroundOverlay(
            bg_path=os.path.join(BASE_TEMP_PATH, "APP", "ASSETS", "ICONS", "FGbackground.jpg"),
            parent=self
        )
        self.background_widget.setGeometry(0, 0, self.width(), self.height())
        self.background_widget.lower()

        # === TOP BAR & HEADER ===
        self.update_button = CustomPushButton(os.path.join(BASE_TEMP_PATH, "APP", "ASSETS", "ICONS", "update.ico"), tip="Mise à jour")
        self.profile_button = CustomPushButton(os.path.join(BASE_TEMP_PATH, "APP", "ASSETS", "ICONS", "profile.ico"), tip="Profil")
        self.settings_button = CustomPushButton(os.path.join(BASE_TEMP_PATH, "APP", "ASSETS", "ICONS", "settings.ico"), tip="Paramètres")
        
        self.update_button.clicked.connect(self.toggle_setup)
        self.profile_button.clicked.connect(self.toggle_profile)
        self.settings_button.clicked.connect(self.toggle_settings)

        TOP_BAR = create_top_buttons(self.update_button, self.profile_button, self.settings_button)
        HEADER = create_header("FG-ToolWatcher", os.path.join(BASE_TEMP_PATH, "APP", "ASSETS", "ICONS", "FG-TWicoBG.ico"))

        # === BOTTOM BAR ===
        self.info_button = CustomPushButton(os.path.join(BASE_TEMP_PATH, "APP", "ASSETS", "ICONS", "info.ico"), tip="À propos")
        self.ticket_button = CustomPushButton(os.path.join(BASE_TEMP_PATH, "APP", "ASSETS", "ICONS", "problem.ico"), tip="Signaler un problème")
        self.github_button = CustomPushButton(os.path.join(BASE_TEMP_PATH, "APP", "ASSETS", "ICONS", "github.ico"), tip="GitHub")

        self.info_button.clicked.connect(lambda: self.show_info(version="V0.1"))
        self.ticket_button.clicked.connect(lambda: self.show_ticket())
        self.github_button.clicked.connect(lambda: self.show_github())

        BOTTOM_BAR = create_bottom_buttons(self.info_button, self.ticket_button, self.github_button)

        # === BUTTONS STATE (top disabled by default) ===
        self.settings_button.setEnabled(False)  
        self.update_button.setEnabled(False)
        self.profile_button.setEnabled(False)
        
        # === PAGES ===
        self.stack = QStackedLayout()
        self.stack_container = QWidget()

        self.transition = FadeTransition(self.stack)

        self.setup_page = SetupPage(update_button=self.update_button, profile_button=self.profile_button, settings_button=self.settings_button, user_config=self.USERconfig, catalog_config=self.CATALOGconfig, parent=self.stack_container)
        self.profile_page = ProfilePage(update_button=self.update_button, profile_button=self.profile_button, settings_button=self.settings_button, user_config=self.USERconfig, catalog_config=self.CATALOGconfig, parent=self.stack_container)
        self.main_page = MainPage(update_button=self.update_button, profile_button=self.profile_button, settings_button=self.settings_button, user_config=self.USERconfig, catalog_config=self.CATALOGconfig, parent=self.stack_container)
        self.catalog_page = CatalogPage(update_button=self.update_button, profile_button=self.profile_button, settings_button=self.settings_button, user_config=self.USERconfig, catalog_config=self.CATALOGconfig, parent=self.stack_container)
        self.settings_page = SettingsPage(update_button=self.update_button, profile_button=self.profile_button, settings_button=self.settings_button, user_config=self.USERconfig, catalog_config=self.CATALOGconfig, parent=self.stack_container)

        self.setup_page.setup_finished.connect(lambda: self.transition.fade_to(self.profile_page if not self.USERconfig.get("user_mail") else self.main_page, on_finished=lambda: self._update_top_buttons()))
        self.profile_page.user_saved.connect(lambda: self.transition.fade_to(self.main_page, on_finished=lambda: self._update_top_buttons()))
        self.settings_page.settings_saved.connect(lambda: self.transition.fade_to(self.main_page, on_finished=lambda: self._update_top_buttons()))

        self.main_page.calibrate_button.clicked.connect(self.toggle_calibration)

        self.stack.addWidget(self.setup_page)       # index 0
        self.stack.addWidget(self.profile_page)     # index 1
        self.stack.addWidget(self.main_page)        # index 2
        self.stack.addWidget(self.catalog_page)     # index 3
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
        
        main_layout.addStretch()


    # === FUNCTIONS ===
    def toggle_settings(self):        
        if self.stack.currentIndex() == 2:
            self.transition.fade_to(self.settings_page, on_finished=lambda: self._update_top_buttons())
        else:
            self.transition.fade_to(self.main_page, on_finished=lambda: self._update_top_buttons())

    def toggle_setup(self):
        self.setup_page.label.setText("Préparation de l'application...")
        self.setup_page.start_setup()
        self.transition.fade_to(self.setup_page, on_finished=lambda: self._update_top_buttons())

    def toggle_profile(self):
        self.transition.fade_to(self.profile_page, on_finished=lambda: self._update_top_buttons())

    def toggle_calibration(self):
        self.transition.fade_to(self.catalog_page, on_start=lambda: self.catalog_page.refresh_list(), on_finished=lambda: self._update_top_buttons())


    def show_info(self, version=1.0, ID=None):
        QMessageBox.information(self, "À propos", f"Créé par LECHAT Jérôme \nVersion : {version}\nID : {ID}")
    
    def show_ticket(self):
        TicketService(self.USERconfig, parent=self).exec()
    
    def show_github(self):
        QDesktopServices.openUrl(QUrl("https://github.com/jejeAKAgg/FG-ToolWatcher"))


    def _update_top_buttons(self):
        current_index = self.stack.currentIndex()
        current_page = self.stack.widget(current_index)

        if current_page == self.settings_page:
            self.settings_button.setEnabled(True)
            self.settings_button.setText("Menu")
            self.update_button.setEnabled(False)
            self.profile_button.setEnabled(False)
        elif current_page == self.setup_page:
            self.settings_button.setEnabled(False)
            self.settings_button.setText("")
            self.update_button.setEnabled(False)
            self.profile_button.setEnabled(False)
        elif current_page == self.profile_page:
            if self.USERconfig.get("user_mail"):
                self.settings_button.setEnabled(True)
                self.settings_button.setText("Menu")
                self.update_button.setEnabled(False)
                self.profile_button.setEnabled(False)
            else:
                self.settings_button.setEnabled(False)
                self.settings_button.setText("")
                self.update_button.setEnabled(False)
                self.profile_button.setEnabled(False)
        elif current_page == self.main_page:
            self.settings_button.setEnabled(True)
            self.settings_button.setText("")
            self.update_button.setEnabled(True)
            self.profile_button.setEnabled(True)
        elif current_page == self.catalog_page:
            self.settings_button.setEnabled(True)
            self.settings_button.setText("Menu")
            self.update_button.setEnabled(False)
            self.profile_button.setEnabled(False)
        else:
            self.update_button.setEnabled(True)
            self.settings_button.setText("")
            self.profile_button.setEnabled(True)
            self.settings_button.setEnabled(True)




if __name__ == "__main__":
    
    # Initializing the application GUI
    app = QApplication(sys.argv)
    window = WatcherGUI()
    window.show()

    # Initializing the logging system
    log_manager = LogService()
    if log_manager.init_logging():
        LogService.logger("WatcherGUI").info("GUI application starting.")
    
    sys.exit(app.exec())